from datetime import date
from pathlib import Path

from services.recouvrement_service import calculer_etat_facture

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_reste_du_tient_compte_reglements_avoirs_acomptes_et_ras():
    r = calculer_etat_facture(
        total_ttc=1200,
        total_ht=1000,
        total_regle=300,
        total_avoirs=120,
        total_acomptes=200,
        taux_ras=10,
        ras_comptabilisee=True,
        echeance=date(2026, 9, 30),
        date_reference=date(2026, 9, 11),
    )
    assert r['montant_ras'] == 100
    assert r['total_impute'] == 720
    assert r['reste_du'] == 480
    assert r['statut_paiement'] == 'partiellement_reglee'
    assert r['statut_echeance'] == 'a_echoir'


def test_facture_soldee_n_est_jamais_affichee_en_retard():
    r = calculer_etat_facture(
        total_ttc=1200, total_ht=1000, total_regle=1200,
        echeance=date(2026, 1, 1), date_reference=date(2026, 9, 11),
    )
    assert r['reste_du'] == 0
    assert r['statut'] == 'reglee'
    assert r['jours_retard'] == 0


def test_balance_agee_31_60_jours():
    r = calculer_etat_facture(
        total_ttc=1000, total_ht=1000,
        echeance=date(2026, 8, 1), date_reference=date(2026, 9, 11),
    )
    assert r['jours_retard'] == 41
    assert r['statut'] == 'en_retard'
    assert r['tranche_age'] == '31_60'


def test_surpaiement_devient_credit_tiers_sans_reste_negatif():
    r = calculer_etat_facture(
        total_ttc=1000, total_ht=1000, total_regle=1100,
        echeance=date(2026, 9, 1), date_reference=date(2026, 9, 11),
    )
    assert r['reste_du'] == 0
    assert r['credit_tiers'] == 100
    assert r['statut'] == 'reglee'


def test_migration_fact7_cree_historique_et_indexes():
    sql = read('hisabpro-backend/034_recouvrement.sql')
    permissions = read('hisabpro-backend/034b_recouvrement_permissions.sql')
    assert 'CREATE TABLE IF NOT EXISTS relances_recouvrement' in sql
    assert 'ck_relance_niveau' in sql
    assert 'ix_factures_recouvrement' in sql
    assert 'ix_reglements_facture_statut' in sql
    assert 'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE relances_recouvrement TO hisabpro' in permissions
    assert 'GRANT USAGE, SELECT, UPDATE ON SEQUENCE relances_recouvrement_id_seq TO hisabpro' in permissions
    assert 'COMMIT;' in sql
    assert 'COMMIT;' in permissions


def test_api_recouvrement_expose_situation_et_relances():
    src = read('hisabpro-backend/routers/recouvrement.py')
    assert '@router.get("/situation")' in src
    assert '@router.get("/relances")' in src
    assert '@router.post("/relances", status_code=201)' in src
    assert 'Cette facture est déjà soldée' in src
    assert 'montant_promis > ligne["reste_du"]' in src


def test_situation_est_calculee_cote_serveur_sans_limite_2000():
    src = read('src/pages/SituationFinanciere.jsx')
    assert '/api/recouvrement/situation?exercice=' in src
    assert 'limit=2000' not in src
    assert 'Échéances & impayés' in src
    assert 'Balance âgée' in src
    assert 'Historique des relances clients' in src


def test_ui_relance_affiche_reste_retard_promesse_et_prochaine_relance():
    src = read('src/pages/SituationFinanciere.jsx')
    assert 'Reste à payer' in src
    assert 'date_promesse_reglement' in src
    assert 'montant_promis' in src
    assert 'prochaine_relance' in src
    assert 'Relancer' in src


def test_main_enregistre_router_recouvrement():
    src = read('hisabpro-backend/main.py')
    assert 'recouvrement' in src
    assert 'app.include_router(recouvrement.router)' in src


def test_hotfix_permissions_fact7_est_rejouable_sur_base_deja_migree():
    sql = read('hisabpro-backend/034b_recouvrement_permissions.sql')
    assert 'relances_recouvrement TO hisabpro' in sql
    assert 'relances_recouvrement_id_seq TO hisabpro' in sql
    assert 'COMMIT;' in sql
