from datetime import date
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND / "services"))

import fiscalite_acomptes_service as service


def test_premier_exercice_sans_reference_est_non_applicable():
    ref = service.determiner_reference_acomptes(
        exercice=2026,
        liquidation_precedente=None,
        categorie_is="droit_commun",
        exercice_reference_existe=False,
    )
    assert ref["disponible"] is False
    assert ref["non_applicable"] is True
    assert ref["source"] == "premier_exercice"
    assert ref["montant_annuel"] == Decimal("0.00")

    situation = service.construire_acomptes(
        date_debut=date(2026, 1, 1),
        reference=ref,
        date_reference=date(2026, 9, 20),
    )
    assert [a["statut"] for a in situation["acomptes"]] == ["non_applicable"] * 4
    assert situation["total_du"] == Decimal("0.00")


def test_exercice_precedent_sans_liquidation_reste_reference_manquante():
    ref = service.determiner_reference_acomptes(
        exercice=2026,
        liquidation_precedente=None,
        categorie_is="droit_commun",
        exercice_reference_existe=True,
    )
    assert ref["non_applicable"] is False
    assert ref["source"] == "indisponible"

    situation = service.construire_acomptes(
        date_debut=date(2026, 1, 1),
        reference=ref,
        date_reference=date(2026, 9, 20),
    )
    assert [a["statut"] for a in situation["acomptes"]] == ["reference_manquante"] * 4


def test_route_et_ui_distinguent_premier_exercice_et_reference_manquante():
    router = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    page = (ROOT / "src" / "pages" / "FiscaliteIS.jsx").read_text(encoding="utf-8")
    css = (ROOT / "src" / "pages" / "FiscaliteIS.module.css").read_text(encoding="utf-8")

    assert "_exercice_reference_existe" in router
    assert "not reference_acomptes.get(\"non_applicable\")" in router
    assert "non_applicable:'Non applicable'" in page
    assert "Aucun acompte à saisir" in page
    assert "acompte_non_applicable" in css
