from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.cloture_service import construire_cascade_resultat


def _solde_lignes(lignes):
    return sum(
        (Decimal(str(l.get("debit", 0))) - Decimal(str(l.get("credit", 0))) for l in lignes),
        Decimal("0"),
    )


def test_cascade_classe8_benefice():
    lignes, resultat, compte = construire_cascade_resultat({
        "6111": Decimal("100.00"),
        "7111": Decimal("-300.00"),
        "6311": Decimal("20.00"),
        "7386": Decimal("-5.00"),
        "6585": Decimal("10.00"),
        "7585": Decimal("-2.00"),
        "6701": Decimal("30.00"),
    })
    assert resultat == Decimal("147.00")
    assert compte == "1191"
    assert _solde_lignes(lignes) == Decimal("0.00")
    comptes = {l["compte"] for l in lignes}
    assert {"8100", "8300", "8400", "8500", "8600", "8800", "1191"} <= comptes


def test_cascade_classe8_perte():
    lignes, resultat, compte = construire_cascade_resultat({
        "6111": Decimal("300.00"),
        "7111": Decimal("-200.00"),
    })
    assert resultat == Decimal("-100.00")
    assert compte == "1199"
    assert _solde_lignes(lignes) == Decimal("0.00")


def test_cascade_ne_genere_jamais_de_montant_negatif():
    lignes, _, _ = construire_cascade_resultat({
        "6111": Decimal("-25.00"),  # solde atypique créditeur
        "7111": Decimal("-100.00"),
    })
    assert all(Decimal(str(l.get("debit", 0))) >= 0 for l in lignes)
    assert all(Decimal(str(l.get("credit", 0))) >= 0 for l in lignes)


def test_router_cloture_utilise_la_cascade_classe8():
    src = (BACKEND / "routers" / "cloture.py").read_text(encoding="utf-8")
    assert "construire_cascade_resultat(soldes)" in src
    assert "8100/8300/8400/8500/8600/8800" in src
