"""Lecture PostgreSQL nonce et rendu PDF réel, sans base utilisateur."""
from datetime import date
from decimal import Decimal
from io import BytesIO
import json
import re
import uuid
from types import SimpleNamespace

import pytest
from pypdf import PdfReader
from sqlalchemy.orm import Session
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from contextlib import closing

import models
from services.livre_inventaire_service import _stocks
from services.livre_inventaire_pdf import generer_livre_inventaire_pdf, _mad, _quantite


@pytest.fixture
def stock_db(application):
    cluster = application['cluster']
    verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
    with closing(client(application)[0]) as api, Session(application['engine']) as db:
        response = api.get('/api/societe/moi')
        assert response.status_code == 200, response.text
        sid = response.json()['id']
        article = models.Article(societe_id=sid, code='STOCK-'+uuid.uuid4().hex[:10], designation='Stock fictif',
            stock_actuel=10, cmup=20, actif=True, is_stockable=True)
        db.add(article)
        db.commit()
        yield db, article


@pytest.mark.parametrize('champ,valeur', [('stock_actuel', None), ('cmup', None),
    ('cmup', float('inf')), ('cmup', -1), ('stock_actuel', float('inf')),
    ('stock_actuel', float('nan')), ('cmup', 1e308)])
def test_livre_sources_inconnues_diagnostiquees_sans_reparation(stock_db, champ, valeur):
    db, article = stock_db
    setattr(article, champ, valeur)
    db.commit()
    before = (repr(article.stock_actuel), repr(article.cmup))
    result = _stocks(db, article.societe_id, date(2026, 12, 31), {})
    assert result['valorisation_complete'] is False
    assert result['valeur_physique'] is None and result['ecart_physique_comptable'] is None
    assert result['lignes'][0]['valeur'] is None and result['diagnostics']
    json.dumps(result, allow_nan=False)
    db.refresh(article)
    assert (repr(article.stock_actuel), repr(article.cmup)) == before
    assert db.query(models.InventaireStock).filter_by(societe_id=article.societe_id).count() == 0


def test_livre_valeur_connue_cmup_precision_et_zero(stock_db):
    db, article = stock_db
    article.cmup = 20.1234
    db.commit()
    result = _stocks(db, article.societe_id, date(2026, 12, 31), {'3111': Decimal('201.23')})
    assert result['valeur_physique'] == 201.23 and result['ecart_physique_comptable'] == 0
    assert result['lignes'][0]['cmup'] == 20.1234
    assert result['valorisation_complete'] is True and result['diagnostics'] == []
    article.cmup = 0
    db.commit()
    zero = _stocks(db, article.societe_id, date(2026, 12, 31), {})
    assert zero['valeur_physique'] == 0 and zero['valorisation_complete'] is True


def test_livre_grande_valeur_finie_sans_limite_arbitraire(stock_db):
    db, article = stock_db
    article.cmup = 1e307
    db.commit()
    result = _stocks(db, article.societe_id, date(2026, 12, 31), {})
    assert result['valeur_physique'] == 1e308
    assert result['ecart_physique_comptable'] == 1e308
    assert result['valorisation_complete'] is True
    json.dumps(result, allow_nan=False)


def test_snapshot_historique_cout_non_fini_ne_devient_pas_zero(stock_db):
    db, article = stock_db
    inv = models.InventaireStock(societe_id=article.societe_id, exercice=2026,
        date_inventaire=date(2026, 12, 31), reference='INV-FICTIF', total_valeur=160)
    db.add(inv); db.flush()
    line = models.InventaireStockLigne(inventaire_id=inv.id, article_id=article.id,
        code=article.code, designation=article.designation, quantite_reelle=8,
        quantite_theorique=10, ecart_quantite=-2, cmup=20, valeur_stock=160,
        valeur_ecart=-40, compte_stock='3111', compte_variation='6114')
    db.add(line); db.commit()
    line.cmup = Decimal('NaN')
    db.commit()
    before = tuple(map(str, (line.cmup, line.valeur_stock, inv.total_valeur)))
    result = _stocks(db, article.societe_id, date(2026, 12, 31), {'3111': Decimal('160')})
    assert result['inventaire_valide'] is True and result['valorisation_complete'] is False
    assert result['lignes'][0]['cmup'] is None and result['lignes'][0]['valeur'] == 160
    assert result['valeur_physique'] is None and result['ecart_physique_comptable'] is None
    db.refresh(line); db.refresh(inv)
    assert tuple(map(str, (line.cmup, line.valeur_stock, inv.total_valeur))) == before


@pytest.mark.parametrize('nombre', [None, float('nan'), float('inf'), -float('inf'), True, 'absent'])
def test_pdf_nombres_inconnus_ne_deviennent_pas_zero(nombre):
    assert _mad(nombre) == _quantite(nombre) == 'À vérifier'


def test_pdf_reel_inventaire_incomplet_lisible():
    snapshot = {'exercice': {'annee': 2026, 'date_debut': '2026-01-01',
        'date_fin': '2026-12-31', 'statut': 'ouvert'}, 'bilan': {}, 'cpc': {},
        'stocks': {'valorisation_complete': False, 'valeur_physique': None,
            'ecart_physique_comptable': None, 'valeur_comptable_brute': 0,
            'depreciations': 0, 'valeur_comptable_nette': 0,
            'diagnostics': [{'code': 'FICTIF', 'message': 'CMUP absent'}],
            'lignes': [{'code': 'FICTIF', 'designation': 'Article fictif',
                'quantite': None, 'cmup': None, 'valeur': None}]}}
    pdf = generer_livre_inventaire_pdf(SimpleNamespace(raison_sociale='Recette fictive'), snapshot)
    reader = PdfReader(BytesIO(pdf))
    text = '\n'.join(p.extract_text() for p in reader.pages)
    assert len(reader.pages) >= 2 and 'CMUP absent' in text
    assert 'À vérifier' in text and 'Valorisation du stock à vérifier' in text
    assert re.search(r'\b(?:nan|[+-]?inf(?:inity)?)\b', text.lower()) is None
    assert _mad(0) == '0,00' and _quantite(0) == '0'
