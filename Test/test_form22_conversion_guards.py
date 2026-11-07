from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_devis_api_exposes_real_downstream_documents():
    schemas = read("hisabpro-backend/schemas.py")
    commercial = read("hisabpro-backend/routers/commercial.py")
    assert "bon_commande_id: Optional[int] = None" in schemas
    assert "bon_commande_numero: Optional[str] = None" in schemas
    assert '"bon_commande_id": bc_id' in commercial
    assert '"bon_commande_numero": bc_num' in commercial
    assert "_facture_directe_du_devis" in commercial


def test_devis_transform_buttons_only_exist_when_no_downstream_document():
    src = read("src/pages/Commercial.jsx")
    assert "d.statut === 'accepte' && !d.bon_commande_id && !d.facture_id" in src
    assert "Document déjà transformé" in src
    assert "Facture créée" in src
    assert "BC créé" in src


def test_opening_invoice_form_does_not_mark_devis_converted():
    src = read("src/pages/Commercial.jsx")
    block = src[src.index("async function convertirEnFacture"):src.index("async function charger()")]
    assert "statut: 'converti'" not in block
    factures = read("src/pages/Factures.jsx")
    assert "JSON.stringify({ facture_id: facture.id, statut: 'converti' })" not in factures
    assert "JSON.stringify({ facture_id: facture.id, statut: 'facture' })" not in factures
    assert "Les liens amont sont portés par les lignes source" in factures


def test_devis_to_bc_is_locked_and_rejects_existing_downstream_document():
    src = read("hisabpro-backend/routers/commercial.py")
    block = src[src.index("def convertir_devis_en_bc"):src.index("# ═══════════════════════════════════════════════════════════════════════════════\n# BON DE COMMANDE")]
    assert ".with_for_update().first()" in block
    assert "facture_existante = _facture_directe_du_devis" in block
    assert 'devis.statut = "converti"' in block
    assert "HTTPException(409" in block


def test_direct_invoice_from_devis_is_protected_server_side():
    src = read("hisabpro-backend/routers/factures.py")
    assert "def _verifier_conversion_directe_devis" in src
    assert "Poursuivez la facturation depuis ce BC" in src
    assert "Une facture ({libelle}) existe déjà pour ce devis" in src
    create = src[src.index("def creer_facture"):src.index("@router.post(\"/{facture_id}/valider\")")]
    assert "_verifier_conversion_directe_devis(db, societe_id, data.lignes)" in create


def test_completed_transformation_is_visually_an_state_not_an_action():
    css = read("src/pages/Commercial.module.css")
    assert ".transformDone" in css
    assert "cursor: default" in css
