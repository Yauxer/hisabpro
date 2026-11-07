"""Paramètres TVA numériques finis, aucune mutation pour une saisie invalide."""
from datetime import date
import json

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

import models
from routers.tva import TVAParametresIn
from test_e2e_facturation_isole import application
from test_e2e_recouvrement_isole import dossier_synthetique


@pytest.mark.parametrize('champ', ['credit_ouverture', 'prorata_deduction_pct'])
@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), True, False])
def test_parametre_tva_non_fini_ou_booleen_refuse(champ, valeur):
    with pytest.raises(ValidationError):
        TVAParametresIn(**{champ: valeur})


@pytest.mark.parametrize('champ', ['credit_ouverture', 'prorata_deduction_pct'])
@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), True])
def test_api_parametre_tva_refuse_sans_alterer_valeurs(application, champ, valeur):
    dossier = dossier_synthetique(application)
    annee = date.today().year
    with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer ' + dossier['token']}) as api:
        url = f'/api/tva/parametres/{annee}'
        assert api.put(url, json={'credit_ouverture': 20, 'prorata_deduction_pct': 80}).status_code == 200
        avant = api.get(url).json()
        payload = {'credit_ouverture': 20, 'prorata_deduction_pct': 80, champ: valeur}
        response = api.put(url, content=json.dumps(payload), headers={'Content-Type': 'application/json'})
        assert response.status_code == 422, response.text
        assert api.get(url).json() == avant
        with Session(application['engine']) as db:
            rows = db.query(models.TVAParametreExercice).join(models.Societe).filter(
                models.Societe.raison_sociale.like('%' + dossier['suffix'] + '%')).all()
            assert all(float(row.credit_ouverture) == 20 and float(row.prorata_deduction_pct) == 80 for row in rows)
