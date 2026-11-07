"""Fichiers négatifs originaux, erreurs visibles et absence de persistance."""
from pathlib import Path
import hashlib
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,ok
from cahier_suite777_support import core
from test_e2e_cahier_balances809_isole import panneau,importer,controle,conserver,BASE
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

R=Path(__file__).resolve().parents[1];DOC=R/'docs/recette'
CAS=[('HP-NEG-046','balance_desequilibree.csv','déséquilibrée'),
 ('HP-NEG-047','balance_compte_inconnu.csv','absent du plan'),
 ('HP-NEG-048','balance_compte_double.csv','doublon'),
 ('HP-NEG-049','balance_montant_nan.csv','fini'),
 ('HP-NEG-050','balance_resultat_et_gestion.csv','simultanés')]

@pytest.mark.parametrize('largeur',[1440,390])
def test_811_cinq_imports_invalides_refuses_sans_effet(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'negatifs811') as (api,page,sid,preuve):
  avant=core(application,sid);assert avant==();plan=ok(api.get('/api/plan-comptable'));versions=ok(api.get(BASE,params={'exercice':2025}));assert versions==[]
  p=panneau(page,application,2025);preuve['negatifs811']=[]
  for cas,fichier,motif in CAS:
   source=DOC/'negatifs'/fichier;sha=hashlib.sha256(source.read_bytes()).hexdigest();p.get_by_label('Balance N',exact=True).set_input_files(str(source))
   with page.expect_response(lambda r:r.url.endswith('/api/etats/liasse/balance/preview') and r.request.method=='POST') as r:p.get_by_role('button',name='Contrôler et préparer',exact=True).click()
   assert r.value.status==422,r.value.text();erreur=ok_erreur=r.value.json()['detail'];assert isinstance(erreur,str) and motif in erreur
   alerte=p.get_by_role('alert');expect(alerte).to_be_visible();expect(alerte).to_contain_text(motif);assert '[object Object]' not in alerte.inner_text()
   assert p.get_by_role('button',name='Conserver une nouvelle version',exact=True).count()==0
   assert core(application,sid)==avant and ok(api.get(BASE,params={'exercice':2025}))==versions and ok(api.get('/api/plan-comptable'))==plan
   image=tmp_path/f'{cas}_{largeur}.png';alerte.scroll_into_view_if_needed();page.screenshot(path=str(image),full_page=True)
   assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
   preuve['negatifs811'].append({'id':cas,'fichier':str(source.relative_to(R)),'sha256':sha,'statut_http':422,'diagnostic':erreur,'zero_persistance':True,'capture':str(image),'capture_sha256':hashlib.sha256(image.read_bytes()).hexdigest()});preuve['cas'].append({'id':cas,'statut':'Réussi'})
  # Le même formulaire doit rester utilisable après les cinq refus.
  importer(page,p,'balance_attendue_2025.csv');controle(p);expect(p.get_by_role('alert')).to_have_count(0);v=conserver(page,p);assert v['version']==1 and len(ok(api.get(BASE,params={'exercice':2025})))==1
  assert core(application,sid)==avant and ok(api.get('/api/etats/liasse/2025'))['archive'] is None
  preuve['correction_valide_apres_5_refus']=True
