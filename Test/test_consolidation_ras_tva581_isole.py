"""Captures et registre099 : parcours connexes sur un même cluster nonce."""
import importlib
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)

for prefixe, module in [
    ('precedent', 'test_consolidation_ras_tva573_isole'),
    ('taux', 'test_ras_tva_taux_ht_isole'),
    ('registre', 'test_ras_tva_registre_isole'),
    ('interface', 'test_e2e_ras_tva_registre_isole'),
]:
    for nom, fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):
            globals()[f'test_{prefixe}_{nom[5:]}'] = fonction
