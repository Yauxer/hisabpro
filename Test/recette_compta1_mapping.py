"""Recette statique COMPTA.1 — chaîne formulaire -> compte -> écriture."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"


def read(p): return p.read_text(encoding="utf-8")

checks = []
def check(label, condition):
    checks.append((label, bool(condition)))

sql = read(BACK / "032_compta_mapping.sql")
models = read(BACK / "models.py")
schemas = read(BACK / "schemas.py")
articles = read(BACK / "routers" / "articles.py")
factures = read(BACK / "routers" / "factures.py")
commercial = read(BACK / "routers" / "commercial.py")
avoirs = read(BACK / "avoirs.py")
acomptes = read(BACK / "acomptes.py")
acomptes_ui = read(SRC / "pages" / "Acomptes.jsx")
service = read(BACK / "services" / "compta_mapping_service.py")

check("Migration article compte vente", "articles ADD COLUMN IF NOT EXISTS compte_vente" in sql)
check("Migration article compte achat", "articles ADD COLUMN IF NOT EXISTS compte_achat" in sql)
check("Snapshot compte tiers facture", "compte_tiers_snapshot" in sql)
check("Snapshot compte vente ligne", "compte_vente_snapshot" in sql)
check("Snapshot compte achat ligne", "compte_achat_snapshot" in sql)
check("Article backend persiste compte vente", "compte_vente    = Column(String(10), nullable=True)" in models)
check("Article backend persiste compte achat", "compte_achat    = Column(String(10), nullable=True)" in models)
check("Schema article expose compte vente", "compte_vente:    Optional[str]" in schemas)
check("Schema article expose compte achat", "compte_achat:    Optional[str]" in schemas)
check("Article peut effacer surcharge", "model_dump(exclude_unset=True)" in articles)
check("Validation fige comptes", "figer_comptes_facture(db, societe_id, facture)" in factures)
check("Facture ventile par comptes", "groupes_facture_par_compte" in factures)
check("Avoir inverse comptes source", "groupes_avoir_par_compte" in avoirs)
check("Règlement utilise compte tiers", "compte=tiers_compte" in commercial)
check("Règlement utilise banque paramétrée", "compte_tresorerie(" in commercial)
check("RAS utilise compte tiers facture", "compte_tiers_facture(db, societe_id, facture)" in commercial)
check("Acompte rattaché au tiers", "tiers_id" in acomptes)
check("Acompte imputation utilise compte facture", "compte_facture = compte_tiers_facture" in acomptes)
check("Acompte UI propose compte bancaire", "Compte bancaire" in acomptes_ui)
check("Service fallback famille", "compte_famille" in service)
check("Service priorité surcharge article", "override" in service)
check("Service réconciliation centime", "_ajuster_groupes" in service)
check("TVA non déductible répartie", "repartir_par_poids" in factures)
check("Avoir TVA non déductible répartie", "repartir_par_poids" in avoirs)

failed = [label for label, ok in checks if not ok]
for label, ok in checks:
    print(("OK " if ok else "KO ") + label)
print(f"\nCOMPTA.1 : {len(checks)-len(failed)}/{len(checks)} contrôles OK")
if failed:
    raise SystemExit("Échecs : " + ", ".join(failed))
