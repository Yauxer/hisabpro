"""Autres générateurs nonRH sous100, témoin de provision non vide préservé."""
import importlib
from test_consolidation_intermodules621_isole import (
    application,application100,application099,application098,application097,application093,
    application092,application091,application090,application089,application087,migration)

MODULES=('test_immobilisations_mutations_concurrentes_isole',
    'test_stock_mouvements_ordinaires_isole','test_reglements_par_tiers_isole',
    'test_rapprochement_ventilation_isole','test_annulation_ventilation_isole',
    'test_finalisation_facture_concurrente_isole','test_e2e_acompte_imputation_isole',
    'test_e2e_acompte_fournisseur_isole')
vus=set()
for i,nom in enumerate(MODULES):
    for cle,fonction in vars(importlib.import_module(nom)).items():
        if cle.startswith('test_') and callable(fonction):
            identite=(fonction.__module__,fonction.__qualname__)
            if identite not in vus:
                vus.add(identite);globals()[f'test_generateur_{i}_{cle[5:]}']=fonction
