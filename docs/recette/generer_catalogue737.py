from pathlib import Path
import importlib.util,re,json,shutil
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from openpyxl.chart import DoughnutChart,Reference
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'docs/CATALOGUE_ARTICLES_COMMERCIAL_737.md'
STEM=HERE/'MODE_EMPLOI_CATALOGUE_ARTICLES_737'

def generer():
 spec=importlib.util.spec_from_file_location('guide737',ROOT/'docs/guide/generer_guide.py')
 guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
 guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs();orig=guide.word_table
 widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
 guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
 guide.docx(blocs);table=guide.Table
 guide.Table=lambda rows,**kw:table(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
 guide.pdf(blocs)
 cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|CAT737-')]
 assert len(cas)==6 and all(len(c)==4 and c[3]=='Non testé' for c in cas)
 data={'societe_fictive':'Catalogue recette737','devise':'MAD','exercice':2026,
  'tiers':[{'nom':'Client fictif737','type':'client'},{'nom':'Fournisseur fictif737','type':'fournisseur'}],
  'articles':[{'code':code,'designation':nom,'is_stockable':False,'prix_vente_ht':'100','prix_achat_ht':'80','tva_declaree':'20','frais_emballage':'0','frais_transport':'0'} for code,nom in [('ALPHA737','Alpha fictif737'),('BETA737','Beta fictif737')]],
  'recherche_vide':'INEXISTANT737','description_libre':'Prestation libre fictive737',
  'attendus':{'vente_selection_ttc':'120.00','achat_selection_ttc':'96.00','libre_ttc':'120.00','ecritures_creees':0,'mouvements_stock_crees':0},
  'statut_humain':'Non testé','limite':'Taux fictif de test sans qualification fiscale réelle.'}
 assert 100*120/100==120 and 80*120/100==96
 (HERE/'DONNEES_CATALOGUE737.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
 ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
 for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([statut,f'=COUNTIF(Commercial!K2:K7,A{i})'])
 ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
 chart=DoughnutChart();chart.title='Recette utilisateur';chart.add_data(Reference(ws,min_col=2,min_row=1,max_row=5),titles_from_data=True);chart.set_categories(Reference(ws,min_col=1,min_row=2,max_row=5));ws.add_chart(chart,'D2')
 ws=wb.create_sheet('Commercial');ws.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu','Écritures attendues','Impact fiscal attendu','Contrôles','Statut humain','Résultat réel','Anomalies','Preuves réelles','Observations','Justificatif attendu'])
 for ident,action,result,statut in cas:ws.append([ident,'Commercial / articles',action,'Société fictive MAD2026 et deux services décrits dans le guide737 ; bac de panne préparé pour CAT737-04','DONNEES_CATALOGUE737.json et guide737',action,result,'Aucune écriture ou mouvement de stock pour ces seuls devis/BC de service','Aucun impôt ou paiement confirmé',result,statut,'','','','','Captures/détails indiqués dans le résultat attendu'])
 validation=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(validation);validation.add('K2:K7')
 ws=wb.create_sheet('Données');ws.append(['Information','Valeur exacte'])
 for a in data['articles']:
  for k,v in a.items():ws.append([a['code']+' '+k,str(v)])
 for t in data['tiers']:ws.append(['Tiers '+t['type'],t['nom']])
 for k,v in data['attendus'].items():ws.append([k,str(v)])
 ws.append(['Recherche sans résultat',data['recherche_vide']]);ws.append(['Description libre',data['description_libre']])
 ws=wb.create_sheet('Preuves');ws.append(['ID','Preuve réelle','Observations'])
 for c in cas:ws.append([c[0],'',''])
 ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
 for ws in wb:
  ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
  for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
  for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=42
  for row in ws:
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
 for i in range(2,8):wb['Commercial'].row_dimensions[i].height=150
 wb.save(STEM.with_suffix('.xlsx'))
 return {'cas_humains_non_testes':6,'feuilles':wb.sheetnames}

if __name__=='__main__':print(generer())
