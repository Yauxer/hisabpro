from pathlib import Path
import importlib.util,re,json,shutil
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from openpyxl.chart import DoughnutChart,Reference
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'docs/LIASSE_BALANCES_LIQUIDATION_753.md'
STEM=HERE/'MODE_EMPLOI_LIQUIDATION_753'

def generer():
 spec=importlib.util.spec_from_file_location('guide753',ROOT/'docs/guide/generer_guide.py')
 guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
 guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs();orig=guide.word_table
 widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
 guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
 guide.docx(blocs);table=guide.Table
 guide.Table=lambda rows,**kw:table(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
 guide.pdf(blocs)
 cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|LIQ753-')]
 assert len(cas)==8 and all(len(c)==4 and c[3]=='Non testé' for c in cas)
 from decimal import Decimal as D,ROUND_HALF_UP
 data={'societe_fictive':'Proposition recette753','devise':'MAD','exercice':2026,
  'profil':{'b12_verifie':'oui','cm_verifiee':'oui','exhaustivite_verifiee':'oui','excedent_verifie':'oui','ordre_examine':'oui','excedent_annuel':'0'},
  'sources':{'resultat_net':'6400','is_comptabilise':'1600','ri':'500','deductions':'200','deficit':'1000','taux_is':'20','benefice':'7300','is_theorique':'1460','cm':'3000','credits_total':'500','deja_utilises':'150','autres_utilisations':'25','credits_disponibles':'325','cash':'1000','excedent_anterieur_impute':'100','acomptes':'1250'},
  'attendus':{'maximum_is_cm':'3000.00','credits_appliques':'325.00','acomptes_appliques':'1250.00','solde_is_propose':'1425.00','excedent_arithmetique':'0.00','sans_css':None,'css_qualifiee100000':'0.00','total_global_is_css':None},
  'statut_humain':'Non testé','limite':'Simulation fictive, aucune éligibilité réelle, imputation ou liquidation confirmée.'}
 assert D('6400')+D('1600')+D('500')-D('200')-D('1000')==D('7300')
 assert D('7300')*D('20')/100==D('1460')
 assert D('500')-D('150')-D('25')==D('325') and D('1000')+D('100')+D('150')==D('1250')
 assert max(D('1460'),D('3000'))-D('325')-D('1250')==D(data['attendus']['solde_is_propose'])
 (HERE/'DONNEES_LIQUIDATION753.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
 ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
 for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([statut,f'=COUNTIF(Fiscalité!K2:K9,A{i})'])
 ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
 chart=DoughnutChart();chart.title='Recette utilisateur';chart.add_data(Reference(ws,min_col=2,min_row=1,max_row=5),titles_from_data=True);chart.set_categories(Reference(ws,min_col=1,min_row=2,max_row=5));ws.add_chart(chart,'D2')
 ws=wb.create_sheet('Fiscalité');ws.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu','Écritures attendues','Impact fiscal attendu','Contrôles','Statut humain','Résultat réel','Anomalies','Preuves réelles','Observations','Justificatif attendu'])
 for ident,action,result,statut in cas:ws.append([ident,'Liasse seule / Proposition IS/CM',action,'Société fictive MAD2026 et préparation01/01–31/12 ; services frontend/backend de test démarrés','DONNEES_LIQUIDATION753.json et REVUE_FICTIVE_LIQ753.md',action,result,'Aucune écriture,retenue ou paiement créé par cette préparation','Solde IS/CM simulé ; CSS séparée, aucune liquidation confirmée',result,statut,'','','','','Captures/versions/exports indiqués dans le résultat attendu'])
 validation=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(validation);validation.add('K2:K9')
 ws=wb.create_sheet('Données');ws.append(['Information','Valeur exacte'])
 for k,v in data['profil'].items():ws.append(['Profil '+k,str(v)])
 for k,v in data['sources'].items():ws.append(['Source '+k,str(v)])
 for k,v in data['attendus'].items():ws.append(['Attendu '+k,'Indisponible' if v is None else v])
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
