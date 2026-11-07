from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_facth_frontend_effets_ne_reference_plus_variable_indefinie():
    src = read(ROOT / "src/pages/Effets.jsx")
    assert "const fraisNum = Number(frais || 0)" in src
    assert "frais: fraisNum" in src
    assert "Les frais ne peuvent pas dépasser le montant du règlement" in src


def test_facth_creation_article_facture_utilise_date_document():
    src = read(ROOT / "src/pages/Factures.jsx")
    assert "dateDoc={date}" in src
    assert "tauxTVAAvecHistorique(dateDoc, tvafamille)" in src
    assert "tauxTVAAvecHistorique(date, transportTVA).map" in src  # transport facture reste valide


def test_facth_reglement_sans_facture_est_refuse_et_annulation_existe():
    src = read(BACK / "routers/commercial.py")
    assert "Un règlement doit être rattaché à une facture" in src
    assert '@router_regl.post("/{reglement_id}/annuler"' in src
    assert 'contrepassation_de_id=original.id' in src
    assert 'r.statut = "annule"' in src
    assert "reglement.ecriture_id = ecriture.id" in src


def test_facth_reglements_annules_sont_exclus_des_soldes_et_tva():
    factures = read(BACK / "routers/factures.py")
    recouv = read(BACK / "services/recouvrement_service.py")
    delais = read(BACK / "services/delais_paiement_service.py")
    tva = read(BACK / "services/tva_service.py")
    assert 'models.Reglement.statut.notin_(["rejete", "annule"])' in factures
    assert 'models.Reglement.statut.notin_(["rejete", "annule"])' in recouv
    assert 'models.Reglement.statut.notin_(["rejete", "annule"])' in delais
    assert 'statut in {"rejete", "annule"}' in tva


def test_facth_recouvrement_et_delais_respectent_factg():
    recouv = read(BACK / "services/recouvrement_service.py")
    delais = read(BACK / "services/delais_paiement_service.py")
    assert 'models.ImputationAcompte.statut == "active"' in recouv
    assert 'models.UtilisationAvoir.type_utilisation == "imputation"' in recouv
    assert 'models.UtilisationAvoir.statut == "active"' in recouv
    assert 'models.ImputationAcompte.statut == "active"' in delais
    assert 'models.UtilisationAvoir.type_utilisation == "imputation"' in delais
    assert '"type": "avoir_impute"' in delais


def test_facth_avoir_pdf_utilise_identites_figees():
    models_src = read(BACK / "models.py")
    avoirs = read(BACK / "avoirs.py")
    migration = read(BACK / "046_factH_audit_final_facturation.sql")
    assert "societe_snapshot_json = Column(Text, nullable=True)" in models_src
    assert "societe_pour_document(societe, avoir)" in avoirs
    assert "tiers_ice_snapshot=getattr(facture, \"tiers_ice_snapshot\", None)" in avoirs
    assert "notes_snapshot=data.notes" in avoirs
    assert "ALTER TABLE avoirs" in migration


def test_facth_source_document_not_prematurely_marked_converted_by_draft():
    src = read(ROOT / "src/pages/Factures.jsx")
    assert "JSON.stringify({ facture_id: facture.id, statut: 'converti' })" not in src
    assert "JSON.stringify({ facture_id: facture.id, statut: 'facture' })" not in src


def test_facth_date_paiement_annulee_ne_declenche_pas_tva():
    from services.tva_service import date_paiement_effective
    r = SimpleNamespace(statut="annule", date_encaissement=None, mode="virement", date=None)
    assert date_paiement_effective(r) is None


def test_facth_documents_commerciaux_finalises_utilisent_snapshots():
    models_src = read(BACK / "models.py")
    commercial = read(BACK / "routers/commercial.py")
    migration = read(BACK / "046_factH_audit_final_facturation.sql")
    assert "def _figer_document_commercial" in commercial
    assert "societe_pour_document(societe, devis)" in commercial
    assert "societe_pour_document(societe, bc)" in commercial
    assert "societe_pour_document(societe, bl)" in commercial
    assert commercial.count("tiers_snapshot_json = Column(Text, nullable=True)") == 0  # champs ORM dans models.py
    assert models_src.count("tiers_snapshot_json = Column(Text, nullable=True)") >= 3
    assert "ALTER TABLE devis ADD COLUMN IF NOT EXISTS societe_snapshot_json" in migration
    assert "ALTER TABLE bons_commande ADD COLUMN IF NOT EXISTS societe_snapshot_json" in migration
    assert "ALTER TABLE bons_livraison ADD COLUMN IF NOT EXISTS societe_snapshot_json" in migration


def test_facth_conversion_devis_bc_utilise_date_et_exercice_de_conversion():
    commercial = read(BACK / "routers/commercial.py")
    assert "date_bc = _date.today()" in commercial
    assert '_exercice_ref(db, current_user["societe_id"], date_bc), "bc", prefixe_bc' in commercial
    assert "type=\"vente\", date=date_bc" in commercial
    assert "exercice=_exercice_ref(db, current_user[\"societe_id\"], date_bc)" in commercial


def test_facth_formulaire_reglement_legacy_ne_permet_plus_sans_facture():
    src = read(ROOT / "src/pages/Commercial.jsx")
    assert "— Sans facture liée —" not in src
    assert "— Choisir une facture —" in src
    assert "Sélectionnez la facture à régler" in src
    assert "!['rejete', 'annule'].includes(r.statut)" in src


def test_facth_reglement_annule_reste_financierement_immuable():
    commercial = read(BACK / "routers/commercial.py")
    assert 'if r.statut == "annule" and any(v is not None for v in impactants.values())' in commercial
    assert "Ce règlement est annulé : ses données financières sont définitivement figées" in commercial
    assert 'if r.facture_id and r.statut not in ("rejete", "annule")' in commercial


def test_facth_balance_agee_reutilise_moteur_recouvrement_unique():
    src = read(ROOT / "src/pages/Balances.jsx")
    assert "/api/recouvrement/situation?" in src
    assert "/api/avoirs?exercice=" not in src[src.index("function BalanceAgee"):src.index("// ── Onglet 3", src.index("function BalanceAgee"))]
    assert "f.tranches.nonEchu" in src
    assert "f.tranches.t4" in src


def test_facth_facture_affiche_reglements_annules_comme_inactifs():
    src = read(ROOT / "src/pages/Factures.jsx")
    assert "!['rejete', 'annule'].includes(r.statut)" in src
    assert "ANNULÉ — contrepassé" in src
