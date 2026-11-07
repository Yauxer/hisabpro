from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND / "services"))

import fiscalite_retraitements_service as service


def _pieces(resultat):
    return next(x for x in resultat["a_confirmer"] if x["categorie"] == "charges_non_justifiees")


def test_charges_sans_reference_exposent_les_comptes_reellement_concernes():
    r = service.analyser_retraitements(
        charges_par_compte={
            "6111": Decimal("1500.00"),
            "6141": Decimal("500.00"),
            "6195": Decimal("3300.00"),
        },
        produits_par_compte={},
        charges_sans_reference=Decimal("2000.00"),
        charges_sans_reference_par_compte={
            "6111": Decimal("1500.00"),
            "6141": Decimal("500.00"),
        },
    )
    pieces = _pieces(r)
    assert pieces["montant_detecte"] == Decimal("2000.00")
    assert pieces["compte_source"] == "6111, 6141"
    assert "6195" not in pieces["compte_source"]


def test_liste_des_comptes_est_bornee_pour_rester_persistable():
    comptes = {f"61{i:03d}": Decimal("1.00") for i in range(50)}
    valeur = service._comptes_concernes_compacts(comptes)
    assert len(valeur) <= 110
    assert valeur.startswith("61000")
    assert "+" in valeur


def test_routeur_agrege_et_transmet_les_comptes_sans_reference():
    src = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    assert 'charges_sans_reference_par_compte = {}' in src
    assert 'charges_sans_reference_par_compte[compte]' in src
    assert '"_charges_sans_reference_par_compte": charges_sans_reference_par_compte' in src
    assert 'charges_sans_reference_par_compte=source["_charges_sans_reference_par_compte"]' in src
