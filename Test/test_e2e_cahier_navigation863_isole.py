"""SEC004 : navigation connectée et géométrie aux dimensions exactes du cahier."""
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_plafonds843_isole import facture843,valider843
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def geometrie863(page,nom,preuve,actions=()):
 h=page.get_by_role('main').get_by_role('heading',level=1);expect(h).to_be_visible();h.scroll_into_view_if_needed();b=h.bounding_box();v=page.viewport_size
 assert b['x']>=-1 and b['x']+b['width']<=v['width']+1,(nom,b,v)
 g=page.evaluate('({largeur:innerWidth,document:document.documentElement.scrollWidth})');assert g['document']<=g['largeur']+1,(nom,g)
 for a in actions:
  expect(a).to_be_visible();a.scroll_into_view_if_needed();q=a.bounding_box();assert q['x']>=-1 and q['x']+q['width']<=v['width']+1,(nom,q,v)
 preuve.setdefault('navigation863',[]).append({'ecran':nom,'viewport':v,'document':g,'titre_dans_largeur':True,'actions_accessibles':len(actions)})

def modal863(page,nom,preuve):
 m=page.get_by_role('dialog');expect(m).to_be_visible();v=page.viewport_size;b=m.bounding_box();assert b['x']>=-1 and b['x']+b['width']<=v['width']+1,(nom,b,v)
 for a in m.get_by_role('button',name='Annuler',exact=True).all():a.scroll_into_view_if_needed();q=a.bounding_box();assert q['x']>=-1 and q['x']+q['width']<=v['width']+1
 preuve.setdefault('modales863',[]).append({'nom':nom,'largeur':b['width'],'viewport':v,'fermeture_accessible':True});m.get_by_role('button',name='Annuler',exact=True).click();m.wait_for(state='hidden')

@pytest.mark.parametrize('largeur,hauteur',[(1366,768),(390,844)])
def test_863_navigation_et_details_sans_debordement(application,largeur,hauteur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'navigation863') as (api,page,sid,preuve):
  page.set_viewport_size({'width':largeur,'height':hauteur});t=next(t for t in DATA['tiers'] if t['code']=='C-SERVICE');t=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'client','compte_client':'3421'}),201);f=facture843(api,t,'vente','2025-01-20',1000,'UX-863');valider843(api);avant=core(application,sid)
  page.goto(application['web_url']+'/factures');geometrie863(page,'Factures',preuve);page.locator('tbody tr').filter(has_text=t['nom']).click();pdf=page.get_by_role('button',name='Télécharger PDF',exact=True);expect(pdf).to_be_visible();pdf.scroll_into_view_if_needed();q=pdf.bounding_box();assert q['x']>=-1 and q['x']+q['width']<=largeur+1;preuve['detail_facture863']={'telechargement_accessible':True}
  page.goto(application['web_url']+'/commercial');devis=page.get_by_role('button',name='Nouveau devis',exact=True);geometrie863(page,'Cycle commercial',preuve,[devis]);devis.click();modal863(page,'Nouveau devis',preuve)
  page.goto(application['web_url']+'/journal');nouvelle=page.get_by_role('button',name='Nouvelle écriture',exact=True);geometrie863(page,'Journal',preuve,[nouvelle]);nouvelle.click();modal863(page,'Nouvelle écriture',preuve)
  page.goto(application['web_url']+'/grand-livre');geometrie863(page,'Grand livre',preuve);page.locator('tbody tr').filter(has_text='3421').first.click();fermer=page.get_by_role('button',name='Fermer le détail',exact=True);geometrie863(page,'Grand livre détail',preuve,[fermer]);expect(page.get_by_role('main')).to_contain_text(f['numero']);fermer.click()
  page.goto(application['web_url']+'/liasse-fiscale');bilan=page.get_by_role('button',name='T1 · Bilan',exact=True);geometrie863(page,'Liasse fiscale',preuve,[bilan]);bilan.click();expect(page.get_by_role('heading',name='T1 · Bilan — Actif',exact=True)).to_be_visible();geometrie863(page,'Bilan',preuve)
  page.get_by_role('button',name='T3–T25 · ETIC',exact=True).click();ouvrir=page.get_by_role('button',name="Ouvrir l'ETIC",exact=True);geometrie863(page,'Liasse ETIC',preuve,[ouvrir]);ouvrir.click();geometrie863(page,'ETIC',preuve)
  page.goto(application['web_url']+'/parametres');geometrie863(page,'Paramètres',preuve);page.reload();geometrie863(page,'Paramètres rechargés',preuve);assert core(application,sid)==avant;preuve['journal863_conserve']=True;preuve['cas'].append({'id':'HP-SEC-004','statut':'Partiel','limite':'Navigation et géométrie automatisées ;appréciation humaine de tous les contenus et formulaires reste à effectuer.'})
