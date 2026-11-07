"""PDF et Excel humains depuis le jeu explicite ;aucun statut automatisé."""
from pathlib import Path
from html import escape
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];D=R/'docs/recette'
def generer():
 jeu=json.loads((D/'JEU_LECTURE_IMMOBILISATIONS_931.json').read_text(encoding='utf8'));cas=jeu['cas'];assert len(cas)==4 and all(c['statut']=='Non testé' for c in cas)
 st=getSampleStyleSheet();font=Path('C:/Windows/Fonts/arial.ttf')
 if font.exists():
  pdfmetrics.registerFont(TTFont('Arial931',str(font)))
  for s in st.byName.values():s.fontName='Arial931'
 st['BodyText'].fontSize=9;st['BodyText'].leading=13;p=lambda t,s='BodyText':Paragraph(escape(str(t)),st[s])
 story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Lecture et reprise des immobilisations931','Heading1'),p('Quatre cas humains Non testé ;recette utilisateur et production distinctes des tests automatiques.')]
 for k,v in jeu.items():
  if k!='cas':story.append(KeepTogether([p(k,'Heading2'),p(v),Spacer(1,8)]))
 story.append(PageBreak());w=Workbook();sy=w.active;sy.title='Synthese';s=w.create_sheet('Lecture immobilisations')
 cles=['id','module','objectif','prerequis','donnees_exactes','actions','attendu','ecritures','fiscalite','statut','resultat_reel','anomalies','observations','preuve']
 s.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures attendues','Fiscalité','Statut','Résultat réel','Anomalies','Observations','Preuves/captures'])
 for c in cas:
  bloc=[p(c['id']+' — '+c['objectif'],'Heading2')]
  for k in ['module','prerequis','donnees_exactes','actions','attendu','ecritures','fiscalite','statut','preuve']:bloc.append(p(k+' : '+c[k]))
  story.append(KeepTogether(bloc+[Spacer(1,12)]));s.append([c.get(k,'') for k in cles])
 pdf=D/'RECETTE_LECTURE_IMMOBILISATIONS_931.pdf';SimpleDocTemplate(str(pdf),title='HisabPro — lecture des immobilisations931').build(story)
 for row in [['HISABPRO — LECTURE IMMOBILISATIONS931'],['Production','Non validée'],['Statut','Nombre']]:sy.append(row)
 for statut in ['Non testé','Réussi','Échoué','Bloqué']:sy.append([statut,f'=COUNTIF(\'Lecture immobilisations\'!J2:J5,"{statut}")'])
 sy.append(['Cas',4]);sy.append(['Progression','=IFERROR(B5/B8,0)']);sy['B9'].number_format='0%'
 d=w.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
 for k,v in jeu.items():
  if k!='cas':d.append([k,v])
 for sh in w:
  sh.freeze_panes='B2';sh.auto_filter.ref=sh.dimensions
  for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=43
  for row in sh:
   sh.row_dimensions[row[0].row].height=280 if sh==s and row[0].row>1 else 90
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
  for c in sh[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='24589C')
 d.column_dimensions['B'].width=100;dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');s.add_data_validation(dv);dv.add('J2:J4')
 x=D/'SUIVI_LECTURE_IMMOBILISATIONS_931.xlsx';dv.add('J5');w.save(x)
 texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c['id'] in texte for c in cas) and '\u25a0' not in texte
 wb=load_workbook(x);assert all(wb['Lecture immobilisations'].cell(i,10).value=='Non testé' for i in range(2,6));wb.close()
 print(json.dumps({'cas_humains':4,'statut':'Tous Non testé','pages':len(PdfReader(pdf).pages),'feuilles':w.sheetnames},ensure_ascii=False))

if __name__=='__main__':generer()
