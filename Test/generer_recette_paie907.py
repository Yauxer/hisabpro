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
JEU={'societe': 'RECETTE PERSONNEL879 — FICTIF, copie isolée uniquement', 'menu_catalogue': '02 · Éléments de paie → Catalogue', 'menu_social': '04 · Charges sociales → Référentiel', 'code_rubrique': 'FRAIS_FICTIF907', 'libelle_rubrique': 'Qualification frais FICTIVE907', 'nature': 'Gain', 'periodicite': 'Mensuelle', 'formule': 'Montant exact', 'debut': '2026-01-01', 'fin': 'Laisser vide', 'compte_charge': 'Laisser vide', 'justificatifs_incompatibilites': 'Laisser vides', 'traitements_IR_CNSS_AMO': 'À vérifier pour les trois ; conditions : Hypothèse fictive sans portée légale', 'frais_professionnels': 'Activer Définir la qualification ; traitement Exclue ; qualification À vérifier ; conditions Hypothèse fictive sans portée légale', 'code_branche': 'DEDUCTION_FICTIVE907', 'regime': 'REGIME_FICTIF907', 'libelle_branche': 'Qualification déduction FICTIVE907', 'organisme': 'Organisme fictif', 'applicabilite_mode_assiette_plafond': 'Laisser À vérifier / À qualifier ; aucun taux ni montant saisi ; composants vides', 'nature_source': 'Réglementaire', 'qualification_sociale': 'À vérifier', 'deductibilite_ir': 'Activer Définir la qualification ; traitement Non déductible ; qualification À vérifier ; conditions Hypothèse fictive sans portée légale', 'motif_proposition': 'Création fictive907', 'motif_decision': 'Contrôle indépendant fictif907', 'reference_controle': 'CTRL-FICTIF907', 'nouvelle_date': '2027-01-01', 'attention': 'Aucune preuve légale fictive à utiliser en production. Tests de validation de preuves uniquement automatisés sur cible éphémère. Aucun calcul fiscal ou écriture dans ce lot.'}
CAS=[('PA-QIR01', 'Vérifier l’absence de qualification historique', 'Copie restaurable ; Personnel actif/protégé ; identité et rémunération habilitées.', 'Migration119 après113–118, anciennes versions issues des cahiers889/907.', 'Consulter une ancienne rubrique puis une ancienne branche. Lire Frais professionnels et Déductibilité IR. Comparer les anciens snapshots du brut/social.', 'Qualification non renseignée affichée À vérifier ; aucune déduction ni inclusion présumée. Anciens snapshots et références inchangés.'), ('PA-QIR02', 'Proposer la qualification de base des frais', 'PA-QIR01 ; préparateur habilité proposer.', 'Tous les champs rubrique du jeu ; code FRAIS_FICTIF907, début2026-01-01, frais Exclue / À vérifier, motif Création fictive907.', 'Catalogue > Créer une rubrique. Remplir les trois conditions IR/CNSS/AMO. Définir la qualification Frais professionnels. Enregistrer puis Consulter FRAIS_FICTIF907.', 'Proposition visible immédiatement ; Exclue / À vérifier et conditions conservées séparément du traitement IR. Aucun taux de frais appliqué. Auto-approbation indisponible.'), ('PA-QIR03', 'Proposer la déductibilité de la part salariale', 'PA-QIR01 ; préparateur.', 'Tous les champs branche du jeu ; DEDUCTION_FICTIVE907, REGIME_FICTIF907, début2026-01-01 ; déductibilité Non déductible / À vérifier.', 'Charges sociales > Référentiel > Créer une branche. Définir Déductibilité IR. Enregistrer, consulter et comparer aux paramètres sociaux.', 'Part salariale seule concernée ; règle fiscale distincte des taux sociaux et de leur qualification. Aucun montant déduit. Une règle inconnue n’est pas transformée en zéro.'), ('PA-QIR04', 'Approuver indépendamment et conserver la date', 'PA-QIR02/03 ; autre décideur habilité approuver.', 'Motif Contrôle indépendant fictif907, référence CTRL-FICTIF907 ; confirmation d’indépendance. Nouvelle version début2027-01-01, motif Révision fictive907.', 'Le décideur approuve les deux propositions À vérifier. Le préparateur propose ensuite une nouvelle version datée2027. Comparer les filtres31/12/2026 et01/01/2027 après approbation indépendante.', 'Dates et acteurs conservés, anciennes versions inchangées. Le statut À vérifier n’est pas une validation réglementaire. Les snapshots existants ne sont pas recalculés.'), ('PA-QIR05', 'Refuser une qualification validée sans preuve', 'Copie isolée ; ne pas saisir de fausse preuve officielle.', 'Nouvelle proposition, qualification Validée après contrôle humain ; laisser au moins la référence, l’article, l’URL, l’empreinte ou la consultation vides.', 'Vérifier que les champs deviennent obligatoires et empêchent l’enregistrement incomplet. Tester une URL non officielle ; annuler. Avec une véritable preuve applicable seulement, le décideur habilité doit confirmer son contrôle ; un décideur sans capacité dédiée ne doit pas approuver.', 'Preuve incomplète refusée. La validation fiscale seule impose la capacité dédiée même si la règle sociale reste À vérifier. L’application ne certifie pas le contenu de la preuve déclarée.'), ('PA-QIR06', 'Vérifier isolation et absence d’effet comptable', 'Deux sociétés fictives et administrateur d’habilitations ; journal relevé avant recette.', 'Identifiants des deux propositions ; motif Fin accès fictif907.', 'Changer de société et constater l’absence des propositions. Révoquer rémunération et Actualiser. Vérifier ordinateur et mobile. Comparer journal, paiements et snapshots avant/après.', 'Données masquées après révocation et isolées par société. Affichage vertical lisible. Aucun calcul de frais, RNI, retenue mensuelle, net, bulletin, paiement ou écriture généré.')]


def generer():
    D.mkdir(exist_ok=True)
    (D/'JEU_QUALIFICATIONS_IR_PAIE_907.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_QUALIFICATIONS_IR_PAIE_907.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial907','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial907'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Qualifications fiscales907','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. Qualifications séparées ; aucune règle fiscale ni déduction implicite. Aucun calcul de paie dans ce lot.'),p('Données exactes à saisir','Heading1')]
    for k,v in JEU.items():story.append(p(k+' : '+str(v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('QualificationsIR');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer le journal avant/après.';fi='Aucune déduction, retenue mensuelle ou net ; qualification de base uniquement, inconnus conservés.';co='Société, droits, indépendance, dates, composition, sources et intégrité des versions.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Captures fiche/version/décision ou refus ; ID branche et version, société et acteurs.'),('Statut','Non testé ; renseigner le classeur et conserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures/ID/version à conserver'])
    pdf=D/'RECETTE_QUALIFICATIONS_IR_PAIE_907.pdf';SimpleDocTemplate(str(pdf),title='HisabPro qualifications fiscales907').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — SOCIAL907'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(QualificationsIR!J2:J7,"{statut}")'])
    s.append(['Cas',6]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=48;s.column_dimensions['B'].width=22
    ch=BarChart();ch.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(ch,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    for k,v in JEU.items():d.append([k,v])
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    x=D/'SUIVI_QUALIFICATIONS_IR_PAIE_907.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['QualificationsIR'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
