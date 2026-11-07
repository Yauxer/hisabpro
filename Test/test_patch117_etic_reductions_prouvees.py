from datetime import date
from types import SimpleNamespace
import pytest
from test_patch116_etic_preuves_comptables import SourceDB, document, principale, bornes
from test_patch099_fec_sources_factures_auto import ligne
from services import etic_service as etic


def reduction(f, montant=30, eid=2, journal="BQ"):
    return SimpleNamespace(id=eid, date=date(2026, 7, 1), journal=journal,
                           reference=f.numero, lignes=[ligne("3421", credit=montant)])


@pytest.mark.parametrize("model,date_key,label", [
    (etic.models.Reglement, "date", "Règlement"),
    (etic.models.ImputationAcompte, "date_imputation", "Imputation d'acompte"),
])
@pytest.mark.parametrize("preuve", [True, False])
def test_reduction_ne_qualifie_le_reste_que_si_ecriture_recoupee(model, date_key, label, preuve):
    f = document()
    row = SimpleNamespace(id=10, facture_id=f.id, montant=30, ecriture_id=2,
                          **{date_key: date(2026, 7, 1)})
    db = SourceDB([f], [principale(f)] + ([reduction(f)] if preuve else []), {model: [row]})
    got = etic._ventilation_factures_par_compte(db, 3, 2026, "vente")["3421"]
    assert got["total_source"] == 90
    assert got["echues"] == (90 if preuve else 0)
    assert bool(got["anomalies_sources"]) is not preuve
    if not preuve:
        assert label in got["anomalies_sources"][0]["motifs"][0]


@pytest.mark.parametrize("champ,valeur", [("reference", "AUTRE"), ("date", date(2026, 8, 1))])
def test_lien_technique_ne_masque_pas_piece_ou_date_incompatible(champ, valeur):
    f = document()
    row = SimpleNamespace(id=10, facture_id=f.id, montant=30, ecriture_id=2, date=date(2026, 7, 1))
    e = reduction(f)
    setattr(e, champ, valeur)
    got = etic._ventilation_factures_par_compte(
        SourceDB([f], [principale(f), e], {etic.models.Reglement: [row]}), 3, 2026, "vente"
    )["3421"]
    assert got["echues"] == 0


def test_ecriture_reutilisee_par_deux_reglements_refusee():
    f = document()
    rows = [SimpleNamespace(id=i, facture_id=f.id, montant=30, ecriture_id=2, date=date(2026, 7, 1)) for i in (10, 11)]
    got = etic._ventilation_factures_par_compte(
        SourceDB([f], [principale(f), reduction(f)], {etic.models.Reglement: rows}), 3, 2026, "vente"
    )["3421"]
    assert got["total_source"] == 60
    assert got["echues"] == 0
    assert "plusieurs imputations" in got["anomalies_sources"][0]["motifs"][-1]


def test_imputation_reference_le_numero_acompte_reel():
    f = document()
    row = SimpleNamespace(id=10, facture_id=f.id, montant=30, ecriture_id=2,
                          date_imputation=date(2026, 7, 1), acompte=SimpleNamespace(numero="ACP-02"))
    e = reduction(f, journal="OD")
    e.reference = "ACP-02"
    got = etic._ventilation_factures_par_compte(
        SourceDB([f], [principale(f), e], {etic.models.ImputationAcompte: [row]}), 3, 2026, "vente"
    )["3421"]
    assert got["echues"] == 90
    assert got["anomalies_sources"] == []


@pytest.mark.parametrize("preuve", [True, False])
def test_avoir_exige_une_piece_AV_exacte(monkeypatch, preuve):
    f = document()
    av = SimpleNamespace(id=10, facture_id=f.id, numero="AV-02", date=date(2026, 7, 1))
    original_total = etic.total_ventilation
    monkeypatch.setattr(etic, "ventilation_avoir", lambda *a, **k: "avoir_test")
    monkeypatch.setattr(etic, "total_ventilation", lambda v: {"ttc": 30} if v == "avoir_test" else original_total(v))
    e = reduction(f, journal="AV")
    e.reference = "AV-02" if preuve else "AV-002"
    got = etic._ventilation_factures_par_compte(
        SourceDB([f], [principale(f), e], {etic.models.Avoir: [av]}), 3, 2026, "vente"
    )["3421"]
    assert got["total_source"] == 90
    assert got["echues"] == (90 if preuve else 0)


@pytest.mark.parametrize("preuve", [True, False])
def test_taux_RAS_seul_ne_prouve_pas_imputation_a_la_cloture(preuve):
    f = document()
    f.ras_taux = 10
    e = reduction(f, montant=10, journal="OD")
    e.lignes.append(ligne("3453", debit=10))
    got = etic._ventilation_factures_par_compte(
        SourceDB([f], [principale(f)] + ([e] if preuve else [])), 3, 2026, "vente"
    )["3421"]
    assert got["total_source"] == 110
    assert got["echues"] == (110 if preuve else 0)
