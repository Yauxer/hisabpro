"""SEC001–003 : sessions réelles, invitations et mots de passe, preuves sans secrets."""
import base64,json
import httpx,pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_administration_isole import connexion,observer
from test_e2e_cahier_avant_is823_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)
ANCIEN='Recette!Atlas2025';NOUVEAU='Recette!Atlas2025Long'

def jeton(api,email,password):
 r=api.post('/api/auth/login',json={'email':email,'password':password});assert r.status_code==200
 return r.json()['access_token']

def avec(api,token,path):return api.get(path,headers={'Authorization':'Bearer '+token})

def changer(api,page,app,email,role,preuve):
 ancien=jeton(api,email,ANCIEN);payload=json.loads(base64.urlsafe_b64decode(ancien.split('.')[1]+'==='));assert 'pwd_version' in payload
 avant=avec(api,ancien,'/api/auth/me');assert avant.status_code==200 and avant.json()['role']==role;uid=avant.json()['id'];sid=avant.json()['societe_id'];n=[];page.on('request',lambda r:n.append(1) if r.method=='POST' and r.url.endswith('/api/auth/mot-de-passe') else None)
 page.goto(app['web_url']+'/parametres');page.get_by_role('button',name='Mon compte',exact=True).click();section=page.get_by_role('region',name='Sécurité du compte personnel')
 section.get_by_label('Mot de passe actuel',exact=True).fill('Recette!Incorrect2025');section.get_by_label('Nouveau mot de passe',exact=True).fill(NOUVEAU);section.get_by_label('Confirmer le nouveau mot de passe',exact=True).fill(NOUVEAU)
 with page.expect_response(lambda r:r.url.endswith('/api/auth/mot-de-passe') and r.request.method=='POST') as rr:section.get_by_role('button',name='Modifier mon mot de passe',exact=True).click()
 assert rr.value.status==400;expect(section.get_by_role('alert')).to_contain_text('actuel est incorrect');assert avec(api,ancien,'/api/auth/me').status_code==200;nb=len(n)
 section.get_by_label('Mot de passe actuel',exact=True).fill(ANCIEN);section.get_by_label('Confirmer le nouveau mot de passe',exact=True).fill('ConfirmationFictiveDifferente835!');section.get_by_role('button',name='Modifier mon mot de passe',exact=True).click();expect(section.get_by_role('alert')).to_contain_text('confirmation');assert len(n)==nb and avec(api,ancien,'/api/auth/me').status_code==200
 section.get_by_label('Confirmer le nouveau mot de passe',exact=True).fill(NOUVEAU)
 with page.expect_response(lambda r:r.url.endswith('/api/auth/mot-de-passe') and r.request.method=='POST') as rr:section.get_by_role('button',name='Modifier mon mot de passe',exact=True).click()
 assert rr.value.status==204;expect(section.get_by_role('status')).to_contain_text('Reconnectez-vous');expect(section.locator('input[type=password]')).to_have_count(0);assert page.evaluate("localStorage.getItem('hisabpro_token')") is None
 assert avec(api,ancien,'/api/auth/me').status_code==401
 r=api.post('/api/auth/login',json={'email':email,'password':ANCIEN});assert r.status_code==401
 neuf=jeton(api,email,NOUVEAU);me=avec(api,neuf,'/api/auth/me');assert me.status_code==200 and me.json()['id']==uid and me.json()['role']==role and me.json()['societe_id']==sid
 section.get_by_role('button',name='Revenir à la connexion',exact=True).click();expect(page.get_by_role('button',name='Se connecter',exact=True)).to_be_visible();connexion(page,app['web_url'],email,NOUVEAU)
 if role=='admin':api.headers['Authorization']='Bearer '+neuf
 preuve.setdefault('mots_de_passe835',[]).append({'role':role,'user_id':uid,'societe_id':sid,'actuel_incorrect':400,'confirmation_differente_sans_post':True,'changement':204,'ancien_secret':401,'ancien_jeton_versionne':401,'nouvelle_connexion':200,'roles_societe_conserves':True,'secrets_et_jetons_exclus':True})

@pytest.mark.parametrize('largeur',[1440,390])
def test_835_revocation_invite_et_mot_de_passe_admin_lecture(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'securite835') as (api,page,sid,preuve):
  me=ok(api.get('/api/auth/me'));e=ok(api.post('/api/ecritures',json={'date':'2025-01-01','date_piece':'2025-01-01','journal':'BQ','reference':'PROTEGE-835','libelle':'Témoin comptable fictif réservé à A835','lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}]}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'));initial=core(application,sid);assert len(initial)==1
  email_b=f'invite835-{sid}@hisabpro-recette.example';nom_b=f'Société B fictive835 {sid}';r=api.post('/api/auth/register',json={'nom':'Compte principal B fictif','email':email_b,'password':ANCIEN,'raison_sociale':nom_b});assert r.status_code==200;token_b=r.json()['access_token'];profil_b=avec(api,token_b,'/api/auth/me');assert profil_b.status_code==200;uid_b=profil_b.json()['id'];sid_b=profil_b.json()['societe_id']
  page.goto(application['web_url']+'/parametres');page.get_by_role('button',name='Utilisateurs',exact=True).click();page.get_by_role('button',name='Donner accès à un utilisateur existant',exact=True).click();page.get_by_label('E-mail du compte existant',exact=True).fill(email_b);page.get_by_label('Rôle dans cette société',exact=True).select_option('lecture')
  with page.expect_response(lambda r:f'/api/societes/{sid}/inviter?' in r.url and r.request.method=='POST') as rr:page.get_by_role('button',name='Accorder cet accès',exact=True).click()
  assert rr.value.status==200;row=page.locator('tbody tr').filter(has_text=email_b);expect(row).to_contain_text('Accès invité')
  ctx=page.context.browser.new_context(viewport={'width':largeur,'height':1050});gp=ctx.new_page();gp.set_default_timeout(15000);errors,serveur=observer(gp,application['api_url'])
  try:
   connexion(gp,application['web_url'],email_b,ANCIEN);gp.get_by_role('button',name=nom_b,exact=True).click();gp.get_by_role('button').filter(has=gp.get_by_text(DATA['societe']['raison_sociale'],exact=True)).click();expect(gp.get_by_role('button',name=DATA['societe']['raison_sociale'],exact=True)).to_be_visible();token_a=gp.evaluate("localStorage.getItem('hisabpro_token')");assert avec(api,token_a,'/api/auth/me').json()['role']=='lecture'
   gp.goto(application['web_url']+'/cloture');gp.get_by_label('Exercice actif',exact=True).select_option('2025');gp.goto(application['web_url']+'/journal');expect(gp.get_by_text('PROTEGE-835',exact=True)).to_be_visible()
   with page.expect_response(lambda r:r.url.endswith(f'/api/utilisateurs/{uid_b}') and r.request.method=='PATCH') as rr:row.get_by_title("Désactiver l'accès",exact=True).click()
   assert rr.value.status==200;expect(row).to_contain_text('Désactivé');assert avec(api,token_a,'/api/societe/moi').status_code==403 and avec(api,token_a,'/api/ecritures?exercice=2025').status_code==403
   with gp.expect_response(lambda r:r.url.startswith(application['api_url']) and r.status==403):gp.reload(wait_until='domcontentloaded')
   # Le profil est désormais contrôlé avant le montage des fournisseurs de
   # données : après révocation, tout l'écran protégé reste absent. Ne pas
   # attendre l'ancien composant de calendrier, qui n'est plus rendu ici.
   expect(gp.get_by_text('PROTEGE-835',exact=True)).to_have_count(0);expect(gp.get_by_role('alert')).to_contain_text('révoqué');expect(gp.get_by_role('main')).to_have_count(0);expect(gp.get_by_label('Exercice comptable',exact=True)).to_have_count(0);gp.get_by_role('button',name='Réessayer',exact=True).click();expect(gp.get_by_role('alert')).to_contain_text('révoqué');expect(gp.get_by_role('main')).to_have_count(0);b=avec(api,token_b,'/api/auth/me');assert b.status_code==200 and b.json()['societe_id']==sid_b and b.json()['id']==uid_b and b.json()['role']=='admin';assert not errors and not serveur
   preuve['revocation835']={'invite_id':uid_b,'societe_A':sid,'societe_principale_B':sid_b,'ancien_jeton_A':403,'journal_A':403,'compte_principal_B':200,'ancien_temoin_absent_apres_rechargement':True,'compte_principal_non_supprime':True}
  finally:ctx.close()
  changer(api,page,application,me['email'],'admin',preuve);lecteur=ok(api.post('/api/utilisateurs',json={'nom':'Lecteur personnel fictif835','email':f'lecture835-{sid}@hisabpro-recette.example','mot_de_passe':ANCIEN,'role':'lecture'}),201)
  ctx=page.context.browser.new_context(viewport={'width':largeur,'height':1050});lp=ctx.new_page();lp.set_default_timeout(15000);errors,serveur=observer(lp,application['api_url'])
  try:
   connexion(lp,application['web_url'],lecteur['email'],ANCIEN);changer(api,lp,application,lecteur['email'],'lecture',preuve);assert not errors and not serveur
  finally:ctx.close()
  assert core(application,sid)==initial and ok(api.get('/api/auth/me'))['id']==me['id'];preuve['temoin835_conserve']=True;preuve['cas'] += [{'id':c,'statut':'Réussi'} for c in ['HP-SEC-001','HP-SEC-002','HP-SEC-003']]
