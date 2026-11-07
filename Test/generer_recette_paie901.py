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
JEU={'societe': 'RECETTE PERSONNEL879 — FICTIF, copie isolée', 'menu': '05 · Fiscalité salariale', 'annee': '2026 uniquement', 'revenu_net_imposable_annuel_declare': '200000.00', 'personnes_retenues_pour_reduction': '2', 'reference_rni': 'RNI-ANNUEL-FICTIF901', 'reference_famille': 'FAMILLE-FICTIVE901', 'motif': 'Contrôle annuel entièrement FICTIF901', 'confirmation_cadre': 'Cocher après vérification du RNI et du cadre général fictifs.', 'confirmation_famille': 'Cocher après contrôle des deux personnes éligibles du jeu fictif ; ne pas déduire depuis état civil.', 'confirmation_mode': 'Cocher résultat arithmétique, aucune paie ni déclaration validée.', 'tranches_contribution_attendues': '0.0000 + 2000.0000 + 4000.0000 + 6000.0000 + 27200.0000 + 7400.0000', 'ir_avant_reduction': '46600.0000', 'reduction_theorique': '1200.00', 'reduction_appliquee': '1200.0000', 'ir_arithmetique': '45400.0000', 'essai_inconnu': 'Personnes laissées Inconnu, confirmation famille non cochée ; même RNI200000.00, autres champs inchangés.', 'essai_borne': 'RNI40000.01, personnes0, deux références inchangées, confirmer le cadre et l’éligibilité de la déclaration0.', 'essai_borne_resultat': 'IR arithmétique0.0010 ; ce n’est pas un montant à déclarer ou prélever.', 'essai_zero': 'RNI0.00, personnes0, références et confirmations connues ; résultat0.0000 distinct d’À compléter.', 'essai_reduction_plafonnee': 'RNI41000.00, personnes6, mêmes références et confirmations ; avant réduction100.0000, théorique3600.00, appliquée100.0000, résultat0.0000.', 'retenue_mensuelle_net_montant_declaration': 'Non calculés / Non déterminé dans tous les cas.', 'attention': 'RNI et personnes entièrement fictifs. Aucun calcul automatique d’assiette, frais, cotisations déductibles ou arrondis de liquidation. Tous les statuts humains Non testé.'}
CAS=[('PA-IRAN01', 'Ouvrir le contrôle et lire son périmètre', 'Copie isolée restaurable, Personnel actif/protégé et habilitations identité/rémunération/proposer.', 'Migration118 installée par le technicien après le socle paie ; année2026.', 'Ouvrir05 · Fiscalité salariale > Consulter le barème et ses sources. Vérifier les six tranches, la réduction et les dates. Fermer le barème.', 'Contrôle annuel seulement, année2026 identifiée, sources accessibles par liens ; aucune mise à jour des anciens barèmes de la base. Aucun salaire multiplié par12 ou net présumé.'), ('PA-IRAN02', 'Contrôler l’oracle annuel exact', 'PA-IRAN01 ; revenu net annuel du jeu fictif déjà établi après déductions.', 'RNI200000.00, personnes2, références RNI-ANNUEL-FICTIF901 et FAMILLE-FICTIVE901, motif Contrôle annuel entièrement FICTIF901 ; trois confirmations cochées.', 'Nouveau contrôle annuel IR. Saisir tous les champs du jeu, confirmer le cadre général, l’éligibilité fiscale et le mode arithmétique. Calculer et conserver. Déplier Détail exact par tranche et le Référentiel conservé.', 'Somme progressive46600.0000 ; réduction1200.00, appliquée1200.0000 ; résultat45400.0000. Référentiel, sources et empreintes conservés. Quatre décimales exactes avant les arrondis de liquidation ; aucun impôt exigible ni net déterminé.'), ('PA-IRAN03', 'Préserver une famille ou un RNI inconnus', 'PA-IRAN02 ; créer de nouveaux contrôles, sans écraser le premier.', 'Essai1 : RNI200000.00 et personnes Inconnu, ne pas confirmer la famille. Essai2 : RNI vide et cadre non confirmé, personnes2 et famille confirmée ; mêmes références/motif avec suffixe INCONNU.', 'Enregistrer les deux contrôles pédagogiques et relire les anomalies. Ne pas saisir0 pour faire disparaître une inconnue.', 'Essai1 : impôt avant réduction46600.0000 connu, résultat après réduction À compléter. Essai2 : RNI inconnu, aucun revenu mensuel de substitution, résultat À compléter. L’état civil RH ne renseigne pas le compteur.'), ('PA-IRAN04', 'Vérifier une borne fractionnaire et un vrai zéro', 'PA-IRAN02 ; contrôles distincts.', 'RNI40000.01 puis RNI0.00 ; personnes0, références inchangées, cadre et déclaration0 confirmés, motif Contrôle borne FICTIF901.', 'Calculer chaque contrôle et comparer le résultat exact. Lire le statut du montant à déclarer et de la retenue mensuelle.', '40000.01 donne0.0010 mathématique, sans arrondi de liquidation inventé ; RNI0.00 connu donne0.0000 et non À compléter. Montant à déclarer Non déterminé, retenue et net Non calculés dans les deux cas.'), ('PA-IRAN05', 'Plafonner la réduction à l’impôt sans crédit fictif', 'PA-IRAN02 ; conserver l’identifiant du premier contrôle.', 'RNI41000.00, personnes6 retenues, deux références et confirmations, motif Contrôle réduction FICTIF901.', 'Calculer et conserver. Comparer réduction théorique et appliquée. Réouvrir ensuite le premier contrôle200000/2 depuis la liste.', 'Avant réduction100.0000, réduction théorique3600.00, appliquée100.0000, résultat0.0000 ; aucune créance fiscale ou restitution automatique. Ancien contrôle reste45400.0000, avec ses sources initiales.'), ('PA-IRAN06', 'Vérifier reprise, accès et séparation de la paie', 'Deux sociétés, administrateur d’habilitations ; comptes et journal photographiés avant la recette.', 'Motif révocation Fin accès contrôle annuel901 ; IDs des contrôles, références et empreintes conservés.', 'Vérifier qu’un double clic pendant une requête ne duplique pas le contrôle ; un nouveau contrôle volontaire crée un nouvel ID. Contrôler l’absence de bouton Déclarer/Valider une paie définitive. Changer de société, puis révoquer rémunération et cliquer Actualiser. Comparer journal et soldes avant/après.', 'Historique et isolation conservés, données masquées après révocation. Aucun bulletin, écriture, paiement, déclaration, retenue mensuelle ou net bancaire. Année2026 seule disponible ; autres années à qualifier séparément. Recette utilisateur et production non validées.')]


def generer():
    from decimal import Decimal as Dm
    avant=Dm('20000')*Dm('.10')+Dm('20000')*Dm('.20')+Dm('20000')*Dm('.30')+Dm('80000')*Dm('.34')+Dm('20000')*Dm('.37')
    assert avant==Dm('46600') and avant-Dm('2')*Dm('600')==Dm('45400')
    assert Dm('.01')*Dm('.10')==Dm('.0010')
    assert max(Dm('0'),Dm('1000')*Dm('.10')-Dm('6')*Dm('600'))==0
    D.mkdir(exist_ok=True)
    (D/'JEU_IR_ANNUEL_PAIE_901.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_IR_ANNUEL_PAIE_901.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial901','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial901'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Contrôle annuel du barème IR901','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. Barème annuel sur RNI déclaré, avant arrondis de liquidation. Aucune retenue mensuelle, déclaration ou paie définitive.'),p('Données exactes à saisir','Heading1')]
    for k,v in JEU.items():story.append(p(k+' : '+str(v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('IRAnnuel');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer le journal avant/après.';fi='Contrôle arithmétique annuel uniquement ; montant à déclarer, retenue mensuelle et net non déterminés.';co='Société, droits, année, RNI déclaré, éligibilité, exactitude par tranche, inconnues et intégrité des snapshots.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Captures fiche/version/décision ou refus ; ID branche et version, société et acteurs.'),('Statut','Non testé ; renseigner le classeur et conserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures/ID/version à conserver'])
    pdf=D/'RECETTE_IR_ANNUEL_PAIE_901.pdf';SimpleDocTemplate(str(pdf),title='HisabPro contrôle annuel IR901').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — IR ANNUEL901'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(IRAnnuel!J2:J7,"{statut}")'])
    s.append(['Cas',6]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=48;s.column_dimensions['B'].width=22
    ch=BarChart();ch.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(ch,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    for k,v in JEU.items():d.append([k,v])
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    x=D/'SUIVI_IR_ANNUEL_PAIE_901.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['IRAnnuel'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
