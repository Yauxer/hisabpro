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
from generer_recette_paie913 import JEU as JEU913
JEU={**JEU913,'menu':'05 · Fiscalité salariale → Cumuls et frais annuels → Contrôler l’IR de ce RNI',
 'installation':'122 après121 sur copie isolée ; droits identité, rémunération et proposition ; jeu913 préalablement constitué.',
 'source':'Contrôle des frais annuels complet, RNI83881.0200. Utiliser le bouton de son résultat, puis Charger le RNI annuel ; aucun RNI à saisir.',
 'personnes_charge':'2','reference_famille':'FAMILLE-FICTIVE915','motif':'Contrôle IR sourcé FICTIF915',
 'confirmations':'Confirmer la source annuelle, le barème général, l’éligibilité des deux personnes et le périmètre arithmétique uniquement dans le jeu fictif.',
 'attendus':'RNI source83881.0200 ; base annuelle arrondie83890.00 ; IR avant réduction7167.0000 ; réduction1200.0000 ; IR annuel5967.0000. Aucun montant à déclarer, verser ou retenir mensuellement.'}
CAS=[
 ('PA-IRS01','Ouvrir le RNI source sans ressaisie','Jeu913 complet sur copie, douze préparations distinctes ; droits de proposition.',
  'Source913 au RNI83881.0200 ; noter son ID et son empreinte.',
  'Ouvrir le résultat du cumul annuel. Cliquer Contrôler l’IR de ce RNI puis Charger le RNI annuel. Vérifier identité, année et douze périodes.',
  'Le formulaire reprend l’identifiant réel ; aucun champ de revenu ou taux modifiable. La source exacte reste affichée.'),
 ('PA-IRS02','Calculer l’IR annuel sur base arrondie','PA-IRS01 ; cadre général et famille fictive vérifiés.',
  '2 personnes ; référence FAMILLE-FICTIVE915 ; motif Contrôle IR sourcé FICTIF915. Cocher les quatre confirmations.',
  'Calculer et conserver l’IR annuel sourcé. Comparer RNI source, base, tranches, réduction et IR.',
  '83881.0200 avant arrondi,83890.00 de base ; 2000+4000+1167=7167 avant famille ; 2×600=1200 ; IR5967.0000. Versement et retenue mensuelle inconnus.'),
 ('PA-IRS03','Garder la famille inconnue','Même source complète ; ouvrir un nouveau contrôle sourcé.',
  'Personnes à charge Inconnu ; aucune référence familiale. Source, cadre et périmètre confirmés.',
  'Charger la source puis calculer. Lire le résultat et l’anomalie familiale.',
  'IR avant réduction7167.0000 ; IR après réduction À compléter. Aucun zéro familial implicite.'),
 ('PA-IRS04','Revenir au contrôle des frais annuel','PA-IRS02 ; résultat IR ouvert.',
  'Aucune nouvelle donnée ; ID et empreinte source notés.',
  'Cliquer Consulter le contrôle des frais annuels source. Comparer le résultat et ses douze sources au contrôle initial.',
  'Même contrôle annuel, même RNI et mêmes empreintes. Le retour ne crée ni ne recalcule un contrôle.'),
 ('PA-IRS05','Refuser une source partielle ou périmée','Copie isolée ; deux acteurs distincts pour approuver une nouvelle variable.',
  'Contrôle913 à onze mois puis source complète ; ajouter une variable fictive approuvée de100.00 sur novembre après le contrôle complet.',
  'Tenter un IR depuis la source partielle. Puis tenter un nouveau contrôle depuis la source complète devenue périmée. Relire un ancien IR déjà conservé.',
  'Refus409 dans les deux créations ; l’ancien résultat et sa source restent identiques. Aucune écriture validée modifiée.'),
 ('PA-IRS06','Vérifier sociétés, révocation et écrans étroits','Deux sociétés fictives isolées ; administrateur disponible.',
  'Même source appartenant à A ; utilisateur de B puis utilisateur de A privé du droit lire_remuneration.',
  'Essayer la source de A depuis B. Revenir sur A, révoquer le droit et Actualiser. Vérifier le parcours à390px puis1440px.',
  'Aucune source inter-société ; erreur d’habilitation après révocation, montant retiré de l’écran. Aucun défilement horizontal de page ou donnée salariale stockée dans le navigateur.')]

def generer():
    D.mkdir(exist_ok=True)
    (D/'JEU_IR_SOURCE_PAIE_915.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_IR_SOURCE_PAIE_915.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial915','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial915'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('IR annuel depuis un RNI constitué915','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. RNI source conservé, base annuelle arrondie et IR relié ; sans retenue mensuelle, versement ou paie définitive.'),p('Données exactes à saisir','Heading1')]
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
    pdf=D/'RECETTE_IR_SOURCE_PAIE_915.pdf';SimpleDocTemplate(str(pdf),title='HisabPro IR annuel sourcé915').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — IR ANNUEL915'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
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
    x=D/'SUIVI_IR_SOURCE_PAIE_915.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['IRAnnuel'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
