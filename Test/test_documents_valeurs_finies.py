"""Lignes commerciales : rejets avant numérotation, stock ou comptabilité."""
from datetime import date
import json

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

import models
import schemas
from test_e2e_facturation_isole import application
from test_e2e_recouvrement_isole import dossier_synthetique

CHAMPS = [(schema, champ) for schema, champs in [
    (schemas.LigneFactureCreate, ['quantite', 'prix_unitaire', 'rabais', 'remise', 'remise2', 'tva']),
    (schemas.LigneDevisCreate, ['quantite', 'prix_unitaire', 'tva']),
    (schemas.LigneBCCreate, ['quantite', 'prix_unitaire', 'rabais', 'remise', 'remise2', 'tva']),
    (schemas.LigneBLCreate, ['quantite_prevue', 'quantite_livree', 'prix_unitaire', 'rabais', 'remise', 'remise2', 'tva']),
] for champ in champs]


@pytest.mark.parametrize('schema,champ', CHAMPS, ids=[s.__name__ + '-' + c for s, c in CHAMPS])
@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), True, False])
def test_ligne_refuse_nombre_non_fini_ou_booleen(schema, champ, valeur):
    with pytest.raises(ValidationError):
        schema(**{'description': 'Ligne fictive', 'prix_unitaire': 100, champ: valeur})


@pytest.mark.parametrize('schema', [schemas.LigneFactureCreate, schemas.LigneDevisCreate,
                                    schemas.LigneBCCreate, schemas.LigneBLCreate])
def test_ligne_gratuite_et_quantites_fractionnaires_restent_valides(schema):
    payload = {'description': 'Fictif gratuit', 'prix_unitaire': 0, 'tva': 0}
    payload['quantite_prevue' if schema is schemas.LigneBLCreate else 'quantite'] = 0.5
    assert schema(**payload).prix_unitaire == 0


@pytest.mark.parametrize('url', ['/api/factures', '/api/devis', '/api/bons-commande', '/api/bons-livraison'])
@pytest.mark.parametrize('valeur', [float('nan'), True])
def test_api_creation_invalide_ne_change_aucune_source(application, url, valeur):
    dossier = dossier_synthetique(application)
    def instantane():
        with Session(application['engine']) as db:
            sid = db.get(models.Facture, dossier['fid']).societe_id
            tables = [models.Facture, models.Devis, models.BonCommande, models.BonLivraison,
                      models.Ecriture, models.MouvementStock]
            return tuple(tuple(tuple((c.name, getattr(obj, c.name)) for c in obj.__table__.columns)
                               for obj in db.query(table).filter_by(societe_id=sid).order_by(table.id).all())
                         for table in tables)
    avant = instantane()
    payload = {'date': date.today().isoformat(), 'tiers': dossier['nom'], 'type': 'vente',
               'lignes': [{'description': 'Ligne à refuser', 'prix_unitaire': valeur}]}
    with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer ' + dossier['token']}) as api:
        response = api.post(url, content=json.dumps(payload), headers={'Content-Type': 'application/json'})
        assert response.status_code == 422, response.text
    assert instantane() == avant
