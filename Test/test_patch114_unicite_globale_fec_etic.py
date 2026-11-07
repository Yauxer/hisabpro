"""Les sources déjà documentées ne doivent pas disparaître des collisions."""
from test_patch113_fec_etic_references_exactes import (
    QuerySources, SourcesDB, facture, ecriture,
)
from services import etic_service as etic
from services import fec_source_recovery_service as fec


def test_etic_facture_moderne_ne_masque_pas_collision_historique(monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    monkeypatch.setattr(etic, "_ttc_facture_etic", lambda f: f.montant)
    moderne, ancienne = facture(1, "02"), facture(2, "02")
    moderne.est_validee = moderne.est_comptabilisee = True
    db = SourcesDB([moderne, ancienne], [ecriture("02")])
    fs, ids = etic._factures_eligibles_etic(db, 3, 2026, "achat", moderne.date)
    assert fs == [moderne]
    assert ids == set()


def test_etic_reference_distincte_recupere_historique_a_cote_moderne(monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    monkeypatch.setattr(etic, "_ttc_facture_etic", lambda f: f.montant)
    moderne, ancienne = facture(1, "02"), facture(2, "002")
    moderne.est_validee = moderne.est_comptabilisee = True
    db = SourcesDB([moderne, ancienne], [ecriture("02"), ecriture("002")])
    fs, ids = etic._factures_eligibles_etic(db, 3, 2026, "achat", moderne.date)
    assert {f.id for f in fs} == {1, 2}
    assert ids == {2}


class RecoveryDB(SourcesDB):
    def __init__(self, factures, ecritures):
        super().__init__(factures, ecritures)
        self.added = []
        self.committed = False

    def query(self, model):
        if model is etic.models.Tiers:
            from types import SimpleNamespace
            return QuerySources([SimpleNamespace(id=1, nom="Fournisseur", code_aux_fournisseur="F01")])
        return super().query(model)

    def add(self, row):
        self.added.append(row)

    def commit(self):
        self.committed = True


def test_fec_ecriture_complete_reserve_aussi_la_facture_source(monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    complete, incomplete = ecriture("02"), ecriture("02")
    complete.id, incomplete.id = 10, 11
    for ec in (complete, incomplete):
        ec.justificatifs = []
    complete.lignes[0].tiers_id = 1
    complete.lignes[0].compte_auxiliaire_snapshot = "F01"
    complete.lignes[0].libelle_auxiliaire_snapshot = "Fournisseur"
    db = RecoveryDB([facture(1, "02")], [complete, incomplete])
    result = fec.recuperer_depuis_factures(db, 3, 2026)
    assert result["nb_non_resolus"] == 1
    assert "plusieurs écritures" in result["non_resolus"][0]["raison"]
    assert result["nb_auxiliaires_ajoutes"] == result["nb_references_ajoutees"] == 0
    assert db.added == []
    assert not db.committed
