"""Parcours RAS et cockpit, sources finales585, sur un cluster PostgreSQL nonce."""
import importlib
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)

for prefixe, module in [
    ('precedent', 'test_consolidation_ras_tva581_isole'),
    ('empreinte', 'test_ras_tva_registre_empreinte_isole'),
    ('cockpit', 'test_e2e_liasse_ras_tva_isole'),
]:
    for nom, fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):
            globals()[f'test_{prefixe}_{nom[5:]}'] = fonction
