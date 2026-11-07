from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"


def test_050_ajoute_les_index_de_reporting_definitif():
    sql = (BACK / "050_balance_grand_livre_final.sql").read_text(encoding="utf-8")
    assert "ix_ecritures_reporting_definitif" in sql
    assert "WHERE est_validee = TRUE AND numero_ecriture IS NOT NULL" in sql
    assert "ix_lignes_ecriture_reporting_compte" in sql
    assert "ix_tiers_reporting_compte_client" in sql
    assert "ix_tiers_reporting_compte_fournisseur" in sql


def test_balance_serveur_calcule_ouverture_mouvements_et_solde_final():
    src = (BACK / "routers" / "ecritures.py").read_text(encoding="utf-8")
    bloc = src[src.index('@router.get("/reporting/balance")'):src.index('@router.get("/reporting/grand-livre")')]
    assert '"solde_initial"' in bloc
    assert '"solde_final"' in bloc
    assert "ec.date < date_from" in bloc
    assert '"ecart_ouverture"' in bloc
    assert '"ecart_mouvements"' in bloc
    assert '"ecart_final"' in bloc


def test_balance_auxiliaire_ne_prend_plus_le_libelle_global_comme_tiers_par_defaut():
    src = (BACK / "routers" / "ecritures.py").read_text(encoding="utf-8")
    assert "def _resoudre_auxiliaire_reporting" in src
    assert '"compte_auxiliaire"' in src
    assert '"identifie"' in src
    assert "Les noms les plus longs sont testés en premier" in src
    # Les tiers historiques inactifs restent identifiables dans les états.
    index_bloc = src[src.index("def _index_tiers_reporting"):src.index("def _prefixe_tiers")]
    assert "models.Tiers.societe_id == societe_id" in index_bloc
    assert ".actif" not in index_bloc and "models.Tiers.actif" not in index_bloc


def test_grand_livre_serveur_expose_solde_ouverture_cumul_et_tiers():
    src = (BACK / "routers" / "ecritures.py").read_text(encoding="utf-8")
    bloc = src[src.index('@router.get("/reporting/grand-livre")'):src.index('MONTANT_QUANTUM')]
    assert '"solde_initial"' in bloc
    assert '"solde_cumule"' in bloc
    assert '"tiers_id"' in bloc
    assert '"tiers_identifie"' in bloc
    assert "soldes_ouverture" in bloc
    assert ".limit(" not in bloc


def test_page_balance_affiche_ouverture_final_et_auxiliaires_identifies():
    page = (SRC / "pages" / "Balances.jsx").read_text(encoding="utf-8")
    css = (SRC / "pages" / "Balances.module.css").read_text(encoding="utf-8")
    assert "Initial D" in page and "Initial C" in page
    assert "Final D" in page and "Final C" in page
    assert "Non identifié" in page
    assert "rapport.auxiliaire" in page
    assert "ecrituresAux" not in page
    assert "tableXLarge" in page
    assert "min-width: 1180px" in css


def test_balance_resultat_ne_masque_plus_les_soldes_anormaux():
    page = (SRC / "pages" / "Balances.jsx").read_text(encoding="utf-8")
    assert "charges.reduce((s, l) => s + l.solde, 0)" in page
    assert "produits.reduce((s, l) => s + l.solde, 0)" in page
    assert "Math.max(0, l.solde)" not in page


def test_comparatif_utilise_la_meme_plage_de_dates_en_n_moins_1():
    page = (SRC / "pages" / "Balances.jsx").read_text(encoding="utf-8")
    assert "decalerAnneeISO(dateDebut, -1)" in page
    assert "decalerAnneeISO(dateFin, -1)" in page
    assert "dateFrom: dateDebutN1, dateTo: dateFinN1" in page


def test_page_grand_livre_a_periode_scroll_detail_et_solde_cumule():
    page = (SRC / "pages" / "GrandLivre.jsx").read_text(encoding="utf-8")
    css = (SRC / "pages" / "GrandLivre.module.css").read_text(encoding="utf-8")
    assert 'type="date" value={dateDebut}' in page
    assert 'type="date" value={dateFin}' in page
    assert "Solde initial" in page
    assert "Solde cumulé" in page
    assert "N° écriture" in page and "Référence" in page and "Tiers" in page
    assert "tiers_identifie" in page
    assert "min-width:1280px" in css
    assert "overflow:auto" in css.replace(" ", "")
