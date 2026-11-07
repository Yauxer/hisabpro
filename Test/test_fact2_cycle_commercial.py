from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'
SRC = ROOT / 'src'


def read(p):
    return p.read_text(encoding='utf-8')


def test_bc_exposes_delivery_and_invoicing_progress():
    schemas = read(BACK / 'schemas.py')
    router = read(BACK / 'routers' / 'commercial.py')
    for token in [
        'livraison_pct', 'facturation_pct', 'reste_a_livrer_ht',
        'reste_a_facturer_ht', 'nb_bons_logistiques', 'nb_factures',
    ]:
        assert token in schemas
        assert token in router
    assert 'source_ligne_bc_id.in_(ids)' in router


def test_direct_bc_invoice_is_blocked_after_partial_invoice():
    router = read(BACK / 'routers' / 'commercial.py')
    block = router.split('def convertir_bc_en_facture', 1)[1].split('def consulter_reliquat', 1)[0]
    assert '_deja_facture_par_ligne' in block
    assert 'déjà facturé, au moins partiellement' in block


def test_partial_delivery_and_reception_remain_available_until_reliquat_zero():
    ui = read(SRC / 'pages' / 'Commercial.jsx')
    assert "(bc.livraison_pct || 0) < 100" in ui
    assert 'Un bon de réception (' not in ui
    assert 'plusieurs BR' in ui


def test_bc_becomes_structurally_immutable_after_downstream_document():
    router = read(BACK / 'routers' / 'commercial.py')
    block = router.split('def modifier_bc', 1)[1].split('@router_bc.delete', 1)[0]
    assert 'a déjà généré un document en aval' in block
    assert 'champs_structurels' in block
    delete = router.split('def supprimer_bc', 1)[1].split('@router_bc.post("/{bc_id}/convertir-facture"', 1)[0]
    assert 'a déjà généré une livraison/réception ou une facture' in delete


def test_closed_exercise_is_reported_before_postgresql_500_for_payments():
    router = read(BACK / 'routers' / 'commercial.py')
    create = router.split('def creer_reglement', 1)[1].split('class TransitionIn', 1)[0]
    assert '_verifier_date_operation_ouverte(db, societe_id, data.date, "règlement")' in create
    assert 'verifier_date_ecriture' in router
    assert 'date_operation > _date.today()' in router
    transition = router.split('def transition_reglement', 1)[1].split('@router_regl.patch', 1)[0]
    assert '_verifier_date_operation_ouverte' in transition


def test_payment_before_invoice_redirects_to_deposit_workflow():
    router = read(BACK / 'routers' / 'commercial.py')
    create = router.split('def creer_reglement', 1)[1].split('class TransitionIn', 1)[0]
    assert 'data.date < facture.date' in create
    assert 'module Acomptes' in create


def test_accounted_payment_is_not_editable_or_deletable_normally():
    router = read(BACK / 'routers' / 'commercial.py')
    edit = router.split('def modifier_reglement', 1)[1].split('@router_regl.delete', 1)[0]
    assert 'ses données financières sont figées' in edit
    assert 'annulation/contrepassation' in edit
    delete = router.split('def supprimer_reglement', 1)[1].split('# ═══════════════════════════════════════════════════════════════════════════════\n# BON DE RÉCEPTION', 1)[0]
    assert 'ne peut plus être supprimé' in delete


def test_bc_table_is_direct_for_user():
    ui = read(SRC / 'pages' / 'Commercial.jsx')
    assert '<th>Livraison</th><th>Facturation</th>' in ui
    assert 'MAD HT restant' in ui
    assert 'Facturer directement la commande' in ui
    assert 'TVA, remises et rabais sont repris du bon de commande' in ui
    assert 'La date doit appartenir à un exercice comptable ouvert.' in ui


def test_bl_deletion_recalculates_bc_progress_state():
    router = read(BACK / 'routers' / 'commercial.py')
    delete = router.split('def supprimer_bl', 1)[1].split('# ═══════════════════════════════════════════════════════════════════════════════\n# RÈGLEMENTS', 1)[0]
    assert 'reliquat_bon_commande' in delete
    assert '_deja_facture_par_ligne' in delete
    assert 'bc.statut = "en_attente"' in delete
