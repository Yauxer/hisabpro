"""NEG027/028 : dotation définitive unique et résiduelle supérieure au coût refusée."""
from decimal import Decimal as D
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from test_e2e_cahier_immobilisation785_isole import capital,acquisition,amortissement
from navigation823_support import navigations_completes823
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def etat853(api,app,sid):
 return {'journal':core(app,sid),'immobilisations':ok(api.get('/api/immobilisations')),'tiers':ok(api.get('/api/tiers')),'exercices':ok(api.get('/api/exercices'))}

@pytest.mark.parametrize('largeur',[1440,390])
def test_853_dotation_unique_et_residuelle_cout(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'immo853') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='F-IMMO');f=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':t['type'],'compte_fournisseur':t['compte']}),201);b=DATA['banque'];ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  capital(page,application,sid,preuve);immo=acquisition(api,page,application,sid,f,preuve);amortissement(api,page,application,sid,immo,preuve);avant=etat853(api,application,sid);assert len(avant['journal'])==4 and all(e[7] for e in avant['journal'])
  # Les trois points d'entrée réutilisent le même stock de dotations existantes.
  unitaire=api.post(f'/api/immobilisations/{immo["id"]}/generer-ecriture',params={'annee':2025});assert unitaire.status_code==409 and 'existe déjà' in unitaire.json()['detail'];lot=ok(api.post('/api/immobilisations/generer-dotations-annee',params={'annee':2025}));assert lot['nb_generees']==0 and lot['nb_ignorees']==1 and lot['total_dotation']==0;cloture=ok(api.post('/api/cloture/generer-dotations',params={'exercice':2025}));assert cloture['nb_generees']==0;assert etat853(api,application,sid)==avant
  es=ok(api.get('/api/ecritures',params={'exercice':2025}));dot=[e for e in es if e['reference']==f'AM-2025-{immo["id"]}'];assert len(dot)==1 and dot[0]['est_validee'] and {(l['compte'],D(str(l['debit'])),D(str(l['credit']))) for l in dot[0]['lignes']}=={('61935',D(4800),D(0)),('28355',D(0),D(4800))};preuve['dotation853']={'unitaire_refuse':409,'lot_nb_nouvelles':0,'cloture_nb_nouvelles':0,'montant_unique':4800,'nb_ecritures_dotation':1,'journal_registre_conserves':True}
  page.goto(application['web_url']+'/immobilisations');page.get_by_role('button',name='Nouvelle immobilisation',exact=True).click();m=page.locator('[class*="modalOverlay"]').first;m.get_by_placeholder('Ex: Serveur Dell PowerEdge',exact=True).fill('Copie résiduelle fictive853');champ(m,'Référence / n° série').fill('IMMO-NEG028');champ(m,'Catégorie','select').select_option('Matériel informatique');m.get_by_placeholder('Rechercher ou saisir un nouveau fournisseur').fill(f['nom']);m.get_by_role('button').filter(has_text=f['nom']).click()
  for label,val in [('Date d’acquisition *','2025-01-01'),('Date de mise en service *','2025-01-01'),('Prix d’acquisition HT *','1000'),('Durée (années)','5'),('Valeur résiduelle','1001')]:champ(m,label).fill(val)
  champ(m,'Méthode','select').select_option('lineaire')
  with page.expect_response(lambda r:r.url.endswith('/api/immobilisations') and r.request.method=='POST') as rr:m.get_by_role('button',name='Créer',exact=True).click()
  assert rr.value.status==400;expect(m.get_by_text('La valeur résiduelle ne peut pas dépasser le coût',exact=False)).to_be_visible();assert etat853(api,application,sid)==avant
  payload={'designation':'Copie résiduelle fictive853','reference':'IMMO-NEG028','categorie':'Matériel informatique','date_acquisition':'2025-01-01','date_mise_en_service':'2025-01-01','prix_acquisition_ht':1000,'taux_tva':20,'tva_recuperable_pct':100,'fournisseur_tiers_id':f['id'],'duree_amort':5,'methode':'lineaire','compte_immo':'2355','compte_amort':'28355','compte_dotation':'61935','valeur_residuelle':1001};r=api.post('/api/immobilisations',json=payload);assert r.status_code==400 and 'valeur résiduelle' in r.json()['detail'];assert etat853(api,application,sid)==avant
  preuve['residuelle853']={'cout':1000,'residuelle_refusee':1001,'UI_statut':400,'API_statut':400,'aucune_mutation':True}
  champ(m,'Valeur résiduelle').fill('0')
  with page.expect_response(lambda r:r.url.endswith('/api/immobilisations') and r.request.method=='POST') as rr:m.get_by_role('button',name='Créer',exact=True).click()
  positif=ok(rr.value,201);m.wait_for(state='hidden');assert D(str(positif['valeur_brute']))==1000 and D(str(positif['valeur_residuelle']))==0;fin=core(application,sid);assert len(ok(api.get('/api/immobilisations')))==2 and all(e in fin for e in avant['journal']);preuve['residuelle853']['creation_valide_1000_residuelle0']=True;preuve['cas'] += [{'id':c,'statut':'Réussi'} for c in ['HP-NEG-027','HP-NEG-028']]
