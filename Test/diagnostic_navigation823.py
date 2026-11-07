"""Diagnostic explicite : réseau CDP et polices pendant navigations complètes."""
from pathlib import Path
from navigation823_support import navigations_completes823
import pytest,hashlib
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire
from test_e2e_cahier_avant_is817_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_823_diagnostic_reseau_polices(application,tmp_path,largeur,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'navigation823_synchronisee') as (api,page,sid,preuve):
  cdp=page.context.new_cdp_session(page);cdp.send('Network.enable');pending={};failures=[];preuve['reseau823']={'en_attente':pending,'echecs':failures};preuve['navigations823']=[]
  cdp.on('Network.requestWillBeSent',lambda p:pending.update({p['requestId']:{'url':p['request']['url'],'type':p.get('type'),'timestamp':p.get('timestamp')}}))
  cdp.on('Network.loadingFinished',lambda p:pending.pop(p['requestId'],None))
  def fail(p):
   r=pending.pop(p['requestId'],None);failures.append({'request':r,'erreur':p.get('errorText'),'cancelled':p.get('canceled')})
  cdp.on('Network.loadingFailed',fail)
  try:
   for route in ['/journal','/immobilisations','/factures','/lettrage','/grand-livre']*6:
    page.goto(application['web_url']+route);expect(page.get_by_role('main')).to_be_visible();preuve['navigations823'].append(route)
   page.wait_for_function("document.fonts.status === 'loaded'",timeout=15000)
   assert len(preuve['navigations823'])==30
  finally:
   preuve['polices823']=page.evaluate("({etat:document.fonts.status,faces:[...document.fonts].filter(f=>f.status!=='unloaded').map(f=>({famille:f.family,etat:f.status})),ressources:performance.getEntriesByType('resource').filter(r=>r.name.includes('woff')).map(r=>({nom:r.name,duree:r.duration,octets:r.transferSize}))})")
   p=tmp_path/'serveur_navigation823.log';p.write_bytes(application['web_log'].read_bytes());preuve['serveur823']={'chemin':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
