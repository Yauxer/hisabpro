from pathlib import Path
import importlib.util,re,json,shutil
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from openpyxl.chart import DoughnutChart,Reference
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'docs/LIASSE_BALANCES_CSS_743.md'
STEM=HERE/'MODE_EMPLOI_CSS_743'

def generer():
 spec=importlib.util.spec_from_file_location('guide743',ROOT/'docs/guide/generer_guide.py')
 guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
 guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs();orig=guide.word_table
 widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
 guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
 guide.docx(blocs);table=guide.Table
 guide.Table=lambda rows,**kw:table(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
 guide.pdf(blocs)
 cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|CSS743-')]
 assert len(cas)==8 and all(len(c)==4 and c[3]=='Non testé' for c in cas)
 from decimal import Decimal as D,ROUND_HALF_UP
 data={'societe_fictive':'CM recette741','devise':'MAD','annee_css':2026,
  'reference_fiscale':{'exercice':2025,'resultat_avant_is':'2000000','reintegrations':'0','deductions':'0','deficit_impute':'0','benefice_net_fiscal':'2000000','source':'NOTE-CSS2025-743'},
  'qualification':{'regime':'Société relevant de l’IS','dernier_clos_confirme':'oui','exoneration_permanente':'non'},
  'attendus':{'css':'30000.00','taux_proportionnel':'1.500','css_declaree_contexte':'0.00','ecart':'30000.00','date_echeance':None,'solde_is':None},
  'seuils':[{'base':b,'taux':t,'css':c} for b,t,c in [('999999.99','0','0.00'),('1000000','1.5','15000.00'),('2000000','1.5','30000.00'),('5000000','2.5','125000.00'),('10000000','3.5','350000.00'),('40000000','5','2000000.00')]],
  'statut_humain':'Non testé','limite':'Données exclusivement fictives,aucune qualification réelle/liquidation/paiement confirmé.'}
 assert D('2000000')+D('0')-D('0')-D('0')==D(data['reference_fiscale']['benefice_net_fiscal'])
 for r in data['seuils']:assert (D(r['base'])*D(r['taux'])/100).quantize(D('.01'),rounding=ROUND_HALF_UP)==D(r['css'])
 (HERE/'DONNEES_CSS743.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
 ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
 for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([statut,f'=COUNTIF(Fiscalité!K2:K9,A{i})'])
 ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
 chart=DoughnutChart();chart.title='Recette utilisateur';chart.add_data(Reference(ws,min_col=2,min_row=1,max_row=5),titles_from_data=True);chart.set_categories(Reference(ws,min_col=1,min_row=2,max_row=5));ws.add_chart(chart,'D2')
 ws=wb.create_sheet('Fiscalité');ws.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu','Écritures attendues','Impact fiscal attendu','Contrôles','Statut humain','Résultat réel','Anomalies','Preuves réelles','Observations','Justificatif attendu'])
 for ident,action,result,statut in cas:ws.append([ident,'Liasse seule / CSS',action,'Société fictive MAD2026 et deux services décrits dans le guide743 ; bac de panne préparé pour CAT737-04','DONNEES_CATALOGUE737.json et guide743',action,result,'Aucune écriture ou paiement créé par cette préparation','CSS conditionnelle etécart selon le cas,aucun paiement confirmé',result,statut,'','','','','Captures/détails indiqués dans le résultat attendu'])
 validation=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(validation);validation.add('K2:K9')
 ws=wb.create_sheet('Données');ws.append(['Information','Valeur exacte'])
 for k,v in data['reference_fiscale'].items():ws.append(['Référence '+k,str(v)])
 for k,v in data['qualification'].items():ws.append(['Qualification '+k,v])
 for k,v in data['attendus'].items():ws.append(['Attendu '+k,'Indisponible' if v is None else v])
 for r in data['seuils']:ws.append(['Base'+r['base']+' / Taux'+r['taux']+'%','CSS'+r['css']+'MAD'])
 ws=wb.create_sheet('Preuves');ws.append(['ID','Preuve réelle','Observations'])
 for c in cas:ws.append([c[0],'',''])
 ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
 for ws in wb:
  ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
  for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
  for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=42
  for row in ws:
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
 for i in range(2,10):wb['Fiscalité'].row_dimensions[i].height=150
 wb.save(STEM.with_suffix('.xlsx'))
 return {'cas_humains_non_testes':8,'feuilles':wb.sheetnames}

if __name__=='__main__':print(generer())
