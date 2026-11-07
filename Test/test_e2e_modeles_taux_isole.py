"""Changer le taux proposé conserve HT : oracles100/20/120→100/10/110."""
from datetime import date
from decimal import Decimal
import pytest
from playwright.sync_api import sync_playwright,expect
from test_e2e_runtime_session_isole import application,application090,application089,application087,migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion,observer
from test_e2e_facturation_isole import champ
from browser_support import chromium_executable


@pytest.mark.parametrize('sens,largeur',[('vente',1440),('achat',390)])
def test_taux_modele_20_10_zero_20_conserve_ht_et_equilibre(application,sens,largeur):
    api,email,password=client(application)
    try:
        nom='Tiers fictif TVA465 '+sens
        ok(api.post('/api/tiers',json={'nom':nom,'type':'client' if sens=='vente' else 'fournisseur'}),201)
        m=next(m for m in ok(api.get('/api/modeles')) if m['code']==('vente_marchandises' if sens=='vente' else 'achat_marchandises'))
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
                errors,server_errors=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/journal')
                page.get_by_role('button',name='Nouvelle écriture',exact=True).click()
                modal=page.get_by_role('dialog')
                modal.get_by_role('button',name="Choisir un modèle d'écriture",exact=True).click()
                page.get_by_placeholder('Rechercher une opération...').fill(m['libelle'])
                with page.expect_response(lambda r:r.url.split('?')[0].endswith('/api/tiers') and r.request.method=='GET'):
                    page.get_by_role('button').filter(has=page.get_by_text(m['libelle'],exact=True)).click()
                rows=modal.locator('tbody tr');expect(rows).to_have_count(4)
                index=2 if sens=='vente' else 0
                rows.nth(index).locator('td[data-label="'+('Crédit' if sens=='vente' else 'Débit')+' (MAD)"] input').fill('100')
                taux=modal.locator('select').filter(has=page.locator('option[value="20"]')).filter(has=page.locator('option[value="10"]'))
                for valeur,attendus in [('10',[110,10,100] if sens=='vente' else [100,10,110]),
                                         ('0',[100,0,100]),('20',[120,20,100] if sens=='vente' else [100,20,120])]:
                    taux.select_option(valeur)
                    for i,montant in enumerate(attendus):
                        champ_montant=rows.nth(i).locator(f'td[data-label="'+('Débit' if m['lignes'][i]['sens']=='debit' else 'Crédit')+' (MAD)"] input')
                        assert Decimal(champ_montant.input_value() or '0')==Decimal(montant)
                champ(modal,'Référence du justificatif').fill('TVA-FICTIVE465-'+sens)
                modal.get_by_placeholder('Nom client / fournisseur...').fill(nom)
                modal.locator('li').filter(has_text=nom).click()
                expect(modal.get_by_text('Auxiliaire sélectionné',exact=True)).to_be_visible()
                modal.get_by_label('Valider immédiatement',exact=False).check()
                with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/api/ecritures')) as saved:
                    modal.get_by_role('button',name="Enregistrer l'écriture",exact=True).click()
                assert saved.value.status==201,saved.value.text()
                e=ok(api.get('/api/ecritures',params={'exercice':date.today().year}))[0]
                assert e['est_validee']
                assert sum(l['debit'] for l in e['lignes'])==sum(l['credit'] for l in e['lignes'])==120
                assert not errors,errors
                assert not server_errors,server_errors
            finally:browser.close()
    finally:api.close()
