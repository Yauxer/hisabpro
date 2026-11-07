"""Instruments : mêmes parcours/oracles, vrai main:app et LOGIN SQL limité091.

Les fixtures historiques plus partielles sont remplacées par l'installation
complète, pas les API métier ni les assertions. Aucun SQL rejoué après les pièces.
"""
from test_e2e_runtime_session_isole import (
    application, application090, application089, application087, migration,
)
from test_e2e_encaissement_frais_rapprochement_isole import (
    test_encaissement_frais_validation_proposition_et_lettrage as test_runtime_encaissement_frais_rapprochement_lettrage,
    test_annee_frais_2025_cloture_an2026_pointage_archive_et_fec as test_runtime_annee_frais_cloture_an_fec,
)
from test_e2e_cheque_impaye_isole import (
    test_cheque_impaye_remplacement_validation_et_lettrage as test_runtime_cheque_impaye_remplacement_lettrage,
)
from test_e2e_effets_frais_precision_isole import (
    test_frais_demi_centime_erreur_precise_et_statut_conserve as test_runtime_refus_frais_demi_centime,
)
