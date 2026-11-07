"""Préparation, raccordement, précision, exports et Edge sur une cible nonce098."""
import importlib
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)

for numero, module in [
    ('561', 'test_ventes_raccordement_isole'),
    ('423', 'test_ventes_exports_isole'), ('428', 'test_ventes_precision_source_isole'),
    ('UI418', 'test_e2e_ventes_preparation_isole'), ('UI423', 'test_e2e_ventes_exports_isole'),
]:
    for nom, fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):
            globals()[f'test_{numero}_{nom[5:]}'] = fonction

# test_ventes_preparation_isole est exécuté séparément avec son ancien banc.
# Son injection -Infinity reproduit une base historique ; le schéma098 refuse
# déjà cette donnée par CHECK. Ne pas retirer la contrainte pour préparer le test.
