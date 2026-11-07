"""RAS TVA573 et parcours RAS existants sur le même PostgreSQL nonce099."""
import importlib
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)

for prefixe, module in [
    ('capture', 'test_ras_tva_capture_isole'),
    ('interface', 'test_e2e_ras_tva_capture_isole'),
    ('libre', 'test_ras_capture_reglement_postgres'),
    ('simulation', 'test_ras_tva_simulation_isole'),
]:
    for nom, fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):
            globals()[f'test_{prefixe}_{nom[5:]}'] = fonction

from test_e2e_ras_capture_isole import test_captures_declarees_reglements_od_et_annulation_tracees as test_ancien_parcours_capture_lettrage
