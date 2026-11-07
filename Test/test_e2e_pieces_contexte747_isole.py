"""Multipart natif : refus courant/ancien, pièce aboutie et JSON tardif."""
from contextlib import closing
from pathlib import Path
from uuid import uuid4
import base64,hashlib,json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_e2e_session200745_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,client_http)
from test_balance_contexte_fiscal735_isole import creer
from test_balance_documents691_isole import pdf_fictif,path
from test_e2e_administration_isole import observer
from browser_support import chromium_executable
ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('cas',['refus_ancien','succes_ancien','decodage_ancien','succes_courant','refus_courant'])
def test_747_multipart_contexte_et_octets(application,client_http,cas):
 a,email,_=client(application);b,_,_=client(application)
 with closing(a),closing(b),sync_playwright() as p:
  v=creer(a);endpoint=path(v);sid=ok(a.get('/api/auth/me'))['societe_id']
  sid_b=ok(b.get('/api/auth/me'))['societe_id']
  ok(b.post(f'/api/societes/{sid_b}/inviter',params={'email':email,'role':'lecture'}))
  token_b=ok(a.post(f'/api/societes/switcher/{sid_b}'))['access_token']
  old='invalide747' if cas.startswith('refus') else a.headers['Authorization'].split(' ',1)[1]
  ancien=cas.endswith('ancien');attendu=401 if cas.startswith('refus') else 201
  raw=pdf_fictif();cle=str(uuid4());pending=[];reponses=[];posts=[]
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();observer(page,application['api_url'])
   page.goto(application['web_url'],wait_until='domcontentloaded');page.add_script_tag(content=client_http)
   page.evaluate('t=>{localStorage.setItem("hisabpro_token",t);localStorage.setItem("hisabpro_role","admin");window.__doc747="initial"}',old)
   if cas in ('refus_ancien','succes_ancien'):
    def retenir(route):
     if route.request.method!='POST':return route.continue_()
     rep=route.fetch();assert rep.status==attendu
     pending.append((route,rep));page.evaluate('window.__retenu747=true')
    page.route('**'+endpoint,retenir)
   elif cas=='decodage_ancien':
    page.evaluate('''endpoint=>{const original=Response.prototype.json;Response.prototype.json=async function(...args){
     const r=await original.apply(this,args);if(this.url.endsWith(endpoint)){window.__retenu747=true;await new Promise(f=>window.__liberer747=f)}return r}}''',endpoint)
   page.on('response',lambda r:reponses.append(r) if r.url.endswith(endpoint) and r.request.method=='POST' else None)
   page.on('request',lambda r:posts.append(r) if r.url.endswith(endpoint) and r.method=='POST' else None)
   avant=donnees_metier(application)
   page.evaluate('''({id,empreinte,cle,raw})=>{const f=new FormData();f.append('cle',cle);f.append('empreinte',empreinte);
    f.append('reference','SOURCE FICTIVE747');f.append('file',new Blob([Uint8Array.from(atob(raw),c=>c.charCodeAt(0))],{type:'application/pdf'}),'piece_fictive747.pdf');
    window.__result747=null;window.__http739.etatsAPI.joindreDocumentBalance(id,f)
     .then(r=>window.__result747={succes:true,id:r?.id}).catch(e=>window.__result747={erreur:e.message})}''',
    {'id':v['id'],'empreinte':v['empreinte_sha256'],'cle':cle,'raw':base64.b64encode(raw).decode('ascii')})
   if ancien:
    page.wait_for_function('window.__retenu747===true')
    page.evaluate('t=>{localStorage.setItem("hisabpro_token",t);localStorage.setItem("hisabpro_role","lecture")}',token_b)
    if cas=='decodage_ancien':page.evaluate('window.__liberer747()')
    else:
     route,rep=pending.pop()
     with page.expect_response(lambda r:r.url.endswith(endpoint) and r.request.method=='POST'):route.fulfill(response=rep)
   if cas=='refus_courant':
    page.wait_for_function('localStorage.getItem("hisabpro_token")===null');expect(page.get_by_role('button',name='Se connecter',exact=True)).to_be_visible()
   else:
    page.wait_for_function('window.__result747!==null || window.__doc747!=="initial"')
    if ancien:
     assert page.evaluate('localStorage.getItem("hisabpro_token")')==token_b
     assert page.evaluate('localStorage.getItem("hisabpro_role")')=='lecture'
     assert 'session a changé' in page.evaluate('window.__result747?.erreur || ""')
     assert page.evaluate('window.__doc747')=='initial'
    else:assert page.evaluate('window.__result747.succes') is True
   assert len(posts)==1 and len(reponses)==1 and reponses[0].status==attendu
   documents=ok(a.get(endpoint))['documents'];apres=donnees_metier(application)
   if attendu==201:
    assert len(documents)==1;d=documents[0]
    assert d['sha256']==hashlib.sha256(raw).hexdigest() and d['taille']==len(raw)
    assert a.get(endpoint+f'/{d["id"]}').content==raw
    assert b.get(endpoint+f'/{d["id"]}',headers={'Authorization':'Bearer '+token_b}).status_code==404
    assert ok(a.get(BASE+f'/{v["id"]}'))==v
    assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balance_documents')
    dossier=application['uploads_dir']/str(sid)/'balance_preparation_documents'/str(v['id'])
    assert len(list(dossier.iterdir()))==1
   else:
    assert documents==[] and apres==avant
    dossier=application['uploads_dir']/str(sid)/'balance_preparation_documents'/str(v['id'])
    assert not dossier.exists() or not list(dossier.iterdir())
  finally:browser.close()
