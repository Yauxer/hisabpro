from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
from services import fec_source_recovery_service as fec
from services import etic_service as etic


def facture(fid, numero, reference=None, tiers_id=1, montant="240"):
    return SimpleNamespace(id=fid, type="achat", date=date(2026, 5, 22),
                           numero=numero, reference=reference, tiers_id=tiers_id,
                           montant=Decimal(montant))


def ecriture(reference=None, libelle="", montant="240"):
    return SimpleNamespace(journal="AC", date=date(2026, 5, 22),
                           reference=reference, libelle=libelle,
                           lignes=[SimpleNamespace(compte="4411", debit=0,
                                                   credit=Decimal(montant))])


@pytest.fixture(params=["fec", "etic"])
def choisir(request, monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    monkeypatch.setattr(etic, "_ttc_facture_etic", lambda f: f.montant)
    if request.param == "fec":
        return fec.choisir_facture_source
    return lambda e, fs: etic._choisir_facture_historique_etic(e, fs, "achat")


@pytest.mark.parametrize("reference", ["02", "002"])
def test_reference_exacte_prioritaire_sur_libelle_concurrent(choisir, reference):
    f02, f002 = facture(1, "02"), facture(2, "002")
    concurrent = "002" if reference == "02" else "02"
    assert choisir(ecriture(reference, "Facture " + concurrent), [f002, f02]) is (f02 if reference == "02" else f002)


def test_reference_fournisseur_exacte(choisir):
    f02, f002 = facture(1, "ACH-A", "02"), facture(2, "ACH-B", "002")
    assert choisir(ecriture("02"), [f002, f02]) is f02


def test_reference_numerique_differente_refusee_meme_candidat_unique(choisir):
    assert choisir(ecriture("02"), [facture(1, "002")]) is None


def test_references_identiques_restent_ambigues_malgre_libelle(choisir):
    assert choisir(ecriture("02", "Facture ACH-A"),
                   [facture(1, "ACH-A", "02"), facture(2, "ACH-B", "02")]) is None


def test_candidats_ambigus_sans_reference(choisir):
    assert choisir(ecriture(), [facture(1, "02"), facture(2, "002")]) is None


def test_candidat_unique_date_montant(choisir):
    f = facture(1, "02")
    assert choisir(ecriture(), [f, facture(2, "002", montant="1200")]) is f


def test_libelle_identifiant_entier_sans_collision(choisir):
    f02, f002 = facture(1, "02"), facture(2, "002")
    assert choisir(ecriture(libelle="Facture 002 fournisseur"), [f02, f002]) is f002


def test_identifiant_partiel_ne_departage_pas(choisir):
    assert choisir(ecriture(libelle="Facture 1002"), [facture(1, "02"), facture(2, "002")]) is None


def test_reference_exacte_ne_contourne_pas_date_et_montant(choisir):
    f = facture(1, "02", montant="1200")
    assert choisir(ecriture("02"), [f]) is None
    f.montant = Decimal("240")
    f.date = date(2026, 5, 23)
    assert choisir(ecriture("02"), [f]) is None


def test_montant_collectif_net_coherent_fec_etic(choisir):
    ec = ecriture("02", montant="300")
    ec.lignes[0].debit = Decimal("60")
    f = facture(1, "02")
    assert choisir(ec, [f]) is f


def test_fec_ne_detourne_pas_reference_sans_tiers(monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    monkeypatch.setattr(etic, "_ttc_facture_etic", lambda f: f.montant)
    f02, f002 = facture(1, "02", tiers_id=None), facture(2, "002")
    assert fec.choisir_facture_source(ecriture("02"), [f02, f002]) is None
    assert etic._choisir_facture_historique_etic(ecriture("02"), [f02, f002], "achat") is f02


def test_absence_tiers_ne_supprime_pas_ambiguite_fec(monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    assert fec.choisir_facture_source(ecriture(), [facture(1, "02", tiers_id=None), facture(2, "002")]) is None


def test_recuperation_fec_garde_les_candidats_sans_tiers():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "hisabpro-backend/services/fec_source_recovery_service.py").read_text(encoding="utf-8")
    assert "models.Facture.tiers_id.isnot(None)" not in source


class QuerySources:
    def __init__(self, rows):
        self.rows = rows

    def options(self, *args):
        return self

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return self.rows


class SourcesDB:
    def __init__(self, factures, ecritures):
        self.factures = factures
        self.ecritures = ecritures

    def query(self, model):
        return QuerySources(self.factures if model is etic.models.Facture else self.ecritures)


def test_pipeline_etic_recupere_02_et_002_separement(monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    monkeypatch.setattr(etic, "_ttc_facture_etic", lambda f: f.montant)
    f02, f002 = facture(1, "02", tiers_id=None), facture(2, "002")
    db = SourcesDB([f02, f002], [ecriture("02"), ecriture("002")])
    fs, ids = etic._factures_eligibles_etic(db, 3, 2026, "achat", date(2026, 12, 31))
    assert {f.id for f in fs} == ids == {1, 2}


def test_pipeline_etic_refuse_facture_associee_a_deux_ecritures(monkeypatch):
    monkeypatch.setattr(fec, "_facture_ttc", lambda f: f.montant)
    monkeypatch.setattr(etic, "_ttc_facture_etic", lambda f: f.montant)
    db = SourcesDB([facture(1, "02")], [ecriture("02"), ecriture("02")])
    assert etic._factures_eligibles_etic(db, 3, 2026, "achat", date(2026, 12, 31)) == ([], set())
