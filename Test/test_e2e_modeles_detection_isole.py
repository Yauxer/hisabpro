"""Détection réelle de modèle après saisie d'un montant, pas d'API interceptée."""
from contextlib import closing
from decimal import Decimal
import pytest
from sqlalchemy import text
from test_justificatifs_modeles_runtime_isole import (
    application, application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import champ
from browser_support import chromium_executable


@pytest.mark.parametrize('sens,largeur',[('achat',1440),('vente',390)])
def test_detection_conserve_ht_100_tva20_ttc120_et_permet_validation(application,sens,largeur,tmp_path):
    playwright=pytest.importorskip('playwright.sync_api')
    api,email,password=client(application)
    with closing(api),playwright.sync_playwright() as p:
        nom=f'Tiers fictif détection455 {sens}'
        tiers=ok(api.post('/api/tiers',json={'nom':nom,'type':'client' if sens=='vente' else 'fournisseur'}),201)
        code='7111' if sens=='vente' else '6111'
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000})
            page.set_default_timeout(15000)
            errors,server_errors=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/journal',wait_until='domcontentloaded')
            page.get_by_role('button',name='Nouvelle écriture',exact=True).click()
            modal=page.get_by_role('dialog');rows=modal.locator('tbody tr')
            with page.expect_response(lambda r:r.url.endswith('/api/modeles/par-compte/'+code)) as detection:
                rows.nth(0).get_by_placeholder('Ex: 6111').fill(code)
            assert detection.value.status==200
            modal.get_by_text('Modèle détecté',exact=True).wait_for()
            rows.nth(0).locator('td[data-label="'+('Crédit' if sens=='vente' else 'Débit')+' (MAD)"] input').fill('100')
            with page.expect_response(lambda r:r.url.split('?')[0].endswith('/api/tiers') and r.request.method=='GET'):
                modal.get_by_role('button',name='Appliquer',exact=True).click()
            playwright.expect(rows).to_have_count(4)
            valeurs={}
            for row in rows.all():
                compte=row.get_by_placeholder('Ex: 6111').input_value()
                if compte:
                    def montant(col):
                        return Decimal(row.locator(f'td[data-label="{col} (MAD)"] input').input_value().replace(',','.') or '0')
                    valeurs[compte]=(montant('Débit'),montant('Crédit'))
            attendu=({'6111':(100,0),'34552':(20,0),'4411':(0,120)} if sens=='achat' else
                     {'3421':(120,0),'4455':(0,20),'7111':(0,100)})
            assert valeurs==attendu,('Le montant HT saisi doit rester100, sans transformer la contrepartie.',valeurs)
            modal.get_by_placeholder('Nom client / fournisseur...').fill(nom)
            modal.locator('li').filter(has_text=nom).click()
            modal.get_by_text('Auxiliaire sélectionné',exact=True).wait_for()
            champ(modal,'Référence du justificatif').fill('DETECTION-FICTIVE455-'+sens)
            modal.get_by_label('Valider immédiatement',exact=False).check()
            with page.expect_response(lambda r:r.url.endswith('/api/ecritures') and r.request.method=='POST') as enregistrer:
                modal.get_by_role('button',name="Enregistrer l'écriture",exact=True).click()
            assert enregistrer.value.status==201,enregistrer.value.text()
            eid=enregistrer.value.json()['id'];modal.wait_for(state='hidden')
            with application['engine'].connect() as db:
                assert db.scalar(text('SELECT est_validee FROM ecritures WHERE id=:id'),{'id':eid}) is True
                lignes=db.execute(text('SELECT compte,debit,credit,tiers_id FROM lignes_ecriture WHERE ecriture_id=:id'),{'id':eid}).all()
                assert {l.compte:(l.debit,l.credit) for l in lignes}==attendu
                assert next(l.tiers_id for l in lignes if l.compte in ('3421','4411'))==tiers['id']
            assert not errors and not server_errors,(errors,server_errors)
        except BaseException:
            print(page.locator('body').inner_text()[-5000:])
            page.screenshot(path=str(tmp_path/f'detection455-{sens}.png'),full_page=True)
            raise
        finally:browser.close()
