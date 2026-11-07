"""Sous SQL100 : parcours inventaire antérieurs, suppression613, reprises et Edge."""
import importlib
from test_reprises_provisions615_isole import (
    application,application099,application098,application097,application093,application092,
    application091,application090,application089,application087,migration)

for prefixe,module in [('ancien','test_consolidation_provisions603_isole'),
    ('suppression','test_suppression_inventaire613_isole'),
    ('reprises','test_reprises_provisions615_isole'),('chronologie','test_reprises_chronologie615_isole'),
    ('ui','test_e2e_reprises_provisions615_isole')]:
    for nom,fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):globals()[f'test_{prefixe}_{nom[5:]}']=fonction
