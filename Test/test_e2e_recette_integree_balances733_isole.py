"""Recette intégrée733 : CSV importés puis tous compléments connectés dans Edge."""
from contextlib import closing
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_recette_integree_balances733_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,R,D,sources,completer,verifier,verifier_export,
 b12_body,b13_body,b14_body,extra_body,c3_url)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from test_e2e_balance_passage_fiscal725_isole import saisir as saisir12,sauver as sauver12,SUMMARY as S12,REGION as R12
from test_e2e_balance_resultat_courant721_isole import saisir as saisir13,sauver as sauver13,SUMMARY as S13,REGION as R13
from test_e2e_balance_tva727_isole import saisir as saisir14,sauver as sauver14,SUMMARY as S14,REGION as R14
from test_e2e_balance_c3_extra731_isole import saisir as saisir_extra,sauver as sauver_extra,SUMMARY as SX,REGION as RX,actualiser_c3,C3
from test_e2e_balance_comparatif_n2729_isole import saisir as saisir_n2,sauver as sauver_n2,SUMMARY as SN2,REGION as RN2
from browser_support import chromium_executable


def initialiser_c3(page,panel,v):
 panel.get_by_text(C3,exact=True).click();c=panel.get_by_role('region',name='Indicateurs C3 de la préparation',exact=True)
 c.get_by_role('checkbox').check()
 with page.expect_response(lambda r:r.url.endswith(c3_url(v)) and r.request.method=='POST') as rep:
  c.get_by_role('button',name='Conserver les indicateurs C3 dans une nouvelle version',exact=True).click()
 assert rep.value.status==201;v=rep.value.json()
 expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
 return v


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_733_csv_raccords_fiscaux_c3_exports_et_lecture_connectes(application,role,largeur,tmp_path):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  s,v=sources(api)
  if role=='lecture':v=completer(api,s,v)
  if role!='admin':
   email=email.replace('@','-'+role+'@');ok(api.post('/api/utilisateurs',json={'nom':'Intégré fictif733','email':email,'mot_de_passe':password,'role':role}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(12000)
   errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   avant=donnees_metier(application);panel,_=ouvrir(page,application,v,role=='lecture')
   if role!='lecture':
    # Vrais CSV du cahier, vrai parsing frontend et vraie conservation API.
    panel.get_by_label('Balance N',exact=True).set_input_files(str(R/'docs/recette/BALANCE_FICTIVE_INTEGREE733_N.csv'))
    panel.get_by_label('Balance N-1 facultative',exact=True).set_input_files(str(R/'docs/recette/BALANCE_FICTIVE_INTEGREE733_N1.csv'))
    panel.get_by_role('button',name='Contrôler et préparer',exact=True).click()
    expect(panel.get_by_text('Balances contrôlées — préparation à compléter. Aucune écriture créée.',exact=True)).to_be_visible()
    with page.expect_response(lambda r:r.url.endswith(BASE) and r.request.method=='POST') as rep:
     panel.get_by_role('button',name='Conserver une nouvelle version',exact=True).click()
    assert rep.value.status==201;v=rep.value.json()
    expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
    panel.get_by_text(SN2,exact=True).click();detail=panel.get_by_role('region',name=RN2,exact=True)
    saisir_n2(detail,s,D['reference_n2']);v,detail=sauver_n2(page,panel,detail,v)
    v=initialiser_c3(page,panel,v)
    for summary,region,body,saisir,sauver in [(S12,R12,b12_body,saisir12,sauver12),(S13,R13,b13_body,saisir13,sauver13),(S14,R14,b14_body,saisir14,sauver14),(SX,RX,extra_body,saisir_extra,sauver_extra)]:
     panel.get_by_text(summary,exact=True).click();detail=panel.get_by_role('region',name=region,exact=True)
     for t in body(v)['tables']:saisir(detail,t)
     v,detail=sauver(page,panel,detail,v)
    expect(panel).to_contain_text('Un complément extra-comptable C3 est conservé. Conservez une nouvelle version')
    v,c=actualiser_c3(page,panel,v)
   else:
    for summary,region in [(S12,R12),(S13,R13),(S14,R14),(SX,RX)]:
     panel.get_by_text(summary,exact=True).click();detail=panel.get_by_role('region',name=region,exact=True)
     assert detail.get_by_role('button',name='Conserver les tableaux ETIC dans une nouvelle version',exact=True).count()==0
    panel.get_by_text(C3,exact=True).click();c=panel.get_by_role('region',name='Indicateurs C3 de la préparation',exact=True)
   verifier(v);expect(c).to_contain_text('17.520,00 MAD');expect(c).to_contain_text('6.020,00 MAD')
   extra=c.get_by_role('region',name='Déclarations extra-comptables C3',exact=True)
   expect(extra).to_contain_text('3,50 personnes');expect(extra).to_contain_text('60,20 MAD / titre')
   c.get_by_label('Période des indicateurs',exact=True).select_option('n1');expect(c).to_contain_text('13.200,00 MAD')
   c.get_by_label('Période des indicateurs',exact=True).select_option('n2');expect(c).to_contain_text('11.000,00 MAD')
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/f'integre733-{role}.zip';rep.value.save_as(dest);export=verifier_export(dest.read_bytes(),v)
   apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
   assert ok(api.get(BASE+f'/{s["id"]}'))==s
   c.get_by_label('Période des indicateurs',exact=True).select_option('n');extra.scroll_into_view_if_needed()
   page.screenshot(path=str(tmp_path/f'integre733-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
   (R/f'.codex-tests/recette733_{role}_preuve.json').write_text(json.dumps({'role':role,'largeur':largeur,
    'csv_reels_importes':role!='lecture','complements_connectes':True,'oracles_croises_valides':True,
    'metier_hors_preparation_inchange':True,'source_n2_preservee':True,'export':export,
    'erreurs_navigateur':errors,'erreurs_serveur':serveur},ensure_ascii=False,indent=2),encoding='utf8')
  finally:browser.close()
