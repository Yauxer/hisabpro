from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"


def test_schema_api_accepte_les_sources_de_compte_assistees():
    src = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    assert "compte_source: Optional[str] = Field(default=None, max_length=120)" in src


def test_modele_sqlalchemy_est_aligne_sur_le_schema_api():
    src = (BACKEND / "models.py").read_text(encoding="utf-8")
    assert "compte_source = Column(String(120), nullable=True)" in src


def test_candidat_charges_sans_reference_rentre_dans_la_nouvelle_limite():
    service = (BACKEND / "services" / "fiscalite_retraitements_service.py").read_text(encoding="utf-8")
    value = "Comptes de charges concernés"
    assert value in service
    assert len(value) > 20
    assert len(value) <= 120


def test_migration_elargit_compte_source():
    sql = (BACKEND / "064_fiscal_retraitement_compte_source.sql").read_text(encoding="utf-8")
    assert "ALTER COLUMN compte_source TYPE VARCHAR(120)" in sql
