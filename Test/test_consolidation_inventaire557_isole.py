"""Qualification regroupée 553/555/557, une application complète nonce098."""
import importlib
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)

for numero, module in (
    ('553', 'test_ajustements_inventaire_isole'),
    ('555', 'test_apercu_inventaire_isole'),
    ('557', 'test_reouverture_periodes_isole'),
):
    for nom, fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):
            globals()[f'test_{numero}_{nom[5:]}'] = fonction
