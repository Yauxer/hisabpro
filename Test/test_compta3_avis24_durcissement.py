"""COMPTA.3 — garde-fous statiques Avis n°24 / irréversibilité."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_migration_038_verrouille_ecritures_et_lignes_definitives():
    sql = read(BACK / "038_compta3_avis24_durcissement.sql")
    assert "contrepassation_de_id" in sql
    assert "hisabpro_proteger_ecriture_definitive" in sql
    assert "hisabpro_proteger_lignes_ecriture_definitive" in sql
    assert "Utilisez une contrepassation" in sql
    assert "uq_ecritures_contrepassation_de" in sql


def test_migration_038_limite_deux_periodes_et_interdit_reouverture():
    sql = read(BACK / "038_compta3_avis24_durcissement.sql")
    assert "'a_venir','ouverte','fermee'" in sql
    assert "au plus deux périodes peuvent être ouvertes simultanément" in sql
    assert "OLD.statut = 'fermee'" in sql
    assert "réouverture interdite" in sql
    assert "hisabpro_proteger_exercice_cloture" in sql
    assert "hisabpro_proteger_trace_cloture" in sql


def test_migration_038_audit_periodes_append_only():
    sql = read(BACK / "038_compta3_avis24_durcissement.sql")
    assert "CREATE TABLE IF NOT EXISTS audit_periodes_comptables" in sql
    assert "hisabpro_auditer_periode" in sql
    assert "audit_periodes_comptables est append-only" in sql
    assert "REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON audit_periodes_comptables FROM hisabpro" in sql


def test_backend_contrepassation_remplace_devalidation():
    src = read(BACK / "routers" / "ecritures.py")
    ast.parse(src)
    assert '@router.post("/{ecriture_id}/contrepasser")' in src
    assert "contrepassation_de_id=original.id" in src
    assert "debit=_montant_decimal(ligne.credit)" in src
    assert "credit=_montant_decimal(ligne.debit)" in src
    assert "COMPTA.3 : une écriture validée est définitive" in src
    assert "est_validee=False" in src  # création des lignes avant numérotation


def test_backend_periodes_et_cloture_definitives():
    service = read(BACK / "services" / "exercices_service.py")
    exercices = read(BACK / "routers" / "exercices.py")
    cloture = read(BACK / "routers" / "cloture.py")
    ast.parse(service); ast.parse(exercices); ast.parse(cloture)
    assert 'STATUTS_PERIODE = {"a_venir", "ouverte", "fermee"}' in service
    assert 'periode.statut != "ouverte"' in service
    assert "une clôture comptable est définitive" in service
    # Le patch 059 remplace les anciennes restrictions de 038 sur les mois,
    # sans revenir sur la clôture annuelle ou l'immuabilité des écritures.
    assert "ouvrir_toutes_periodes" in exercices
    assert "_set_audit_periode" in exercices
    assert "ex.statut == \"cloture\"" in exercices
    assert "db.delete(cloture)" not in cloture
    assert "Les corrections doivent être comptabilisées sur une période ouverte ultérieure" in cloture


def test_schema_et_front_exposent_statut_et_contrepassation():
    schema = read(BACK / "schemas.py")
    journal = read(ROOT / "src" / "pages" / "Journal.jsx")
    api = read(ROOT / "src" / "services" / "api.js")
    ctx = read(ROOT / "src" / "data" / "EcrituresContext.jsx")
    cloture = read(ROOT / "src" / "pages" / "Cloture.jsx")
    assert "est_validee:      bool = False" in schema
    assert "contrepassation_de_id: Optional[int] = None" in schema
    assert "contrepasserEcriture" in journal
    assert "ecrituresAPI.contrepasser" in ctx
    assert "/contrepasser`" in api
    assert "Rouvrir l'exercice" not in cloture
    assert "Fermée (réouvrable)" in cloture


if __name__ == "__main__":
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj):
            obj()
    print("OK — COMPTA.3 Avis 24")
