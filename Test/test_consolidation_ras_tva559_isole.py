"""Assistant559 et recettes TVA existantes, même application nonce098."""
import importlib
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)

for numero, module in [('559', 'test_ras_tva_simulation_isole'), ('TVA', 'test_e2e_tva_isole')]:
    for nom, fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):
            globals()[f'test_{numero}_{nom[5:]}'] = fonction
