"""Le client HTTP réel ne doit pas restituer une réponse d'une ancienne société."""
from contextlib import closing
from pathlib import Path
import json
import pytest
from playwright.sync_api import sync_playwright
from test_balance_css743_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier)
from test_balance_contexte_fiscal735_isole import creer
from test_balance_css743_isole import body as css_body,url as css_url
from test_e2e_session401739_isole import client_http
from test_e2e_administration_isole import observer
from browser_support import chromium_executable
ROOT=Path(__file__).resolve().parents[1]


def scenario(application,client_http,genre,moment=None):
 a,email_a,_=client(application);b,_,_=client(application)
 with closing(a),closing(b),sync_playwright() as p:
  v=creer(a);sid_a=ok(a.get('/api/auth/me'))['societe_id']
  sid_b=ok(b.get('/api/auth/me'))['societe_id']
  ok(b.post(f'/api/societes/{sid_b}/inviter',params={'email':email_a,'role':'lecture'}))
  token_b=ok(a.post(f'/api/societes/switcher/{sid_b}'))['access_token']
  profil_b=ok(a.get('/api/auth/me',headers={'Authorization':'Bearer '+token_b}))
  assert profil_b['id']==ok(a.get('/api/auth/me'))['id']
  assert profil_b['role']=='lecture' and profil_b['societe_id']!=sid_a
  endpoint='/api/auth/me' if genre=='json' else css_url(v) if genre=='post' else BASE+f'/{v["id"]}/pdf'
  if genre!='json':assert b.get(endpoint,headers={'Authorization':'Bearer '+token_b}).status_code==404
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();errors,_=observer(page,application['api_url'])
   page.goto(application['web_url'],wait_until='domcontentloaded');page.add_script_tag(content=client_http)
   token_a=a.headers['Authorization'].split(' ',1)[1]
   page.evaluate('t=>{localStorage.setItem("hisabpro_token",t);localStorage.setItem("hisabpro_role","admin");window.__document745="initial"}',token_a)
   pending=[]
   if moment=='entetes':
    def retenir(route):
     if genre=='post' and route.request.method!='POST':return route.continue_()
     rep=route.fetch();assert rep.status==(201 if genre=='post' else 200)
     pending.append((route,rep));page.evaluate('window.__retenu745=true')
    page.route('**'+endpoint,retenir,times=1)
   elif moment=='decodage':
    # Garde le corps JSON/blob natif intégral ; seul l'achèvement du décodage
    # est retenu pour reproduire la course après réception des en-têtes.
    page.evaluate('''({m,endpoint})=>{const original=Response.prototype[m];
     Response.prototype[m]=async function(...args){const contenu=await original.apply(this,args);
      if(this.url.endsWith(endpoint)){window.__retenu745=true;await new Promise(r=>window.__liberer745=r)}
      return contenu}}''',{'m':'json' if genre=='json' else 'blob','endpoint':endpoint})
   avant=donnees_metier(application);posts=[]
   page.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith(endpoint) else None)
   versions_avant=ok(a.get(BASE,params={'exercice':v['exercice']}))
   expression='window.__http739.authAPI.me()' if genre=='json' else f'window.__http739.etatsAPI.preparationBalancePDF({v["id"]})'
   if genre=='post':expression=f'window.__http739.etatsAPI.conserverBalanceCSS({v["id"]},'+json.dumps(css_body(v))+')'
   page.evaluate('e=>{window.__resultat745=null;eval(e).then(r=>window.__resultat745={succes:true,role:r?.role,societe_id:r?.societe_id,taille:r?.blob?.size,filename:r?.filename}).catch(e=>window.__resultat745={erreur:e.message})}',expression)
   if moment:
    page.wait_for_function('window.__retenu745===true')
    page.evaluate('t=>{localStorage.setItem("hisabpro_token",t);localStorage.setItem("hisabpro_role","lecture")}',token_b)
    if moment=='entetes':
     route,rep=pending.pop()
     if genre=='post':sauve=rep.json()
     with page.expect_response(lambda r:r.url.endswith(endpoint)):route.fulfill(response=rep)
    else:page.evaluate('window.__liberer745()')
   page.wait_for_function('window.__resultat745!==null')
   resultat=page.evaluate('window.__resultat745')
   preuve={'genre':genre,'moment':moment,'resultat':resultat,'role_local':page.evaluate('localStorage.getItem("hisabpro_role")'),'nouveau_role_attendu':'lecture' if moment else 'admin'}
   (ROOT/f'.codex-tests/reponse745_{moment}_{genre}.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
   if moment:
    assert 'session a changé' in resultat.get('erreur',''),preuve
    assert page.evaluate('localStorage.getItem("hisabpro_token")')==token_b
    assert page.evaluate('localStorage.getItem("hisabpro_role")')=='lecture'
    assert ok(b.get('/api/auth/me',headers={'Authorization':'Bearer '+token_b}))==profil_b
   else:
    assert resultat['succes'] and page.evaluate('localStorage.getItem("hisabpro_token")')==token_a
    if genre=='json':assert resultat['societe_id']==sid_a and resultat['role']=='admin'
    else:assert resultat['taille']>100 and resultat['filename'].endswith('.pdf')
   assert page.evaluate('window.__document745')=='initial' and not errors
   apres=donnees_metier(application)
   if genre=='post':
    assert len(posts)==1
    assert len(ok(a.get(BASE,params={'exercice':v['exercice']})))==len(versions_avant)+1
    assert ok(a.get(BASE+f'/{sauve["id"]}'))==sauve and ok(a.get(BASE+f'/{v["id"]}'))==v
    assert b.get(BASE+f'/{sauve["id"]}',headers={'Authorization':'Bearer '+token_b}).status_code==404
    assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')
   else:assert apres==avant
  finally:browser.close()


@pytest.mark.parametrize('genre',['json','telechargement'])
@pytest.mark.parametrize('moment',['entetes','decodage'])
def test_745_reponse200_reelle_ancienne_session_rejetee(application,client_http,genre,moment):
 scenario(application,client_http,genre,moment)


@pytest.mark.parametrize('genre',['json','telechargement'])
def test_745_reponse200_session_courante_conservee(application,client_http,genre):
 scenario(application,client_http,genre)


def test_745_post_abouti_ancienne_societe_non_rejoue(application,client_http):
 scenario(application,client_http,'post','entetes')
