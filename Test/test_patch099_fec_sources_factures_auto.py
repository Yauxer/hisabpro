from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

from services.fec_source_recovery_service import (  # noqa: E402
    choisir_facture_source,
    _reference_facture_source,
)


def ligne(compte, debit=0, credit=0, libelle=""):
    return SimpleNamespace(compte=compte, debit=Decimal(str(debit)), credit=Decimal(str(credit)), libelle=libelle)


def facture(fid, *, type_, d, tiers_id, tiers, numero, reference, ttc):
    # Une ligne à 20 % suffit pour produire exactement le TTC voulu dans les cas de test.
    ht = Decimal(str(ttc)) / Decimal("1.20")
    lf = SimpleNamespace(
        quantite=Decimal("1"), prix_unitaire=ht, tva=Decimal("20"),
        qualification_tva="taxable", remise=0, remise2=0, rabais=0,
    )
    return SimpleNamespace(
        id=fid, type=type_, date=d, tiers_id=tiers_id, tiers=tiers,
        numero=numero, reference=reference, lignes=[lf], remise_globale=0,
        ristourne=0, escompte=0, frais_transport_ht=0, frais_transport_tva=20,
        frais_transport_mode="accessoire", frais_transport_qualification_tva="taxable",
        frais_emballage_ht=0, frais_emballage_tva=20, frais_emballage_mode="perdu",
        frais_emballage_qualification_tva="taxable",
    )


def test_facture_unique_retrouvee_par_date_et_ttc():
    d = date(2026, 5, 8)
    ec = SimpleNamespace(journal="VT", date=d, reference=None, libelle="Vente de tapis", lignes=[ligne("3421", debit="120")])
    f = facture(10, type_="vente", d=d, tiers_id=3, tiers="Akayax", numero="2026-002", reference=None, ttc="120")
    assert choisir_facture_source(ec, [f]).id == 10


def test_ambiguite_date_ttc_nest_pas_forcee():
    d = date(2026, 5, 22)
    ec = SimpleNamespace(journal="VT", date=d, reference=None, libelle="FA°", lignes=[ligne("3421", debit="120")])
    f1 = facture(1, type_="vente", d=d, tiers_id=1, tiers="A", numero="A-1", reference=None, ttc="120")
    f2 = facture(2, type_="vente", d=d, tiers_id=2, tiers="B", numero="B-1", reference=None, ttc="120")
    assert choisir_facture_source(ec, [f1, f2]) is None


def test_numero_exact_dans_libelle_departage_un_ttc_identique():
    d = date(2026, 5, 22)
    ec = SimpleNamespace(journal="VT", date=d, reference=None, libelle="FA° B-1", lignes=[ligne("3421", debit="120")])
    f1 = facture(1, type_="vente", d=d, tiers_id=1, tiers="A", numero="A-1", reference=None, ttc="120")
    f2 = facture(2, type_="vente", d=d, tiers_id=2, tiers="B", numero="B-1", reference=None, ttc="120")
    assert choisir_facture_source(ec, [f1, f2]).id == 2


def test_reference_piece_vente_et_achat_vient_de_la_facture():
    d = date(2026, 1, 1)
    vente = facture(1, type_="vente", d=d, tiers_id=1, tiers="C", numero="FA-1", reference="CMD-1", ttc="120")
    achat = facture(2, type_="achat", d=d, tiers_id=2, tiers="F", numero="INT-1", reference="FOUR-77", ttc="120")
    assert _reference_facture_source(vente) == "FA-1"
    assert _reference_facture_source(achat) == "FOUR-77"


def test_integration_route_et_frontend_patch099():
    fec = (BACK / "routers" / "fec.py").read_text(encoding="utf-8")
    journal = (ROOT / "src" / "pages" / "Journal.jsx").read_text(encoding="utf-8")
    service = (BACK / "services" / "fec_source_recovery_service.py").read_text(encoding="utf-8")
    assert '@router.post("/reparer-sources-factures")' in fec
    assert "recuperer_depuis_factures" in fec
    assert "/api/fec/reparer-sources-factures" in journal
    assert "journal + date + montant TTC" in service
    assert 'source_type="facture_source_auto"' in service
    assert "LigneAuxiliaireComplement" in service
    assert "EcritureJustificatif" in service
