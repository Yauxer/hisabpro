"""Les 17 mouvements du relevé fourni, sans modifier le journal définitif."""
from pathlib import Path
from decimal import Decimal as D
import csv,hashlib
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from cahier_suite777_support import core
from cahier_semestre789_support import manuelle
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

R=Path(__file__).resolve().parents[1];DOC=R/'docs/recette';DATES={'date_debut':'2025-01-01','date_fin':'2025-12-31'}
FICHIERS=['releve_banque_recette_2025.xlsx','releve_banque_recette_2025.csv','negatifs/releve_debit_credit_simultanes.csv']

def situation(api):return ok(api.get('/api/rapprochement/5141/situation',params=DATES))

def importer_releve(page,fichier):
 page.get_by_role('button',name='Import Excel / CSV',exact=True).click();page.locator('input[type="file"]').set_input_files(str(DOC/fichier))
 expect(page.get_by_role('button',name='Enregistrer le relevé',exact=True)).to_be_visible()
 with page.expect_response(lambda r:r.url.endswith('/api/rapprochement/import') and r.request.method=='POST') as r:page.get_by_role('button',name='Enregistrer le relevé',exact=True).click()
 d=ok(r.value,201);expect(page.get_by_text(f'Import enregistré : {d["nb_creees"]} ligne(s), {d["nb_ignorees"]} doublon(s) ignoré(s).',exact=True)).to_be_visible();return d

@pytest.mark.parametrize('largeur',[1440,390])
def test_813_banque_releve_integral_pointage_et_doublons(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'banque813r') as (api,page,sid,preuve):
  empreintes={f:hashlib.sha256((DOC/f).read_bytes()).hexdigest() for f in FICHIERS};preuve['sources813']=empreintes
  with (DOC/FICHIERS[1]).open(encoding='utf-8-sig') as f:releve=list(csv.DictReader(f,delimiter=';'))
  assert len(releve)==17 and sum((D(l['Crédit'])-D(l['Débit']) for l in releve),D(0))==D('287730')
  tiers={}
  for t in DATA['tiers']:tiers[t['code']]=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':t['type'],('compte_client' if t['type']=='client' else 'compte_fournisseur'):t['compte']}),201)
  b=DATA['banque'];ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  for o in sorted(DATA['operations'],key=lambda x:x['date']):
   if o['reference_recette']=='FRAIS-BQ':continue
   lignes=[{'compte':l['compte'],'debit':l['debit'],'credit':l['credit'],'libelle':o['description'],**({'tiers_id':tiers[l['tiers']]['id']} if l['tiers'] else {})} for l in o['lignes']]
   e=ok(api.post('/api/ecritures',json={'date':o['date'],'date_piece':o['date'],'journal':o['journal'],'libelle':o['description'],'reference':o['reference_recette'],'lignes':lignes,'est_validee':False}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
  assert len(core(application,sid))==49;manuelle(page,application,sid,'FRAIS-BQ',preuve);avant=core(application,sid);assert len(avant)==50
  frais=[e for e in ok(api.get('/api/ecritures',params={'exercice':2025})) if e['reference']=='FRAIS-BQ'];assert len(frais)==1 and frais[0]['date']==frais[0]['date_piece']=='2025-12-31' and frais[0]['est_validee'];assert {l['compte']:(D(str(l['debit'])),D(str(l['credit']))) for l in frais[0]['lignes']}=={'61473':(D(60),D(0)),'5141':(D(0),D(60))};preuve['cas'].append({'id':'HP-BNQ-001','statut':'Réussi'})
  page.goto(application['web_url']+'/rapprochement');expect(page.get_by_role('heading',name='Rapprochement bancaire',exact=True)).to_be_visible();expect(page.locator('input[type="date"]').nth(0)).to_have_value(DATES['date_debut']);expect(page.locator('input[type="date"]').nth(1)).to_have_value(DATES['date_fin'])
  assert situation(api)['lignes_releve']==[]
  # Fichier négatif exact : le parseur ne doit omettre ni accepter cette ligne.
  page.get_by_role('button',name='Import Excel / CSV',exact=True).click();page.locator('input[type="file"]').set_input_files(str(DOC/FICHIERS[2]));expect(page.get_by_text('Ligne 2 : Une seule colonne Débit ou Crédit doit porter un montant positif.',exact=True)).to_be_visible();expect(page.get_by_role('button',name='Enregistrer le relevé',exact=True)).to_have_count(0);assert situation(api)['lignes_releve']==[] and core(application,sid)==avant
  image=tmp_path/f'releve_invalide813_{largeur}.png';page.screenshot(path=str(image),full_page=True);preuve['releve_invalide813']={'capture':str(image),'sha256':hashlib.sha256(image.read_bytes()).hexdigest()};preuve['cas'].append({'id':'HP-NEG-024','statut':'Réussi'})
  # Le panneau d'import est déjà ouvert après l'échec.
  page.locator('input[type="file"]').set_input_files(str(DOC/FICHIERS[0]))
  with page.expect_response(lambda r:r.url.endswith('/api/rapprochement/import') and r.request.method=='POST') as r:page.get_by_role('button',name='Enregistrer le relevé',exact=True).click()
  importe=ok(r.value,201);assert (importe['nb_creees'],importe['nb_ignorees'])==(17,0)
  expect(page.get_by_text('Import enregistré : 17 ligne(s), 0 doublon(s) ignoré(s).',exact=True)).to_be_visible()
  page.get_by_placeholder('Début de période',exact=True).fill('0')
  with page.expect_response(lambda r:r.url.endswith('/api/rapprochement/5141/etat') and r.request.method=='PUT') as r:page.get_by_placeholder('Facultatif : solde indiqué par la banque',exact=True).click()
  ok(r.value);page.get_by_placeholder('Facultatif : solde indiqué par la banque',exact=True).fill('287730')
  with page.expect_response(lambda r:r.url.endswith('/api/rapprochement/5141/etat') and r.request.method=='PUT') as r:page.get_by_role('heading',name='Rapprochement bancaire',exact=True).click()
  ok(r.value);expect(page.get_by_text('✓ Équilibré',exact=True)).to_be_visible();expect(page.get_by_text('✓ Initial + mouvements = final',exact=True)).to_be_visible()
  s=situation(api);assert len(s['ecritures'])==len(s['lignes_releve'])==17 and D(str(s['solde_comptable_final']))==D('287730');couples={}
  for l in s['lignes_releve']:
   ref=l['libelle'].split(' — ')[0];source=next(r for r in releve if r['Libellé']==l['libelle']);sens='credit' if D(source['Crédit']) else 'debit';montant=D(source['Crédit']) or D(source['Débit']);assert l['date']==source['Date'] and l['sens']==sens and D(str(l['montant']))==montant
   es=[e for e in s['ecritures'] if e['reference']==ref and e['date']==l['date'] and D(str(e['debit'] if sens=='credit' else e['credit']))==montant];assert len(es)==1;couples[l['id']]=es[0]['ligne_id']
  preuve['cas'].append({'id':'HP-BNQ-002','statut':'Réussi'})
  with page.expect_response(lambda r:'/5141/propositions?' in r.url and r.request.method=='GET') as r:page.get_by_role('button',name='Proposer les rapprochements',exact=True).click()
  propositions=ok(r.value);assert propositions['propositions']==[] and len(propositions['sans_correspondance'])==17
  # Le libellé du fichier contient référence + descriptif : aucun appariement
  # approximatif ne doit être accepté au nom de l'automatisation.
  dialog=page.get_by_role('dialog',name='Propositions de rapprochement',exact=True);expect(dialog.get_by_text('Les propositions exigent',exact=False)).to_be_visible();dialog.get_by_role('button',name='Fermer',exact=True).click();assert not any(l['rapprochee'] for l in situation(api)['lignes_releve'])
  filtres=page.locator('select').filter(has=page.locator('option[value="non_rapprochees"]'));expect(filtres).to_have_count(2);filtres.nth(1).select_option('non_rapprochees')
  for l in s['lignes_releve']:
   row=page.locator('tbody tr').filter(has_text=l['libelle']).filter(has=page.locator('select'));expect(row).to_have_count(1)
   with page.expect_response(lambda r:r.url.endswith(f'/api/rapprochement/{l["id"]}/rapprocher') and r.request.method=='POST') as r:row.locator('select').select_option(str(couples[l['id']]))
   ok(r.value)
  apres=situation(api);assert all(l['rapprochee'] and l['ecriture_ligne_id']==couples[l['id']] for l in apres['lignes_releve']);assert all(e['rapprochee'] for e in apres['ecritures']);assert core(application,sid)==avant
  page.reload(wait_until='domcontentloaded');expect(page.get_by_text('✓ Équilibré',exact=True)).to_be_visible();assert page.get_by_placeholder('Début de période',exact=True).input_value()=='0' and D(page.get_by_placeholder('Facultatif : solde indiqué par la banque',exact=True).input_value())==D('287730')
  for l in apres['lignes_releve']:expect(page.locator('tbody tr').filter(has_text=l['libelle']).filter(has=page.locator('select')).locator('select')).to_have_value(str(couples[l['id']]))
  preuve['cas'].append({'id':'HP-BNQ-003','statut':'Réussi'})
  doublons=[]
  for fichier in FICHIERS[:2]:
   d=importer_releve(page,fichier);assert (d['nb_creees'],d['nb_ignorees'])==(0,17);doublons.append({'fichier':fichier,'resultat':d})
  fin=situation(api);assert fin==apres and core(application,sid)==avant;assert {f:hashlib.sha256((DOC/f).read_bytes()).hexdigest() for f in FICHIERS}==empreintes
  preuve['cas'].append({'id':'HP-BNQ-004','statut':'Réussi'});preuve['banque813']={'situation_avant_pointage':s,'situation_finale':fin,'propositions':propositions,'doublons':doublons,'couples':couples,'journal_50_inchange':True,'solde_final':'287730'}
