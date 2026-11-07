"""Échéanciers : nombres invalides refusés avant remplacement, PG isolé."""
from datetime import date
import json

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

import models
from routers.echeanciers import EcheanceIn
from services.echeancier_service import normaliser_echeances
from test_e2e_facturation_isole import application
from test_e2e_recouvrement_isole import dossier_synthetique

INVALIDES = [float('nan'), float('inf'), -float('inf'), 'NaN', 'Infinity', True, False, {}, [], 'invalide']


@pytest.mark.parametrize('valeur', INVALIDES)
def test_normalisation_refuse_valeur_invalide(valeur):
    with pytest.raises(ValueError):
        normaliser_echeances([{'date_echeance': date(2026, 5, 1), 'montant': valeur}], 1200, date(2026, 1, 1))


@pytest.mark.parametrize('valeur', INVALIDES)
def test_schema_refuse_valeur_invalide(valeur):
    with pytest.raises(ValidationError):
        EcheanceIn(date_echeance='2026-05-01', montant=valeur)


@pytest.mark.parametrize('total', [float('nan'), float('inf'), True])
def test_total_contractuel_invalide_ne_peut_valider_echeances(total):
    with pytest.raises(ValueError):
        normaliser_echeances([{'date_echeance': date(2026, 5, 1), 'montant': 1}], total, date(2026, 1, 1))


def test_ventilation_contractuelle_valide_conserve_arrondis_et_tri():
    rows = normaliser_echeances([
        {'date_echeance': date(2026, 6, 1), 'montant': '800.25'},
        {'date_echeance': date(2026, 5, 1), 'montant': 399.75},
    ], 1200, date(2026, 1, 1))
    assert [r['montant'] for r in rows] == [399.75, 800.25]
    assert [r['ordre'] for r in rows] == [1, 2]


@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), True, {}])
def test_api_refuse_sans_changer_echeancier_ou_facture(application, valeur):
    dossier = dossier_synthetique(application)
    with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer ' + dossier['token']}) as api:
        url = f"/api/factures/{dossier['fid']}/echeancier"
        payload = {'echeances': [{'date_echeance': '2099-05-01', 'montant': 1200}]}
        response = api.put(url, json=payload)
        assert response.status_code == 200, response.text
        def instantane():
            with Session(application['engine']) as db:
                facture = db.get(models.Facture, dossier['fid'])
                colonnes = lambda obj: tuple((c.name, getattr(obj, c.name)) for c in obj.__table__.columns)
                return colonnes(facture), tuple(colonnes(e) for e in sorted(facture.echeances, key=lambda e: e.id)), tuple(colonnes(l) for l in facture.lignes)
        avant = instantane()
        payload['echeances'][0]['montant'] = valeur
        response = api.put(url, content=json.dumps(payload), headers={'Content-Type': 'application/json'})
        assert response.status_code == 422, response.text
        assert instantane() == avant
        response = api.get(url)
        assert response.status_code == 200 and response.json()['total_echeancier'] == 1200
