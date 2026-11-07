from types import SimpleNamespace
import pytest
from test_patch113_fec_etic_references_exactes import facture, ecriture, choisir
from test_patch114_unicite_globale_fec_etic import RecoveryDB
from services import fec_source_recovery_service as fec


def test_reference_corrigee_prioritaire_02_002_coherente_fec_etic(choisir):
    ec = ecriture("02")
    ec.justificatifs = [SimpleNamespace(reference="002", prioritaire=True, date_piece=None)]
    f02, f002 = facture(1, "02"), facture(2, "002")
    assert choisir(ec, [f02, f002]) is f002
    assert ec.reference == "02"  # L'écriture définitive reste intacte.


@pytest.mark.parametrize("complement", [False, True])
def test_tiers_contradictoire_ne_force_pas_rapprochement(choisir, complement):
    ec = ecriture("02")
    ligne = ec.lignes[0]
    if complement:
        ligne.auxiliaire_complements = [SimpleNamespace(tiers_id=2, compte_auxiliaire_snapshot="F02", libelle_auxiliaire_snapshot="Autre")]
    else:
        ligne.tiers_id = 2
    assert choisir(ec, [facture(1, "02", tiers_id=1)]) is None


def test_conflit_tiers_ne_masque_pas_facture_concurrente(choisir):
    ec = ecriture()
    ec.lignes[0].tiers_id = 1
    assert choisir(ec, [facture(1, "02", tiers_id=1), facture(2, "002", tiers_id=2)]) is None


def test_snapshot_compte_divergent_bloque_recuperation_FEC(monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    f = facture(1, "02")
    f.compte_tiers_snapshot = "44110001"
    assert fec.choisir_facture_source(ecriture("02"), [f]) is None


def test_piece_complete_en_conflit_reserve_quand_meme_la_source(monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    complete, incomplete = ecriture("02"), ecriture("02")
    complete.id, incomplete.id = 10, 11
    complete.lignes[0].tiers_id = 2
    complete.lignes[0].compte_auxiliaire_snapshot = "F02"
    complete.lignes[0].libelle_auxiliaire_snapshot = "Autre"
    db = RecoveryDB([facture(1, "02")], [complete, incomplete])
    result = fec.recuperer_depuis_factures(db, 3, 2026)
    assert result["nb_non_resolus"] == 1
    assert "plusieurs écritures" in result["non_resolus"][0]["raison"]
    assert db.added == []
    assert not db.committed
