"""API/Edge/PostgreSQL nonce : ventilations, clôture, AN et paiement N des factures N-1."""
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path
import json
import uuid
import pytest
from openpyxl import load_workbook
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_e2e_administration_isole import connexion, observer
from test_e2e_annee_connectee_isole import ok, lignes_comptables, valider_brouillons_ui, ORACLE as PROFIL
from test_e2e_balances_exports_isole import telecharger

ORACLE=json.loads((Path(__file__).resolve().parents[1]/'docs/recette/oracle_annee_ventilation_2025_2026.json').read_text(encoding='utf-8'))


def ok_ui(response,statut=200):
    assert response.status==statut,response.text()
    return response.json()


def test_oracle_independant_ventilations_soldes_et_an():
    factures=ORACLE['factures_par_sens']
    for f in factures:
        assert D(f['ht'])+D(f['tva'])==D(f['ttc'])
    assert sum(map(D,ORACLE['ventilations']))==D(ORACLE['paiement_par_sens_2025'])==240
    assert sum(D(f['ttc']) for f in factures)-240==D(ORACLE['reste_par_sens'])==120
    assert 1000+2*360+2*240==D(ORACLE['journal_avant_impot']['debit'])==2200
    assert 1+4+4==ORACLE['journal_avant_impot']['ecritures']
    assert 2+4*3+4*2==ORACLE['journal_avant_impot']['lignes']
    assert 300*D('.0025')==D(ORACLE['impot_laboratoire']['proportionnelle'])==D('.75')
    for champ,total in [('soldes_an_2026','total_an'),('soldes_2026_apres_reglements','total_soldes_2026')]:
        soldes=list(map(D,ORACLE[champ].values()))
        assert sum(soldes)==0
        assert sum(x for x in soldes if x>0)==D(ORACLE[total])
        assert -sum(x for x in soldes if x<0)==D(ORACLE[total])
    assert D(ORACLE['soldes_an_2026']['3421'])-120==0
    assert D(ORACLE['soldes_an_2026']['4411'])+120==0


def soldes(db,sid,annee):
    result=defaultdict(lambda:D(0))
    for e in db.query(models.Ecriture).filter_by(societe_id=sid,exercice=annee):
        for l in e.lignes: result[l.compte]+=l.debit-l.credit
    return dict(result)


def test_annee_ventilation_cloture_an_reglements_anciens_lettrage_et_exports(application,tmp_path,controle_banque=None):
    api,email,password=client(application)
    try:
        societe=ok(api.patch('/api/societe/moi',json={'forme_juridique':'SARL','regime_fiscal':'is','regime_tva':'encaissement',
            'periodicite_tva':'mensuelle','devise':'MAD','capital_social':1000,'exercice_debut':2020}))
        sid=societe['id']
        annees={e['annee'] for e in ok(api.get('/api/exercices'))}
        for annee in [2025,2026]:
            if annee not in annees:
                ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}),201)
        ok(api.put('/api/fiscalite/is/2025/parametres',json=PROFIL['profil']['parametres_is']))
        ok(api.post('/api/ecritures',json={'date':'2025-01-01','date_piece':'2025-01-01','journal':'BQ',
            'reference':'CAP-VENT-ANNUEL','libelle':'Apport bancaire fictif ventilation annuelle',
            'lignes':[{'compte':'5141','debit':1000},{'compte':'1111','credit':1000}]}),201)
        tiers,factures={},{}
        for sens in ['vente','achat']:
            nom='Annuel ventilation fictif '+sens+' '+uuid.uuid4().hex[:6]
            tiers[sens]=ok(api.post('/api/tiers',json={'nom':nom,'type':'client' if sens=='vente' else 'fournisseur'}),201)
            factures[sens]=[]
            for index,prix in enumerate([100,200]):
                f=ok(api.post('/api/factures',json={'type':sens,'date':f'2025-06-0{index+1}','tiers':nom,
                    'tiers_id':tiers[sens]['id'],'reference':f'ANN-{sens}-{index+1}','date_echeance':'2025-07-31',
                    'lignes':[{'description':'Article fictif hors suivi de stock','quantite':1,'prix_unitaire':prix,'tva':20}]}),201)
                f.update(ok(api.post(f"/api/factures/{f['id']}/valider",json={})))
                f['ecriture_id']=ok(api.post(f"/api/factures/{f['id']}/comptabiliser",json={}))['ecriture_id']
                factures[sens].append(f)
        from playwright.sync_api import sync_playwright,expect
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(accept_downloads=True)
                page.set_default_timeout(20000)
                page.on('dialog',lambda d:d.accept())
                erreurs,serveurs=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                select_annee=page.locator('select').filter(has=page.locator('option[value="2025"]')).first
                select_annee.select_option('2025')
                reglements={}
                page.goto(application['web_url']+'/commercial')
                for sens in ['vente','achat']:
                    page.get_by_role('button',name='Vente' if sens=='vente' else 'Achat',exact=True).click()
                    page.get_by_role('button',name='Règlements',exact=True).click()
                    page.get_by_role('button',name='Ventiler par tiers',exact=True).click()
                    modal=page.get_by_role('dialog',name='Règlement par tiers',exact=True)
                    modal.locator('select').first.select_option(str(tiers[sens]['id']))
                    modal.get_by_label('Date du paiement',exact=True).fill('2025-06-15')
                    modal.get_by_label('Montant du paiement (MAD)',exact=True).fill('240')
                    modal.get_by_label('Référence du paiement',exact=True).fill('VIR-ANNUEL-'+sens)
                    for f in factures[sens]: modal.get_by_label('Montant pour '+f['numero'],exact=True).fill('120')
                    with page.expect_response(lambda r:r.url.endswith('/api/reglements/par-tiers') and r.request.method=='POST') as response:
                        modal.get_by_role('button',name='Enregistrer la ventilation',exact=True).click()
                    reglements[sens]=ok_ui(response.value,201)
                    modal.wait_for(state='hidden')
                    expect(page.locator('tbody tr')).to_have_count(2)
                valider_brouillons_ui(page,application,9)
                with Session(application['engine']) as db:
                    es=db.query(models.Ecriture).filter_by(societe_id=sid,exercice=2025).all()
                    assert len(es)==9 and sum(len(e.lignes) for e in es)==22
                    assert sum(l.debit for e in es for l in e.lignes)==sum(l.credit for e in es for l in e.lignes)==2200
                    assert soldes(db,sid,2025)=={c:D(v) for c,v in ORACLE['soldes_avant_impot'].items()}
                    for sens,compte,code in [('vente','3421','AVA'),('achat','4411','AVB')]:
                        toutes=[l for e in es for l in e.lignes if l.compte==compte]
                        assert len(toutes)==4 and abs(sum(l.debit-l.credit for l in toutes))==120
                        refuse=api.post('/api/lettrage/comptable/lettrer',json={'ligne_ids':[l.id for l in toutes],'code':code})
                        assert refuse.status_code==400,refuse.text
                        premiere=factures[sens][0]
                        reg=next(r for r in reglements[sens] if r['facture_id']==premiere['id'])
                        ids=[l.id for e in es if e.id in {premiere['ecriture_id'],reg['ecriture_id']} for l in e.lignes if l.compte==compte]
                        assert len(ids)==2
                        assert ok(api.post('/api/lettrage/comptable/lettrer',json={'ligne_ids':ids,'code':code}))['nb']==2
                tva=ok(api.get('/api/tva/declaration?exercice=2025'))
                assert D(str(tva['collectee']['total']))==D(str(tva['recuperable']['total']))==40
                assert tva['tva_due']==0 and tva['credit_tva']==0
                if controle_banque: controle_banque('avant_cloture',api,page,reglements,sid,application)
                originals=lignes_comptables(application,sid)
                page.goto(application['web_url']+'/cloture')
                bouton=page.get_by_role('button',name="Clôturer l'exercice 2025",exact=True)
                expect(bouton).to_be_enabled()
                with page.expect_response(lambda r:'/api/cloture/cloturer?exercice=2025' in r.url) as response:
                    bouton.click()
                cloture=ok_ui(response.value)
                assert cloture['a_nouveaux_sur']==2026 and D(str(cloture['resultat_net']))==-3000
                with Session(application['engine']) as db:
                    an=db.get(models.Ecriture,db.query(models.ClotureExercice).filter_by(societe_id=sid,exercice=2025).one().ecriture_an_id)
                    assert soldes(db,sid,2026)=={c:D(v) for c,v in ORACLE['soldes_an_2026'].items()}
                    assert sum(l.debit for l in an.lignes)==sum(l.credit for l in an.lignes)==4180
                    assert {l.tiers_id for l in an.lignes if l.compte in ['3421','4411']}=={x['id'] for x in tiers.values()}
                    an_id=an.id
                assert originals<=lignes_comptables(application,sid)
                if controle_banque: controle_banque('apres_cloture',api,page,reglements,sid,application)
                futurs={}
                for sens in ['vente','achat']:
                    f=factures[sens][1]
                    futurs[sens]=ok(api.post('/api/reglements',json={'facture_id':f['id'],'date':'2026-02-15',
                        'tiers':tiers[sens]['nom'],'montant':120,'mode':'virement','reference':'SOLDE-ANNUEL-'+sens}),201)
                    assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==0
                select_annee.select_option('2026')
                valider_brouillons_ui(page,application,2)
                for sens,compte in [('vente','3421'),('achat','4411')]:
                    with Session(application['engine']) as db:
                        ls=[l for eid in [an_id,futurs[sens]['ecriture_id']] for l in db.get(models.Ecriture,eid).lignes if l.compte==compte]
                        ids=[l.id for l in ls]
                        assert len(ids)==2 and sum(l.debit-l.credit for l in ls)==0
                    assert ok(api.post('/api/lettrage/comptable/lettrer',json={'ligne_ids':ids,'code':'ANA' if sens=='vente' else 'ANB'}))['nb']==2
                page.goto(application['web_url']+'/commercial')
                for sens in ['vente','achat']:
                    page.get_by_role('button',name='Vente' if sens=='vente' else 'Achat',exact=True).click()
                    page.get_by_role('button',name='Règlements',exact=True).click()
                    ligne=page.locator('tbody tr')
                    expect(ligne).to_have_count(1)
                    expect(ligne).to_contain_text(factures[sens][1]['numero'])
                    expect(ligne).to_contain_text('Soldée')
                with Session(application['engine']) as db:
                    assert soldes(db,sid,2026)=={c:D(v) for c,v in ORACLE['soldes_2026_apres_reglements'].items()}
                assert originals<=lignes_comptables(application,sid)
                if controle_banque: controle_banque('apres_paiements',api,page,futurs,sid,application)
                for annee in [2025,2026]:
                    controle=ok(api.get(f'/api/fec/apercu?exercice={annee}'))
                    assert controle['conforme_export'],controle
                    r=api.get(f'/api/fec/export?exercice={annee}')
                    assert r.status_code==200 and len(r.content.splitlines())>5
                    (tmp_path/f'FEC-ventilation-{annee}.txt').write_bytes(r.content)
                page.goto(application['web_url']+'/balances')
                page.get_by_text('Balance équilibrée',exact=False).wait_for()
                book=load_workbook(telecharger(page,'Excel',tmp_path,'ventilation-2026'),data_only=True)
                total=next(r for r in book['Balance'].values if r[0]=='TOTAL GÉNÉRAL')
                assert total[6:]==(4060,4060)
                assert not erreurs and not serveurs,(erreurs,serveurs)
            finally:
                browser.close()
    finally:
        api.close()
