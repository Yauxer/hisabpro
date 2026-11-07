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
JEU={
 'societe':'RECETTE PERSONNEL879 — FICTIF', 'code_regime':'REGIME_FICTIF', 'code_branche':'B1_FICTIVE',
 'libelle':'Branche de recette sans portée légale', 'organisme':'Organisme fictif',
 'applicabilite':'Applicable sous les conditions déclarées', 'mode':'Taux en pourcentage', 'assiette':'CNSS',
 'taux_salarial_pourcent':'1.234567', 'taux_patronal_pourcent':'2.5', 'plafonnement':'Plafond en montant',
 'plafond_MAD':'5000.00', 'unite':'Mensuelle', 'composants':'CT_FICTIF, IPE_FICTIF',
 'debut':'2026-01-01', 'fin':'Laisser vide', 'nature_source':'Réglementaire', 'qualification':'À vérifier',
 'conditions':'Hypothèse fictive de recette ; ne pas utiliser pour une paie réelle.',
 'motif_proposition':'Création de B1 fictive897', 'motif_decision':'Contrôle indépendant fictif897',
 'reference_controle':'CTRL-FICTIF897', 'nouvelle_date':'2027-01-01','nouveau_taux_salarial':'1.5',
 'attention':'Aucun taux légal préchargé. Aucun calcul de cotisation, IR, net, bulletin ou écriture dans ce lot.'}
CAS=[
 ('PA-SOC01','Ouvrir le référentiel vide','Copie isolée restaurable, Personnel protégé et module actif ; habilitations identité/rémunération et proposer pour le préparateur.','Migration116 après115 ; société fictive du cahier887.','Faire installer116 sur copie. Ouvrir Personnel & Paie > 04 · Charges sociales. Consulter les avertissements.','Écran accessible, référentiel initial vide ; aucune valeur légale inventée ni régime attribué aux salariés.'),
 ('PA-SOC02','Créer une branche exacte et inspecter sa version','PA-SOC01 ; compte préparateur.','Tous les champs du jeu ci-dessus. Sources, article, URL, empreinte et consultation laissés vides puisque qualification À vérifier.','Créer une branche. Saisir exactement les données. Laisser les champs facultatifs vides. Enregistrer la proposition, puis Consulter B1_FICTIVE.','Version1 Proposée visible immédiatement ; taux1.234567 et2.5 conservés sans flottant. Deux composants distincts. Le préparateur ne peut pas approuver sa proposition.'),
 ('PA-SOC03','Faire approuver par une personne indépendante','Deuxième utilisateur habilité approuver et lire identité/rémunération ; ne pas utiliser le compte du préparateur.','Motif Contrôle indépendant fictif897 ; référence CTRL-FICTIF897 ; confirmation d’indépendance.','Se connecter avec le décideur. Consulter B1_FICTIVE > Approuver la version1. Saisir motif, référence et confirmation, puis confirmer.','Version1 Approuvée ; acteur, date, motif et référence conservés. La qualification reste À vérifier ; aucune conformité automatique ni paie produite.'),
 ('PA-SOC04','Bloquer une double couverture','B1_FICTIVE approuvée.','Nouvelle branche IPE_DOUBLE, même régime REGIME_FICTIF, mêmes paramètres, composant IPE_FICTIF seulement, début2026-01-01 ; motif Test doublon fictif897.','Créer la proposition IPE_DOUBLE et tenter de la faire approuver par le décideur indépendant.','Refus explicite : composant déjà couvert dans ce régime sur cette période. La proposition reste Proposée. Un autre régime distinct ne constitue pas le même périmètre ; cela ne justifie pas son affectation à un salarié.'),
 ('PA-SOC05','Conserver l’histoire et sélectionner la date','B1_FICTIVE version1 approuvée.','Nouvelle version : début2027-01-01, taux salarial1.5, autres données inchangées ; motif Révision fictive897.','Depuis le préparateur, Consulter B1_FICTIVE > Proposer une nouvelle version. La date de début doit être vide : saisir la nouvelle date. Enregistrer et faire approuver indépendamment. Filtrer au31/12/2026 puis01/01/2027.','Ancienne version intacte et applicable en2026 ; nouvelle applicable en2027. Aucune modification d’une ancienne paie. Une fin de validité explicite ne réactive pas une version antérieure.'),
 ('PA-SOC06','Vérifier qualification, sources et révocation','Copie de recette uniquement ; administrateur des habilitations et deux comptes séparés.','Branche SOURCE_TEST, régime TEST_SOURCE, composant GARANTIE_TEST. Ne qualifier aucune véritable règle avec des pièces fictives.','Vérifier qu’une proposition déclarée Validée exige référence, texte, empreinte et consultation ; une source réglementaire exige article et URL officielle HTTPS. Vérifier qu’un décideur sans habilitation dédiée ne peut pas approuver cette qualification. Ne pas inventer une preuve. Révoquer ensuite lire_remuneration au préparateur et cliquer Actualiser.','Preuves manquantes refusées ; approbation qualifiée réservée au décideur habilité ayant confirmé son contrôle. Après révocation, détail et formulaire disparaissent, API interdite. Deuxième société ne voit pas ces branches. Les tests automatisés de qualification emploient des preuves explicitement fictives sur base isolée uniquement.')
]


def generer():
    D.mkdir(exist_ok=True)
    (D/'JEU_SOCIAL_PAIE_897.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_SOCIAL_PAIE_897.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial897','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial897'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Référentiel des charges sociales897','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. Paramétrage versionné uniquement ; aucune cotisation réelle ni paie définitive calculée.'),p('Données exactes à saisir','Heading1')]
    for k,v in JEU.items():story.append(p(k+' : '+str(v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('Social');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer le journal avant/après.';fi='Aucun calcul de cotisation, IR ou net à payer ; inconnus conservés.';co='Société, droits, indépendance, dates, composition, sources et intégrité des versions.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Captures fiche/version/décision ou refus ; ID branche et version, société et acteurs.'),('Statut','Non testé ; renseigner le classeur et conserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures/ID/version à conserver'])
    pdf=D/'RECETTE_SOCIAL_PAIE_897.pdf';SimpleDocTemplate(str(pdf),title='HisabPro référentiel social897').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — SOCIAL897'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(Social!J2:J7,"{statut}")'])
    s.append(['Cas',6]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=48;s.column_dimensions['B'].width=22
    ch=BarChart();ch.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(ch,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    for k,v in JEU.items():d.append([k,v])
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    x=D/'SUIVI_SOCIAL_PAIE_897.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['Social'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
