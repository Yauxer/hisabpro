"""Recette du référentiel social ; aucune hypothèse fictive n'est un taux légal."""
from pathlib import Path
from html import escape
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart,Reference
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];D=R/'docs/personnel-paie'
from generer_recette_paie915 import JEU as JEU915
JEU={**JEU915,'menu':'05 · Fiscalité salariale → Contrôle annuel IR → Consulter le contrôle',
 'installation':'Code917 après915, migration122 déjà installée sur copie ; aucune nouvelle migration. Habilitations identité et rémunération requises.',
 'logo':'Paramètres société : importer un PNG puis un JPEG via le formulaire existant. Tester aussi une société de recette neuve sans logo. Ne pas déduire une suppression du simple envoi de null à l’API.',
 'source':'Reprendre le contrôle915 sur RNI83881.0200 et base83890.00 ;2 personnes éligibles du jeu, IR5967.0000. Noter son ID et ses empreintes.',
 'format':'PDF et Excel ; aucun montant à ressaisir. Les cellules du classeur sont textuelles pour conserver les décimales exactes, sans formules automatiques.',
 'attendus':'RNI83881.0200 ; base83890.00 ; IR7167.0000 avant réduction,1200.0000 déduits, IR5967.0000. Douze lignes de sources, mêmes IDs/empreintes, logo actuel et mention de contrôle annuel interne.'}
CAS=[
 ('PA-DOC01','Télécharger le PDF avec logo','Copie isolée et contrôle915 complet ; société avec logoPNG.',
  'Aucun champ supplémentaire ; ouvrir le contrôle au RNI83881.0200.',
  'Ouvrir Consulter le contrôle puis Télécharger le contrôle IR en PDF. Lire toutes les pages et les douze sources. Consulter l’historique Personnel avec un compte habilité à l’audit.',
  'PDF privé lisible avec logo, RNI exact, base83890.00 et IR5967.0000. IDs/empreintes conservés. Événement CONTROLE_IR_EXPORTE associé au dossier, sans recopier les montants dans son motif.'),
 ('PA-DOC02','Comparer le classeur aux résultats et au PDF','PA-DOC01 ; même contrôle.',
  'Aucune nouvelle donnée ; télécharger le formatExcel.',
  'Ouvrir Identite, IR annuel, Frais annuels, Tranches, Sources mensuelles, Regles et anomalies et Logo société. Comparer chaque montant et les douze périodes. Vérifier les références commençant par= dans un jeu distinct.',
  'Les valeurs exactes sont du texte, sans conversion flottante, formule ou lien externe actif ajouté par HisabPro. Douze sources, mêmes empreintes et un logo. Aucune mensualisation ou donnée CNSS/bancaire personnelle exportée.'),
 ('PA-DOC03','Tester JPEG et absence de logo','Société du jeu avec JPEG ; seconde société fictive neuve sans logo et avec son propre contrôle.',
  'Importer un JPEG dans Paramètres société ; aucune URL externe. Dans la seconde société, ne pas importer de logo.',
  'TéléchargerPDF etExcel dans chaque société. Comparer l’identité et les images.',
  'JPEG présent dans les deux formats. Sans logo, documents utilisables, aucune image d’une autre société. Identité et logo sont ceux de la société actuelle, explicitement distingués du salarié conservé dans le snapshot.'),
 ('PA-DOC04','Relire un ancien contrôle sans recalcul','Contrôle915 complet conservé ; ajout de variable fictive réalisé ensuite sur la copie.',
  'Ajouter et faire approuver100.00 sur novembre, référence APRES-SNAPSHOT-FICTIF917.',
  'Tenter un nouveau contrôleIR sur l’ancienne source, puis rouvrir et exporter le contrôle précédemment conservé.',
  'Nouvelle création refusée car source périmée. Ancien document toujours consultable, mêmes RNI/IR/empreintes ; portée historique explicite. Aucun recalcul ni écriture comptable.'),
 ('PA-DOC05','Conserver les inconnues dans les documents','Source annuelle complète ; nouveau contrôleIR avec famille inconnue.',
  'Personnes à charge Inconnu ; référence famille vide. Confirmer uniquement source, cadre et périmètre arithmétique.',
  'Conserver ce contrôle puis téléchargerPDF etExcel. Lire les valeurs de famille, IR final, retenue mensuelle et net.',
  'Famille et IR final À compléter, IR avant réduction7167.0000. Pas de zéro implicite ; retenue et net Non calculés, versement Non déterminé.'),
 ('PA-DOC06','Protéger les téléchargements et vérifier la restauration','Deux sociétés fictives et comptePersonnel seul ; administrateur habilité ; sauvegarde de copie restaurable.',
  'Identifiant du contrôle de la sociétéA ; utilisateurB ; retrait de lire_remuneration à l’utilisateurA.',
  'Essayer l’export depuisB, révoquer le droit deA et Actualiser. Vérifier390px et1440px. Faire restaurer la copie dans une seconde cible et comparer documents, logo, empreintes et événements.',
  'Accès étranger refusé, révocation effective et boutons retirés aprèsActualiser. Pas de montant stocké dans le navigateur. Après restauration, mêmes sections et montants, logo et événements. La sauvegarde d’exploitation reste à valider séparément.')]

def generer():
    D.mkdir(exist_ok=True)
    (D/'JEU_DOC_IR_PAIE_917.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_DOC_IR_PAIE_917.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial917','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial917'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Documents du contrôle IR annuel917','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. PDF et Excel du contrôle conservé, logo et provenance ; sans retenue mensuelle, versement ou paie définitive.'),p('Données exactes à saisir','Heading1')]
    for k,v in JEU.items():
        if k=='periodes_exactes':
            story.append(p('Douze périodes et références exactes','Heading2'))
            for m in v:story.append(p(m['periode']+' — Date variable '+m['date_effet_variable']+' — Référence '+m['reference_variable']))
        else:story.append(p(k+' : '+str(v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('IRAnnuel');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer le journal avant/après.';fi='Contrôle arithmétique annuel uniquement ; montant à déclarer, retenue mensuelle et net non déterminés.';co='Société, droits, année, RNI source et base arrondie, éligibilité, exactitude par tranche, inconnues et intégrité des snapshots.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Captures fiche/version/décision ou refus ; ID branche et version, société et acteurs.'),('Statut','Non testé ; renseigner le classeur et conserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures/ID/version à conserver'])
    pdf=D/'RECETTE_DOC_IR_PAIE_917.pdf';SimpleDocTemplate(str(pdf),title='HisabPro IR annuel sourcé917').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — IR ANNUEL917'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(IRAnnuel!J2:J7,"{statut}")'])
    s.append(['Cas',6]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=48;s.column_dimensions['B'].width=22
    ch=BarChart();ch.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(ch,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    for k,v in JEU.items():d.append([k,'Voir feuille Periodes et tableau du PDF' if isinstance(v,list) else v])
    per=wb.create_sheet('Periodes');per.append(list(JEU['periodes_exactes'][0]))
    for m in JEU['periodes_exactes']:per.append(list(m.values()))
    per.freeze_panes='C2';per.auto_filter.ref=per.dimensions
    for col in per.columns:per.column_dimensions[col[0].column_letter].width=30
    for row in per:
        per.row_dimensions[row[0].row].height=40
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for row in d:
        d.row_dimensions[row[0].row].height=min(409,max(30,((len(str(row[1].value or ''))+84)//85)*15+10))
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    x=D/'SUIVI_DOC_IR_PAIE_917.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['IRAnnuel'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
