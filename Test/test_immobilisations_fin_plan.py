"""La situation à date conserve les centimes du plan amortissable achevé."""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from services import immobilisations_service as immo_service


def immobilisation(methode="lineaire", residuelle=0, duree=3, debut=date(2026, 1, 1)):
    return SimpleNamespace(valeur_brute=10000, valeur_residuelle=residuelle,
        duree_amort=duree, date_acquisition=debut, date_mise_en_service=debut,
        methode=methode, amortissable=True, date_sortie=None)


@pytest.mark.parametrize("methode", ["lineaire", "degressif"])
@pytest.mark.parametrize("residuelle", [0, Decimal("123.45")])
@pytest.mark.parametrize("debut", [date(2026, 1, 1), date(2026, 7, 1)])
def test_situation_achevee_identique_au_plan_normal(methode, residuelle, debut):
    immo = immobilisation(methode=methode, residuelle=residuelle, debut=debut)
    plan = immo_service.calculer_tableau_amortissement(immo)
    dernier = plan[-1]
    for cutoff in [dernier["fin_periode"], date(2040, 12, 31)]:
        situation = immo_service.situation_a_date(immo, cutoff)
        assert situation["cumul"] == dernier["cumul"]
        assert situation["vnc"] == Decimal(str(residuelle))
        assert situation["cumul"] == Decimal("10000") - Decimal(str(residuelle))


@pytest.mark.parametrize("methode", ["lineaire", "degressif"])
def test_sortie_dernier_jour_acheve_aussi_le_plan(methode):
    immo = immobilisation(methode=methode)
    plan = immo_service.calculer_tableau_amortissement(immo)
    immo.date_sortie = plan[-1]["fin_periode"]
    situation = immo_service.situation_a_date(immo, date(2040, 1, 1))
    assert situation["cumul"] == Decimal("10000.00")
    assert situation["vnc"] == Decimal("0.00")


def test_sortie_avant_fin_ne_force_pas_un_amortissement_integral():
    immo = immobilisation()
    immo.date_sortie = date(2027, 12, 31)
    situation = immo_service.situation_a_date(immo, date(2040, 1, 1))
    assert situation["cumul"] == Decimal("6666.66")
    assert situation["vnc"] == Decimal("3333.34")


def test_dotation_derniere_annee_absorbe_centime_comme_plan_normal():
    immo = immobilisation()
    dotation = immo_service.dotation_sur_periode(immo, date(2028, 1, 1), date(2028, 12, 31))
    assert dotation["dotation"] == Decimal("3333.34")
    assert dotation["cumul_fin"] == Decimal("10000.00")


def test_resultat_cession_apres_plan_ne_cree_pas_moins_value_fictive():
    immo = immobilisation()
    resultat = immo_service.resultat_cession(immo, date(2030, 1, 1), 0)
    assert resultat["vnc"] == 0
    assert resultat["resultat_cession"] == 0
    assert resultat["nature_resultat"] == "neutre"
