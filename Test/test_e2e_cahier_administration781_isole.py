"""Cas administratifs exacts du cahier :calendrier,rôles etcloisonnement réel."""
from pathlib import Path
from uuid import uuid4
import json
import httpx
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion,observer
from cahier_formulaires773_support import DATA,ROOT,ok,champ,laboratoire,referentiels
from cahier_cycle775_support import cycle
from cahier_suite777_support import suite,core
from cahier_inventaire779_support import inventaire
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def test_781_creation_exercice2025_absent_calendrier_source(application,tmp_path):
 c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);s=DATA['societe'];email=f'calendrier781-{uuid4().hex[:8]}@hisabpro-recette.example';preuve={'cible':str(c['directory']),'cas':'HP-ADM-003','variation':'Pour tester absence2025,laisserpremierexercice àvaleur inscription2026 jusqu’àlacréationUI2025,puisappliquer premierexercice2025 ;aucunexercice supprimé.','erreur':None}
 with httpx.Client(base_url=application['api_url']) as api,sync_playwright() as p:
  auth=ok(api.post('/api/auth/register',json={'nom':s['nom_admin'],'email':email,'password':s['password_test'],'raison_sociale':s['raison_sociale']}));api.headers['Authorization']='Bearer '+auth['access_token'];avant=ok(api.get('/api/exercices'));assert 2025 not in {e['annee'] for e in avant}
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True);page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(15000);errors,server=observer(page,application['api_url'])
  try:
   connexion(page,application['web_url'],email,s['password_test']);page.goto(application['web_url']+'/cloture');page.get_by_role('button',name='Créer un exercice',exact=True).click();page.get_by_label('Année de clôture du nouvel exercice').fill('2025');page.get_by_label('Date de début du nouvel exercice').fill('2025-01-01');page.get_by_label('Date de clôture du nouvel exercice').fill('2025-12-31')
   with page.expect_response(lambda r:r.url.endswith('/api/exercices') and r.request.method=='POST') as r:page.get_by_role('button',name='Créer cet exercice',exact=True).click()
   ex=ok(r.value,201);assert ex['annee']==2025;expect(page.get_by_label('Exercice actif',exact=True)).to_have_value('2025');ok(api.patch('/api/societe/moi',json={'exercice_debut':2025}))
   exercices=ok(api.get('/api/exercices'));assert len([e for e in exercices if e['annee']==2025])==1
   for annee in [2025,2026]:
    e=next(e for e in exercices if e['annee']==annee);assert e['date_debut']==f'{annee}-01-01' and e['date_fin']==f'{annee}-12-31';ps=ok(api.get(f'/api/exercices/{annee}/periodes'));assert len(ps)==12 and [p['numero'] for p in ps]==list(range(1,13))
   refus=api.post('/api/exercices',json={'annee':2025,'date_debut':'2025-01-01','date_fin':'2025-12-31'});assert refus.status_code==409 and 'existe déjà' in refus.json()['detail'];assert len(ok(api.get('/api/exercices')))==len(exercices)
   page.reload(wait_until='domcontentloaded');expect(page.get_by_label('Exercice actif',exact=True)).to_have_value('2025');assert not errors and not server,(errors,server);preuve['statut']='Réussi';preuve['periodes2025_2026']=24;preuve['doublon_refuse409']=True
   page.screenshot(path=str(ROOT/'.codex-tests/calendrier781.png'),full_page=True)
  except BaseException as e:preuve['erreur']=repr(e);print(page.locator('body').inner_text()[-3000:]);raise
  finally:(ROOT/'.codex-tests/calendrier781_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8');browser.close()

def test_781_utilisateurs_source_et_societeB_cloisonnee(application,tmp_path):
 with laboratoire(application,1440,tmp_path,'administration781') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);cycle(api,page,application,sid,tiers,articles,preuve,tmp_path);suite(api,page,application,sid,tiers,articles,preuve);inventaire(api,page,application,sid,articles,preuve);initial=core(application,sid);assert len(initial)==14
  e=next(e for e in preuve['operations'] if e['reference']=='ACH-01');pdf=(ROOT/'docs/recette/justificatifs/ACH-01.pdf').read_bytes();piece=ok(api.post(f'/api/attachments/ecriture/{e["id"]}',files={'file':('ACH-01.pdf',pdf,'application/pdf')}));assert api.get(piece['url']).content==pdf
  page.goto(application['web_url']+'/parametres');page.get_by_role('button',name='Utilisateurs',exact=True).click()
  users=[('Comptable Recette','comptable@hisabpro-recette.example','Recette!Compta2025','comptable'),('Lecteur Recette','lecture@hisabpro-recette.example','Recette!Lecture2025','lecture')]
  for nom,email,password,role in users:
   page.get_by_role('button',name='Ajouter un utilisateur',exact=True).click();page.get_by_text('Nom complet',exact=True).locator('..').locator('input').fill(nom);page.get_by_text('Adresse e-mail',exact=True).locator('..').locator('input').fill(email);page.locator('input[autocomplete="new-password"]').fill(password);champ(page,'Rôle','select').select_option(role)
   with page.expect_response(lambda r:r.url.endswith('/api/utilisateurs') and r.request.method=='POST') as r:page.get_by_role('button',name='Créer le compte',exact=True).click()
   user=ok(r.value,201);assert user['role']==role;expect(page.locator('tbody tr').filter(has_text=email)).to_have_count(1)
  droits=[]
  for nom,email,password,role in users:
   autre=page.context.browser.new_page(viewport={'width':390 if role=='lecture' else 1440,'height':1000});erreurs,serveur=observer(autre,application['api_url'])
   try:
    connexion(autre,application['web_url'],email,password);assert autre.evaluate("localStorage.getItem('hisabpro_role')")==role;token=autre.evaluate("localStorage.getItem('hisabpro_token')")
    with httpx.Client(base_url=application['api_url'],headers={'Authorization':'Bearer '+token}) as acteur:
     me=ok(acteur.get('/api/auth/me'));assert me['societe_id']==sid;assert len(ok(acteur.get('/api/factures',params={'exercice':2025})))==4
     refus=acteur.post('/api/utilisateurs',json={'nom':'Interdit fictif','email':f'interdit-{uuid4().hex[:8]}@hisabpro-recette.example','mot_de_passe':'Recette!Interdit2025','role':'lecture'});assert refus.status_code==403
     corps={'date':'2025-12-31','journal':'OD','libelle':'Contrôle temporaire des droits — fictif','reference':'CTRL-ROLE-COMPTABLE-781','lignes':[{'compte':'5141','debit':1},{'compte':'1111','credit':1}]}
     r=acteur.post('/api/ecritures',json=corps)
     if role=='lecture':assert r.status_code==403
     else:
      brouillon=ok(r,201);assert not brouillon['est_validee'];assert acteur.delete(f'/api/ecritures/{brouillon["id"]}').status_code==204
     assert core(application,sid)==initial
    assert not erreurs and not serveur,(erreurs,serveur);droits.append({'email':email,'role':role,'connexion_UI':True,'administration_refusee403':True,'saisie_api':'403' if role=='lecture' else '201puis204draftfictif'})
   finally:autre.close()
  preuve['cas'].append({'id':'HP-ADM-016','statut':'Réussi'});preuve['roles781']=droits
  autre=page.context.browser.new_page(viewport={'width':1440,'height':1000});erreurs,serveur=observer(autre,application['api_url'])
  try:
   autre.goto(application['web_url']);autre.get_by_role('button',name='Créer un compte',exact=True).click();autre.get_by_placeholder('Prénom NOM').fill('Administrateur B Recette');autre.get_by_placeholder('Ma Société SARL').fill('ATLAS RECETTE B — FICTIVE');autre.get_by_placeholder('Casablanca').fill('Casablanca');autre.get_by_placeholder('admin@societe.ma').fill('adminb@hisabpro-recette.example');autre.locator('input[type="password"]').fill('Recette!AtlasB2025');autre.get_by_role('button',name='Créer mon compte',exact=True).click();autre.wait_for_url('**/dashboard');token=autre.evaluate("localStorage.getItem('hisabpro_token')")
   with httpx.Client(base_url=application['api_url'],headers={'Authorization':'Bearer '+token}) as b:
    sb=ok(b.get('/api/societe/moi'));assert sb['id']!=sid and sb['raison_sociale']=='ATLAS RECETTE B — FICTIVE';assert ok(b.get('/api/tiers'))==[] and ok(b.get('/api/articles'))==[] and ok(b.get('/api/factures',params={'exercice':2026}))==[]
    assert b.get(f'/api/factures/{preuve["cycle"]["factures"][0]}/pdf').status_code==404;assert b.get(piece['url']).status_code==404
    bilan=ok(b.get('/api/etats/liasse/2026'))['etats']['bilan'];assert bilan['actif']['total']['net']==0 and bilan['passif']['total']==0
    assert {s['id'] for s in ok(b.get('/api/societes/mes-societes'))}=={sb['id']};assert {s['id'] for s in ok(api.get('/api/societes/mes-societes'))}=={sid}
   autre.goto(application['web_url']+'/tiers');expect(autre.get_by_text('Client Marchandises Recette',exact=True)).to_have_count(0);expect(autre.get_by_role('button',name='ATLAS RECETTE B — FICTIVE',exact=True)).to_be_visible();assert not erreurs and not serveur,(erreurs,serveur)
   assert core(application,sid)==initial;preuve['cas'].append({'id':'HP-ADM-017','statut':'Réussi'});preuve['societeB781']={'id':sb['id'],'aucun_acces_tiers_factures_articles_soldes_A':True,'pdf_facture_et_piece_A_refuses404':True,'selecteurs_cloisonnes':True,'14ecritures_A_inchangees':True}
   autre.screenshot(path=str(ROOT/'.codex-tests/societeB781.png'),full_page=True)
  finally:autre.close()
