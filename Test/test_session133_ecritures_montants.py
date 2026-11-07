"""Montants invalides : schémas et vraie API PG éphémère, sans données réelles."""
from decimal import Decimal
import json

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import pytest
from sqlalchemy.orm import Session

import models
import schemas
from routers.ecritures import _montant_decimal, _verifier_equilibre
from test_session132_operations_postgres import engine, dossier, client
from services.api_validation_service import erreur_validation_json


INVALIDES = ['NaN', 'sNaN', 'Infinity', '-Infinity', '1e999', True, False]


@pytest.mark.parametrize('valeur', INVALIDES + [float('nan'), float('inf'), Decimal('NaN')])
def test_conversion_refuse_montant_non_fini_et_booleen(valeur):
    with pytest.raises(HTTPException) as exc:
        _montant_decimal(valeur)
    assert exc.value.status_code == 422


@pytest.mark.parametrize('valeur', INVALIDES)
@pytest.mark.parametrize('champ', ['debit', 'credit'])
def test_schema_refuse_avant_coercition(valeur, champ):
    ligne = {'compte': '5141', 'debit': 0, 'credit': 0, champ: valeur}
    with pytest.raises(ValidationError):
        schemas.LigneEcritureCreate(**ligne)


def charge(valeur=100):
    return {'date': '2026-05-01', 'journal': 'OD', 'libelle': 'Montants isolés',
            'lignes': [{'compte': '5141', 'debit': valeur, 'credit': 0},
                       {'compte': '1111', 'debit': 0, 'credit': 100}]}


def snapshot(engine, identifiant):
    with Session(engine) as db:
        e = db.get(models.Ecriture, identifiant)
        return (e.libelle, e.date, e.journal, e.reference, e.numero_ecriture,
                tuple((l.id, l.compte, l.debit, l.credit) for l in e.lignes))


@pytest.mark.parametrize('valeur', INVALIDES + [float('nan'), float('inf')])
@pytest.mark.parametrize('operation', ['creation', 'modification'])
def test_api_pg_rejet_ne_modifie_ni_lignes_ni_entete(engine, dossier, client, valeur, operation):
    client.app.add_exception_handler(RequestValidationError, erreur_validation_json)
    # TestClient a démarré lifespan ; reconstruire son middleware avant la
    # première requête pour enregistrer le même handler que main.app.
    client.app.middleware_stack = None
    original = client.post('/api/ecritures', json=charge())
    assert original.status_code == 201, original.text
    identifiant = original.json()['id']
    avant = snapshot(engine, identifiant)
    url = '/api/ecritures' if operation == 'creation' else f'/api/ecritures/{identifiant}'
    donnees = charge(valeur)
    donnees['libelle'] = 'Ne doit pas être enregistré'
    reponse = (client.post if operation == 'creation' else client.patch)(url,
        content=json.dumps(donnees), headers={'Content-Type': 'application/json'})
    assert reponse.status_code == 422, reponse.text
    assert reponse.json()['detail']
    assert snapshot(engine, identifiant) == avant
    with Session(engine) as db:
        assert db.query(models.Ecriture).filter_by(societe_id=dossier['societe_id']).count() == 1


@pytest.mark.parametrize('valeur', [0, '0', '100.105', Decimal('100.105')])
def test_conversion_monetaire_valide_conserve_arrondi(valeur):
    attendu = Decimal('0.00') if str(valeur) == '0' else Decimal('100.11')
    assert _montant_decimal(valeur) == attendu


def test_equilibre_au_centime_reste_strict():
    from types import SimpleNamespace
    with pytest.raises(HTTPException) as exc:
        _verifier_equilibre([SimpleNamespace(debit='100.105', credit=0),
                            SimpleNamespace(debit=0, credit='100.10')])
    assert exc.value.status_code == 400


def test_vraie_app_422_serialisable_sans_connexion_reelle():
    from e2e_isole_support import application_isolee
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    with application_isolee() as app:
        # Les dépendances d'auth sont résolues avant les champs de body ; une
        # route auth sans authentification vérifie le même handler applicatif.
        requete = Request(app['api_url'] + '/api/auth/register',
            data=json.dumps({'nom': float('nan'), 'email': 'fictif@example.invalid',
                             'password': 'SecretRecette133!', 'raison_sociale': 'Fictive'}).encode(),
            headers={'Content-Type': 'application/json'})
        with pytest.raises(HTTPError) as erreur:
            urlopen(requete, timeout=10)
        assert erreur.value.code == 422
        details = json.loads(erreur.value.read())['detail']
        assert details[0]['input'] == 'nan'
