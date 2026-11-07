# -*- coding: utf-8 -*-
"""Non-régression de l'ouverture des périodes d'un exercice non clôturé."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


def source(f):
    return f.read_text(encoding="utf-8")


def test_059_default_periodes_non_cloture_toutes_ouvertes():
    src = source(BACK / "services" / "exercices_service.py")
    ast.parse(src)
    bloc = src.split("def _statuts_periodes_par_defaut(", 1)[1].split("def _creer_periodes_si_absentes(", 1)[0]
    assert '"fermee" if getattr(exercice, "statut", None) == "cloture" else "ouverte"' in bloc
    assert "return [statut] * len(periodes)" in bloc
    assert "index_courant" not in bloc


def test_059_synchronisation_ne_ferme_pas_les_mois_et_ne_reouvre_pas_fermures_manuelles():
    src = source(BACK / "services" / "exercices_service.py")
    bloc = src.split("def activer_periodes_de_travail(", 1)[1].split("def _fin_standard_12_mois(", 1)[0]
    assert 'if periode.statut == "a_venir":' in bloc
    assert 'periode.statut = "ouverte"' in bloc
    assert 'periode.statut == "fermee"' not in bloc
    assert "len(ouvertes) >= 2" not in bloc


def test_059_reouverture_admin_individuelle_et_toutes_sans_limite_de_deux():
    src = source(BACK / "routers" / "exercices.py")
    ast.parse(src)
    individuel = src.split("def changer_statut_periode(", 1)[1].split('''@router.post("/{annee}/periodes/ouvrir-toutes")''', 1)[0]
    global_ = src.split("def ouvrir_toutes_periodes(", 1)[1]
    assert "current_user=Depends(requiert_admin)" in individuel
    assert "current_user=Depends(requiert_admin)" in global_
    assert 'p.statut = "ouverte"' in individuel
    assert 'periode.statut = "ouverte"' in global_
    assert "with_for_update().first()" in individuel
    assert "with_for_update().first()" in global_
    assert "ouvertes >= 2" not in src


def test_059_cloture_definitive_jamais_reouverte():
    src = source(BACK / "routers" / "exercices.py")
    sql = source(BACK / "059_ouverture_periodes_comptables.sql")
    assert src.count('models.ClotureExercice.id') >= 2
    assert src.count('ex.statut == "cloture"') >= 2
    assert "v_statut = 'cloture' OR EXISTS" in sql
    assert "FROM clotures_exercice ce" in sql


def test_059_migration_redefinit_garde_et_conserve_audit():
    sql = source(BACK / "059_ouverture_periodes_comptables.sql")
    assert "CREATE OR REPLACE FUNCTION hisabpro_proteger_statut_periode()" in sql
    assert "trg_hisabpro_proteger_statut_periode" in sql
    assert "DROP TRIGGER IF EXISTS trg_hisabpro_audit_periode" not in sql
    assert "DROP TABLE" not in sql
    assert "UPDATE periodes_comptables" not in sql
    assert "v_nb >= 2" not in sql
    assert "COMMIT;" in sql


def test_059_interface_propose_ouvrir_toutes_et_reouverture_individuelle():
    src = source(ROOT / "src" / "pages" / "Cloture.jsx")
    assert "async function ouvrirToutesPeriodes()" in src
    assert "/periodes/ouvrir-toutes" in src
    assert "Ouvrir toutes les périodes" in src
    assert "Fermée (réouvrable)" in src
    assert "disabled = action || verrouillee || !estAdmin()" in src
    assert "Cette période pourra être rouverte ultérieurement" in src


def test_059_documentation_couvre_verrouillage_exercice_et_tracabilite():
    doc = source(ROOT / "docs" / "MANUEL_SYSTEME_COMPTABLE_HISABPRO.md")
    assert "**Périodes comptables (patch 059)**" in doc
    assert "audit append-only" in doc
    assert "clôture définitive" in doc
    assert "contrepassation" in doc
