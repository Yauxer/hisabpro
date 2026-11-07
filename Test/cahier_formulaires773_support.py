"""Données du cahier principal, saisies UI réelles ; aucun appel métier simulé."""
from pathlib import Path
from uuid import uuid4
from contextlib import contextmanager
import hashlib,json
import httpx
from playwright.sync_api import sync_playwright,expect
from sqlalchemy import text
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion,observer
from test_e2e_facturation_isole import champ
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/recette/jeu_donnees_recette.json'
DATA=json.loads(SOURCE.read_text(encoding='utf8'))

def ok(r,status=200):
 code=r.status_code if isinstance(r,httpx.Response) else r.status
 assert code==status,(r.text if isinstance(r,httpx.Response) else r.text())
 return r.json()

def ouvrir_avance(modal,title):modal.locator('summary').filter(has_text=title).click()

@contextmanager
def laboratoire(application,largeur,tmp_path,nom='referentiels'):
 c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
 s=DATA['societe'];email=f'cahier773-{uuid4().hex[:8]}@hisabpro-recette.example'
 preuve={'cible_isolee':str(c['directory']),'nonce':c['nonce'],'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'largeur':largeur,'cas':[],'tiers':{},'articles':{},'erreur':None,'preconditions':'Société et paramètres par API ;leurs formulaires ont été testés séparément769. Email de laboratoire unique ;autres valeurs exactes du cahier.'}
 with httpx.Client(base_url=application['api_url'],timeout=30) as api,sync_playwright() as p:
  auth=ok(api.post('/api/auth/register',json={'nom':s['nom_admin'],'email':email,'password':s['password_test'],'raison_sociale':s['raison_sociale']}));api.headers['Authorization']='Bearer '+auth['access_token']
  profil=ok(api.patch('/api/societe/moi',json={k:s[k] for k in ['raison_sociale','forme_juridique','ville','adresse','capital_social','devise','identifiant_fiscal','ice','rc','patente','exercice_debut','regime_fiscal','regime_tva','periodicite_tva']}));sid=profil['id']
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True);page=browser.new_page(viewport={'width':largeur,'height':1050},accept_downloads=True);page.set_default_timeout(15000)
  errors,serveur=observer(page,application['api_url'])
  def accepter_dialogue(d):
   entree={'type':d.type,'message':d.message[:300]};preuve.setdefault('dialogues',[]).append(entree)
   try:d.accept()
   except BaseException as exc:
    entree['erreur_acceptation']=repr(exc);raise
  page.on('dialog',accepter_dialogue)
  try:
   connexion(page,application['web_url'],email,s['password_test']);page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2025');expect(page.get_by_label('Exercice actif',exact=True)).to_have_value('2025')
   yield api,page,sid,preuve
   assert not errors and not serveur,(errors,serveur)
   page.screenshot(path=str(ROOT/f'.codex-tests/cahier773_{nom}_{largeur}.png'),full_page=True)
  except BaseException as e:
   preuve['erreur']=repr(e)
   # Ne pas remplacer la cause initiale par un second timeout de diagnostic
   # lorsque la navigation a laissé un document sans body ou une page fermée.
   try:print('DIAGNOSTIC',page.url,errors,serveur,page.locator('body').inner_text(timeout=1000)[-4500:])
   except BaseException as diagnostic:preuve['erreur_diagnostic_body']=repr(diagnostic)
   try:page.screenshot(path=str(tmp_path/f'cahier773_{nom}_echec.png'),full_page=True,timeout=1000)
   except BaseException as diagnostic:preuve['erreur_diagnostic_capture']=repr(diagnostic)
   raise
  finally:
   (ROOT/f'.codex-tests/cahier773_{nom}_{largeur}_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8');browser.close()

def referentiels(api,page,application,sid,preuve):
 tiers={};articles={};page.goto(application['web_url']+'/tiers')
 for i,t in enumerate(DATA['tiers']):
  page.get_by_role('button',name='Nouveau tiers',exact=True).click();modal=page.get_by_role('dialog',name='Nouveau tiers',exact=True)
  modal.get_by_role('button',name='Client' if t['type']=='client' else 'Fournisseur',exact=True).click();modal.get_by_placeholder('Ex. Atlas Distribution SARL').fill(t['nom'])
  ouvrir_avance(modal,'Paramétrage comptable');label='Compte client' if t['type']=='client' else 'Compte fournisseur';champ(modal,label).fill(t['compte'])
  with page.expect_response(lambda r:r.url.endswith('/api/tiers') and r.request.method=='POST') as r:modal.get_by_role('button',name='Créer le tiers',exact=True).click()
  record=ok(r.value,201);tiers[t['code']]=record;modal.wait_for(state='hidden')
  expect(page.locator('tbody tr').first).to_contain_text(t['nom']);page.locator('tbody tr').filter(has_text=t['nom']).click();page.get_by_role('button',name='Modifier le tiers',exact=True).click()
  edition=page.get_by_role('dialog',name='Modifier le tiers',exact=True);ouvrir_avance(edition,'Paramétrage comptable');expect(champ(edition,label)).to_have_value(t['compte']);edition.get_by_role('button',name='Annuler',exact=True).click()
  cle='compte_client' if t['type']=='client' else 'compte_fournisseur';aux='code_aux_client' if t['type']=='client' else 'code_aux_fournisseur';assert record[cle]==t['compte'] and record[aux]
  preuve['tiers'][t['code']]={'id':record['id'],'compte':record[cle],'auxiliaire':record[aux]};preuve['cas'].append({'id':f'HP-ADM-{i+6:03d}','statut':'Réussi','controle':'Création UI,réouverture compte,auxiliaire généré etlecture API'})
 assert len(ok(api.get('/api/tiers')))==7
 page.reload(wait_until='domcontentloaded');expect(page.locator('tbody tr').first).to_contain_text(DATA['tiers'][-1]['nom'])
 page.goto(application['web_url']+'/articles')
 for i,a in enumerate(DATA['articles']):
  page.get_by_role('button',name='Nouvel article',exact=True).click();modal=page.get_by_role('dialog',name='Nouvel article',exact=True)
  champ(modal,'Code').fill(a['code']);champ(modal,'Désignation').fill(a['designation']);champ(modal,'Prix vente HT').fill(str(a.get('prix_vente',0)));champ(modal,'Prix achat HT').fill(str(a.get('prix_achat',0)));champ(modal,'TVA proposée','select').select_option(str(a['tva']))
  modal.get_by_role('button',name='Article stockable' if a['type']=='produit' else 'Service / frais',exact=True).click()
  if a['type']=='produit':champ(modal,'Stock initial').fill('0')
  else:champ(modal,'Unité','select').select_option('forfait')
  ouvrir_avance(modal,'Comptes comptables')
  for source,label in [('compte_vente','Compte de vente'),('compte_achat',"Compte d'achat")]:
   if source in a:champ(modal,label).fill(a[source])
  with page.expect_response(lambda r:r.url.endswith('/api/articles') and r.request.method=='POST') as r:modal.get_by_role('button',name='Créer l’article',exact=True).click()
  record=ok(r.value,201);articles[a['code']]=record;modal.wait_for(state='hidden');page.locator('tbody tr').filter(has_text=a['designation']).click()
  edition=page.get_by_role('dialog',name="Modifier l'article",exact=True);expect(champ(edition,'Code')).to_have_value(a['code']);expect(champ(edition,'TVA proposée','select')).to_have_value('20');ouvrir_avance(edition,'Comptes comptables')
  for cle,label in [('compte_vente','Compte de vente'),('compte_achat',"Compte d'achat")]:
   if cle in a:expect(champ(edition,label)).to_have_value(a[cle]);assert record[cle]==a[cle]
  if a['type']=='produit':expect(champ(edition,'Stock actuel')).to_have_value('0');assert record['stock_actuel']==0
  else:assert record['is_stockable'] is False and record['unite']=='forfait'
  edition.get_by_role('button',name='Annuler',exact=True).click()
  assert record['prix_vente_ht']==a.get('prix_vente',0) and record['prix_achat_ht']==a.get('prix_achat',0) and record['tva']==20
  preuve['articles'][a['code']]={'id':record['id'],'stockable':record['is_stockable'],'stock':record['stock_actuel'],'tva':record['tva'],'compte_achat':record['compte_achat'],'compte_vente':record['compte_vente']};preuve['cas'].append({'id':f'HP-ADM-{i+13:03d}','statut':'Réussi','controle':'Création UI,réouverture prix/TVA/comptes,stock zéro ouservice etlecture API ;comptes stock3111/6114 àvérifier séparément eninventaire'})
 assert len(ok(api.get('/api/articles')))==3
 with application['engine'].connect() as db:
  assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid'),{'sid':sid})==0
  for a in DATA['articles'][1:]:assert db.scalar(text('SELECT count(*) FROM mouvements_stock WHERE societe_id=:sid AND article_id=:aid'),{'sid':sid,'aid':articles[a['code']]['id']})==0
 return tiers,articles
