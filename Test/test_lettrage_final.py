from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"


def test_049_verrouille_lettrage_cloture_et_historique():
    sql = (BACK / "049_lettrage_final.sql").read_text(encoding="utf-8")
    assert "Exercice % clôturé : le lettrage est en lecture seule" in sql
    assert "Historique de lettrage immuable" in sql
    assert "Un lettrage délettré est historique" in sql
    assert "REVOKE DELETE ON lettrages_comptables FROM hisabpro" in sql
    assert "Le code % appartient déjà à un autre compte/tiers/exercice" in sql
    assert "CREATE CONSTRAINT TRIGGER trg_hisabpro_check_lettrage_equilibre" in sql
    assert "DEFERRABLE INITIALLY DEFERRED" in sql
    assert "v_debit <> v_credit" in sql


def test_backend_lettrage_impose_un_auxiliaire_et_un_exercice_ouverts():
    src = (BACK / "lettrage.py").read_text(encoding="utf-8")
    assert "def _cle_tiers_ligne" in src
    assert "if compte not in {\"3421\", \"4411\"}" in src
    assert "Le lettrage doit concerner un seul client/fournisseur" in src
    assert "Le lettrage manuel doit porter sur un même exercice" in src
    assert "_verifier_exercice_modifiable(db, societe_id, exercice)" in src
    assert "Tiers non identifié" in src
    # 959 : équilibre obligatoire sauf lettrage partiel explicitement demandé.
    assert "if debit != credit and not partiel:" in src


def test_generation_codes_lettrage_est_serialisee():
    src = (BACK / "lettrage.py").read_text(encoding="utf-8")
    assert "pg_advisory_xact_lock" in src
    assert "_verrouiller_generation_codes(db, sid)" in src
    assert "Les codes historiques désactivés restent réservés" in src


def test_lettrage_auto_groupe_sur_ligne_auxiliaire_et_date_proche():
    src = (BACK / "lettrage.py").read_text(encoding="utf-8")
    assert "_normaliser_tiers(l.libelle)" in src
    assert "groupes.setdefault(((ligne.compte or \"\").strip(), cle_tiers)" in src
    assert "abs((x[1].date - ecriture_debit.date).days)" in src
    # L'ancien regroupement sur le libellé global de l'écriture ne doit plus piloter l'auto-lettrage.
    bloc = src[src.index('@router.post("/comptable/auto")'):src.index('def _prochain_code')]
    assert "e.libelle or l.libelle" not in bloc


def test_anciennes_routes_mutantes_sont_desactivees():
    src = (BACK / "lettrage.py").read_text(encoding="utf-8")
    assert "Ancienne API désactivée : utilisez le lettrage comptable" in src
    assert "Ancienne API désactivée : utilisez /api/rapprochement" in src
    assert "def lettrer_legacy" in src
    assert "def rapprocher_legacy" in src


def test_page_lettrage_a_filtres_scroll_et_mode_lecture_seule():
    page = (SRC / "pages" / "Lettrage.jsx").read_text(encoding="utf-8")
    css = (SRC / "pages" / "Lettrage.module.css").read_text(encoding="utf-8")
    assert "exercice?.statut === 'cloture'" in page
    assert "Lettrage auto exact" in page
    assert "Non lettrées" in page
    assert "N° écriture" in page and "Référence" in page and "Date lettrage" in page
    assert "tiersLigne" in page
    assert "memeAuxiliaire" in page
    assert "min-width: 1450px" in css
    assert "overflow: auto" in css
    assert "position: sticky" in css


def test_selection_garde_les_totaux_meme_si_un_filtre_cache_des_lignes():
    page = (SRC / "pages" / "Lettrage.jsx").read_text(encoding="utf-8")
    assert "const lignesSelectionnees = useMemo" in page
    assert "lignes.filter(l => selection.has(l.ligne_id))" in page
    assert "for (const l of lignesSelectionnees)" in page


def test_fec_et_grand_livre_prechargent_les_metadonnees_de_lettrage():
    fec = (BACK / "routers" / "fec.py").read_text(encoding="utf-8")
    ecritures = (BACK / "routers" / "ecritures.py").read_text(encoding="utf-8")
    assert "joinedload(models.Ecriture.lignes).joinedload(models.LigneEcriture.lettrages)" in fec
    assert "options(joinedload(models.LigneEcriture.lettrages))" in ecritures
