"""Coupure de transport explicite ;reprise sur API/PG nonce sans faux montants."""
from pathlib import Path
import json,pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from navigation823_support import navigations_completes823
from test_e2e_administration_isole import connexion,observer
from test_immobilisations_apercu927_isole import (
 application,application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,preparer,photo)

R=Path(__file__).resolve().parents[1]
def kpi(page,label):return page.locator('div[class*="kpiCard"]').filter(has=page.get_by_text(label,exact=True))

@pytest.mark.parametrize('largeur',[1440,390])
@pytest.mark.parametrize('role',['lecture','admin'])
def test_931_registre_et_plan_indisponibles_ne_deviennent_pas_vides(application,largeur,role,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,f'erreurs931_{role}') as (api,parent,sid,preuve):
  i=preparer(api);email=ok(api.get('/api/auth/me'))['email'];password=DATA['societe']['password_test']
  if role=='lecture':
   email=f'lecture931-{sid}@hisabpro-recette.example';ok(api.post('/api/utilisateurs',json={'nom':'Lecteur FICTIF931','email':email,'mot_de_passe':password,'role':role}),201)
  ctx=parent.context.browser.new_context(viewport={'width':largeur,'height':1050});page=ctx.new_page();page.set_default_timeout(15000);errors,server=observer(page,application['api_url'])
  try:
   connexion(page,application['web_url'],email,password);page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2026');avant=photo(application,sid)
   coupures=[];mutations=[]
   def couper(route):coupures.append(route.request.url);route.abort('internetdisconnected')
   registre=lambda u:u.split('?')[0]==application['api_url']+'/api/immobilisations'
   plan=lambda u:u.split('?')[0]==application['api_url']+f'/api/immobilisations/{i["id"]}/tableau'
   page.on('request',lambda r:mutations.append((r.method,r.url)) if '/api/immobilisations' in r.url and r.method not in ['GET','OPTIONS'] else None)
   page.route(registre,couper);page.goto(application['web_url']+'/immobilisations')
   alerte=page.get_by_role('alert').filter(has_text='Impossible de charger le registre');expect(alerte).to_be_visible()
   expect(page.get_by_text('Aucune immobilisation',exact=True)).to_have_count(0)
   for label in ['Valeur brute active','Amortissements cumulés','VNC active','Biens actifs']:
    card=kpi(page,label);expect(card).to_contain_text('—');b=card.bounding_box();assert b and b['x']>=0 and b['x']+b['width']<=largeur+1,b
   bouton=page.get_by_role('button',name='Nouvelle immobilisation',exact=True).bounding_box();assert bouton and bouton['x']+bouton['width']<=largeur+1,bouton
   expect(page.get_by_role('button',name='Dotations 2026',exact=True)).to_be_disabled()
   d=R/'docs/recette/preuves';d.mkdir(exist_ok=True);page.screenshot(path=str(d/f'931_{largeur}_{role}_registre_indisponible.png'))
   assert photo(application,sid)==avant
   page.unroute(registre,couper)
   with page.expect_response(lambda r:registre(r.url) and r.request.method=='GET') as rr:alerte.get_by_role('button',name='Réessayer le registre',exact=True).click()
   lignes=ok(rr.value);assert [l['id'] for l in lignes]==[i['id']]
   expect(alerte).to_have_count(0);expect(kpi(page,'Valeur brute active')).to_contain_text('24.000,00 MAD');expect(kpi(page,'Biens actifs')).to_contain_text('1 biens')
   row=page.locator('tbody tr').filter(has_text=i['designation']);expect(row).to_have_count(1)
   page.route(plan,couper);row.click();erreur_plan=page.get_by_role('alert').filter(has_text='Impossible de charger le plan');expect(erreur_plan).to_be_visible()
   expect(page.get_by_role('button',name='Générer',exact=True)).to_have_count(0)
   page.screenshot(path=str(d/f'931_{largeur}_{role}_plan_indisponible.png'));assert photo(application,sid)==avant
   page.unroute(plan,couper)
   with page.expect_response(lambda r:plan(r.url) and r.request.method=='GET') as rr:erreur_plan.get_by_role('button',name='Réessayer le plan',exact=True).click()
   reponse=ok(rr.value);assert reponse['tableau'] and reponse['immobilisation']['id']==i['id']
   expect(erreur_plan).to_have_count(0);expect(page.get_by_role('cell',name='2025',exact=True).locator('..')).to_contain_text('4.800,00 MAD')
   boutons=page.get_by_role('button',name='Générer',exact=True)
   if role=='lecture':expect(boutons).to_have_count(0)
   else:expect(boutons.first).to_be_enabled()
   assert len(coupures)==2 and not mutations and not errors and not server,(coupures,mutations,errors,server)
   assert photo(application,sid)==avant
   preuve['erreurs931']={'role':role,'pannes':'Deux requêtes GET interrompues explicitement dans Edge ;aucun montant/JSON financier substitué.','coupures_transport':2,'reprises_HTTP_reelles':2,'registre_inconnu_ne_signifie_pas_zero':True,'plan_indisponible_ne_signifie_pas_vide':True,'droits_conserves':True,'comptabilite_calendrier_sequences_inchanges':True,'mutations_UI':mutations}
  finally:ctx.close()

@pytest.mark.parametrize('largeur',[1440,390])
def test_931_registre_reellement_vide_affiche_zero_apres_lecture(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'vide931') as (api,page,sid,preuve):
  avant=photo(application,sid)
  with page.expect_response(lambda r:r.url.split('?')[0]==application['api_url']+'/api/immobilisations' and r.request.method=='GET') as rr:page.goto(application['web_url']+'/immobilisations')
  assert ok(rr.value)==[];expect(page.get_by_text('Aucune immobilisation',exact=True)).to_be_visible()
  for label in ['Valeur brute active','Amortissements cumulés','VNC active']:expect(kpi(page,label)).to_contain_text('0,00 MAD')
  expect(kpi(page,'Biens actifs')).to_contain_text('0 biens');expect(page.get_by_role('alert')).to_have_count(0)
  assert photo(application,sid)==avant;preuve['vide931']={'GET_reel':200,'resultat':[],'zero_justifie':True,'comptabilite_inchangee':True}

@pytest.mark.parametrize('largeur',[1440,390])
def test_931_modification_enregistree_mais_rafraichissement_indisponible(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'rafraichissement931') as (api,page,sid,preuve):
  i=preparer(api);page.goto(application['web_url']+'/immobilisations');expect(page.locator('tbody tr').filter(has_text=i['designation'])).to_have_count(1);avant=photo(application,sid)
  page.get_by_title('Modifier',exact=True).click();m=page.locator('[class*="modalOverlay"]').filter(has=page.get_by_placeholder('Ex: Serveur Dell PowerEdge',exact=True));m.get_by_placeholder('Ex: Serveur Dell PowerEdge',exact=True).fill('Bien RENOMME FICTIF931')
  registre=lambda u:u.split('?')[0]==application['api_url']+'/api/immobilisations'
  def couper(route):route.abort('internetdisconnected')
  page.route(registre,couper);mutations=[]
  page.on('request',lambda r:mutations.append(r.method) if r.url.split('?')[0]==application['api_url']+f'/api/immobilisations/{i["id"]}' and r.method not in ['GET','OPTIONS'] else None)
  with page.expect_response(lambda r:r.url.endswith(f'/api/immobilisations/{i["id"]}') and r.request.method=='PATCH') as rr:m.get_by_role('button',name='Modifier',exact=True).click()
  ok(rr.value);m.wait_for(state='hidden');alerte=page.get_by_role('alert').filter(has_text='Impossible de charger le registre');expect(alerte).to_be_visible()
  for label in ['Valeur brute active','Amortissements cumulés','VNC active','Biens actifs']:expect(kpi(page,label)).to_contain_text('—')
  expect(page.get_by_text('Aucune immobilisation',exact=True)).to_have_count(0);assert not page.locator('tbody').count()
  apres=photo(application,sid)
  for k in avant:
   if k!='immobilisations':assert apres[k]==avant[k],k
  assert [json.loads(x)['designation'] for x in apres['immobilisations']]==['Bien RENOMME FICTIF931']
  page.unroute(registre,couper)
  with page.expect_response(lambda r:registre(r.url) and r.request.method=='GET') as rr:alerte.get_by_role('button',name='Réessayer le registre',exact=True).click()
  assert ok(rr.value)[0]['designation']=='Bien RENOMME FICTIF931';expect(alerte).to_have_count(0);expect(page.locator('tbody tr').filter(has_text='Bien RENOMME FICTIF931')).to_have_count(1)
  expect(kpi(page,'Valeur brute active')).to_contain_text('24.000,00 MAD');assert photo(application,sid)==apres and mutations==['PATCH']
  page.get_by_title('Modifier',exact=True).click();champ(m,'Durée (années)').fill('6')
  with page.expect_response(lambda r:r.url.endswith(f'/api/immobilisations/{i["id"]}') and r.request.method=='PATCH') as rr:m.get_by_role('button',name='Modifier',exact=True).click()
  assert rr.value.status==409 and rr.value.request.post_data_json['duree_amort']==6
  expect(m).to_contain_text('verrouillé');m.get_by_role('button',name='Annuler',exact=True).click()
  assert photo(application,sid)==apres and mutations==['PATCH','PATCH']
  preuve['rafraichissement931']={'modification_descriptive_reelle':'Bien RENOMME FICTIF931','PATCH_reel':200,'panne':'GET de rafraîchissement interrompu explicitement','indicateurs_anciens_masques':True,'reprise_GET_reelle_sans_nouvelle_modification':True,'tentative_distincte_changement_plan_refusee':409,'ecritures_lignes_calendrier_sequences_inchanges':True}
