from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'
SRC = ROOT / 'src'


def read(p):
    return p.read_text(encoding='utf-8')


def test_migration_adds_stable_links_and_snapshots():
    sql = read(BACK / '028_facturation_fondations.sql')
    for token in [
        'factures       ADD COLUMN IF NOT EXISTS tiers_id',
        'lignes_devis ADD COLUMN IF NOT EXISTS article_id',
        'lignes_bon_commande ADD COLUMN IF NOT EXISTS source_ligne_devis_id',
        'lignes_bon_livraison ADD COLUMN IF NOT EXISTS source_ligne_bc_id',
        'lignes_facture ADD COLUMN IF NOT EXISTS source_ligne_bl_id',
        'tiers_ice_snapshot', 'tiers_if_snapshot', 'tiers_rc_snapshot',
    ]:
        assert token in sql
    assert sql.strip().endswith('COMMIT;')


def test_bc_and_bl_keep_vat_and_commercial_conditions():
    models = read(BACK / 'models.py')
    for field in ['tva             = Column(Float, nullable=False, default=20.0)',
                  'remise          = Column(Float, nullable=False, default=0.0)',
                  'remise2         = Column(Float, nullable=False, default=0.0)',
                  'rabais          = Column(Float, nullable=False, default=0.0)']:
        assert field in models

    commercial = read(BACK / 'routers' / 'commercial.py')
    # Conversions must copy VAT from source lines; never force every converted line to 20%.
    assert 'tva=l.tva' in commercial
    assert 'source_ligne_bc_id=l.id' in commercial
    assert 'source_ligne_bl_id=l.id' in commercial
    assert not re.search(r'tva\s*=\s*20(?:\.0)?\s*[,)]', commercial)


def test_documents_and_lines_have_stable_ids():
    models = read(BACK / 'models.py')
    for field in [
        'tiers_id = Column(Integer, ForeignKey("tiers.id", ondelete="SET NULL")',
        'article_id    = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL")',
        'source_ligne_devis_id', 'source_ligne_bc_id', 'source_ligne_bl_id',
    ]:
        assert field in models

    schemas = read(BACK / 'schemas.py')
    assert schemas.count('tiers_id:') >= 8
    assert schemas.count('article_id:') >= 5


def test_invoice_creation_saves_legal_tier_snapshot():
    router = read(BACK / 'routers' / 'factures.py')
    for token in [
        'tiers_ice_snapshot', 'tiers_if_snapshot', 'tiers_rc_snapshot',
        'tiers_adresse_snapshot', 'tiers_ville_snapshot',
        'article_id=(article.id if article else None)',
    ]:
        assert token in router


def test_sidebar_absorbs_commercial_into_facturation():
    sidebar = read(SRC / 'components' / 'Sidebar.jsx')
    assert "label: 'Facturation'" in sidebar
    assert "to: '/commercial'" in sidebar
    assert "label: 'Cycle commercial'" in sidebar
    assert "id: 'commercial'" not in sidebar


def test_user_pipeline_is_in_physical_order():
    ui = read(SRC / 'pages' / 'Commercial.jsx')
    assert '<h1 className={styles.pageTitle}>Cycle commercial</h1>' in ui
    assert 'Devis → Bon de commande → Bon de livraison → Facture → Règlement' in ui
    assert 'Bon de commande → Bon de réception → Facture fournisseur → Règlement' in ui
    # UI tab ordering must match the physical flows.
    vente = ui.split('const ONGLETS_VENTE = [', 1)[1].split(']', 1)[0]
    assert vente.index("id: 'devis'") < vente.index("id: 'bc'") < vente.index("id: 'bl'") < vente.index("id: 'factures'") < vente.index("id: 'regl'")
    achat = ui.split('const ONGLETS_ACHAT = [', 1)[1].split(']', 1)[0]
    assert achat.index("id: 'bc'") < achat.index("id: 'br'") < achat.index("id: 'factures'") < achat.index("id: 'regl'")


def test_devis_stock_shortage_is_warning_not_blocker():
    ui = read(SRC / 'pages' / 'Commercial.jsx')
    assert 'Le devis reste autorisé' in ui
    assert 'Impossible de créer le devis' not in ui


def test_bl_and_br_no_longer_require_invoice_first():
    ui = read(SRC / 'pages' / 'Commercial.jsx')
    assert "Vous devez d'abord créer une facture" not in ui


def test_partial_delivery_uses_stable_bc_line_id():
    ui = read(SRC / 'pages' / 'Commercial.jsx')
    router = read(BACK / 'routers' / 'commercial.py')
    assert 'ligne_bc_id' in ui
    assert 'ligne_bc_id' in router
    assert 'source_ligne_bc_id' in router


def test_multiple_partial_bl_can_each_be_invoiced():
    router = read(BACK / 'routers' / 'commercial.py')
    # Direct BC invoicing still links bc.facture_id. BL invoicing must not overwrite
    # the BC with a single invoice id, otherwise the second partial BL is blocked.
    direct = router.find('bc.facture_id = facture.id')
    bl_ep = router.find('def convertir_bl_en_facture')
    assert direct != -1 and bl_ep != -1 and direct < bl_ep
    assert 'bc.facture_id = facture.id' not in router[bl_ep:]
    # FACT.3 : l'état multi-factures est désormais dérivé des lignes source BL.
    assert '_situation_facturation_bl' in router[bl_ep:]
    assert 'source_ligne_bl_id' in router[bl_ep:]
