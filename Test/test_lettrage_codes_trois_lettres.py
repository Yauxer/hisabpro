"""Nouveaux codes >=3 lettres, conservation des historiques, PG isolé."""
from datetime import date

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import models
from lettrage import _code_depuis_set
from test_e2e_facturation_isole import application
from test_e2e_recouvrement_isole import dossier_synthetique


@pytest.mark.parametrize('codes,attendu', [(set(), 'AAA'), ({'A', 'AA'}, 'AAA'),
    ({'A', 'AAA', 'AAB'}, 'AAC'), ({'AAA', 'AAB', 'AAC'}, 'AAD')])
def test_generateur_commence_par_trois_lettres_sans_recycler(codes, attendu):
    avant = codes.copy()
    assert _code_depuis_set(codes) == attendu
    assert codes == avant


@pytest.mark.parametrize('code', ['A', 'AB', 'AAA', None])
def test_api_nouveaux_codes_et_historique_court(application, code):
    dossier = dossier_synthetique(application)
    with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer ' + dossier['token']}) as api:
        response = api.post(f"/api/factures/{dossier['fid']}/comptabiliser")
        assert response.status_code == 200, response.text
        response = api.post('/api/reglements', json={'facture_id': dossier['fid'], 'tiers': dossier['nom'],
            'date': date.today().isoformat(), 'montant': 1200, 'mode': 'virement', 'comptabiliser': True})
        assert response.status_code == 201, response.text
        with Session(application['engine']) as db:
            sid = db.get(models.Facture, dossier['fid']).societe_id
            eids = [e.id for e in db.query(models.Ecriture).filter_by(societe_id=sid).all()]
        for eid in eids:
            assert api.post(f'/api/ecritures/{eid}/valider').status_code == 200
        response = api.get('/api/lettrage/comptable', params={'exercice': date.today().year, 'compte': '3421'})
        assert response.status_code == 200, response.text
        ids = [r['ligne_id'] for r in response.json()]
        assert len(ids) == 2
        def source():
            with application['engine'].connect() as db:
                return db.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l '
                    'JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid ORDER BY l.id'), {'sid': sid}).all()
        avant = source()
        response = api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': ids, 'code': code})
        if code in ('A', 'AB'):
            assert response.status_code == 400, response.text
            assert source() == avant
            assert all(r['code_lettrage'] is None for r in api.get('/api/lettrage/comptable', params={
                'exercice': date.today().year, 'compte': '3421'}).json())
        else:
            assert response.status_code == 200, response.text
            assert response.json()['code'] == 'AAA'
            assert source() == avant
            relecture = api.get('/api/lettrage/comptable', params={'exercice': date.today().year, 'compte': '3421'}).json()
            assert {r['code_lettrage'] for r in relecture} == {'AAA'}
