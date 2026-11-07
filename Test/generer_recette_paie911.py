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
JEU={'societe': 'RECETTE PERSONNEL879 — FICTIF, copie isolée', 'menu': '05 · Fiscalité salariale → Contrôle annuel IR', 'annee': '2026', 'rni_annuel_deja_etabli': '40000.01', 'personnes_charge_confirmees': '0', 'reference_rni': 'RNI-FICTIF911', 'reference_famille': 'FAMILLE-FICTIVE911', 'motif': 'Contrôle annuel FICTIF911', 'confirmations': 'Cadre général/RNI ; éligibilité fiscale de zéro personne ; périmètre arithmétique sans paie ou déclaration.', 'attendu_sans_arrondi': '0.0010', 'base_annuelle_arrondie': '40010.00', 'ir_avant_reduction_sur_base_arrondie': '1.0000', 'reduction_appliquee': '0.0000', 'ir_comparatif': '1.0000', 'ecart': '0.9990', 'source': 'CGI2026 article167 page317, copieDGI duCRI, SHAfe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1', 'essai_multiple': 'RNI40010.00, mêmes personnes/références/confirmations ; base40010.00, impôt1.0000, écart0.0000.', 'essai_famille_inconnue': 'RNI40000.01, personnes Inconnu, ne pas confirmer la famille ; base40010.00 connue, impôt après réduction À compléter.', 'essai_reduction': 'RNI40000.01, personnes6 confirmées ; réduction appliquée1.0000 sur base arrondie, résultat0.0000, aucun crédit.', 'essai_zero': 'RNI0.00 et personnes0 confirmés ; base0.00 connue, résultat0.0000.', 'attention': 'Données fictives ; aucune retenue mensuelle, somme à verser, imputation, déclaration ou paie définitive.'}
CAS=[('PA-ARR01', 'Comparer avant/après arrondi annuel', 'Copie isolée ; Personnel actif/protégé et habilitations identité/rémunération/proposer ; RNI annuel déjà établi.', 'Tous les champs du jeu principal40000.01/0.', 'Créer un contrôle annuel, saisir les références et confirmations, calculer ; lire Comparaison sur base annuelle arrondie.', 'Sans arrondi0.0010 ; base40010.00 ; avant réduction1.0000 ; réduction0.0000 ; comparatif1.0000 ; écart0.9990. Versement non déterminé.'), ('PA-ARR02', 'Conserver une base déjà multiple', 'PA-ARR01 ; nouveau contrôle.', 'RNI40010.00, personnes0, mêmes références/confirmations, motif Multiple FICTIF911.', 'Calculer et comparer la base déclarée à la base arrondie.', 'Base40010.00 conservée, résultat1.0000 etécart0.0000 ; aucune dizaine supplémentaire.'), ('PA-ARR03', 'Préserver les inconnues', 'Nouveaux contrôles, aucun ancien résultat écrasé.', 'Essai1 RNI40000.01/personnes Inconnu, famille non confirmée. Essai2 RNI vide/cadre non confirmé, personnes0/famille confirmée.', 'Calculer séparément et lire les anomalies.', 'Essai1 : base40010.00 etimpôt avant réduction1.0000 connus, résultat après famille À compléter. Essai2 : base etcomparaison inconnues, jamais zéro présumé.'), ('PA-ARR04', 'Plafonner une réduction et distinguer zéro', 'PA-ARR01 ; contrôles distincts.', 'RNI40000.01/personnes6, puisRNI0.00/personnes0 ; références etconfirmations du jeu.', 'Calculer chaque cas etcomparer réduction appliquée, résultat etversement.', 'Premier : réduction1.0000 sur base arrondie,résultat0.0000 ; second : base0.00 connue,résultat0.0000. Aucun crédit fictif ni versement déterminé.'), ('PA-ARR05', 'Conserver les contrôles historiques', 'Un véritable contrôle créé avant911 est présent sur copie ; sinon noter ce cas Bloqué sans inventer un historique.', 'ID etempreinte de l’ancien contrôle ; nouveauRNI40000.01/0 si nécessaire.', 'Relire l’ancien contrôle, comparer à la preuve conservée avantmiseàjour. Créer ensuite un nouveau contrôle etrelire le premier.', 'Ancien contenu/référentiel/empreinte inchangés,sans comparaison ajoutée rétroactivement. Nouveau contrôle conserve la règle911 etson document. Le rejeu idempotent authentique911 est couvert par le testAPI fourni.'), ('PA-ARR06', 'Vérifier sources et limites', 'Deux sociétés fictives, administrateur d’habilitations ; journal relevé avantrecette.', 'IDdu nouveau contrôle, motif Fin accès FICTIF911.', 'Ouvrir la source article167, vérifier empreinte/date affichées. Changer de société,révoquer rémunération etActualiser. Comparer journal etpaiements.', 'Sources conservées,isolation etrévocation effectives,aucun débordement mobile. Aucun net,bulletin,paiement,écriture oumontantàdéclarer ; production nonvalidée.')]


def generer():
    from decimal import Decimal as Dm
    avant=Dm('20000')*Dm('.10')+Dm('20000')*Dm('.20')+Dm('20000')*Dm('.30')+Dm('80000')*Dm('.34')+Dm('20000')*Dm('.37')
    assert avant==Dm('46600') and avant-Dm('2')*Dm('600')==Dm('45400')
    assert Dm('.01')*Dm('.10')==Dm('.0010')
    assert max(Dm('0'),Dm('1000')*Dm('.10')-Dm('6')*Dm('600'))==0
    D.mkdir(exist_ok=True)
    (D/'JEU_ARRONDI_ANNUEL_PAIE_911.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_ARRONDI_ANNUEL_PAIE_911.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial911','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial911'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Comparaison de base annuelle arrondie911','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. Comparaison annuelle avant/après arrondi de base ; aucune retenue mensuelle, imputation, somme à verser ou paie définitive.'),p('Données exactes à saisir','Heading1')]
    for k,v in JEU.items():story.append(p(k+' : '+str(v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('IRAnnuel');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer le journal avant/après.';fi='Contrôle arithmétique annuel uniquement ; montant à déclarer, retenue mensuelle et net non déterminés.';co='Société, droits, année, RNI déclaré, éligibilité, exactitude par tranche, inconnues et intégrité des snapshots.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Captures fiche/version/décision ou refus ; ID branche et version, société et acteurs.'),('Statut','Non testé ; renseigner le classeur et conserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures/ID/version à conserver'])
    pdf=D/'RECETTE_ARRONDI_ANNUEL_PAIE_911.pdf';SimpleDocTemplate(str(pdf),title='HisabPro comparaison annuelle911').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — IR ANNUEL911'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(IRAnnuel!J2:J7,"{statut}")'])
    s.append(['Cas',6]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=48;s.column_dimensions['B'].width=22
    ch=BarChart();ch.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(ch,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    for k,v in JEU.items():d.append([k,v])
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    x=D/'SUIVI_ARRONDI_ANNUEL_PAIE_911.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['IRAnnuel'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
