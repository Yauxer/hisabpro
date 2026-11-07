"""Les cinq avances sont accessibles et calculables depuis le catalogue Paie réel."""
from contextlib import closing
from decimal import Decimal
import pytest
from playwright.sync_api import sync_playwright,expect
from test_modeles_avances_runtime_isole import (
    application,application091,application090,application089,application087,migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion,observer
from test_e2e_facturation_isole import champ
from recette_restauration_consolidee_084 import empreintes_tables
from browser_support import chromium_executable

ORACLES=[
    ('paie_avance_banque','BQ',[('3431',100,0),('5141',0,100)]),
    ('paie_avance_especes','CA',[('3431',100,0),('5161',0,100)]),
    ('paie_recuperation_avance','SA',[('4432',100,0),('3431',0,100)]),
    ('paie_remboursement_avance_banque','BQ',[('3431',0,100),('5141',100,0)]),
    ('paie_remboursement_avance_especes','CA',[('3431',0,100),('5161',100,0)]),
]


def comptabilite_et_catalogue(app):
    return {k:v for k,v in empreintes_tables(app['engine']).items()
            if k in {'ecritures','lignes_ecriture','modeles_ecritures','lignes_modele'}}


@pytest.mark.parametrize('largeur',[1440,390])
def test_cinq_modeles_paie_categorie_calcul_et_annulation_sans_ecriture(application,largeur):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        modeles={m['code']:m for m in ok(api.get('/api/modeles'))}
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
            erreurs,serveur=observer(page,application['api_url'])
            page.on('dialog',lambda d:d.accept())
            connexion(page,application['web_url'],email,password)
            avant=comptabilite_et_catalogue(application)
            for code,journal,attendus in ORACLES:
                page.goto(application['web_url']+'/journal',wait_until='domcontentloaded')
                page.get_by_role('button',name='Nouvelle écriture',exact=True).click()
                modal=page.get_by_role('dialog')
                modal.get_by_role('button',name="Choisir un modèle d'écriture",exact=True).click()
                page.get_by_role('button',name='Paie',exact=True).click()
                for autre,_,_ in ORACLES:
                    expect(page.get_by_text(modeles[autre]['libelle'],exact=True)).to_be_visible()
                page.get_by_role('button').filter(has=page.get_by_text(modeles[code]['libelle'],exact=True)).click()
                expect(champ(modal,'Journal','select')).to_have_value(journal)
                lignes=modal.locator('tbody tr');expect(lignes).to_have_count(3)
                sens='Débit' if attendus[0][1] else 'Crédit'
                lignes.nth(0).locator(f'td[data-label="{sens} (MAD)"] input').fill('100')
                for index,(compte,debit,credit) in enumerate(attendus):
                    ligne=lignes.nth(index)
                    expect(ligne.get_by_placeholder('Ex: 6111')).to_have_value(compte)
                    for cote,valeur in [('Débit',debit),('Crédit',credit)]:
                        assert Decimal(ligne.locator(f'td[data-label="{cote} (MAD)"] input').input_value() or '0')==valeur
                modal.get_by_role('button',name='Annuler',exact=True).click()
                expect(modal).to_have_count(0)
            assert comptabilite_et_catalogue(application)==avant
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()
