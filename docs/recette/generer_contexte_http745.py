from pathlib import Path
import importlib.util,re,json
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import DoughnutChart,Reference
from openpyxl.workbook.properties import CalcProperties
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=ROOT/'docs/SESSIONS_CONTEXTE_HTTP_745.md';STEM=HERE/'MODE_EMPLOI_CONTEXTE_HTTP_745'
def generer():
 spec=importlib.util.spec_from_file_location('guide745',ROOT/'docs/guide/generer_guide.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
 g.SOURCE=SOURCE;g.STEM=STEM;blocs=g.blocs();orig=g.word_table
 widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
 g.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
 g.docx(blocs);t=g.Table;g.Table=lambda rows,**kw:t(rows,**{**kw,'colWidths':[24*g.mm,64*g.mm,63*g.mm,19*g.mm]});g.pdf(blocs)
 cas=[[c.strip() for c in l.strip('|').split('|')] for l in SOURCE.read_text(encoding='utf-8-sig').splitlines() if l.startswith('|SES745-')]
 assert len(cas)==4 and all(len(c)==4 and c[3]=='Non testé' for c in cas)
 data={'societes_fictives':['Session A745','Session B745'],'devise':'MAD','exercice':2026,
  'roles_meme_utilisateur':{'A':'admin','B':'lecture'},'preparation_fictive':'Petit CSV du guide741,dansA',
  'attendus':{'GET_courant':'profil/fichier conservé','ancienne_reponse':'ignorée sans déconnexion nouvelle session','POST_abouti':'une version dansA,aucun rejeu dansB','ecritures_creees':0},
  'statut_humain':'Non testé','limite':'Bac isolé avec responsable pour latence,aucune donnée réelle.'}
 (HERE/'DONNEES_CONTEXTE_HTTP745.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True);ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
 for i,s in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([s,f'=COUNTIF(Administration!K2:K5,A{i})'])
 ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
 c=DoughnutChart();c.title='Recette utilisateur';c.add_data(Reference(ws,min_col=2,min_row=1,max_row=5),titles_from_data=True);c.set_categories(Reference(ws,min_col=1,min_row=2,max_row=5));ws.add_chart(c,'D2')
 ws=wb.create_sheet('Administration');ws.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu','Écritures attendues','Impact fiscal attendu','Contrôles','Statut humain','Résultat réel','Anomalies','Preuves réelles','Observations','Justificatif attendu'])
 for ident,action,result,status in cas:ws.append([ident,'Administration / session',action,'Bac isolé ; compte fictif du guide745 ; responsable technique pour SES739-03/04','DONNEES_SESSIONS739.json et guide745',action,result,'Aucune écriture ni paiement','Aucun',result,status,'','','','','Capture et trace indiquées dans le résultat attendu'])
 d=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(d);d.add('K2:K5')
 ws=wb.create_sheet('Données');ws.append(['Information','Valeur fictive'])
 for k,v in data.items():ws.append([k,str(v)])
 ws=wb.create_sheet('Preuves');ws.append(['ID','Preuve réelle','Observations'])
 for a in cas:ws.append([a[0],'',''])
 ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
 for ws in wb:
  ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
  for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
  for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=42
  for row in ws:
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
 for i in range(2,6):wb['Administration'].row_dimensions[i].height=150
 wb.save(STEM.with_suffix('.xlsx'));return {'cas_non_testes':len(cas),'feuilles':wb.sheetnames}
if __name__=='__main__':print(generer())

