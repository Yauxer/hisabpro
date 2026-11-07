"""Factures sources : référence fournisseur et RAS distincte, PG nonce."""
from contextlib import closing
from datetime import date, timedelta
import uuid
import pytest
from sqlalchemy import text
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier
from test_journal_liberation_reglement_source_isole import preparer, etat
from test_reglement_comptabilisation_concurrente_isole import metier
from test_multi_societes_runtime_isole import ok
from test_contrepassation_concurrente_isole import original


def factures(api):
    return ok(api.get('/api/factures', params={'exercice': date.today().year}))


def source(app, fid):
    with app['engine'].connect() as c:
        f = c.execute(text('SELECT societe_id,numero,reference,type FROM factures WHERE id=:i'), {'i': fid}).one()
        ref = f.reference or f.numero if f.type == 'achat' else f.numero
        ids = c.execute(text("SELECT id FROM ecritures WHERE societe_id=:s AND source='facture' AND reference=:r ORDER BY id"), {'s': f.societe_id, 'r': ref}).scalars().all()
        return ids


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_facture_suppression_puis_regeneration_sans_touch_reglements(application, sens):
    with closing(client(application)[0]) as api:
        fids, _, rows = preparer(api, sens)
        avant = etat(application, rows);eid = source(application, fids[0])[0]
        assert api.delete(f'/api/ecritures/{eid}').status_code == 204
        regs, fs = etat(application, rows)
        assert regs == avant[0] and not fs[0].est_comptabilisee and fs[1] == avant[1][1]
        nouvel = ok(api.post(f'/api/factures/{fids[0]}/comptabiliser', json={}))['ecriture_id']
        assert nouvel != eid and source(application, fids[0]) == [nouvel]
        assert etat(application, rows) == avant


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_ras_historique_comptabilisee_separement_reste_intacte(application, sens):
    with closing(client(application)[0]) as api:
        tid, fids, p = dossier(api, sens, ras=10)
        f = next(x for x in factures(api) if x['id'] == fids[0])
        paiement = ok(api.post('/api/reglements', json={'facture_id': f['id'],
            'tiers': f['tiers'], 'date': p['date'], 'montant': 110, 'mode': 'virement'}), 201)
        ref = f['reference'] or f['numero'] if sens == 'achat' else f['numero']
        ls = ([{'compte': '3453', 'debit': 10}, {'compte': '3421', 'credit': 10, 'tiers_id': tid}]
              if sens == 'vente' else [{'compte': '4411', 'debit': 10, 'tiers_id': tid}, {'compte': '4457', 'credit': 10}])
        od = ok(api.post('/api/ecritures', json={'date': p['date'], 'journal': 'OD',
            'reference': ref, 'libelle': f"Retenue à la source — {f['numero']} {f['tiers']}", 'lignes': ls}), 201)['id']
        # Historique fictif, créé dans le seul bac nonce. Le marqueur est posé
        # sur un brouillon avant sa validation réelle ; aucun définitif réécrit.
        c = application['cluster']
        from postgres_isole import verifier_cible_isolee
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        with application['engine'].begin() as db:
            assert db.execute(text("UPDATE ecritures SET source='reglement' WHERE id=:i AND NOT est_validee"), {'i': od}).rowcount == 1
            db.execute(text('UPDATE factures SET ras_comptabilisee=true WHERE id=:i'), {'i': f['id']})
        ok(api.post(f'/api/ecritures/{od}/valider', json={}))
        avant = original(application, od)
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['montant_ras_impute'] == 10
        eid = source(application, f['id'])[0]
        assert api.delete(f'/api/ecritures/{eid}').status_code == 204
        with application['engine'].connect() as db:
            assert db.execute(text('SELECT est_comptabilisee,ras_comptabilisee FROM factures WHERE id=:i'), {'i': f['id']}).one() == (False, True)
        assert original(application, od) == avant
        situation = ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert situation['montant_ras_impute'] == 10 and situation['solde_restant'] == 0
        ok(api.post(f"/api/factures/{f['id']}/comptabiliser", json={}))
        assert original(application, od) == avant
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['montant_ras_impute'] == 10
        assert paiement['est_comptabilisee']


def creer_achat(api, tid, nom, ref, montant=100):
    f = ok(api.post('/api/factures', json={'type': 'achat', 'date': date.today().isoformat(),
        'tiers': nom, 'tiers_id': tid, 'reference': ref, 'lignes': [
            {'description': 'Service fictif536', 'quantite': 1, 'prix_unitaire': montant, 'tva': 20}]}), 201)
    ok(api.post(f"/api/factures/{f['id']}/valider", json={}))
    eid = ok(api.post(f"/api/factures/{f['id']}/comptabiliser", json={}))['ecriture_id']
    return f, eid


@pytest.mark.parametrize('indice', [0, 1])
def test_meme_reference_de_deux_fournisseurs_respecte_auxiliaire(application, indice):
    with closing(client(application)[0]) as api:
        ref = 'REFERENCE-COMMUNE-'+uuid.uuid4().hex[:8];docs=[]
        for i in (0, 1):
            nom = f'Fournisseur fictif536 {i}'
            tid = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur'}), 201)['id']
            docs.append(creer_achat(api, tid, nom, ref, montant=(i+1)*100))
        assert api.delete(f'/api/ecritures/{docs[indice][1]}').status_code == 204
        flags = {f['id']: f['est_comptabilisee'] for f in factures(api)}
        assert not flags[docs[indice][0]['id']] and flags[docs[1-indice][0]['id']]


@pytest.mark.parametrize('prefixe', ['AM-', 'ACQ-'])
def test_reference_fournisseur_ne_change_pas_origine_de_la_piece(application, prefixe):
    with closing(client(application)[0]) as api:
        nom = 'Fournisseur préfixe fictif536'
        tid = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur'}), 201)['id']
        f, eid = creer_achat(api, tid, nom, prefixe+'REFERENCE-FICTIVE536')
        assert api.delete(f'/api/ecritures/{eid}').status_code == 204
        assert not next(x for x in factures(api) if x['id'] == f['id'])['est_comptabilisee']


def test_reference_fournisseurs_sans_auxiliaire_ambigue_refuse_sans_choix_arbitraire(application):
    with closing(client(application)[0]) as api:
        docs = []
        for i in (0, 1):
            nom = f'Fournisseur historique fictif536 {i}'
            tid = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur'}), 201)['id']
            docs.append(creer_achat(api, tid, nom, 'AMBIGUE-FICTIVE536', montant=(i+1)*100))
        # Le doublon chez un même fournisseur est déjà refusé par l'API.
        # Ici deux fournisseurs distincts sont légitimes ; seul l'auxiliaire
        # du brouillon manque dans cet historique synthétique isolé.
        c = application['cluster']
        from postgres_isole import verifier_cible_isolee
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        with application['engine'].begin() as db:
            assert db.scalar(text('SELECT NOT est_validee FROM ecritures WHERE id=:i'), {'i': docs[0][1]})
            db.execute(text('UPDATE lignes_ecriture SET tiers_id=NULL,nature_auxiliaire=NULL,compte_auxiliaire_snapshot=NULL,libelle_auxiliaire_snapshot=NULL WHERE ecriture_id=:i'), {'i': docs[0][1]})
        avant = metier(application)
        reponse = api.delete(f'/api/ecritures/{docs[0][1]}')
        assert reponse.status_code == 409, reponse.text
        assert metier(application) == avant


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('reference', ['RENOMMEE-SANS-LIEN-FICTIVE536', ''])
def test_reference_facture_renommee_ou_vide_retrouve_origine_auditee(application, sens, reference):
    with closing(client(application)[0]) as api:
        fids, _, rows = preparer(api, sens)
        eid = source(application, fids[0])[0]
        ok(api.patch(f'/api/ecritures/{eid}', json={'reference': reference}))
        avant = etat(application, rows)
        reponse = api.delete(f'/api/ecritures/{eid}')
        assert reponse.status_code == 204, reponse.text
        regs, fs = etat(application, rows)
        assert regs == avant[0] and not fs[0].est_comptabilisee and fs[1] == avant[1][1]
        ok(api.post(f'/api/factures/{fids[0]}/comptabiliser', json={}))


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_reference_renommee_vers_autre_facture_ne_libere_pas_la_mauvaise(application, sens):
    with closing(client(application)[0]) as api:
        fids, _, rows = preparer(api, sens)
        fs = {f['id']: f for f in factures(api)}
        autre_ref = fs[fids[1]]['reference'] if sens == 'achat' else fs[fids[1]]['numero']
        eid = source(application, fids[0])[0]
        ok(api.patch(f'/api/ecritures/{eid}', json={'reference': autre_ref}))
        assert api.delete(f'/api/ecritures/{eid}').status_code == 204
        regs, flags = etat(application, rows)
        assert not flags[0].est_comptabilisee and flags[1].est_comptabilisee
        assert all(r.est_comptabilisee for r in regs)


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_date_source_modifiee_refuse_sans_reaffectation_implicite(application, sens):
    with closing(client(application)[0]) as api:
        fids, _, _ = preparer(api, sens)
        eid = source(application, fids[0])[0]
        ok(api.patch(f'/api/ecritures/{eid}', json={'date': (date.today()-timedelta(days=1)).isoformat()}))
        avant = metier(application)
        reponse = api.delete(f'/api/ecritures/{eid}')
        assert reponse.status_code == 409, reponse.text
        assert metier(application) == avant
