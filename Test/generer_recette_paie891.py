"""Recette des variables,à la suite des cahiers887 et889."""
from pathlib import Path
from html import escape
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,PageBreak,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart,Reference
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];D=R/'docs/personnel-paie'
JEU={'societe':'RECETTE PERSONNEL879 — FICTIF','salarie':'P001 — Salma FICTIVE','base_contractuelle_novembre':'9000.10','rubrique':'PRIME_FICTIVE889','periode':'2026-11','date_effet':'2026-11-15','montant':'800.01','source_reference':'VAR-P001-NOV2026-01','motif':'Variable fictive de recette891','justificatif_ATTESTATION_FICTIVE':'ATTEST-P001-NOV2026','justificatif_MISSION_FICTIVE':'MISSION-P001-NOV2026',
 'deuxieme_rubrique_code':'QUANT_FICTIVE891','deuxieme_rubrique_libelle':'Quantité FICTIVE891','deuxieme_rubrique_nature':'GAIN','deuxieme_rubrique_periodicite':'ponctuelle','deuxieme_rubrique_formule':'QUANTITE_TAUX','deuxieme_rubrique_debut':'2026-01-01','deuxieme_rubrique_regles':'IR,CNSS,AMO :traitement etstatut A_VERIFIER,conditions Hypothèse FICTIVE891 ;aucune valeur réglementaire,aucun plafond ;justificatif ATTESTATION_FICTIVE seulement,aucune incompatibilité,aucun compte de charge.',
 'deuxieme_variable_quantite':'3','deuxieme_variable_taux':'0.335','deuxieme_variable_source':'VAR-P001-NOV2026-02','deuxieme_variable_justificatif':'ATTEST-QUANT-P001-NOV2026','deuxieme_variable_motif':'Quantité fictive de recette891','montant_independant_produit_arrondi':'1.01','somme_deux_gains':'801.02','base_plus_deux_gains_illustratif':'9801.12','attention':'Ces sommes ne sont ni un net à payer ni un bulletin ;données entièrement fictives.'}
CAS=json.loads((D/'CAS_VARIABLES_PAIE_891.json').read_text(encoding='utf8'))

def generer():
    (D/'JEU_VARIABLES_PAIE_891.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial891','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial891'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Variables mensuelles de paie 891','Heading1'),p('Complément de 10 cas, à la suite des cahiers 887 et 889. Tous les statuts humains sont Non testé. Installation et procédures réelles sur copie seulement ; aucun PostgreSQL utilisateur utilisé par les autotests. Les variables et leurs approbations ne constituent pas une paie définitive.'),p('Données exactes','Heading1')]
    for k,v in JEU.items():story.append(p(k+' : '+v))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('Variables');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer les pièces et soldes avant/après.';fi='Aucune liquidation IR/sociale ; statuts réglementaires antérieurs inchangés.';co='Société, droits, acteurs, date, période, exactitude monétaire, sources, historique.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Capture des champs, du résultat/refus, identifiant de variable et acteur.'),('Statut','Non testé ; résultat réel, anomalies et observations à renseigner dans Excel.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([str(t) for t in [ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Capture/ID à conserver']])
    pdf=D/'RECETTE_VARIABLES_PAIE_891.pdf';SimpleDocTemplate(str(pdf),leftMargin=1.7*cm,rightMargin=1.7*cm,title='HisabPro variables891').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    for i in range(2,12):w.row_dimensions[i].height=150
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J11')
    for row in [['HISABPRO —VARIABLES891'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(Variables!J2:J11,"{statut}")'])
    s.append(['Cas',10]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=48;s.column_dimensions['B'].width=22
    ch=BarChart();ch.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(ch,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    for k,v in JEU.items():d.append([k,v])
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for i in range(2,d.max_row+1):d.row_dimensions[i].height=48
    x=D/'SUIVI_VARIABLES_PAIE_891.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['Variables'].cell(i,10).value=='Non testé' for i in range(2,12))
    from decimal import Decimal
    assert Decimal(JEU['base_contractuelle_novembre'])+Decimal(JEU['montant'])+Decimal(JEU['montant_independant_produit_arrondi'])==Decimal(JEU['base_plus_deux_gains_illustratif'])
    print(json.dumps({'cas':10,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))

if __name__=='__main__':generer()
