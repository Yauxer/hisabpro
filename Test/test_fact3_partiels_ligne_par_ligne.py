from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'
SRC = ROOT / 'src'


def read(p):
    return p.read_text(encoding='utf-8')


def test_bc_lines_expose_ordered_delivered_invoiced_and_remaining_quantities():
    schemas = read(BACK / 'schemas.py')
    router = read(BACK / 'routers' / 'commercial.py')
    for token in [
        'quantite_commandee', 'quantite_livree', 'quantite_facturee',
        'reste_a_livrer', 'reste_a_facturer', 'livre_non_facture',
    ]:
        assert token in schemas
        assert token in router
    assert 'def _situation_lignes_bc' in router


def test_bl_invoice_reliquat_is_derived_from_source_line_ids():
    router = read(BACK / 'routers' / 'commercial.py')
    assert 'def _facturation_par_ligne_bl' in router
    assert 'source_ligne_bl_id.in_(ids)' in router
    assert 'def _situation_facturation_bl' in router
    assert '@router_bl.get("/{bl_id}/reliquat-facturation")' in router


def test_same_bl_can_generate_multiple_partial_invoices_without_overbilling():
    router = read(BACK / 'routers' / 'commercial.py')
    block = router.split('def convertir_bl_en_facture', 1)[1].split('@router_regl.post("/{reglement_id}/comptabiliser")', 1)[0]
    assert 'ConvertirBLFactureIn' in block
    assert 'reste_a_facturer' in block
    assert 'supérieure au reliquat' in block
    assert 'if not bl.facture_id:' in block
    assert 'bl.facture_id = facture.id' in block
    assert 'déjà entièrement facturé' in block


def test_manual_invoice_api_cannot_exceed_source_bc_or_bl_quantity():
    router = read(BACK / 'routers' / 'factures.py')
    assert 'def _verifier_reliquats_sources' in router
    assert 'quantité facturée' in router
    assert 'supérieure à la quantité livrée/réceptionnée' in router
    assert 'supérieure à la quantité commandée' in router
    # creation + edition
    assert router.count('_verifier_reliquats_sources(') >= 3


def test_user_can_see_line_by_line_cycle_and_partial_invoice_modal():
    ui = read(SRC / 'pages' / 'Commercial.jsx')
    css = read(SRC / 'pages' / 'Commercial.module.css')
    assert 'Voir le détail commandé / livré / facturé' in ui
    assert 'Reste à facturer' in ui
    assert 'reliquat-facturation' in ui
    assert 'Vous pouvez facturer seulement une partie' in ui
    assert 'Facturer tout ou partie du reliquat de ce bon' in ui
    assert '.cycleLineTable' in css
    assert '.quantiteInput' in css


def test_bl_list_shows_facturation_progress_not_single_invoice_flag():
    ui = read(SRC / 'pages' / 'Commercial.jsx')
    bl_block = ui.split('function OngletBonsLivraison', 1)[1].split('function FormulaireReglementComplet', 1)[0]
    assert 'bl.facturation_pct' in bl_block
    assert 'bl.reste_a_facturer_ht' in bl_block
    assert '!bl.facture_id' not in bl_block
