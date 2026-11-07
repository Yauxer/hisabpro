"""Suppression Journal : seul le document réellement lié est libéré, PG nonce."""
from contextlib import closing
from datetime import date
import pytest
from sqlalchemy import text
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier, poster
from test_reglement_comptabilisation_concurrente_isole import metier, comptabiliser
from test_reglement_annulation_source_isole import annuler
from test_multi_societes_runtime_isole import ok


def preparer(api, sens):
    _, fids, p = dossier(api, sens)
    rows = ok(poster(api, p), 201)
    return fids, p, rows


def etat(app, rows):
    with app['engine'].connect() as c:
        sid = c.scalar(text('SELECT societe_id FROM reglements WHERE id=:i'), {'i': rows[0]['id']})
        regs = c.execute(text('SELECT id,est_comptabilisee,ecriture_id,statut,ecriture_annulation_id FROM reglements WHERE societe_id=:s ORDER BY id'), {'s': sid}).all()
        fs = c.execute(text('SELECT id,numero,est_comptabilisee FROM factures WHERE societe_id=:s ORDER BY id'), {'s': sid}).all()
        return regs, fs


def verifier_liberation(app, api, rows, indice, avant):
    apres, fs = etat(app, rows)
    assert fs == avant[1]
    for old, new in zip(avant[0], apres):
        if old.id == rows[indice]['id']:
            assert not new.est_comptabilisee and new.ecriture_id is None
            assert new.statut == old.statut
        else:
            assert new == old
    ok(comptabiliser(api, rows[indice]['id']))
    fin, fs = etat(app, rows)
    assert fs == avant[1]
    for old, new in zip(avant[0], fin):
        if old.id == rows[indice]['id']:
            assert new.est_comptabilisee and new.ecriture_id and new.ecriture_id != old.ecriture_id
        else:
            assert new == old


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('indice', [0, 1])
def test_reference_bancaire_partagee_libere_le_bon_reglement(application, sens, indice):
    with closing(client(application)[0]) as api:
        _, _, rows = preparer(api, sens)
        avant = etat(application, rows)
        assert api.delete(f"/api/ecritures/{rows[indice]['ecriture_id']}").status_code == 204
        verifier_liberation(application, api, rows, indice, avant)


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('reference', ['facture', 'autre_reglement', 'renommee'])
def test_lien_natif_prioritaire_sur_reference_renommee_ou_en_collision(application, sens, reference):
    with closing(client(application)[0]) as api:
        _, _, rows = preparer(api, sens)
        avant = etat(application, rows)
        ref = avant[1][0].numero if reference == 'facture' else (
            'REG-'+str(rows[0]['id']) if reference == 'autre_reglement' else 'RENOMMEE-FICTIVE534')
        ok(api.patch(f"/api/ecritures/{rows[1]['ecriture_id']}", json={'reference': ref}))
        assert api.delete(f"/api/ecritures/{rows[1]['ecriture_id']}").status_code == 204
        verifier_liberation(application, api, rows, 1, avant)


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('reference', ['facture', 'banque'])
def test_piece_manuelle_de_meme_reference_ne_libere_aucun_document(application, sens, reference):
    with closing(client(application)[0]) as api:
        _, p, rows = preparer(api, sens)
        avant = etat(application, rows)
        ref = avant[1][0].numero if reference == 'facture' else p['reference']
        eid = ok(api.post('/api/ecritures', json={'date': date.today().isoformat(),
            'journal': 'OD', 'reference': ref, 'libelle': 'Manuelle fictive534',
            'lignes': [{'compte': '5141', 'debit': 10}, {'compte': '4481', 'credit': 10}]}), 201)['id']
        assert api.delete(f'/api/ecritures/{eid}').status_code == 204
        assert etat(application, rows) == avant


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_correction_liee_a_annulation_ne_peut_pas_disparaitre(application, sens):
    with closing(client(application)[0]) as api:
        _, _, rows = preparer(api, sens)
        ok(api.post(f"/api/ecritures/{rows[0]['ecriture_id']}/valider", json={}))
        annulation = ok(annuler(api, rows[0]['id']))
        cid = annulation['ecriture_annulation_id']
        avant = metier(application)
        reponse = api.delete(f'/api/ecritures/{cid}')
        assert reponse.status_code == 409, reponse.text
        assert metier(application) == avant


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_source_liee_a_deux_reglements_refusee_atomiquement(application, sens):
    with closing(client(application)[0]) as api:
        _, _, rows = preparer(api, sens)
        c = application['cluster']
        from postgres_isole import verifier_cible_isolee
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        with application['engine'].begin() as db:
            db.execute(text('UPDATE reglements SET ecriture_id=:e WHERE id=:i'),
                {'e': rows[0]['ecriture_id'], 'i': rows[1]['id']})
        avant = metier(application)
        reponse = api.delete(f"/api/ecritures/{rows[0]['ecriture_id']}")
        assert reponse.status_code == 409, reponse.text
        assert metier(application) == avant


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('cas', ['unique', 'ambigu', 'montant', 'origine_annulee'])
def test_historique_sans_lien_et_origine_annulee(application, sens, cas):
    with closing(client(application)[0]) as api:
        _, _, rows = preparer(api, sens)
        eid = rows[0]['ecriture_id']
        if cas == 'origine_annulee':
            ok(annuler(api, rows[0]['id']))
        else:
            c = application['cluster']
            from postgres_isole import verifier_cible_isolee
            assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
            with application['engine'].begin() as db:
                ids = [r['id'] for r in rows] if cas == 'ambigu' else [rows[0]['id']]
                db.execute(text('UPDATE reglements SET ecriture_id=NULL WHERE id=ANY(:ids)'), {'ids': ids})
            if cas == 'montant':
                collectif = '3421' if sens == 'vente' else '4411'
                lignes = [{'compte': '5141', 'debit': 60}, {'compte': collectif, 'credit': 60}] if sens == 'vente' else [
                    {'compte': collectif, 'debit': 60}, {'compte': '5141', 'credit': 60}]
                ok(api.patch(f'/api/ecritures/{eid}', json={'lignes': lignes}))
        avant = metier(application)
        reponse = api.delete(f'/api/ecritures/{eid}')
        assert reponse.status_code == (204 if cas == 'unique' else 409), reponse.text
        if cas == 'unique':
            regs, _ = etat(application, rows)
            assert not regs[0].est_comptabilisee and regs[0].ecriture_id is None
            assert regs[1].est_comptabilisee and regs[1].ecriture_id == rows[1]['ecriture_id']
            ok(comptabiliser(api, rows[0]['id']))
        else:
            assert metier(application) == avant
