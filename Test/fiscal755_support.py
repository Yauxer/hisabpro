"""Support du scénario annuel755 ; oracles lus du calcul indépendant livré."""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile
from uuid import uuid4
import hashlib,json
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_liquidation753_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,
 b12_body,b12_url,cm_body,cm_url,css_body,css_url,credits_body,credits_url,ap_body,ap_url,
 body as liq_body,url as liq_url)
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'docs/recette/DONNEES_FISCALES755.json').read_text(encoding='utf-8'))


def bodies(v):
 b=b12_body(v);b['tables'][0]['lignes'][0].update(reintegrations='0',deductions='0',deficit_disponible='0',taux_is='20',regime_avantages='Droit commun déclaré2026, aucun avantage/déficit/retraitement pour le scénario fictif755',reference_source='NOTE755-B12, opérations et balances N/N-1 fournies')
 c=cm_body(v);c['tables'][0]['lignes'][0]['reference_source']='NOTE755-CM, régime normal et absence exonérations justifiés dans le scénario'
 s=css_body(v);s['tables'][0]['lignes'][0].update(benefice_reference='100000',reference_source='NOTE755-CSS, dernier clos2025 bénéfice fiscal100000')
 cr=credits_body(v);cr['tables'][0]['lignes'][0]['reference_source']='NOTE755-CR, liste exhaustive fictive';cr['tables'][1]['lignes']=deepcopy(D['credits'])
 a=ap_body(v);a['tables'][0]['lignes'][0].update(date_controle=D['date_controle'],reference_source='NOTE755-REF et liquidation2025 fictive, excédent100')
 a['tables'][1]['lignes']=[dict(x,nature='Mouvement fictif acompte'+x['numero'],rattachement_confirme='oui') for x in D['acomptes']]
 l=liq_body(v);l['tables'][0]['lignes'][0]['reference_source']='REVUE755, calculs indépendants et justificatifs fictifs fournis'
 return {'b12':b,'cm':c,'css':s,'credits':cr,'acomptes':a,'liquidation':l}


def payload():
 return {'exercice':2026,'fichier_n':'BALANCE_FICTIVE_FISCALE755_N.csv','fichier_n1':'BALANCE_FICTIVE_FISCALE755_N1.csv',
         'lignes_n':deepcopy(D['balance_n']),'lignes_n1':deepcopy(D['balance_n1'])}
def completer(api,v):
 for k,url in [('b12',b12_url),('cm',cm_url),('css',css_url),('credits',credits_url),('acomptes',ap_url),('liquidation',liq_url)]:
  v=ok(api.post(url(v),json=bodies(v)[k]),201)
 return v
def creer(api):return completer(api,ok(api.post(BASE,json=payload()),201))
def verifier(v):
 c=v['contenu'];a=D['attendus'];p=c['preparation']
 assert v['exercice']==2026 and p['pret_a_deposer'] is False
 assert p['balance_n']['nb_comptes']==9 and p['balance_n']['total_debit']==float(a['debit_credit_n'])
 assert p['etats']['cpc']['resultat_net']==96000 and p['etats_n1']['cpc']['resultat_net']==82500
 assert p['etats']['bilan']['actif']['total']['net']==p['etats']['bilan']['passif']['total']==212500
 assert p['etats_n1']['bilan']['actif']['total']['net']==p['etats_n1']['bilan']['passif']['total']==110000
 assert c['passage_fiscal_documentaire']['controle_passage_fiscal']['montants']['is_theorique_taux_declare']==a['is_theorique']
 cm=c['cotisation_minimale_documentaire']['controle_cm']['montants'];assert cm['base_comptable_brute']==a['cm_base'] and cm['cm_calculee']==a['cm_calculee'] and cm['cm_exigible']==a['cm_exigible']
 cr=c['credits_is_documentaires']['controle_credits']['montants'];assert cr['credits_proposes']==a['credits_disponibles'] and cr['deja_impute_acomptes']==a['credits_deja_utilises']
 ap=c['acomptes_is_documentaires']['controle_acomptes'];assert ap['montants']['acomptes_proposes']==a['acomptes_imputables'] and ap['montants']['versements_declares']==a['acomptes_cash']
 assert [x['statut'] for x in ap['echeancier']]==['couvert_declare']*4 and [x['reste'] for x in ap['echeancier']]==['0.00']*4
 l=c['liquidation_is_documentaire']['controle_liquidation'];assert l['proposition_disponible'] and l['montants']['solde_is_propose']==a['solde_is_propose']
 assert l['montants']['css_separee']=='0.00' and l['montants']['excedent_arithmetique']=='0.00' and not l['liquidation_confirmee'] and not l['paiement_confirme'] and not l['pret_a_deposer'] and l['total_global_is_css'] is None
 assert not any(l['sources_conservees'][k] is None for k in ('b12','cm','credits','acomptes','css'))
 return l


def verifier_export(raw,v):
 with ZipFile(BytesIO(raw)) as z:
  assert z.testzip() is None
  m=json.loads(z.read('MANIFESTE_SHA256.json'));assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
  for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
  assert json.loads(z.read('preparation.json'))==v
  assert json.loads(z.read('liquidation_is_documentaire.json'))['controle_liquidation']==verifier(v)
  w=load_workbook(BytesIO(z.read('preparation.xlsx')));vals=dict(list(w['Proposition IS CM'].values)[1:]);assert vals['Solde IS/CM proposé à payer']==3650 and vals['Acomptes justifiés proposés']==20000 and vals['Crédits qualifiés disponibles après utilisations antérieures']==350
  with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(n.startswith('xl/media/') for n in x.namelist())
  p=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(x.extract_text() or '' for x in p.pages);assert '3 650,00' in txt and '192 150,00' in txt and any(x.images for x in p.pages)
  return {'fichiers':len(z.namelist()),'pages_pdf':len(p.pages),'feuilles_excel':w.sheetnames,'solde':'3650.00','logos_pdf_xlsx':True,'sha256_zip':hashlib.sha256(raw).hexdigest()}
