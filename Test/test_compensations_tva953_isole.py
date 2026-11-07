"""Compensations signées, historiques inconnus, bornes et migrations sur PG nonce."""
from contextlib import closing
from pathlib import Path
from decimal import Decimal as D
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from test_tva_acomptes945_isole import (
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, dossier, ok, core,
)
from postgres_isole import cluster_isole, verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]


def jeu(api, app, nature='vente', regime='encaissement'):
    sid, tiers, banque = dossier(api, app, regime, 'client' if nature == 'vente' else 'fournisseur')
    fs = []
    for jour in ['2025-01-10', '2025-03-01']:
        f = ok(api.post('/api/factures', json={'type': nature, 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
            'date': jour, 'reference': 'FICTIF953-'+jour, 'lignes': [{'description': 'Service FICTIF953', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
        ok(api.post(f'/api/factures/{f["id"]}/valider'))
        e = ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))
        ok(api.post(f'/api/ecritures/{e["ecriture_id"]}/valider'))
        fs.append(f)
    ok(api.post('/api/reglements', json={'facture_id': fs[0]['id'], 'tiers': tiers['nom'], 'date': '2025-01-10',
        'montant': 1200, 'mode': 'virement', 'compte_bancaire_id': banque['id'], 'comptabiliser': True}), 201)
    a = ok(api.post('/api/avoirs', json={'facture_id': fs[0]['id'], 'date': '2025-02-10', 'motif': 'Retour FICTIF953',
        'lignes': [{'facture_ligne_id': fs[0]['lignes'][0]['id'], 'quantite': 1}]}), 201)
    ok(api.post(f'/api/avoirs/{a["id"]}/comptabiliser'))
    return sid, tiers, fs, a


def imputation(f, **kw):
    return dict({'type_utilisation': 'imputation', 'facture_id': f['id'], 'montant': 600,
        'date_utilisation': '2025-03-15', 'date_acceptation_compensation': '2025-03-15', 'reference': 'REC-COMP953'}, **kw)


def tva(api, mois, nature='collectee'):
    r = ok(api.get('/api/tva/declaration', params={'exercice': 2025, 'mois': mois}))
    return D(str(r[nature]['total'])), r


@pytest.mark.parametrize('nature,regime,attendu', [('vente','encaissement','100'),('vente','debit','200'),('achat','encaissement','100')])
def test_953_compensation_partielle_datee_sans_doublon_et_originaux(application, nature, regime, attendu):
    with closing(client(application)[0]) as api:
        sid, _, fs, a = jeu(api, application, nature, regime); avant = core(application, sid)
        r = ok(api.post(f'/api/avoirs/{a["id"]}/utiliser', json=imputation(fs[1])))
        u = r['utilisations'][-1]
        assert u['date_acceptation_compensation'] == '2025-03-15' and u['reference'] == 'REC-COMP953'
        cle = 'collectee' if nature == 'vente' else 'recuperable'
        assert tva(api, 3, cle)[0] == D(attendu)
        assert tva(api, 4, cle)[0] == 0
        assert tva(api, 1, cle)[0] == 200 and tva(api, 2, cle)[0] == -200
        assert core(application, sid) == avant
        assert ok(api.get(f'/api/factures/{fs[1]["id"]}/reglements'))['solde_restant'] == 600


def test_953_imputation_historique_sans_signature_signalee_non_inventee(application):
    with closing(client(application)[0]) as api:
        sid, _, fs, a = jeu(api, application); avant = core(application, sid)
        r = ok(api.post(f'/api/avoirs/{a["id"]}/utiliser', json=imputation(fs[1], date_acceptation_compensation=None, reference=None)))
        assert r['utilisations'][-1]['date_acceptation_compensation'] is None
        valeur, detail = tva(api, 3)
        assert valeur == 0 and any('accord de compensation non confirmé' in s for s in detail['alertes'])
        assert core(application, sid) == avant
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT date_acceptation_compensation FROM utilisations_avoirs WHERE id=:id'), {'id':r['utilisations'][-1]['id']}) is None


@pytest.mark.parametrize('changement', [
    {'reference': ''}, {'reference': ' '}, {'reference': 'x'*101},
    {'date_acceptation_compensation':'2025-03-14'},
    {'date_acceptation_compensation':'2025-02-01','date_utilisation':'2025-02-01'},
    {'type_utilisation':'remboursement'},
])
def test_953_accord_incomplet_ou_date_incoherente_refuse_sans_mutation(application, changement):
    with closing(client(application)[0]) as api:
        sid, _, fs, a = jeu(api, application); avant = core(application, sid)
        r = api.post(f'/api/avoirs/{a["id"]}/utiliser', json=imputation(fs[1], **changement))
        assert r.status_code == 422, r.text
        assert ok(api.get('/api/avoirs', params={'exercice':2025}))[0]['utilisations'] == []
        assert core(application, sid) == avant and tva(api, 3)[0] == 0


def test_953_annulation_effective_preserve_periode_anterieure(application):
    with closing(client(application)[0]) as api:
        sid, _, fs, a = jeu(api, application)
        r = ok(api.post(f'/api/avoirs/{a["id"]}/utiliser', json=imputation(fs[1])))
        uid = r['utilisations'][-1]['id']; avant = core(application, sid)
        assert api.post(f'/api/avoirs/{a["id"]}/utilisations/{uid}/annuler', params={'date_annulation':'2025-03-14'}).status_code == 422
        assert tva(api, 3)[0] == 100
        r = ok(api.post(f'/api/avoirs/{a["id"]}/utilisations/{uid}/annuler', params={'date_annulation':'2025-04-01'}))
        assert r['utilisations'][-1]['date_annulation_effective'] == '2025-04-01'
        assert tva(api, 3)[0] == 100 and tva(api, 4)[0] == -100
        assert core(application, sid) == avant


def test_953_compensation_inter_societes_refusee(application):
    with closing(client(application)[0]) as a1, closing(client(application)[0]) as a2:
        sid1, _, fs1, av1 = jeu(a1, application)
        sid2, _, fs2, av2 = jeu(a2, application)
        avant1, avant2 = core(application,sid1), core(application,sid2)
        assert a1.post(f'/api/avoirs/{av2["id"]}/utiliser',json=imputation(fs1[1])).status_code == 404
        assert a1.post(f'/api/avoirs/{av1["id"]}/utiliser',json=imputation(fs2[1])).status_code == 404
        assert core(application,sid1)==avant1 and core(application,sid2)==avant2


def test_953_migration126_ancienne_table_rejeu_et_contrainte_sql():
    # Cluster propre minimal : reproduit la table déployée sans les nouvelles colonnes.
    with cluster_isole() as c:
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        engine = create_engine(c['url'])
        try:
            with engine.begin() as db:
                db.execute(text("CREATE TABLE public.utilisations_avoirs(id integer primary key,type_utilisation text,date_utilisation date,reference text)"))
                db.execute(text("INSERT INTO public.utilisations_avoirs VALUES(1,'imputation','2025-03-15',NULL)"))
            script=(ROOT/'hisabpro-backend/126_avoirs_compensations_tva.sql').read_text(encoding='utf8')
            for _ in range(2):
                raw=engine.raw_connection()
                try:
                    raw.autocommit=True
                    with raw.cursor() as cur:cur.execute(script)
                finally:raw.close()
                with engine.connect() as db:
                    r=db.execute(text('SELECT * FROM public.utilisations_avoirs')).one()
                    assert tuple(map(str,r[:3]))==('1','imputation','2025-03-15') and r[3:]==(None,None,None)
            with pytest.raises(DBAPIError):
                with engine.begin() as db:db.execute(text("UPDATE public.utilisations_avoirs SET date_acceptation_compensation='2025-03-15'"))
            with engine.begin() as db:db.execute(text("UPDATE public.utilisations_avoirs SET date_acceptation_compensation='2025-03-15',reference='ACCORD-FICTIF'"))
        finally:engine.dispose()
