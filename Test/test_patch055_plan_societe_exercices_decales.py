from datetime import date
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

from services.exercices_utils import date_fin_max_douze_mois, generer_periodes_dates


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_055_exercice_decale_12_mois_est_accepte_et_reference_par_cloture():
    # 01/07/2026 -> 30/06/2027 forme bien douze périodes mensuelles.
    assert len(generer_periodes_dates(date(2026, 7, 1), date(2027, 6, 30))) == 12
    service = read(BACK / "services" / "exercices_service.py")
    assert "def _fin_standard_12_mois" in service
    assert "return date_fin_max_douze_mois(debut)" in service


def test_055_reference_exercice_doit_etre_annee_de_cloture():
    route = read(BACK / "routers" / "exercices.py")
    models = read(BACK / "models.py")
    assert "if fin.year != annee" in route
    assert "EXTRACT(YEAR FROM date_fin)::int = annee" in models


def test_055_exercice_ne_peut_pas_depasser_douze_mois():
    # Limite appréciée en mois calendaires et non avec un simple <= 365 jours.
    assert date_fin_max_douze_mois(date(2023, 1, 1)) == date(2023, 12, 31)
    assert date_fin_max_douze_mois(date(2023, 3, 1)) == date(2024, 2, 29)
    assert date_fin_max_douze_mois(date(2024, 2, 29)) == date(2025, 2, 28)

    # Bornes exactes acceptées, y compris autour d'une année bissextile.
    generer_periodes_dates(date(2023, 1, 1), date(2023, 12, 31))
    generer_periodes_dates(date(2023, 3, 1), date(2024, 2, 29))
    generer_periodes_dates(date(2024, 2, 29), date(2025, 2, 28))

    # Le jour anniversaire est déjà le premier jour d'un 13e mois inclusif.
    with pytest.raises(ValueError):
        generer_periodes_dates(date(2023, 1, 1), date(2024, 1, 1))
    with pytest.raises(ValueError):
        generer_periodes_dates(date(2023, 2, 28), date(2024, 2, 28))
    with pytest.raises(ValueError):
        generer_periodes_dates(date(2024, 2, 29), date(2025, 3, 1))
    with pytest.raises(ValueError):
        generer_periodes_dates(date(2026, 7, 1), date(2027, 7, 1))


def test_055_periodes_mensuelles_traversent_correctement_deux_annees():
    periodes = generer_periodes_dates(date(2026, 7, 1), date(2027, 6, 30))
    assert len(periodes) == 12
    assert periodes[0]["libelle"] == "Juillet 2026"
    assert periodes[-1]["libelle"] == "Juin 2027"
    assert periodes[0]["date_debut"] == date(2026, 7, 1)
    assert periodes[-1]["date_fin"] == date(2027, 6, 30)


def test_055_migration_cree_plan_societe_et_garde_db_sur_comptes_actifs():
    sql = read(BACK / "055_plan_comptable_societe_exercices_decales.sql")
    assert "CREATE TABLE IF NOT EXISTS plan_comptable_cgnc_reference" in sql
    assert "CREATE TABLE IF NOT EXISTS comptes_societe" in sql
    assert "ck_exercice_annee_reference_fin" in sql
    assert "EXTRACT(YEAR FROM date_fin)::int = annee" in sql
    assert "date_debut + INTERVAL '1 year'" in sql
    assert "EXTRACT(MONTH FROM date_debut) = 2" in sql
    assert "EXTRACT(DAY FROM date_debut) = 29" in sql
    assert "CREATE OR REPLACE FUNCTION hisabpro_verifier_compte_societe()" in sql
    assert "BEFORE INSERT OR UPDATE OF compte, ecriture_id ON lignes_ecriture" in sql
    assert "numero=NEW.compte AND actif=TRUE" in sql


def test_055_migration_materialise_le_referentiel_cgnc_complet():
    sql = read(BACK / "055_plan_comptable_societe_exercices_decales.sql")
    js = read(ROOT / "src" / "data" / "planComptes.js")
    comptes_js = set(re.findall(r"\{ compte: '([0-9]{4,10})'", js))
    # Limite la lecture aux VALUES du référentiel, avant l'ON CONFLICT associé.
    bloc = sql.split("INSERT INTO plan_comptable_cgnc_reference", 1)[1].split("ON CONFLICT (numero)", 1)[0]
    comptes_sql = set(re.findall(r"\('([0-9]{4,10})',", bloc))
    assert len(comptes_js) >= 800
    assert comptes_sql == comptes_js


def test_055_saisie_manuelle_refuse_compte_absent_ou_desactive():
    src = read(BACK / "routers" / "ecritures.py")
    assert "def _verifier_comptes_plan" in src
    assert "models.CompteSociete.actif == True" in src
    assert src.count("_verifier_comptes_plan(db, current_user[\"societe_id\"], data.lignes)") >= 2


def test_055_documents_commerciaux_utilisent_exercice_reel_de_la_date():
    commercial = read(BACK / "routers" / "commercial.py")
    factures = read(BACK / "routers" / "factures.py")
    assert "def _exercice_ref" in commercial
    assert "trouver_exercice_pour_date(db, societe_id, d).annee" in commercial
    assert "exercice_bl_annee = _exercice_ref" in commercial
    assert "date_bc.year" not in commercial
    assert "data.date.year" not in commercial
    assert "trouver_exercice_pour_date" in factures


def test_055_immobilisations_et_cloture_utilisent_dates_reelles_exercice():
    immos = read(BACK / "routers" / "immobilisations.py")
    cloture = read(BACK / "routers" / "cloture.py")
    service = read(BACK / "services" / "immobilisations_service.py")
    assert "def _exercice_ouvert_pour_date" in immos
    assert "def _ligne_dotation_exercice" in immos
    assert "dotation_sur_periode" in immos
    assert "def dotation_sur_periode" in service
    assert "exercice_suivant.annee" in cloture


def test_055_plan_societe_alimente_fec_etic_liasse_et_frontend():
    fec = read(BACK / "services" / "fec_service.py")
    etic = read(BACK / "services" / "etic_service.py")
    liasse = read(BACK / "services" / "liasse_service.py")
    layout = read(ROOT / "src" / "components" / "Layout.jsx")
    assert "libelle_compte(compte, db=db, societe_id=societe_id)" in fec
    assert "libelle_compte(c, db=db, societe_id=sid)" in etic
    assert "detail_cpc(s, db=db, societe_id=societe_id)" in liasse
    # Les lectures historiques doivent conserver le libellé des comptes inactifs.
    assert "planComptableAPI.lister(true)" in layout
    cache = read(ROOT / 'src' / 'data' / 'planComptableCache.js')
    assert 'comptesLecture.filter(c => c.actif)' in cache
    selecteurs = read(ROOT / 'src' / 'data' / 'planComptes.js')
    assert 'c.actif !== false' in selecteurs
    assert "planPret" in layout


def test_055_tva_reste_calendaire_et_est_decouplee_exercice_decale():
    page = read(ROOT / "src" / "pages" / "DeclarationTVA.jsx")
    assert "anneesTVADisponibles" in page
    assert "Année civile TVA" in page
    assert "tvaAPI.declaration(anneeTVA" in page
    assert "tvaAPI.parametres(anneeTVA" in page
