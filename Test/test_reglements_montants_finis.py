"""Règlements : montants finis, API réelle et absence de mutations partielles."""
import json

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

import models
import schemas
from test_e2e_facturation_isole import application
from test_e2e_recouvrement_isole import dossier_synthetique


INVALIDES = [float('nan'), float('inf'), -float('inf'), 'NaN', 'Infinity', True, False, {}, [], 'invalide']


@pytest.mark.parametrize('valeur', INVALIDES)
@pytest.mark.parametrize('schema', [schemas.ReglementCreate, schemas.ReglementUpdate])
def test_schema_refuse_montant_non_fini_ou_booleen(schema, valeur):
    payload = {'montant': valeur}
    if schema is schemas.ReglementCreate:
        payload.update(date='2026-05-01', tiers='Tiers fictif')
    with pytest.raises(ValidationError):
        schema(**payload)


def test_schema_conserve_montant_valide_et_patch_notes():
    assert schemas.ReglementCreate(date='2026-05-01', tiers='Fictif', montant='400.25').montant == 400.25
    assert schemas.ReglementUpdate(montant=400.25).montant == 400.25
    assert schemas.ReglementUpdate(notes='Note seule').montant is None


@pytest.mark.parametrize('methode', ['POST', 'PATCH'])
@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), True, {}])
def test_api_refuse_montant_invalide_sans_changer_facture_reglement_ou_ecriture(application, methode, valeur):
    import httpx
    from datetime import date
    dossier = dossier_synthetique(application)
    with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer ' + dossier['token']}) as api:
        url = '/api/reglements'
        payload = {'date': date.today().isoformat(), 'facture_id': dossier['fid'],
                   'tiers': dossier['nom'], 'montant': valeur, 'mode': 'virement', 'comptabiliser': False}
        if methode == 'PATCH':
            response = api.post(url, json={**payload, 'montant': 400})
            assert response.status_code == 201, response.text
            url += '/' + str(response.json()['id'])
            payload = {'montant': valeur, 'notes': 'Ne doit pas persister'}
        def instantane():
            with Session(application['engine']) as db:
                facture = db.get(models.Facture, dossier['fid'])
                colonnes = lambda obj: tuple((c.name, getattr(obj, c.name)) for c in obj.__table__.columns)
                reglements = db.query(models.Reglement).filter_by(facture_id=dossier['fid']).order_by(models.Reglement.id).all()
                ecritures = db.query(models.Ecriture).filter_by(societe_id=facture.societe_id).order_by(models.Ecriture.id).all()
                return (colonnes(facture), tuple(colonnes(l) for l in facture.lignes),
                        tuple(colonnes(r) for r in reglements),
                        tuple((colonnes(e), tuple(colonnes(l) for l in e.lignes)) for e in ecritures))
        avant = instantane()
        response = api.request(methode, url, content=json.dumps(payload), headers={'Content-Type': 'application/json'})
        assert response.status_code == 422, response.text
        assert instantane() == avant
