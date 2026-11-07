"""Ancienne recette inventaire/exports, calcul, clôture annuelle et suivi d'ouverture."""
import importlib
from test_consolidation_prorata595_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)

for prefixe, module in [('ancien','test_consolidation_prorata595_isole'),
    ('cloture','test_e2e_cloture_prorata599_isole'),
    ('api','test_contrepassations_ouverture_isole'),
    ('ui','test_e2e_contrepassations_ouverture_isole')]:
    for nom, fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):
            globals()[f'test_{prefixe}_{nom[5:]}']=fonction
