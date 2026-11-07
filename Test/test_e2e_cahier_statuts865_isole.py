"""SEC008 : règlements commerciaux et banque ne désignent pas le même solde."""
from collections import defaultdict
from decimal import Decimal as D
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_plafonds843_isole import facture843,valider843
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_865_statuts_solde_commercial_et_banque(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'statuts865') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='C-SERVICE');t=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'client','compte_client':'3421'}),201);b=DATA['banque'];ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  fs=[facture843(api,t,'vente',f'2025-01-0{i}',1000,f'STATUT865-{i}') for i in [1,2,3]]
  for f,montant,mode,ref in [(fs[0],300,'virement','PARTIEL-865'),(fs[1],1200,'effet','EFFET-865'),(fs[2],1200,'virement','SOURCE-AVOIR-865')]:
   ok(api.post('/api/reglements',json={'facture_id':f['id'],'tiers':t['nom'],'date':'2025-02-01','date_echeance':'2025-03-15' if mode=='effet' else None,'montant':montant,'mode':mode,'banque':b['banque'],'reference':ref}),201)
  av=ok(api.post('/api/avoirs',json={'facture_id':fs[2]['id'],'date':'2025-02-02','motif':'Crédit fictif600 pour imputation865','retour_stock':False,'lignes':[{'facture_ligne_id':fs[2]['lignes'][0]['id'],'quantite':0.5}]}),201);assert av['total_ttc']==600;ok(api.post(f'/api/avoirs/{av["id"]}/comptabiliser'));ok(api.post(f'/api/avoirs/{av["id"]}/utiliser',json={'type_utilisation':'imputation','facture_id':fs[0]['id'],'date_utilisation':'2025-02-02','montant':600}));valider843(api);avant=core(application,sid)
  part=ok(api.get(f'/api/factures/{fs[0]["id"]}/reglements'));eff=ok(api.get(f'/api/factures/{fs[1]["id"]}/reglements'));assert part['solde_restant']==300 and part['total_encaisse']==300 and part['total_avoirs']==600;assert eff['solde_restant']==0 and eff['total_encaisse']==0 and eff['total_reglement_en_cours']==1200
  soldes=defaultdict(D)
  for e in avant:
   for l in e[8]:soldes[l[1]]+=D(str(l[2]))-D(str(l[3]))
  assert soldes['5141']==1500 and soldes['3421']==300 and soldes['3425']==1200
  page.goto(application['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text=fs[1]['numero']);expect(row.get_by_text('Règlement en cours',exact=True)).to_be_visible();expect(row.get_by_text('Payée',exact=True)).to_have_count(0);expect(page.locator('tbody tr').filter(has_text=fs[0]['numero']).get_by_text('Part. payée',exact=True)).to_be_visible();row.click();expect(page.get_by_role('dialog').get_by_text('Règlement en cours',exact=True)).to_be_visible()
  page.goto(application['web_url']+'/effets');champ(page,'Statut','select').select_option('tous');row=page.locator('tbody tr').filter(has_text='EFFET-865');expect(row.get_by_text('En portefeuille',exact=True)).to_be_visible();expect(row.get_by_text('Encaissé',exact=True)).to_have_count(0)
  page.goto(application['web_url']+'/commercial');page.get_by_role('button',name='Factures',exact=True).click();row=page.locator('tbody tr').filter(has_text=fs[1]['numero']);expect(row.get_by_text('Règlement en cours',exact=True)).to_be_visible();expect(row.get_by_text('Payée',exact=True)).to_have_count(0)
  situation=ok(api.get('/api/recouvrement/situation',params={'exercice':2025,'date_reference':'2025-12-31'}));assert situation['effets']['portefeuille']==1200;reste=next(f for f in situation['factures'] if f['id']==fs[0]['id']);assert reste['reste_du']==300 and reste['statut_paiement']=='partiellement_reglee';etic=ok(api.get('/api/etats/etic/2025'));b6=next(s for s in etic['sections'] if s['code']=='B6');l=next(l for l in b6['automatique']['lignes'] if l['compte']=='3421');assert D(str(l['echeance_auto_total']))==300
  page.goto(application['web_url']+'/situation');expect(page.get_by_text('Taux de règlement commercial',exact=True)).to_be_visible();expect(page.get_by_text('Taux d’encaissement',exact=True)).to_have_count(0);page.goto(application['web_url']+'/journal');expect(page.get_by_role('main')).to_contain_text('EFFET-865');page.goto(application['web_url']+'/etic');expect(page.get_by_role('main').get_by_role('heading',level=1)).to_contain_text('ETIC');assert core(application,sid)==avant
  preuve['statuts865']={'factures':[f['numero'] for f in fs],'partiel':part,'effet':eff,'soldes':{k:str(soldes[k]) for k in ['5141','3421','3425']},'portefeuille':1200,'etic_3421_auto':300,'aucun_encaissement_effet':True,'journal_conserve':True,'limite':'Trois factures fictives1200MAD, paiement partiel300, effet1200 non encaissé et avoir600 imputé. Statut commercial serveur conservé ;seule présentation désambiguïsée.'};preuve['cas'].append({'id':'HP-SEC-008','statut':'Réussi'})
