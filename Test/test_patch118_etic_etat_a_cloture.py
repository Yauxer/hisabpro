from datetime import date, datetime
from types import SimpleNamespace
import pytest
from test_patch116_etic_preuves_comptables import SourceDB, document, principale, bornes
from test_patch117_etic_reductions_prouvees import reduction
from services import etic_service as etic

FIN = date(2026, 12, 31)


@pytest.mark.parametrize("statut", ["annule", "annulee"])
@pytest.mark.parametrize("jour,active", [(datetime(2026, 12, 31, 17), False), (datetime(2027, 1, 1), True)])
def test_annulation_apres_cloture_ne_modifie_pas_etat_passe(statut, jour, active):
    row = SimpleNamespace(statut=statut, date_annulation=jour)
    assert etic._source_active_a_cloture_etic(row, FIN, {}) == (active, None)


def test_date_comptable_de_contrepassation_prime_sur_horodatage_administratif():
    row = SimpleNamespace(statut="annule", date_annulation=datetime(2027, 2, 1), ecriture_annulation_id=3)
    assert etic._source_active_a_cloture_etic(row, FIN, {3: SimpleNamespace(date=FIN)}) == (False, None)
    assert etic._source_active_a_cloture_etic(row, FIN, {3: SimpleNamespace(date=date(2027, 1, 1))}) == (True, None)


@pytest.mark.parametrize("row", [SimpleNamespace(statut="annule"), SimpleNamespace(statut="rejete"),
                                SimpleNamespace(statut="annule", ecriture_annulation_id=3)])
def test_etat_historique_non_prouvable_est_signale(row):
    active, motif = etic._source_active_a_cloture_etic(row, FIN, {})
    assert not active
    assert motif


def test_reglement_annule_en_N1_reste_impute_a_la_cloture_N():
    f = document()
    row = SimpleNamespace(id=10, facture_id=f.id, montant=30, ecriture_id=2,
                          date=date(2026, 7, 1), statut="annule", date_annulation=datetime(2027, 1, 1))
    got = etic._ventilation_factures_par_compte(
        SourceDB([f], [principale(f), reduction(f)], {etic.models.Reglement: [row]}), 3, 2026, "vente"
    )["3421"]
    assert got["total_source"] == got["echues"] == 90


def test_rejet_non_date_ne_declenche_pas_prefill_du_principal():
    f = document()
    row = SimpleNamespace(id=10, facture_id=f.id, montant=30, ecriture_id=2,
                          date=date(2026, 7, 1), statut="rejete")
    got = etic._ventilation_factures_par_compte(
        SourceDB([f], [principale(f), reduction(f)], {etic.models.Reglement: [row]}), 3, 2026, "vente"
    )["3421"]
    assert got["total_source"] == 120
    assert got["echues"] == 0
    assert "Rejet" in got["anomalies_sources"][0]["motifs"][0]
