"""ADM004/SEC006 : référentiel réel, libellés immédiats et aucune mutation de contrôle."""
import time,pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_855_comptes_journaux_autocompletion_cache(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'plan855') as (api,page,sid,preuve):
  e=ok(api.post('/api/ecritures',json={'date':'2025-01-01','date_piece':'2025-01-01','journal':'BQ','reference':'TEMOIN-855','libelle':'Capital fictif test855','lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}]}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'));avant=core(application,sid);plan=ok(api.get('/api/plan-comptable'));comptes={c['compte']:c for c in plan};attendus={l['compte'] for o in DATA['operations'] for l in o['lignes']};assert attendus<={c for c,v in comptes.items() if v['actif']};assert all(c in comptes for c in ['51111','51112','51132'])
  r=api.delete('/api/plan-comptable/5141');assert r.status_code==409;assert ok(api.get('/api/plan-comptable'))==plan and core(application,sid)==avant
  schema=ok(api.get('/openapi.json'));assert 'CL' not in schema['components']['schemas']['JournalEnum']['enum'];rcl=api.post('/api/ecritures',json={'date':'2025-01-01','journal':'CL','reference':'TENTATIVE-CL-855','libelle':'CLmanuelinterditfictif','lignes':[{'compte':'5141','debit':1},{'compte':'1111','credit':1}]});assert rcl.status_code in {400,409,422};assert core(application,sid)==avant
  page.goto(application['web_url']+'/plan-comptes')
  for c in ['51111','51112','51132']:
   page.get_by_placeholder('Rechercher par numéro ou libellé...',exact=True).fill(c);row=page.locator('tbody tr').filter(has=page.get_by_text(c,exact=True));expect(row).to_have_count(1);expect(row).to_contain_text(comptes[c]['libelle'])
  requetes=[];page.on('request',lambda r:requetes.append(r.url) if '/api/plan-comptable' in r.url and r.method=='GET' else None);page.goto(application['web_url']+'/journal');expect(page.get_by_text('TEMOIN-855',exact=True)).to_be_visible();mesures=[]
  for tour in range(2):
   page.get_by_role('button',name='Nouvelle écriture',exact=True).click();m=page.get_by_role('dialog');journaux=set(champ(m,'Journal *','select').locator('option').evaluate_all('es=>es.map(e=>e.value)'));assert {'AC','VT','AV','BQ','AE','OD','AM','AN'}<=journaux and 'CL' not in journaux;entree=m.locator('tbody tr').first.get_by_placeholder('Ex: 6111',exact=True)
   for code in ['3421','2355']:
    n=len(requetes);t0=time.perf_counter();entree.fill(code);suggestion=m.locator('li').filter(has=page.get_by_text(code,exact=True));expect(suggestion).to_have_count(1);suggestion.click();expect(m.locator('tbody tr').first.locator('[class*="compteTip"]')).to_have_text(comptes[code]['libelle']);assert len(requetes)==n;mesures.append({'tour':tour+1,'compte':code,'libelle':comptes[code]['libelle'],'secondes_observees':round(time.perf_counter()-t0,3),'appel_plan_selection':0})
   m.get_by_role('button',name='Annuler',exact=True).click();expect(m).to_have_count(0)
  assert core(application,sid)==avant and ok(api.get('/api/plan-comptable'))==plan;preuve['plan855']={'comptes_scenario':sorted(attendus),'subdivisions':['51111','51112','51132'],'journaux':sorted(journaux),'CL_reserve_systeme':True,'CL_manuel_refuse':rcl.status_code,'suppression5141_refusee':409,'mesures':mesures,'plan_journal_conserves':True,'limite':'Durées observées en laboratoire,sans seuil de performance production ;cache attesté par absence de nouvelle requête pendant sélections et réouverture.'};preuve['cas'] += [{'id':c,'statut':'Réussi'} for c in ['HP-ADM-004','HP-SEC-006']]
