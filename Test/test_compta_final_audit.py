from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"


def test_047_cree_un_lettrage_separe_des_lignes_definitives():
    sql = (BACK / "047_compta_final_audit.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS lettrages_comptables" in sql
    assert "uq_lettrage_comptable_ligne_actif" in sql
    assert "Le lettrage est réservé aux écritures comptables définitives" in sql
    assert "ALTER TABLE lignes_ecriture\n    ADD COLUMN" not in sql


def test_cloture_ne_peut_plus_forcer_des_dotations_manquantes():
    src = (BACK / "routers" / "cloture.py").read_text(encoding="utf-8")
    assert "forcer_sans_dotations" not in src
    assert "if dotations:" in src


def test_balance_et_grand_livre_serveur_ne_sont_pas_pagines_et_excluent_les_brouillons():
    src = (BACK / "routers" / "ecritures.py").read_text(encoding="utf-8")
    assert '@router.get("/reporting/balance")' in src
    assert '@router.get("/reporting/grand-livre")' in src
    bloc = src[src.index("def _lignes_reporting"):src.index("MONTANT_QUANTUM")]
    assert "models.Ecriture.est_validee.is_(True)" in bloc
    assert "models.Ecriture.numero_ecriture.isnot(None)" in bloc
    assert ".limit(" not in bloc


def test_grand_livre_front_utilise_le_reporting_backend():
    src = (SRC / "pages" / "GrandLivre.jsx").read_text(encoding="utf-8")
    assert "comptabiliteAPI.grandLivre" in src
    assert "useEcritures" not in src
    assert "code_lettrage" in src


def test_balances_front_utilise_les_agregats_backend():
    src = (SRC / "pages" / "Balances.jsx").read_text(encoding="utf-8")
    assert "comptabiliteAPI.balance" in src
    assert "useEcritures" not in src
    assert "rapport.nb_ecritures" in src


def test_lettrage_comptable_est_persistant_et_alimente_le_fec():
    route = (BACK / "lettrage.py").read_text(encoding="utf-8")
    fec = (BACK / "services" / "fec_service.py").read_text(encoding="utf-8")
    front = (SRC / "pages" / "Lettrage.jsx").read_text(encoding="utf-8")
    assert '@router.post("/comptable/lettrer")' in route
    assert "models.LettrageComptable" in route
    assert 'getattr(ligne, "code_lettrage", None)' in fec
    assert 'getattr(ligne, "date_lettrage", None)' in fec
    assert "lettrageAPI.lettrer" in front


def test_rapprochement_est_lie_a_une_ligne_comptable_definitive():
    route = (BACK / "routers" / "rapprochement.py").read_text(encoding="utf-8")
    sql = (BACK / "047_compta_final_audit.sql").read_text(encoding="utf-8")
    assert "ecriture_ligne_id" in route
    assert "models.Ecriture.est_validee.is_(True)" in route
    assert "Cette ligne comptable est déjà rapprochée" in route
    assert "uq_rapprochement_ecriture_ligne_active" in sql
    assert "crédit relevé = débit banque" in sql


def test_rapprochement_front_persiste_solde_et_import():
    src = (SRC / "pages" / "RapprochementBancaire.jsx").read_text(encoding="utf-8")
    assert "rapprochementAPI.enregistrerEtat" in src
    assert "rapprochementAPI.rapprocher" in src
    assert "rapprochementAPI.derapprocher" in src
    assert "rapprochementAPI.importer" in src
    assert "useEcritures" not in src
