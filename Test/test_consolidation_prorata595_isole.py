"""Calcul documentaire, anciens ajustements et téléchargements GET/POST."""
import importlib
from test_ras_tva_capture_isole import (
    application,application098,application097,application093,application092,
    application091,application090,application089,application087,migration,
)

for prefixe,module in [('inventaire','test_consolidation_inventaire557_isole'),
    ('calcul','test_prorata_inventaire_isole'),('parcours','test_e2e_prorata_inventaire_isole'),
    ('exports','test_e2e_ras_tva_registre_isole')]:
    for nom,fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):globals()[f'test_{prefixe}_{nom[5:]}']=fonction
