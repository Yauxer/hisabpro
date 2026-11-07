"""Annulation de règlement et TVA sur encaissements : pas de réécriture des périodes passées.

PostgreSQL nonce et données fictives uniquement.
"""
from contextlib import closing
from decimal import Decimal as D
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from test_compensations_tva953_isole import (  # noqa: F401
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, dossier, ok, core,
)
from postgres_isole import cluster_isole, verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]


def tva(api, mois, cle):
    r = ok(api.get('/api/tva/declaration', params={'exercice': 2025, 'mois': mois}))
    return D(str(r[cle]['total'])), r


def jeu(api, app, nature, comptabiliser=True):
    _, tiers, banque = dossier(api, app, 'encaissement', 'client' if nature == 'vente' else 'fournisseur')
    f = ok(api.post('/api/factures', json={'type': nature, 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
        'date': '2025-01-10', 'reference': 'ANN957', 'lignes': [{'description': 'Service ANN957',
        'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
    ok(api.post(f'/api/factures/{f["id"]}/valider'))
    e = ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))
    ok(api.post(f'/api/ecritures/{e["ecriture_id"]}/valider'))
    r = ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'], 'date': '2025-01-20',
        'montant': 1200, 'mode': 'virement', 'compte_bancaire_id': banque['id'],
        'comptabiliser': comptabiliser}), 201)
    return f, r


@pytest.mark.parametrize('nature', ['vente', 'achat'])
def test_957_annulation_ulterieure_regularisee_dans_sa_periode(application, nature):
    cle = 'collectee' if nature == 'vente' else 'recuperable'
    with closing(client(application)[0]) as api:
        f, r = jeu(api, application, nature)
        assert tva(api, 1, cle)[0] == 200
        ok(api.post(f'/api/reglements/{r["id"]}/annuler', json={'date_annulation': '2025-03-05', 'motif': 'Erreur ANN957'}))
        assert tva(api, 1, cle)[0] == 200
        assert tva(api, 2, cle)[0] == 0
        assert tva(api, 3, cle)[0] == -200
        with application['engine'].connect() as db:
            assert str(db.scalar(text('SELECT date_annulation_effective FROM reglements WHERE id=:i'), {'i': r['id']})) == '2025-03-05'
        assert ok(api.get(f'/api/factures/{f["id"]}/reglements'))['solde_restant'] == 1200


def test_957_annulation_meme_periode_neutre(application):
    with closing(client(application)[0]) as api:
        _, r = jeu(api, application, 'vente')
        ok(api.post(f'/api/reglements/{r["id"]}/annuler', json={'date_annulation': '2025-01-25'}))
        assert tva(api, 1, 'collectee')[0] == 0 and tva(api, 2, 'collectee')[0] == 0


def test_957_historique_sans_date_lu_par_contrepassation_sinon_signale(application):
    with closing(client(application)[0]) as api:
        _, r = jeu(api, application, 'vente')
        ok(api.post(f'/api/reglements/{r["id"]}/annuler', json={'date_annulation': '2025-03-05'}))
        with application['engine'].begin() as db:
            db.execute(text('UPDATE reglements SET date_annulation_effective=NULL WHERE id=:i'), {'i': r['id']})
        assert tva(api, 1, 'collectee')[0] == 200 and tva(api, 3, 'collectee')[0] == -200
        # Sans écriture de contrepassation : aucune date n'est inventée, l'alerte est visible.
        _, r2 = jeu(api, application, 'vente', comptabiliser=False)
        ok(api.post(f'/api/reglements/{r2["id"]}/annuler', json={'date_annulation': '2025-03-06'}))
        with application['engine'].begin() as db:
            db.execute(text('UPDATE reglements SET date_annulation_effective=NULL WHERE id=:i'), {'i': r2['id']})
        _, detail = tva(api, 1, 'collectee')
        assert any('date d\'annulation inconnue' in a for a in detail['alertes'])


def test_957_migration127_rejouable_et_contrainte():
    with cluster_isole() as c:
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        engine = create_engine(c['url'])
        try:
            with engine.begin() as db:
                db.execute(text("CREATE TABLE public.reglements(id integer primary key, statut text, date date)"))
                db.execute(text("INSERT INTO public.reglements VALUES(1,'annule','2025-01-20'),(2,'complet','2025-01-21')"))
            script = (ROOT / 'hisabpro-backend/127_reglements_annulation_effective.sql').read_text(encoding='utf8')
            for _ in range(2):
                raw = engine.raw_connection()
                try:
                    raw.autocommit = True
                    with raw.cursor() as cur:
                        cur.execute(script)
                finally:
                    raw.close()
            with engine.connect() as db:
                assert db.execute(text('SELECT count(*) FROM reglements WHERE date_annulation_effective IS NULL')).scalar() == 2
            with pytest.raises(DBAPIError):
                with engine.begin() as db:
                    db.execute(text("UPDATE reglements SET date_annulation_effective='2025-03-01' WHERE id=2"))
            with engine.begin() as db:
                db.execute(text("UPDATE reglements SET date_annulation_effective='2025-03-01' WHERE id=1"))
            with pytest.raises(DBAPIError):
                with engine.begin() as db:
                    db.execute(text("UPDATE reglements SET date_rejet_effective='2025-03-01' WHERE id=2"))
            with engine.begin() as db:
                db.execute(text("UPDATE reglements SET statut='rejete', date_rejet_effective='2025-03-01' WHERE id=2"))
        finally:
            engine.dispose()
