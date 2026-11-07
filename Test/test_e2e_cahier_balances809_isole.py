"""Quatre fiches 09D : fichiers originaux, Edge et PostgreSQL temporaires."""
from pathlib import Path
from decimal import Decimal as D
from uuid import uuid4
from zipfile import ZipFile
import base64,csv,hashlib,json
import httpx
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from cahier_suite777_support import core
from cahier_etats803_support import telecharger,nombre,valeurs_pdf
from test_etic_b14_liquidations807_isole import poster
from test_e2e_administration_isole import connexion,observer
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

R=Path(__file__).resolve().parents[1];DOC=R/'docs/recette';BASE='/api/etats/liasse/balance/dossiers'
SOURCES=['balance_attendue_2025.csv','balance_attendue_2025.xlsx','a_nouveaux_attendus_2026.csv','images/LOGO_RECETTE_FICTIF.png']

def panneau(page,app,annee,lecture=False):
 page.goto(app['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option(str(annee));page.goto(app['web_url']+'/liasse-fiscale')
 p=page.locator('section').filter(has=page.get_by_role('heading',name='Préparer depuis des balances externes',exact=True));p.get_by_role('button',name='Consulter les préparations' if lecture else 'Importer N / N-1',exact=True).click();return p

def importer(page,p,n,n1=None):
 p.get_by_label('Balance N',exact=True).set_input_files(str(DOC/n));p.get_by_label('Balance N-1 facultative',exact=True).set_input_files(str(DOC/n1) if n1 else [])
 with page.expect_response(lambda r:r.url.endswith('/api/etats/liasse/balance/preview') and r.request.method=='POST') as r:p.get_by_role('button',name='Contrôler et préparer',exact=True).click()
 d=ok(r.value);expect(p.get_by_role('status')).to_contain_text('Balances contrôlées');assert not d['pret_a_deposer'];return d

def controle(p,gestion=True,comparatif=False):
 for label,n,n1 in [('Total actif','337010','337010' if comparatif else None),('Total passif','337010','337010' if comparatif else None),('Résultat net CPC','106409.75' if gestion else None,'106409.75' if comparatif else None),('CAF','112709.75' if gestion else None,'112709.75' if comparatif else None)]:
  row=p.locator('table').first.get_by_role('row').filter(has=p.page.get_by_role('cell',name=label,exact=True));expect(row).to_have_count(1)
  for i,v in [(1,n),(2,n1)]:
   cell=row.locator('td').nth(i)
   if v is None:expect(cell).to_have_text('Indisponible')
   else:assert nombre(cell.inner_text())==D(v),(label,cell.inner_text(),v)

def conserver(page,p):
 with page.expect_response(lambda r:r.url.endswith(BASE) and r.request.method=='POST') as r:p.get_by_role('button',name='Conserver une nouvelle version',exact=True).click()
 v=ok(r.value,201);expect(p.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible();assert len(v['empreinte_sha256'])==64;return v

def relire(page,p,v):
 with page.expect_response(lambda r:r.url.endswith(BASE+'/'+str(v['id'])) and r.request.method=='GET') as r:p.get_by_label('Préparations conservées',exact=True).select_option(str(v['id']))
 assert ok(r.value)==v;expect(p.get_by_text(v['empreinte_sha256'],exact=False)).to_be_visible()

def exports(page,p,tmp_path,nom,v,preuve,gestion=True,comparatif=False):
 fichiers=[]
 for bouton,suffixe in [('Exporter la préparation Excel','xlsx'),('Exporter la préparation PDF','pdf')]:
  with page.expect_download() as r:p.get_by_role('button',name=bouton,exact=True).click()
  dest=tmp_path/f'{nom}.{suffixe}';r.value.save_as(dest);assert dest.stat().st_size>100;fichiers.append(dest)
 wb=load_workbook(fichiers[0],data_only=True);assert ('Empreinte des données normalisées',v['empreinte_sha256']) in list(wb['Dossier'].values)
 assert any(row[1]=='TOTAL GÉNÉRAL ACTIF' and D(str(row[4]))==D('337010') and (D(str(row[5]))==D('337010') if comparatif else row[5]=='Indisponible') for row in wb['Bilan actif'].values)
 for code,valeur in [('CPC','106409.75'),('ESG','112709.75')]:
  valeurs=list(wb[code+' N'].values)
  if gestion:assert any(isinstance(row[1],(int,float)) and D(str(row[1]))==D(valeur) for row in valeurs)
  else:assert any(isinstance(row[0],str) and row[0].startswith('Indisponible') and row[1]=='Indisponible' for row in valeurs)
  if comparatif:assert any(isinstance(row[1],(int,float)) and D(str(row[1]))==D(valeur) for row in wb[code+' N-1'].values)
 assert ('Balance source N-1' in wb.sheetnames) is comparatif
 lecteur=PdfReader(fichiers[1]);texte=' '.join(p.extract_text() or '' for p in lecteur.pages);assert v['empreinte_sha256'] in texte and D('337010') in valeurs_pdf(texte) and 'compléter' in texte
 assert any(page.images for page in lecteur.pages)
 with ZipFile(fichiers[0]) as z:assert any(n.startswith('xl/media/') for n in z.namelist())
 for dest in fichiers:preuve.setdefault('fichiers809',[]).append({'chemin':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})

@pytest.mark.parametrize('largeur',[1440,390])
def test_809_imports_versions_ouverture_comparatif_et_lecture(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'balances809') as (api,page,sid,preuve):
  hashes={n:hashlib.sha256((DOC/n).read_bytes()).hexdigest() for n in SOURCES};preuve['sources809']=hashes
  logo='data:image/png;base64,'+base64.b64encode((DOC/SOURCES[-1]).read_bytes()).decode();ok(api.patch('/api/societe/moi',json={'logo_url':logo}))
  tiers={}
  for t in DATA['tiers']:tiers[t['code']]=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':t['type'],('compte_client' if t['type']=='client' else 'compte_fournisseur'):t['compte']}),201)
  for o in sorted(DATA['operations'],key=lambda x:x['date']):
   ls=[{'compte':l['compte'],'debit':l['debit'],'credit':l['credit'],'libelle':o['description'],**({'tiers_id':tiers[l['tiers']]['id']} if l['tiers'] else {})} for l in o['lignes']];poster(api,o['journal'],o['date'],ls,o['reference_recette'])
  avant=core(application,sid);assert len(avant)==50;etats=ok(api.get('/api/etats/liasse/2025'));assert etats['archive'] is None
  comptes={r['numero'] for r in ok(api.get('/api/plan-comptable'))}
  with (DOC/SOURCES[0]).open(encoding='utf-8-sig') as f:assert {r['compte'] for r in csv.DictReader(f,delimiter=';')}<=comptes
  p=panneau(page,application,2025);d=importer(page,p,SOURCES[0]);controle(p);assert d['etats_n1'] is None and d['balance_n1'] is None
  x=telecharger(page,'Exporter la préparation Excel',tmp_path,'preview809.xlsx');w=load_workbook(x,data_only=True);assert ('Total actif',337010) in list(w['Bilan N'].values) and 'CPC N-1' not in w.sheetnames;preuve.setdefault('fichiers809',[]).append({'chemin':str(x),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()})
  v1=conserver(page,p);assert v1['version']==1;exports(page,p,tmp_path,'v1_809',v1,preuve)
  page.reload(wait_until='domcontentloaded');p=page.locator('section').filter(has=page.get_by_role('heading',name='Préparer depuis des balances externes',exact=True));p.get_by_role('button',name='Importer N / N-1',exact=True).click();relire(page,p,v1);controle(p);assert p.get_by_label('Balance N',exact=True).input_value()=='';exports(page,p,tmp_path,'v1_relu809',v1,preuve)
  d2=importer(page,p,SOURCES[1]);assert d2==d;v2=conserver(page,p);assert v2['id']!=v1['id'] and v2['version']==2 and v2['contenu']['sources']['n']==v1['contenu']['sources']['n'];assert ok(api.get(BASE+'/'+str(v1['id'])))==v1
  relire(page,p,v1);controle(p);preuve['cas'] += [{'id':'HP-LIA-010','statut':'Réussi'},{'id':'HP-LIA-011','statut':'Réussi'}]
  # Ouverture techniquement soldée : ne jamais inventer de CPC/CAF.
  ouverture=importer(page,p,SOURCES[2]);controle(p,gestion=False);assert ouverture['etats']['cpc']['resultat_net'] is None and ouverture['etats']['esg']['caf'] is None
  v3=conserver(page,p);exports(page,p,tmp_path,'ouverture809',v3,preuve,gestion=False);preuve['cas'].append({'id':'HP-LIA-013','statut':'Réussi'})
  if not any(e['annee']==2026 for e in ok(api.get('/api/exercices'))):ok(api.post('/api/exercices',json={'annee':2026,'date_debut':'2026-01-01','date_fin':'2026-12-31'}),201)
  p=panneau(page,application,2026);compare=importer(page,p,SOURCES[2],SOURCES[0]);controle(p,gestion=False,comparatif=True);assert compare['etats']['cpc']['resultat_net'] is None and D(str(compare['etats_n1']['cpc']['resultat_net']))==D('106409.75') and D(str(compare['etats_n1']['esg']['caf']))==D('112709.75')
  v4=conserver(page,p);assert v4['exercice']==2026 and v4['contenu']['periode']=={'debut':'2026-01-01','fin':'2026-12-31'};exports(page,p,tmp_path,'comparatif809',v4,preuve,gestion=False,comparatif=True);preuve['cas'].append({'id':'HP-LIA-014','statut':'Réussi'})
  # Même préparation consultée dans une session lecteur réellement authentifiée.
  email=f'lecteur809-{uuid4().hex}@hisabpro-recette.example';password=DATA['societe']['password_test'];ok(api.post('/api/utilisateurs',json={'nom':'Lecteur fictif809','email':email,'mot_de_passe':password,'role':'lecture'}),201)
  rp=page.context.browser.new_page(viewport={'width':largeur,'height':1050},accept_downloads=True);rp.set_default_timeout(15000);erreurs,serveur=observer(rp,application['api_url'])
  try:
   with rp.expect_response(lambda r:r.url.endswith('/api/auth/login') and r.request.method=='POST') as auth:connexion(rp,application['web_url'],email,password)
   token=ok(auth.value)['access_token'];q=panneau(rp,application,2025,lecture=True);relire(rp,q,v1);controle(q);assert q.get_by_role('button',name='Conserver une nouvelle version',exact=True).count()==0;assert q.get_by_label('Balance N',exact=True).count()==0;exports(rp,q,tmp_path,'lecteur809',v1,preuve)
   with httpx.Client(base_url=application['api_url'],headers={'Authorization':'Bearer '+token},timeout=30) as lecture:
    assert lecture.post(BASE,json={'exercice':2025,'lignes_n':v1['contenu']['sources']['n']}).status_code==403
   assert not erreurs and not serveur,(erreurs,serveur)
  finally:rp.close()
  assert core(application,sid)==avant;apres=ok(api.get('/api/etats/liasse/2025'));assert apres['etats']==etats['etats'] and apres['archive'] is None
  assert {n:hashlib.sha256((DOC/n).read_bytes()).hexdigest() for n in SOURCES}==hashes
  assert all(ok(api.get(BASE+'/'+str(v['id'])))==v for v in [v1,v2,v3,v4])
  preuve['balances809']={'versions':[v1,v2,v3,v4],'journal_50_et_etats_inchanges':True,'lecteur_refus403':True,'sources_originelles_inchangees':True,'comparatif_sans_faux_cpc':True}
