from copy import deepcopy
from decimal import Decimal
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from auth import requiert_ecriture
from database import get_db
from routers.etats import router
from services.balance_import_service import montant_import, normaliser_balance, preparer_balance_liasse


COMPTES = {'1111', '5141', '3421', '7111', '6111', '4411', '1191'}
N = [{'compte': '1111', 'credit': '100000'}, {'compte': '5141', 'debit': '110000'},
     {'compte': '3421', 'debit': '40000'}, {'compte': '7111', 'credit': '60000'},
     {'compte': '6111', 'debit': '20000'}, {'compte': '4411', 'credit': '10000'}]


def test_oracle_bilan_cpc_et_comparatif_independants():
    n1 = [{'compte': '1111', 'credit': '100000'}, {'compte': '5141', 'debit': '100000'}]
    r = preparer_balance_liasse(N, n1, COMPTES)
    assert r['etats']['cpc']['resultat_net'] == 40000
    assert r['etats']['bilan']['actif']['total']['net'] == 150000
    assert r['etats']['bilan']['passif']['total'] == 150000
    assert r['etats_n1']['bilan']['passif']['total'] == 100000
    assert r['etats']['esg']['caf'] == 40000
    assert not r['pret_a_deposer']
    assert 'fiscal' not in r and 'etic' not in r


def test_absence_n1_ne_devient_pas_historique_zero():
    r = preparer_balance_liasse(N, None, COMPTES)
    assert r['etats_n1'] is None and r['balance_n1'] is None


def test_balance_apres_cloture_ne_fabrique_pas_cpc_caf_a_zero():
    closed = [{'compte': '1111', 'credit': '100000'}, {'compte': '1191', 'credit': '40000'},
              {'compte': '5141', 'debit': '140000'}]
    r = preparer_balance_liasse(N, closed, COMPTES)
    assert r['etats_n1']['bilan']['actif']['total']['net'] == 140000
    assert r['etats_n1']['cpc']['resultat_net'] is None
    assert r['etats_n1']['esg']['caf'] is None
    assert r['etats_n1']['cpc']['disponible'] is False


@pytest.mark.parametrize('v', ['-1', 'NaN', 'Infinity', True, '1.234', '1,234.56', '10000000000000'])
def test_montants_invalides_refuses_sans_arrondi_silencieux(v):
    with pytest.raises(ValueError):
        montant_import(v, 'test')


@pytest.mark.parametrize('v', ['1 234,56', '1\u202f234,56', '1234.56', Decimal('1234.560')])
def test_montants_francais_acceptes(v):
    assert montant_import(v, 'test') == Decimal('1234.56')


@pytest.mark.parametrize('compte', ['02', '002', '1111.0', '8', '', '9001', '5142'])
def test_compte_invalide_ou_inconnu_sans_heuristique(compte):
    rows = deepcopy(N); rows[0]['compte'] = compte
    with pytest.raises(ValueError):
        preparer_balance_liasse(rows, None, COMPTES)


def test_doublon_refuse():
    with pytest.raises(ValueError, match='doublon'):
        normaliser_balance(N + [N[0]], COMPTES, 'N')


def test_ecart_un_centime_refuse():
    rows = deepcopy(N); rows[0]['credit'] = '100000.01'
    with pytest.raises(ValueError, match='déséquilibrée'):
        preparer_balance_liasse(rows, None, COMPTES)


def test_resultat_cloture_technique_non_additionne_aux_charges():
    rows = deepcopy(N); rows[0]['credit'] = '60000'; rows.append({'compte': '1191', 'credit': '40000'})
    with pytest.raises(ValueError, match='simultanés'):
        preparer_balance_liasse(rows, None, COMPTES)


def test_compte_non_couvert_ne_devient_pas_reclassement():
    rows = [{'compte': '4381', 'credit': '100'}, {'compte': '5141', 'debit': '100'}]
    with pytest.raises(ValueError, match='états incohérents'):
        preparer_balance_liasse(rows, None, COMPTES | {'4381'})


def test_api_plan_societe_et_aucune_mutation():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    models.CompteSociete.__table__.create(engine)
    with Session(engine) as db:
        for numero in COMPTES:
            db.add(models.CompteSociete(societe_id=1, numero=numero, libelle=numero, classe=numero[0], type_compte='SP'))
        db.add(models.CompteSociete(societe_id=2, numero='5142', libelle='autre société', classe='5', type_compte='SP'))
        db.commit()
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[requiert_ecriture] = lambda: {'societe_id': 1, 'role': 'comptable'}
    def database():
        with Session(engine) as db:
            yield db
            assert not db.new and not db.dirty and not db.deleted
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        assert client.post('/api/etats/liasse/balance/preview', json={'lignes_n': N}).status_code == 200
        rows = deepcopy(N); rows[1]['compte'] = '5142'
        response = client.post('/api/etats/liasse/balance/preview', json={'lignes_n': rows})
        assert response.status_code == 422 and 'plan de la société' in response.text
    with Session(engine) as db:
        assert db.query(models.CompteSociete).count() == len(COMPTES) + 1
    engine.dispose()
