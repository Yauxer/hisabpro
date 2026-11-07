from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "services"))



def txt(path):
    return path.read_text(encoding="utf-8")


def test_catalogue_etic_modele_normal_complet_a1_a3_b1_b14_c1_c5():
    service = txt(BACKEND / "services" / "etic_service.py")
    for code in ["A1","A2","A3","B1","B2","B2bis","B3","B4","B5","B6","B7","B8","B9","B10","B11","B12","B13","B14","C1","C2","C3","C4","C5"]:
        assert f'{{"code": "{code}"' in service
    assert '"sections":"A1-A3, B1-B14, C1-C5"' in service


def test_etic_ne_devine_pas_les_donnees_extra_comptables():
    service = txt(BACKEND / "services" / "etic_service.py")
    for code in ("A1", "A2", "A3", "B8", "B9", "B10", "C1", "C2", "C4", "C5"):
        assert f'{{"code": "{code}", "groupe":' in service
    assert '"mode": "manuel"' in service
    assert '"mode": "assiste"' in service


def test_b12_reutilise_le_moteur_fiscal_patch08():
    service = txt(BACKEND / "services" / "etic_service.py")
    assert "from routers.fiscalite import situation_is" in service
    assert 'data["B12"]' in service
    assert "Réintégrations fiscales (dont IS comptabilisé)" in service
    assert "Bénéfice fiscal imposable" in service


def test_b14_reconstitue_tva_depuis_journal_tv_et_comptes_cgnc():
    service = txt(BACKEND / "services" / "etic_service.py")
    assert '("4455",)' in service
    assert '("34552",)' in service
    assert '("34551",)' in service
    assert 'j=="TV"' in service
    assert "La colonne « déclarations » est reconstituée" in service


def test_b2_compare_registre_immobilisations_et_comptabilite():
    service = txt(BACKEND / "services" / "etic_service.py")
    assert "models.Immobilisation" in service
    assert '"solde_comptable_fin"' in service
    assert '"ecart"' in service


def test_sql_stockage_generique_etic_et_permissions():
    sql = txt(BACKEND / "026_etic_exercice.sql")
    assert "CREATE TABLE IF NOT EXISTS etic_sections_exercice" in sql
    assert "contenu JSONB" in sql
    assert "uq_etic_section_societe_exercice_code" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE etic_sections_exercice TO hisabpro" in sql
    assert "'B2bis'" in sql and "'B14'" in sql and "'C5'" in sql


def test_api_et_interface_exposent_etic():
    router = txt(BACKEND / "routers" / "etats.py")
    api = txt(ROOT / "src" / "services" / "api.js")
    app = txt(ROOT / "src" / "App.jsx")
    sidebar = txt(ROOT / "src" / "components" / "Sidebar.jsx")
    page = txt(ROOT / "src" / "pages" / "Etic.jsx")
    assert '@router.get("/etic/{exercice}")' in router
    assert '@router.put("/etic/{exercice}/{code}")' in router
    assert "/api/etats/etic/${exercice}" in api
    assert '<Route path="etic"' in app
    assert "label: 'ETIC'" not in sidebar
    assert "to: '/liasse-fiscale'" in sidebar
    assert '<Route path="liasse-fiscale"' in app
    cockpit = txt(ROOT / 'src' / 'pages' / 'LiasseFiscale.jsx')
    assert "data.etic?.sections" in cockpit
    assert "navigate('/etic')" in cockpit
    assert "ETIC — État des Informations Complémentaires" in page
    assert "J'ai contrôlé les données automatiques" in page


def test_modele_sqlalchemy_etic_est_multi_societe_et_exercice():
    models = txt(BACKEND / "models.py")
    assert "class ETICSectionExercice" in models
    assert '__tablename__ = "etic_sections_exercice"' in models
    assert 'ForeignKey("societes.id", ondelete="CASCADE")' in models
    assert 'UniqueConstraint("societe_id", "exercice", "code"' in models
