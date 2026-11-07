"""Contrôles des états et du FEC sur le scénario annuel clôturé du cahier."""
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
import csv,io,hashlib,re
from openpyxl import load_workbook
from pypdf import PdfReader
from playwright.sync_api import expect
from cahier_formulaires773_support import ok
from cahier_suite777_support import core

ENTETES=['Code_Journal','Libelle_Journal','Num_Ecriture','Date_Ecriture','Num_Compte','Libelle_Compte','Num_Compte_Aux','Libelle_Compte_Aux','Ref_Piece','Date_Piece','Libelle_Ecriture','Montant_Debit','Montant_Credit','Lettrage_Ecriture','Date_Lettrage','Date_Validation','Montant_Devise','Id_devise']

def nombre(v):
 t=str(v).strip().replace('\u00a0','').replace('\u202f','').replace(' ','')
 if ',' in t:t=t.replace('.','').replace(',','.')
 if t.startswith('(') and t.endswith(')'):t='-'+t[1:-1]
 return D(t or '0')

def valeurs_pdf(texte):
 valeurs=re.findall(r'(?<![\d.,])(?:\d{1,3}(?:[ \u00a0\u202f.]\d{3})+|\d+)[.,]\d{2}(?!\d)',texte)
 return {nombre(v) for v in valeurs}

def enregistrer(preuve,path,nom):
 preuve.setdefault('fichiers803',[]).append({'nom':nom,'chemin':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

def telecharger(page,bouton,tmp_path,nom):
 with page.expect_download() as r:page.get_by_role('button',name=bouton,exact=True).click()
 p=tmp_path/nom;r.value.save_as(p);assert p.stat().st_size>100;return p

def verifier_etats(api,page,app,sid,preuve,tmp_path):
 avant=core(app,sid);fige=ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot'];data=ok(api.get('/api/etats/liasse/2025'));e=data['etats'];b=e['bilan'];esg={r['code']:r for r in e['esg']['lignes']};cpc=e['cpc'];preuve['etats803']={'bilan':b,'cpc':cpc,'esg':e['esg'],'financement':e['tableau_financement'],'controles_liasse':data['controles']}
 assert D(str(b['actif']['total']['net']))==D('337010')==D(str(b['passif']['total'])) and b['equilibre']
 imm=next(l for l in b['actif']['immobilise'] if l['code']=='23');assert [D(str(imm[k])) for k in ['brut','amort_prov','net']]==[D('24000'),D('4800'),D('19200')]
 cl=next(l for l in b['actif']['circulant'] if l['code']=='342');assert [D(str(cl[k])) for k in ['brut','amort_prov','net']]==[D('14400'),D('2000'),D('12400')]
 st=next(l for l in b['actif']['circulant'] if l['code']=='31');assert D(str(st['brut']))==D('6600')
 avant_is=next(r['montant'] for r in cpc['lignes'] if r['code']=='XI')
 assert D(str(cpc['resultat_net']))==D('106409.75') and D(str(avant_is))==D('129830')
 attendus={'I':'22100','II':'132000','IV':'137630','V':'137630','VI':'129330','VII':'1000','IX':'-500','X':'106409.75','CAF':'112709.75'}
 for code,val in attendus.items():assert D(str(esg[code]['montant']))==D(val),(code,esg[code])
 page.goto(app['web_url']+'/liasse-fiscale');expect(page.get_by_text('T1 à T25 : numérotation interne HisabPro',exact=False)).to_be_visible();page.get_by_role('button',name='T1 · Bilan',exact=True).click()
 ligne=page.get_by_role('row').filter(has=page.get_by_role('cell',name=re.compile('^Immobilisations corporelles$',re.I)));expect(ligne).to_have_count(1);cellules=ligne.locator('td').all_text_contents();assert [nombre(v) for v in cellules[2:5]]==[D('24000'),D('4800'),D('19200')],cellules
 for label,vals in [('Stocks',['6600','0','6600']),('Clients et comptes rattachés',['14400','2000','12400'])]:
  ligne=page.get_by_role('row').filter(has=page.get_by_role('cell',name=label,exact=True));expect(ligne).to_have_count(1);assert [nombre(v) for v in ligne.locator('td').all_text_contents()[2:5]]==list(map(D,vals))
 page.get_by_role('button',name='T2 · CPC',exact=True).click();ligne=page.get_by_role('row').filter(has=page.get_by_role('cell',name='XI',exact=True));expect(ligne).to_have_count(1);assert nombre(ligne.locator('td').nth(2).inner_text())==D('129830')
 page.get_by_role('button',name='ESG',exact=True).click()
 for code,val in attendus.items():
  ligne=page.get_by_role('row').filter(has=page.get_by_role('cell',name=code,exact=True));expect(ligne).to_have_count(1);assert nombre(ligne.locator('td').nth(2).inner_text())==D(val)
 excel=telecharger(page,'Excel',tmp_path,'liasse803.xlsx');wb=load_workbook(excel,data_only=True);assert {'T1 Bilan Actif','T1 Bilan Passif','T2 CPC','ESG','Financement'} <= set(wb.sheetnames)
 er={r[0]:r for r in wb['ESG'].values if r[0] in attendus}
 for code,val in attendus.items():assert D(str(er[code][2]))==D(val)
 assert any(r[0]=='XV' and D(str(r[2]))==D('106409.75') for r in wb['T2 CPC'].values)
 pdf=telecharger(page,'PDF',tmp_path,'liasse803.pdf');texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert set(map(D,['337010','106409.75','112709.75','24000','4800']))<=valeurs_pdf(texte);enregistrer(preuve,excel,'Liasse Excel');enregistrer(preuve,pdf,'Liasse PDF');preuve['cas'].append({'id':'HP-ETA-001','statut':'Réussi'})
 assert e['tableau_financement']['applicable'] is False and 2024 not in {x['annee'] for x in ok(api.get('/api/exercices'))};page.get_by_role('button',name='Financement',exact=True).click();expect(page.get_by_text(e['tableau_financement']['motif_non_applicable'],exact=False)).to_be_visible();assert any(r[0]=='Non applicable' for r in wb['Financement'].values);preuve['cas'].append({'id':'HP-ETA-002','statut':'Réussi'})
 livre=ok(api.get('/api/inventaire/livre',params={'exercice':2025}));snap=livre['snapshot'];preuve['livre803']=snap
 for k in ['exercice_cloture','aucun_brouillon','balance_equilibree','bilan_equilibre','inventaire_stock_valide','stock_rapproche','immobilisations_rapprochees']:assert snap['controles'][k],(k,snap['controles'])
 assert D(str(snap['bilan']['total_actif']))==D('337010')==D(str(snap['bilan']['total_passif'])) and D(str(snap['cpc']['resultat_net']))==D('106409.75')
 assert [D(str(snap['immobilisations'][k])) for k in ['valeur_brute','amortissements_cumules','vnc']]==[D('24000'),D('4800'),D('19200')]
 assert D(str(snap['stocks']['valeur_physique']))==D('6600') and D(str(snap['stocks']['ecart_physique_comptable']))==0
 assert sum(D(str(a['montant'])) for a in snap['ajustements_inventaire'] if a['type'] in ['provision_risque','depreciation_client'])==D('3500')
 page.goto(app['web_url']+'/livre-inventaire');expect(page.get_by_role('button',name='Stocks',exact=True)).to_be_visible()
 for tab in ['Stocks','Immobilisations','Ajustements','Balance de clôture','Bilan & CPC']:page.get_by_role('button',name=tab,exact=True).click()
 pdf=telecharger(page,'Exporter PDF',tmp_path,'livre803.pdf');texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert set(map(D,['337010','106409.75','6600','24000','4800']))<=valeurs_pdf(texte);enregistrer(preuve,pdf,'Livre inventaire PDF');controle=ok(api.get('/api/cloture/etat',params={'exercice':2025}));preuve['controle_cloture803']=controle;preuve['cas'].append({'id':'HP-CLO-005','statut':'Réussi'})
 fec=ok(api.get('/api/fec/apercu',params={'exercice':2025}));preuve['fec803']={'controle':fec};assert fec['conforme_export'] and not fec['bloquants']
 reparations=[]
 def observer_reparation(r):
  if r.method=='POST' and '/api/fec/reparer' in r.url:reparations.append(r.url)
 page.on('request',observer_reparation);page.goto(app['web_url']+'/journal');expect(page.get_by_text('CAP-01',exact=True)).to_be_visible();fichier=telecharger(page,'Export FEC',tmp_path,'fec803.txt');page.remove_listener('request',observer_reparation);assert not reparations
 brut=fichier.read_text(encoding='utf-8-sig');reader=csv.DictReader(io.StringIO(brut),delimiter='\t');assert reader.fieldnames==ENTETES,reader.fieldnames;rows=list(reader);es=[x for x in avant if str(x[1]).startswith('2025')];assert len(rows)==145==sum(len(e[-1]) for e in es)
 attendu=Counter((str(e[3].value if hasattr(e[3],'value') else e[3]),e[6],str(e[1]).replace('-',''),l[1],D(str(l[2])),D(str(l[3]))) for e in es for l in e[-1]);reel=Counter((r['Code_Journal'],r['Num_Ecriture'],r['Date_Ecriture'],r['Num_Compte'],nombre(r['Montant_Debit']),nombre(r['Montant_Credit'])) for r in rows);assert reel==attendu
 assert sum(nombre(r['Montant_Debit']) for r in rows)==D('1646060')==sum(nombre(r['Montant_Credit']) for r in rows);assert {'02','002'} <= {r['Ref_Piece'] for r in rows}
 assert all(r['Num_Compte_Aux'] and r['Libelle_Compte_Aux'] for r in rows if r['Num_Compte'] in ['3421','4411']);dates=[r['Date_Ecriture'] for r in rows];assert dates==sorted(dates)
 for ref in ['02','002']:
  groupe=[r for r in rows if r['Ref_Piece']==ref];assert len(groupe)==3 and sum(nombre(r['Montant_Debit']) for r in groupe)==D('240')==sum(nombre(r['Montant_Credit']) for r in groupe)
 preuve['fec803'].update(lignes=len(rows),colonnes=len(ENTETES),total_debit='1646060.00',total_credit='1646060.00',references_litterales=['02','002'],reparations_automatiques=0,precisions='Le cahier cite16colonnes principales ;le format existant en ajoute2 de devise,soit18. Test technique du format actuel,pas validation réglementaire ni dépôt.');enregistrer(preuve,fichier,'FEC texte');preuve['cas'].append({'id':'HP-LIA-003','statut':'Réussi'})
 assert core(app,sid)==avant and ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']==fige;preuve['etats803']['ecritures_et_snapshot_inchanges']=True
