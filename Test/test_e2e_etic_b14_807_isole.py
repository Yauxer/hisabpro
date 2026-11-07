"""B14 rapproché du cahier : Edge réel, clôture préservée, archive non forcée."""
from decimal import Decimal as D
import hashlib,re
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,referentiels,DATA,ok
from cahier_suite777_support import core
from test_e2e_cahier_immobilisation785_isole import capital,acquisition
from cahier_semestre789_support import semestre
from cahier_annuel791_support import annuel
from cahier_cloture793_support import cloturer_cahier
from cahier_tva_echeances795_support import echeances_2026
from cahier_etic805_support import completer_etic,ouvrir,sauvegarder,lire
from cahier_etats803_support import telecharger
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_807_b14_annuel_confirmation_exports_et_archive_protegee(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'b14_807') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  capital(page,application,sid,preuve);immo=acquisition(api,page,application,sid,tiers['F-IMMO'],preuve);semestre(api,page,application,sid,tiers,articles,banque,preuve,tmp_path);annuel(api,page,application,sid,tiers,articles,banque,immo,preuve);cloturer_cahier(api,page,application,sid,preuve)
  echeances_2026(api,page,application,sid,preuve);completer_etic(api,page,application,sid,preuve,tmp_path)
  avant=core(application,sid);snapshot=ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']
  dette=-sum((D(str(l[2]))-D(str(l[3])) for e in avant if e[1].year==2025 for l in e[8] if l[1]=='4456'),D(0));assert dette==D('2400')
  page.goto(application['web_url']+'/etic');p=ouvrir(page,'B14');s=next(s for s in lire(api)['sections'] if s['code']=='B14');a,b,charges,immo,c=s['automatique']['lignes']
  for row,operations,declarations,fin in [(a,'33900','33900','0'),(b,'11680','11600','80'),(charges,'6880','6800','80'),(immo,'4800','4800','0'),(c,'22220','22300','-80')]:
   assert [D(str(row[k])) for k in ['operations','declarations','solde_fin']]==list(map(D,[operations,declarations,fin]))
  expect(p.get_by_text(re.compile('^La colonne « déclarations »'))).to_be_visible()
  rows=p.locator('tbody tr');expect(rows).to_have_count(5)
  expect(rows.nth(0)).to_contain_text('33');expect(rows.nth(0)).to_contain_text('900')
  notes='Rapprochement fictif B14-807 : TVA collectée et liquidée 33 900 MAD ; TVA sur charges comptabilisée 6 880, liquidée 6 800, solde non encore récupéré 80 ; immobilisations comptabilisées et liquidées 4 800. Total récupérable liquidé 11 600. Solde A - B = -80, distinct du compte 4456 : dette déjà liquidée de 2 400 à la clôture, payée le 20/01/2026 dans ce laboratoire. Cinq écritures OD de liquidation rapprochées du cahier ; aucun dépôt fiscal réel affirmé.'
  p.locator('textarea').fill(notes);p.get_by_role('checkbox',name=re.compile("^J'ai contrôlé")).check();b14=sauvegarder(api,page,application,'B14',True);assert b14['contenu']['notes']==notes
  fin=lire(api);assert fin['progression']['completes']==21 and {s['code'] for s in fin['sections'] if not s['complete']}=={'B6','B13'}
  assert core(application,sid)==avant and ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']==snapshot
  page.goto(application['web_url']+'/liasse-fiscale');expect(page.get_by_role('button',name='Finaliser',exact=True)).to_be_disabled();refus=api.post('/api/etats/liasse/2025/finaliser');assert refus.status_code==409
  excel=telecharger(page,'Excel',tmp_path,'liasse_b14_807.xlsx');pdf=telecharger(page,'PDF',tmp_path,'liasse_b14_807.pdf');wb=load_workbook(excel,data_only=True)
  assert any(isinstance(v,str) and notes in v for row in wb['ETIC'].values for v in row)
  texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert 'B14-807' in texte and '21/23' in texte and 'BLOQUANT' in texte
  assert core(application,sid)==avant and ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']==snapshot
  preuve['b14_807']={'section_complete':b14,'progression':fin['progression'],'dette_4456':'2400','archive_refusee':409,'journal_et_snapshot_inchanges':True}
  preuve['fichiers807']=[{'chemin':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [excel,pdf]]
  preuve['cas'].append({'id':'HP-ETA-019','statut':'Réussi'})
