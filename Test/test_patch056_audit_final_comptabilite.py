# -*- coding: utf-8 -*-
"""Patch 056 — dernier audit transversal du noyau comptable."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_056_cloture_definitive_interdite_avant_date_fin():
    src = read(BACK / "routers" / "cloture.py")
    ast.parse(src)
    bloc = src[src.index("def cloturer_exercice"):]
    assert "if date.today() < exercice_obj.date_fin:" in bloc
    assert "Clôture prématurée interdite" in bloc
    # Le garde-fou doit précéder toute préparation de N+1.
    assert bloc.index("if date.today() < exercice_obj.date_fin:") < bloc.index("preparer_exercice_suivant")


def test_056_etat_cloture_expose_la_borne_et_le_frontend_bloque():
    backend = read(BACK / "routers" / "cloture.py")
    ui = read(ROOT / "src" / "pages" / "Cloture.jsx")
    assert '"date_fin_atteinte": date.today() >= exercice_obj.date_fin' in backend
    assert "const dateClotureBloquante" in ui
    assert "|| dateClotureBloquante" in ui
    assert "HisabPro interdit la clôture définitive avant sa date de fin paramétrée" in ui


def test_056_fec_est_recontrole_apres_ecritures_techniques_avant_verrouillage():
    src = read(BACK / "routers" / "cloture.py")
    bloc = src[src.index("def cloturer_exercice"):]
    final_pos = bloc.index("fec_final = controler_fec_exercice")
    an_pos = bloc.index("ecriture_an = models.Ecriture")
    lock_pos = bloc.index("cloture = models.ClotureExercice")
    assert an_pos < final_pos < lock_pos
    assert "Clôture annulée : le contrôle FEC final" in bloc
    assert "db.rollback()" in bloc[final_pos:lock_pos]


def test_056_manuel_est_aligne_avec_plan_societe_et_exercices_decales():
    doc = read(ROOT / "docs" / "MANUEL_SYSTEME_COMPTABLE_HISABPRO.md")
    assert "**Plan comptable par société**" in doc
    assert "**Exercices décalés**" in doc
    assert "douze mois calendaires" in doc
    assert "ne peut pas être déclenchée avant la date de fin" in doc
    assert "une seconde fois après leur génération" in doc
    assert "n'est donc pas encore supporté" not in doc
    assert "n'est pas encore un référentiel persistant administrable" not in doc


def test_056_limites_de_conformite_restent_explicites():
    doc = read(ROOT / "docs" / "MANUEL_SYSTEME_COMPTABLE_HISABPRO.md")
    assert "Restent hors de toute prétention de certification automatique" in doc
    assert "sauvegardes" in doc
    assert "archivage durable" in doc
    assert "formalités de dépôt fiscal" in doc
    assert "PostgreSQL de recette" in doc
