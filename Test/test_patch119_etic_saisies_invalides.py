import os
import pytest
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
from services import etic_service as etic


@pytest.mark.parametrize("code", ["B6", "B7"])
@pytest.mark.parametrize("key", [*etic.VENTILATION_ECHEANCE_KEYS, *etic.VENTILATION_ANALYSE_KEYS])
@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", -1, "abc", True, False])
def test_valeur_invalide_ne_disparait_pas_derriere_auto_ou_neant(code, key, value):
    auto = {"lignes": [{"compte": "3421", "montant": 120,
                        "echeance_auto": {"plus_un_an": 0, "moins_un_an": 0, "echues": 120}}]}
    contenu = {"confirme": True, "autres_analyses_neant": True, "ventilations": {"3421": {key: value}}}
    errors = etic._erreurs_ventilation_b6_b7(code, auto, contenu)
    assert any("montant fini" in e for e in errors)
    assert etic._ventilation_publiee(code, auto, contenu)[0][key] is None


def test_zero_explicitement_saisi_reste_prioritaire():
    auto = {"lignes": [{"compte": "3421", "montant": 120,
                        "echeance_auto": {"plus_un_an": 0, "moins_un_an": 0, "echues": 120}}]}
    contenu = {"autres_analyses_neant": True, "ventilations": {"3421": {"echues": 0, "moins_un_an": 120}}}
    assert etic._erreurs_ventilation_b6_b7("B6", auto, contenu) == []
    assert etic._ventilation_publiee("B6", auto, contenu)[0]["echues"] == 0
