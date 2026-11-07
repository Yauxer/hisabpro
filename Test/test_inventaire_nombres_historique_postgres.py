"""Inventaire historique : lectures sûres et refus avant mutation, PG nonce."""
import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from contextlib import closing
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import models
from services.inventaire_nombres_service import projection_article, projection_snapshot_ligne, somme
from test_e2e_facturation_isole import application
from test_articles_stock_historique_lecture import dossier
from test_ras_lecture_conservation import client


def photo(application):
    with application['engine'].connect() as db:
        return {t: db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t ORDER BY id')).scalars().all()
                for t in ('articles', 'mouvements_stock', 'ecritures', 'lignes_ecriture',
                          'inventaires_stock', 'inventaires_stock_lignes')}


def article(api):
    r = api.post('/api/articles', json={'code': 'INV-'+uuid.uuid4().hex[:10],
        'designation': 'Inventaire fictif', 'stock_actuel': 0, 'prix_achat_ht': 20})
    assert r.status_code == 201, r.text
    return r.json()['id']


@pytest.mark.parametrize('champ,valeur', [('stock_actuel', None), ('stock_actuel', float('nan')),
    ('stock_actuel', float('inf')), ('cmup', None), ('cmup', float('nan')),
    ('cmup', float('inf')), ('cmup', -1), ('cmup', 1e308)])
def test_lecture_et_comptage_invalides_sans_mutation(application, dossier, champ, valeur):
    api, sid = dossier
    aid = article(api)
    with application['engine'].begin() as db:
        db.execute(text('UPDATE articles SET stock_actuel=10, cmup=20 WHERE id=:id'), {'id': aid})
        db.execute(text(f'UPDATE articles SET {champ}=:v WHERE id=:id AND societe_id=:sid'),
                   {'v': valeur, 'id': aid, 'sid': sid})
    avant = photo(application)
    r = api.get('/api/inventaire/feuille')
    assert r.status_code == 200, r.text
    ligne = next(l for l in r.json() if l['article_id'] == aid)
    assert ligne['valeur_theorique'] is None and ligne['nombres_diagnostics']
    r = api.get('/api/inventaire/valorisation')
    assert r.status_code == 200, r.text
    assert r.json()['total_valeur'] is None and r.json()['valorisation_complete'] is False
    r = api.get(f'/api/inventaire/historique/{aid}')
    assert r.status_code == 200, r.text
    assert r.json()['article']['valeur'] is None
    # Même quantité : la branche écart nul ne peut figer un coût inconnu.
    payload = {'date': '2026-06-30', 'lignes': [{'article_id': aid, 'quantite_reelle': 10}]}
    r = api.post('/api/inventaire/simuler', json=payload)
    assert r.status_code == 400, r.text
    r = api.post('/api/inventaire/valider', json=payload)
    assert r.status_code == 409, r.text
    assert photo(application) == avant


def test_oracle_comptage_stock10_cout20_reel8(application, dossier):
    api, sid = dossier
    aid = article(api)
    with application['engine'].begin() as db:
        db.execute(text('UPDATE articles SET stock_actuel=10, cmup=20 WHERE id=:id'), {'id': aid})
    payload = {'date': '2026-06-30', 'reference': 'ORACLE-'+uuid.uuid4().hex[:10],
               'lignes': [{'article_id': aid, 'quantite_reelle': 8}]}
    r = api.post('/api/inventaire/simuler', json=payload)
    assert r.status_code == 200, r.text
    assert r.json()['total_perte'] == 40 and r.json()['valeur_stock_compte'] == 160
    r = api.post('/api/inventaire/valider', json=payload)
    assert r.status_code == 200, r.text
    assert r.json()['total_perte'] == 40 and r.json()['total_valeur'] == 160
    historique = api.get(f'/api/inventaire/historique/{aid}').json()
    assert historique['article']['stock'] == 8 and historique['article']['valeur'] == 160
    assert historique['mouvements'][-1]['valeur'] == 40
    assert historique['mouvements'][-1]['type'] == 'correction'


@pytest.mark.parametrize('valeur', [None, float('nan'), float('inf'), float('-inf'), -1, True])
def test_projection_cout_inconnu_memes_sources_intactes(valeur):
    a = SimpleNamespace(stock_actuel=10, cmup=valeur)
    p = projection_article(a)
    assert p['cmup'] is None and p['valeur'] is None and 'cmup' in p['nombres_diagnostics']
    assert a.cmup is valeur


def test_projection_connue_signee_zero_et_total_depassant_float():
    assert projection_article(SimpleNamespace(stock_actuel=-2, cmup=20))['valeur'] == -40
    assert projection_article(SimpleNamespace(stock_actuel=10, cmup=0))['valeur'] == 0
    assert projection_article(SimpleNamespace(stock_actuel=10, cmup=20.1234))['valeur'] == 201.23
    diag = {}
    assert somme([1e308, 1e308], 'total', diag) is None and diag
    # Une ancienne photographie conserve sa valeur, sans la recalculer.
    p = projection_snapshot_ligne(SimpleNamespace(quantite_reelle=10, cmup=20, valeur_stock=199))
    assert p['valeur'] == 199 and p['nombres_diagnostics'] == {}


def test_mouvements_historique_non_finis_lisibles_et_societe_isolee(application, dossier):
    api, sid = dossier
    aid = article(api)
    with Session(application['engine']) as db:
        db.add(models.MouvementStock(societe_id=sid, article_id=aid, type='entree',
            quantite=float('nan'), stock_avant=float('inf'), stock_apres=10,
            cout_unitaire=None, cmup_apres=-1, date_mouvement=date(2026, 6, 30)))
        db.commit()
    with application['engine'].begin() as db:
        db.execute(text('UPDATE mouvements_stock SET cout_unitaire=NULL WHERE article_id=:id'), {'id': aid})
    avant = photo(application)
    r = api.get(f'/api/inventaire/historique/{aid}')
    assert r.status_code == 200, r.text
    m = r.json()['mouvements'][0]
    assert m['quantite'] is None and m['stock_avant'] is None and m['valeur'] is None
    assert m['cout_unitaire'] is None and m['cmup_apres'] is None
    assert len(m['nombres_diagnostics']) == 5
    with closing(client(application)[0]) as autre:
        assert autre.get(f'/api/inventaire/historique/{aid}').status_code == 404
        assert autre.get('/api/inventaire/feuille').json() == []
    # Nouvelle société créée explicitement ; comparaison de la zone comptable.
    assert photo(application) == avant


def test_snapshot_historique_nan_refuse_generation_sans_effacer_brouillon(application, dossier):
    api, sid = dossier
    aid = article(api)
    with Session(application['engine']) as db:
        inv = models.InventaireStock(societe_id=sid, exercice=2026, date_inventaire=date(2026,12,31),
            reference='NAN-'+uuid.uuid4().hex[:10], total_valeur=Decimal('NaN'), total_perte=0, total_excedent=0)
        db.add(inv)
        db.flush()
        db.add(models.InventaireStockLigne(inventaire_id=inv.id, article_id=aid, code='HIST',
            designation='Historique fictif', quantite_theorique=10, quantite_reelle=10,
            cmup=Decimal('NaN'), valeur_stock=200, valeur_ecart=0))
        ec = models.Ecriture(societe_id=sid, exercice=2026, date=date(2026,12,31), journal='OD',
            reference='STOCK-CLOTURE-2026', libelle='Brouillon conservé', est_validee=False,
            lignes=[models.LigneEcriture(compte='3111', libelle='Stock', debit=200, credit=0),
                    models.LigneEcriture(compte='6114', libelle='Variation', debit=0, credit=200)])
        db.add(ec)
        db.commit()
    avant = photo(application)
    r = api.get('/api/inventaire/stock/cloture?exercice=2026')
    assert r.status_code == 200, r.text
    assert r.json()['valorisation_complete'] is False and r.json()['stock_rapproche'] is False
    assert r.json()['valeur_physique_brute'] is None and r.json()['ecart_brut'] is None
    r = api.get('/api/inventaire/inventaires-stock?exercice=2026')
    assert r.status_code == 200, r.text
    assert r.json()[0]['total_valeur'] is None and r.json()[0]['nombres_diagnostics']
    r = api.post('/api/inventaire/comptabiliser-stock?exercice=2026')
    assert r.status_code == 409, r.text
    assert photo(application) == avant


@pytest.mark.parametrize('valeur', [True, False, None, 'invalide'])
def test_quantite_api_non_numerique_refusee_sans_ecriture(application, dossier, valeur):
    api, sid = dossier
    aid = article(api)
    avant = photo(application)
    payload = {'date': '2026-06-30', 'lignes': [{'article_id': aid, 'quantite_reelle': valeur}]}
    for endpoint in ('simuler', 'valider'):
        r = api.post('/api/inventaire/'+endpoint, json=payload)
        assert r.status_code == 422, r.text
    assert photo(application) == avant


@pytest.mark.parametrize('prix,attendu', [(0, 0), (20, 160)])
def test_cmup_zero_connu_preserve_fallback_metier(application, dossier, prix, attendu):
    api, sid = dossier
    aid = article(api)
    with application['engine'].begin() as db:
        db.execute(text('UPDATE articles SET stock_actuel=10, cmup=0, prix_achat_ht=:p WHERE id=:id'),
                   {'p': prix, 'id': aid})
    payload = {'date': '2026-06-30', 'reference': 'ZERO-'+uuid.uuid4().hex[:10],
               'lignes': [{'article_id': aid, 'quantite_reelle': 8}]}
    r = api.post('/api/inventaire/valider', json=payload)
    assert r.status_code == 200, r.text
    assert r.json()['total_valeur'] == attendu
    assert r.json()['total_perte'] == (0 if prix == 0 else 40)


def test_total_depasse_precision_snapshot_refuse_avant_mutation(application, dossier):
    api, sid = dossier
    ids = [article(api), article(api)]
    with application['engine'].begin() as db:
        for aid in ids:
            db.execute(text('UPDATE articles SET stock_actuel=900, cmup=1e13 WHERE id=:id'), {'id': aid})
    avant = photo(application)
    payload = {'date': '2026-06-30', 'lignes': [{'article_id': aid, 'quantite_reelle': 900} for aid in ids]}
    for endpoint, statut in [('simuler', 400), ('valider', 409)]:
        r = api.post('/api/inventaire/'+endpoint, json=payload)
        assert r.status_code == statut, r.text
        assert 'précision' in r.json()['detail']
    assert photo(application) == avant
