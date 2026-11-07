from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"


def test_048_separe_solde_initial_et_solde_final_sans_perdre_047():
    sql = (BACK / "048_rapprochement_bancaire_final.sql").read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS solde_initial" in sql
    assert "ADD COLUMN IF NOT EXISTS solde_final" in sql
    assert "SET solde_final = solde_releve" in sql
    assert "trg_hisabpro_rapprochement_exercice_cloture" in sql
    assert "trg_hisabpro_rapprochement_etat_cloture" in sql


def test_situation_rapprochement_calcule_le_solde_comptable_cote_serveur():
    src = (BACK / "routers" / "rapprochement.py").read_text(encoding="utf-8")
    assert "def _solde_comptable_fin" in src
    assert "models.Ecriture.est_validee.is_(True)" in src
    assert '"solde_comptable_final"' in src
    assert "models.LigneEcriture.compte == compte" in src


def test_rapprochement_est_lecture_seule_sur_exercice_cloture():
    src = (BACK / "routers" / "rapprochement.py").read_text(encoding="utf-8")
    assert "def _date_est_cloturee" in src
    assert "le rapprochement bancaire est en lecture seule" in src
    assert "_assert_date_modifiable(db, sid, releve.date)" in src
    assert "_assert_plage_modifiable(db, sid, data.date_debut, data.date_fin)" in src


def test_ligne_releve_peut_etre_corrigee_uniquement_avant_rapprochement():
    schema = (BACK / "schemas.py").read_text(encoding="utf-8")
    route = (BACK / "routers" / "rapprochement.py").read_text(encoding="utf-8")
    api = (SRC / "services" / "api.js").read_text(encoding="utf-8")
    assert "class RapprochementLigneUpdate" in schema
    assert "montant:    Optional[float]" in schema
    assert "Dérapprochez cette ligne avant de modifier son contenu" in route
    assert "modifier(id, data)" in api


def test_page_rapprochement_a_scroll_filtres_edition_et_soldes_explicites():
    jsx = (SRC / "pages" / "RapprochementBancaire.jsx").read_text(encoding="utf-8")
    css = (SRC / "pages" / "RapprochementBancaire.module.css").read_text(encoding="utf-8")
    assert "Solde initial du relevé" in jsx
    assert "Solde final du relevé" in jsx
    assert "Contrôle du relevé" in jsx
    assert "rechercheCompta" in jsx and "rechercheReleve" in jsx
    assert "commencerEdition" in jsx and "enregistrerEdition" in jsx
    assert "Exercice clôturé : rapprochement bancaire en lecture seule" in jsx
    assert ".tableWrapper" in css and "overflow: auto" in css
    assert ".tableReleve { min-width: 1050px; }" in css
    assert "position: sticky" in css
