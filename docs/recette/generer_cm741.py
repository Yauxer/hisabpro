from pathlib import Path
import importlib.util,re,json,shutil
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from openpyxl.chart import DoughnutChart,Reference
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'docs/LIASSE_BALANCES_CM_741.md'
STEM=HERE/'MODE_EMPLOI_CM_741'

def generer():
 spec=importlib.util.spec_from_file_location('guide741',ROOT/'docs/guide/generer_guide.py')
 guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
 guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs();orig=guide.word_table
 widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
 guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
 guide.docx(blocs);table=guide.Table
 guide.Table=lambda rows,**kw:table(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
 guide.pdf(blocs)
 cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|CM741-')]
 assert len(cas)==8 and all(len(c)==4 and c[3]=='Non testé' for c in cas)
 from decimal import Decimal as D
 import csv,io
 data={'societe_fictive':'CM recette741','devise':'MAD','exercice':2026,
  'petit':{'balance':[{'compte':'1111','debit':'0','credit':'10000'},{'compte':'5141','debit':'16400','credit':'0'},
    {'compte':'7111','debit':'0','credit':'10000'},{'compte':'6132','debit':'3000','credit':'0'},
    {'compte':'7581','debit':'0','credit':'1000'},{'compte':'6701','debit':'1600','credit':'0'}],
    'b12':{'reintegrations':'500','deductions':'200','deficit':'1000','taux_declare':'20'},
    'cm':{'base':'10000','exclue':'0','reduite':'0','exoneration_totale':'non','minimum_exonere':'non'},
    'attendus':{'equilibre':'21000.00','net':'6400.00','avant_impots':'8000.00','benefice':'7300.00','is_theorique':'1460.00','proportionnelle':'25.00','cm':'3000.00','maximum':'3000.00'}},
  'grand':{'base':'2000000','exclue':'200000','reduite':'500000','exoneration_totale':'non','minimum_exonere':'non',
    'attendus':{'equilibre':'2011000.00','base_standard':'1300000.00','cm_standard':'3250.00','cm_reduite':'750.00','cm':'4000.00','is_theorique':None,'maximum':None}},
  'statut_humain':'Non testé','limite':'Qualifications et exonérations exclusivement fictives,aucune liquidation confirmée.'}
 petit=data['petit'];rows=petit['balance'];grand=[dict(r) for r in rows]
 for r in grand:
  if r['compte']=='5141':r['debit']='2006400'
  elif r['compte']=='7111':r['credit']='2000000'
 data['grand']['balance']=grand
 for lignes,nom,attendu in [(rows,'BALANCE_FICTIVE_CM741_N.csv','21000'),(grand,'BALANCE_FICTIVE_CM741_GRANDE_N.csv','2011000')]:
  assert sum(D(r['debit']) for r in lignes)==sum(D(r['credit']) for r in lignes)==D(attendu)
  txt=io.StringIO(newline='');w=csv.DictWriter(txt,fieldnames=['compte','debit','credit'],delimiter=';',lineterminator='\n');w.writeheader();w.writerows(lignes)
  (HERE/nom).write_text(txt.getvalue(),encoding='utf8')
 assert (D('8000')+D('500')-D('200')-D('1000'))*D('.20')==D('1460')
 assert D('10000')*D('.0025')==D('25')
 assert (D('2000000')-D('200000')-D('500000'))*D('.0025')+D('500000')*D('.0015')==D('4000')
 (HERE/'DONNEES_CM741.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
 ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
 for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([statut,f'=COUNTIF(Fiscalité!K2:K9,A{i})'])
 ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
 chart=DoughnutChart();chart.title='Recette utilisateur';chart.add_data(Reference(ws,min_col=2,min_row=1,max_row=5),titles_from_data=True);chart.set_categories(Reference(ws,min_col=1,min_row=2,max_row=5));ws.add_chart(chart,'D2')
 ws=wb.create_sheet('Fiscalité');ws.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu','Écritures attendues','Impact fiscal attendu','Contrôles','Statut humain','Résultat réel','Anomalies','Preuves réelles','Observations','Justificatif attendu'])
 for ident,action,result,statut in cas:ws.append([ident,'Liasse seule / CM',action,'Société fictive MAD2026 et deux services décrits dans le guide741 ; bac de panne préparé pour CAT737-04','DONNEES_CATALOGUE737.json et guide741',action,result,'Aucune écriture ou paiement créé par cette préparation','CM/max conditionnels conservés selon le cas,aucune liquidation confirmée',result,statut,'','','','','Captures/détails indiqués dans le résultat attendu'])
 validation=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(validation);validation.add('K2:K9')
 ws=wb.create_sheet('Données');ws.append(['Information','Valeur exacte'])
 for nom in ('petit','grand'):
  for k,v in data[nom]['attendus'].items():ws.append([nom+' '+k,'Indisponible' if v is None else v])
  for r in data[nom]['balance']:ws.append([nom+' compte'+r['compte'],'Débit'+r['debit']+' / Crédit'+r['credit']])
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
