"""Modèles existants → Journal définitif → trésorerie manuelle → lettrage → FEC.

Ce parcours ne crée pas de facture ni de règlement commercial hors facture.
Le taux20 est celui du modèle fictivement utilisé, sans qualification fiscale.
"""
from contextlib import closing
from datetime import date
from decimal import Decimal
import re

import pytest
from sqlalchemy import text

from test_justificatifs_modeles_runtime_isole import (
    application, application090, application089, application087, migration,
    original, pdf_fictif,
)
from test_multi_societes_runtime_isole import ok
from test_ras_lecture_conservation import client
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import champ
from browser_support import chromium_executable


@pytest.mark.parametrize('sens,largeur',[('achat',1440),('vente',390)])
def test_modeles_100_20_120_tiers_validation_lettrage_fec(application,sens,largeur,tmp_path):
    playwright=pytest.importorskip('playwright.sync_api')
    api,email,password=client(application)
    with closing(api),playwright.sync_playwright() as p:
        sid=ok(api.get('/api/auth/me'))['societe_id']
        collectif='4411' if sens=='achat' else '3421'
        nom=f'Tiers fictif modèles454 {sens}'
        tiers=ok(api.post('/api/tiers',json={'nom':nom,'type':'fournisseur' if sens=='achat' else 'client'}),201)
        modeles={m['code']:m for m in ok(api.get('/api/modeles'))}
        operation=modeles['achat_marchandises' if sens=='achat' else 'vente_marchandises']
        tresorerie=modeles['paiement_fournisseur' if sens=='achat' else 'encaissement_client']
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True)
            page.set_default_timeout(15000)
            errors,server_errors=observer(page,application['api_url'])
            # Conserver la cause des écrans vides intermittents, sans changer les attentes.
            navigation_errors=[]
            page.on('requestfailed',lambda req:navigation_errors.append({'url':req.url.split('?')[0],'failure':req.failure}))
            page.on('console',lambda msg:navigation_errors.append({'console':msg.text[:600]}) if msg.type=='error' else None)
            page.on('dialog',lambda d:d.accept())
            connexion(page,application['web_url'],email,password)
            ids=[]
            for index,modele in enumerate((operation,tresorerie)):
                page.goto(application['web_url']+'/journal',wait_until='domcontentloaded')
                page.get_by_role('button',name='Nouvelle écriture',exact=True).click()
                modal=page.get_by_role('dialog')
                modal.get_by_role('button',name="Choisir un modèle d'écriture",exact=True).click()
                page.get_by_placeholder('Rechercher une opération...').fill(modele['libelle'])
                with page.expect_response(lambda r:r.url.split('?')[0].endswith('/api/tiers') and r.request.method=='GET') as liste_tiers:
                    page.get_by_role('button').filter(has=page.get_by_text(modele['libelle'],exact=True)).click()
                assert liste_tiers.value.status==200
                rows=modal.locator('tbody tr')
                playwright.expect(rows).to_have_count(len(modele['lignes'])+1)
                if index==0:
                    compte_montant='6111' if sens=='achat' else '7111'
                    sens_montant='Débit' if sens=='achat' else 'Crédit'
                    montant='100'
                else:
                    compte_montant='4411' if sens=='achat' else '5141'
                    sens_montant='Débit';montant='120'
                ligne=next(i for i,l in enumerate(modele['lignes']) if l['compte']==compte_montant)
                rows.nth(ligne).locator(f'td[data-label="{sens_montant} (MAD)"] input').fill(montant)
                aux=next(i for i,l in enumerate(modele['lignes']) if l['compte']==collectif)
                champ_tiers=rows.nth(aux).get_by_placeholder('Nom client / fournisseur...')
                champ_tiers.fill(nom)
                modal.locator('li').filter(has_text=nom).click()
                modal.get_by_text('Auxiliaire sélectionné',exact=True).wait_for()
                ref=f'MODELE-FICTIF454-{sens}-{index}'
                champ(modal,'Référence du justificatif').fill(ref)
                modal.get_by_label('Valider immédiatement',exact=False).check()
                with page.expect_response(lambda r:r.url.endswith('/api/ecritures') and r.request.method=='POST') as enreg:
                    modal.get_by_role('button',name="Enregistrer l'écriture",exact=True).click()
                assert enreg.value.status==201,enreg.value.text()
                eid=enreg.value.json()['id'];ids.append(eid)
                modal.wait_for(state='hidden')
                with application['engine'].connect() as db:
                    e=db.execute(text('SELECT journal,est_validee,source FROM ecritures WHERE id=:id'),{'id':eid}).one()
                    assert e.est_validee and e.journal==modele['journal'] and e.source=='manuel'
                    lignes=db.execute(text('SELECT compte,debit,credit,tiers_id FROM lignes_ecriture WHERE ecriture_id=:id ORDER BY compte'),{'id':eid}).all()
                    expected=({'6111':(100,0),'34552':(20,0),'4411':(0,120)} if sens=='achat' else
                              {'3421':(120,0),'4455':(0,20),'7111':(0,100)}) if index==0 else (
                              {'4411':(120,0),'5141':(0,120)} if sens=='achat' else {'5141':(120,0),'3421':(0,120)})
                    assert {l.compte:(l.debit,l.credit) for l in lignes}==expected
                    assert next(l.tiers_id for l in lignes if l.compte==collectif)==tiers['id']
            avant={eid:original(application,eid) for eid in ids}
            # Rattachement documentaire après validation ; aucune écriture modifiée.
            f=ok(api.post(f'/api/attachments/ecriture/{ids[0]}',files={'file':('modele-fictif454.pdf',pdf_fictif(),'application/pdf')}))
            assert api.get(f['url']).content==pdf_fictif()
            page.goto(application['web_url']+'/lettrage',wait_until='domcontentloaded')
            champ(page,'Compte','select').select_option(collectif)
            champ(page,'Tiers','select').select_option(label=nom)
            boxes=page.locator('tbody input[type=checkbox]')
            playwright.expect(boxes).to_have_count(2)
            for box in boxes.all():box.check()
            with page.expect_response(lambda r:'/api/lettrage' in r.url and r.request.method=='POST') as lettre:
                page.get_by_role('button',name='Lettrer 2 lignes',exact=True).click()
            assert lettre.value.status==200,lettre.value.text()
            page.get_by_text('2 lettrée(s)',exact=True).wait_for()
            page.reload(wait_until='domcontentloaded')
            champ(page,'Compte','select').select_option(collectif)
            champ(page,'Tiers','select').select_option(label=nom)
            page.get_by_text('2 lettrée(s)',exact=True).wait_for()
            assert {eid:original(application,eid) for eid in ids}==avant
            with application['engine'].connect() as db:
                totaux=db.execute(text('SELECT sum(l.debit),sum(l.credit) FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid'),{'sid':sid}).one()
                assert tuple(totaux)==(240,240)
                assert db.scalar(text('SELECT count(*) FROM factures WHERE societe_id=:sid'),{'sid':sid})==0
                assert db.scalar(text('SELECT count(*) FROM reglements WHERE societe_id=:sid'),{'sid':sid})==0
            r=api.get('/api/fec/export',params={'exercice':date.today().year})
            assert r.status_code==200,r.text
            fec=[line.split('\t') for line in r.text.rstrip('\r\n').splitlines()]
            assert len(fec)==6 and all(len(row)==18 for row in fec)
            assert sum(Decimal(row[11].replace(',','.')) for row in fec[1:])==Decimal('240')
            assert sum(Decimal(row[12].replace(',','.')) for row in fec[1:])==Decimal('240')
            lettres=[row[13] for row in fec[1:] if row[4]==collectif]
            assert len(lettres)==2 and len(set(lettres))==1 and re.fullmatch('[A-Z]{3,}',lettres[0])
            (tmp_path/f'modeles454-{sens}.txt').write_bytes(r.content)
            assert not errors and not server_errors,(errors,server_errors)
        except BaseException:
            print(page.url,page.locator('body').inner_text()[-6500:])
            print('DIAGNOSTIC_NAVIGATION',errors,server_errors,navigation_errors)
            page.screenshot(path=str(tmp_path/f'modeles454-{sens}.png'),full_page=True)
            raise
        finally:browser.close()
