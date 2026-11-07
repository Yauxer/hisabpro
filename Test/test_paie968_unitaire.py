"""968 — unitaires : chemins du profil Personnel, schémas exacts, arrondi IR exact."""
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from services.personnel_profil_service import exiger_chemin_personnel
from services.paie_bulletins_service import Creation, Avance, ir_arrondi

P = '/api/employes/personnel/paie'


def requete(methode, chemin):
    return SimpleNamespace(method=methode, url=SimpleNamespace(path=chemin))


@pytest.mark.parametrize('methode,chemin', [
    ('GET', P + '/bulletins'), ('GET', P + '/bulletins/apercu'), ('GET', P + '/bulletins/12'), ('GET', P + '/etats'),
    ('GET', P + '/salaries'), ('GET', P + '/avances'), ('POST', P + '/bulletins'), ('POST', P + '/bulletins/12/annuler'),
    ('POST', P + '/avances'), ('POST', P + '/avances/3/annuler')])
def test_968_profil_personnel_bulletins_et_avances_autorises(methode, chemin):
    exiger_chemin_personnel('personnel', requete(methode, chemin))


@pytest.mark.parametrize('methode,chemin', [
    ('POST', P + '/comptabiliser'), ('POST', P + '/paiements'), ('POST', P + '/avances/3/comptabiliser'),
    ('GET', P + '/bulletins/0'), ('POST', P + '/bulletins/12'), ('GET', P + '/autre'), ('DELETE', P + '/bulletins/12')])
def test_968_profil_personnel_comptabilisation_et_paiement_refuses(methode, chemin):
    with pytest.raises(HTTPException) as e:
        exiger_chemin_personnel('personnel', requete(methode, chemin))
    assert e.value.status_code == 403


def test_968_schemas_montants_exacts_et_champs_fermes():
    base = {'controle_id': 1, 'ir_retenu': '10.00', 'cle_idempotence': str(uuid4()), 'motif': 'Fictif968'}
    assert str(Creation.model_validate(base).ir_retenu) == '10.00'
    for mauvais in [{'ir_retenu': 10.0}, {'ir_retenu': '1.001'}, {'ir_retenu': '-1'}, {'net_a_payer': '1'},
                    {'retenues_avances': [{'avance_id': 1, 'montant': 'NaN'}]}]:
        with pytest.raises(ValidationError):
            Creation.model_validate({**base, **mauvais})
    av = {'employe_id': 1, 'nature': 'PRET', 'date_octroi': '2026-11-02', 'montant': '5000.00', 'mode_versement': 'virement', 'motif': 'Fictif'}
    assert Avance.model_validate(av).retenue_mensuelle is None
    with pytest.raises(ValidationError):
        Avance.model_validate({**av, 'nature': 'DON'})


def test_968_arrondi_ir_sur_fraction_exacte():
    # 62128/125 = 497.024 → 497.02 ; 1/200 = 0.005 → 0.01 (demi supérieur, sans double arrondi).
    assert str(ir_arrondi({'fractions_exactes': {'ir_apres_reduction': {'numerateur': '62128', 'denominateur': '125'}}})) == '497.02'
    assert str(ir_arrondi({'fractions_exactes': {'ir_apres_reduction': {'numerateur': '1', 'denominateur': '200'}}})) == '0.01'
    assert ir_arrondi({'fractions_exactes': {}}) is None
