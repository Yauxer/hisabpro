"""Non-régression inventaire/calcul/clôture/ouverture et familles de provision."""
import importlib
from test_consolidation_contrepassations601_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)

for prefixe,module in [('ancien','test_consolidation_contrepassations601_isole'),
    ('api','test_provisions_comptes603_isole'),('ui','test_e2e_provisions_comptes603_isole')]:
    for nom,fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):
            globals()[f'test_{prefixe}_{nom[5:]}']=fonction
