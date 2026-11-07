from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import os
import pytest
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
from services import etic_service as etic
from test_patch099_fec_sources_factures_auto import facture, ligne
from test_patch113_fec_etic_references_exactes import QuerySources


class SourceDB:
    def __init__(self, fs, es, events=None):
        self.rows = {etic.models.Facture: fs, etic.models.Ecriture: es, **(events or {})}

    def query(self, model):
        return QuerySources(self.rows.get(model, []))


def document(fid=1, type_="vente", compte=None):
    f = facture(fid, type_=type_, d=date(2026, 6, 1), tiers_id=1,
                tiers="Tiers", numero=f"FA-{fid}", reference=None, ttc=120)
    f.est_validee = f.est_comptabilisee = True
    f.date_echeance = date(2026, 7, 1)
    f.echeances = []
    f.compte_tiers_snapshot = compte
    return f


def principale(f, eid=1, compte=None):
    type_ = f.type
    compte = compte or ("3421" if type_ == "vente" else "4411")
    return SimpleNamespace(id=eid, journal="VT" if type_ == "vente" else "AC",
                           date=f.date, reference=f.numero, libelle=f.numero,
                           lignes=[ligne(compte, debit=120 if type_ == "vente" else 0,
                                         credit=120 if type_ == "achat" else 0)])


@pytest.fixture(autouse=True)
def bornes(monkeypatch):
    monkeypatch.setattr(etic, "_bornes", lambda *a: (date(2026, 1, 1), date(2026, 12, 31)))


@pytest.mark.parametrize("type_,compte", [("vente", "3421"), ("achat", "4411")])
def test_flags_comptabilises_ne_prouvent_pas_ecriture_absente(type_, compte):
    f = document(type_=type_)
    got = etic._ventilation_factures_par_compte(SourceDB([f], []), 3, 2026, type_)[compte]
    assert got["total_source"] == Decimal("120")
    assert got["echues"] == 0
    assert got["anomalies_sources"][0]["facture_id"] == f.id


def test_ecriture_double_ne_qualifie_pas_facture_moderne():
    f = document()
    got = etic._ventilation_factures_par_compte(
        SourceDB([f], [principale(f, 1), principale(f, 2)]), 3, 2026, "vente"
    )["3421"]
    assert got["echues"] == 0
    assert "non unique" in got["anomalies_sources"][0]["motifs"][0]


def test_snapshot_subdivision_ne_reclasse_pas_ecriture_collective():
    f = document(type_="achat", compte="44110001")
    got = etic._ventilation_factures_par_compte(
        SourceDB([f], [principale(f, compte="4411")]), 3, 2026, "achat"
    )
    assert "4411" not in got
    assert got["44110001"]["total_source"] == 120
    assert got["44110001"]["echues"] == 0
    assert "compte exact" in got["44110001"]["anomalies_sources"][0]["motifs"][0]


def test_facture_recoupee_prefill_sans_anomalie():
    f = document()
    got = etic._ventilation_factures_par_compte(SourceDB([f], [principale(f)]), 3, 2026, "vente")["3421"]
    assert got["echues"] == got["total_source"] == 120
    assert got["anomalies_sources"] == []


def test_partie_non_prouvee_reste_non_qualifiee(monkeypatch):
    bonne, douteuse = document(1), document(2)
    sources = etic._ventilation_factures_par_compte(SourceDB([bonne, douteuse], [principale(bonne)]), 3, 2026, "vente")
    monkeypatch.setattr(etic, "_ventilation_factures_par_compte", lambda *a: sources)
    lignes = [{"compte": "3421", "montant": 240}]
    etic._ajouter_echeances_auto(object(), 3, 2026, lignes, "vente")
    assert lignes[0]["echeance_auto_partiel"]["echues"] == 120
    assert lignes[0]["echeance_auto_reliquat"] == 120
    assert lignes[0]["echeance_auto_non_qualifie"] == 120
