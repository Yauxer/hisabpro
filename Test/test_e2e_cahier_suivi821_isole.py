"""Relances internes et compléments de délais du cahier, sans envoi externe."""
from pathlib import Path
from decimal import Decimal as D
import csv,io,hashlib
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from cahier_suite777_support import core
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)
R=Path(__file__).resolve().parents[1]

def relances(api):return ok(api.get('/api/recouvrement/relances',params={'exercice':2025}))
def rapport(api,annee=2026,trimestre=1):return ok(api.get('/api/delais-paiement',params={'annee':annee,'trimestre':trimestre}))

@pytest.mark.parametrize('largeur',[1440,390])
def test_821_relance_et_complements_fournisseurs_persistants(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'suivi821') as (api,page,sid,preuve):
  tiers={}
  for t in DATA['tiers']:
   if t['code'] in ['C-IMPAYE','F-CONTROLE']:tiers[t['code']]=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':t['type'],('compte_client' if t['type']=='client' else 'compte_fournisseur'):t['compte']}),201)
  factures=[]
  for type_,cle,ref,jour,echeance,pu,compte in [('achat','F-CONTROLE','02','2025-12-02','2025-12-31',200,'6125'),('achat','F-CONTROLE','002','2025-12-02','2025-12-31',200,'6125'),('vente','C-IMPAYE','VENTE-IMPAYEE','2025-12-10','2025-12-20',12000,'7124')]:
   t=tiers[cle];f=ok(api.post('/api/factures',json={'type':type_,'date':jour,'tiers':t['nom'],'tiers_id':t['id'],'reference':ref,'date_echeance':echeance,'lignes':[{'description':'Service fictif du cahier','quantite':1,'prix_unitaire':pu,'tva':20,'compte_comptable':compte}]}),201);ok(api.post(f'/api/factures/{f["id"]}/valider'));ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'));factures.append(f)
  for e in ok(api.get('/api/ecritures',params={'exercice':2025})):ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
  avant=core(application,sid);assert len(avant)==3;impayee=factures[-1];assert relances(api)==[]
  page.goto(application['web_url']+'/situation');page.get_by_role('button',name='Échéances & impayés',exact=True).click();row=page.locator('tbody tr').filter(has_text=impayee['numero']);row.get_by_role('button',name='Relancer',exact=True).click();m=page.get_by_role('dialog')
  m.get_by_label('Niveau de relance',exact=False).select_option('1');m.get_by_label('Canal',exact=False).select_option('email');m.get_by_label('Date de relance',exact=True).fill('2025-12-22');m.get_by_label('Date promise',exact=True).fill('2026-01-31');m.get_by_label('Prochaine relance',exact=True).fill('');m.get_by_label('Commentaire',exact=False).fill('Suivi fictif du laboratoire, sans envoi externe.')
  with page.expect_response(lambda r:r.url.endswith('/api/recouvrement/relances') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer la relance',exact=True).click()
  cree=ok(r.value,201);m.wait_for(state='hidden');assert cree['facture_id']==impayee['id'] and cree['date_relance']=='2025-12-22' and cree['date_promesse_reglement']=='2026-01-31' and cree['prochaine_relance'] is None and cree['niveau']==1 and cree['canal']=='email'
  preuve['relance_creation819']=cree
  page.reload(wait_until='domcontentloaded');page.get_by_role('button',name='Relances',exact=True).click();row=page.locator('tbody tr').filter(has_text=impayee['numero']);expect(row).to_contain_text('31/01/2026');expect(row).to_contain_text('Suivi fictif du laboratoire, sans envoi externe.');row.get_by_role('button',name='Modifier',exact=True).click();m=page.get_by_role('dialog');m.get_by_label('Date promise',exact=True).fill('2026-02-15');m.get_by_label('Commentaire',exact=False).fill('Promesse fictive modifiée')
  with page.expect_response(lambda r:r.url.endswith('/api/recouvrement/relances/'+str(cree['id'])) and r.request.method=='PATCH') as r:m.get_by_role('button',name='Enregistrer',exact=True).click()
  modifie=ok(r.value);m.wait_for(state='hidden');assert modifie['date_promesse_reglement']=='2026-02-15' and modifie['commentaire']=='Promesse fictive modifiée'
  page.reload(wait_until='domcontentloaded');page.get_by_role('button',name='Relances',exact=True).click();row=page.locator('tbody tr').filter(has_text=impayee['numero']);expect(row).to_contain_text('15/02/2026');expect(row).to_contain_text('Promesse fictive modifiée')
  with page.expect_response(lambda r:r.url.endswith('/api/recouvrement/relances/'+str(cree['id'])) and r.request.method=='PATCH') as r:row.get_by_role('button',name='Annuler la relance',exact=True).click()
  annule=ok(r.value);assert annule['statut']=='annulee';page.reload(wait_until='domcontentloaded');page.get_by_role('button',name='Relances',exact=True).click();expect(page.locator('tbody tr').filter(has_text=impayee['numero'])).to_contain_text('Annulée');assert len(relances(api))==1 and relances(api)[0]['statut']=='annulee' and core(application,sid)==avant
  preuve['relance819']={'cree':cree,'modifie':modifie,'annule':annule,'journal_inchange':True,'envoi_externe':False};preuve['cas'].append({'id':'HP-FAC-012','statut':'Réussi'})
  fin2025=rapport(api,2025,4);assert fin2025['factures']==[]
  preuve['delais_fin2025_vide819']={'echeance':'2025-12-31','fin_periode':'2025-12-31','raison':'Pas encore en retard le jour de l’échéance ; dates conservées, contrôle complémentaire T1 2026.'}
  page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2026');page.goto(application['web_url']+'/delais-paiement');expect(page.get_by_role('heading',name='Délais de paiement',exact=True)).to_be_visible()
  with page.expect_response(lambda r:'/api/delais-paiement?annee=2026&trimestre=1' in r.url and r.request.method=='GET') as trimestre:page.locator('select').filter(has=page.locator('option[value="1"]')).first.select_option('1')
  ok(trimestre.value);r0=rapport(api);assert {r['reference_facture'] for r in r0['factures']}=={'02','002'}
  for f in factures[:2]:
   row=page.locator('tbody tr').filter(has=page.get_by_text(f['reference'],exact=True));expect(row).to_have_count(1);row.get_by_title('Compléter',exact=True).click();form=page.locator('form').filter(has=page.get_by_role('heading',name='Compléter la déclaration',exact=True));form.get_by_label('Date de livraison / service',exact=True).fill('2025-12-02');assert not form.get_by_role('checkbox').nth(0).is_checked() and not form.get_by_role('checkbox').nth(1).is_checked()
   with page.expect_response(lambda r:r.url.endswith('/api/delais-paiement/factures/'+str(f['id'])) and r.request.method=='PATCH') as r:form.get_by_role('button',name='Enregistrer',exact=True).click()
   ok(r.value);expect(form).to_have_count(0)
  page.reload(wait_until='domcontentloaded')
  with page.expect_response(lambda r:'/api/delais-paiement?annee=2026&trimestre=1' in r.url and r.request.method=='GET') as trimestre:page.locator('select').filter(has=page.locator('option[value="1"]')).first.select_option('1')
  ok(trimestre.value);r1=rapport(api);assert len(r1['factures'])==2 and {r['reference_facture'] for r in r1['factures']}=={'02','002'}
  for r in r1['factures']:assert r['date_livraison_service']=='2025-12-02' and r['date_echeance']=='2025-12-31' and not r['litige_judiciaire'] and not r['hors_champ'] and D(str(r['montant_ttc']))==D(240)
  with page.expect_download() as out:page.get_by_role('button',name='Exporter CSV',exact=True).click()
  assert out.value.suggested_filename=='delais_paiement_2026_T1.csv';preuve['nom_export819']={'recu':out.value.suggested_filename,'conforme':True};p=tmp_path/f'delais819_{largeur}.csv';out.value.save_as(p);rows=list(csv.DictReader(io.StringIO(p.read_text(encoding='utf-8-sig')),delimiter=';'));assert len(rows)==2 and {r['Reference facture'] for r in rows}=={'02','002'} and all(r['Date livraison/service']=='2025-12-02' and r['Date echeance']=='2025-12-31' for r in rows);assert core(application,sid)==avant
  preuve['delais819']={'avant':r0,'apres':r1,'journal_inchange':True,'limite':'État préparatoire, informations fournisseur et assujettissement à qualifier ;aucune amende ni dépôt réel validé.'};preuve['fichier819']={'chemin':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};preuve['cas'].append({'id':'HP-FAC-017','statut':'Partiel','limite':'Le cas initial demande T4 2025 mais ces factures échéance31/12 ne sont pas encore en retard ;compléments et export contrôlés enT1 2026 sans changer les dates.'})

def test_821_cors_expose_nom_sans_ouvrir_origines(application):
 import httpx
 with httpx.Client(base_url=application['api_url']) as api:
  permis=application['web_url'];etranger='https://origine-exterieure.invalid'
  r=api.get('/api/health',headers={'Origin':permis});assert r.status_code==200 and r.headers['access-control-allow-origin']==permis
  assert 'content-disposition' in [v.strip().lower() for v in r.headers['access-control-expose-headers'].split(',')]
  r=api.options('/api/delais-paiement/export.csv?annee=2026&trimestre=1',headers={'Origin':permis,'Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'authorization'});assert r.status_code==200 and r.headers['access-control-allow-origin']==permis
  r=api.options('/api/delais-paiement/export.csv?annee=2026&trimestre=1',headers={'Origin':etranger,'Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'authorization'});assert r.status_code==400 and 'access-control-allow-origin' not in r.headers
  r=api.get('/api/health',headers={'Origin':etranger});assert 'access-control-allow-origin' not in r.headers
  r=api.get('/api/delais-paiement/export.csv?annee=2026&trimestre=1',headers={'Origin':permis});assert r.status_code==401
