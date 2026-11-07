"""Complément de recette du catalogue,avec hypothèses exclusivement fictives."""
from pathlib import Path
from html import escape
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart,Reference
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];D=R/'docs/personnel-paie'
HYPOTHESE='Hypothèse FICTIVE889 ;aucune valeur réglementaire'
REGLES={reg:{'traitement':'PLAFOND_MONTANT' if plafond else 'SOUMIS','statut_reglementaire':'A_VERIFIER','plafond':plafond,'unite':'operation','conditions':HYPOTHESE} for reg,plafond in [('IR','500.00'),('CNSS','300.00'),('AMO',None)]}
JEU={'code':'PRIME_FICTIVE889','motif':'Exemple entièrement fictif889','contenu':{'libelle':'Prime FICTIVE889','nature':'GAIN','periodicite':'mensuelle','formule':'MONTANT','date_debut':'2026-01-01','date_fin':None,'compte_charge':None,'justificatifs':['ATTESTATION_FICTIVE','MISSION_FICTIVE'],'incompatibilites':[],'regles':REGLES}}
CAS=[
 ('PA-CAT01','Installer sans inventer de données','Copie isolée et restaurable ;socle105–112,technicien.','Migration113,code889. Aucun script de données fiscales historique.','Appliquer113 sur la copie,redémarrer avec le code actuel ;ouvrir02 · Éléments de paie.','Catalogue vide et aucun droit expert attribué automatiquement ;absence de modification des anciens taux.'),
 ('PA-CAT02','Déléguer les accès utiles','Administrateur et trois comptes fictifs du cahier887.','Préparateur :identité,rémunération,Créer et proposer. Décideur :identité,rémunération,Approuver ou rejeter. Lecteur restreint :identité seule.','Personnel >Habilitations :accorder ces droits,activer protection ;se connecter successivement aux comptes.','Lectures et actions conformes ;lecteur identité seule refusé. Aucune ouverture comptable pour Personnel seul.'),
 ('PA-CAT03','Créer une rubrique complète','Préparateur habilité,catalogue vide.','Toutes les valeurs de JEU_CATALOGUE_PAIE_889.json ;justificatifs saisis ATTESTATION_FICTIVE, MISSION_FICTIVE.','Créer une rubrique ;saisir les valeurs,les trois régimes et leurs conditions ;enregistrer puis Consulter PRIME_FICTIVE889.','Version1 Proposée,nouvelle rubrique en tête sansF5 ;deux types de preuves conservés et aucune version approuvée applicable.'),
 ('PA-CAT04','Contrôler l’indépendance','Version1 Proposée ;deux utilisateurs distincts.','Motif Contrôle indépendant fictif889 ;référence CONTROLE-FICTIF889.','Préparateur :vérifier approbation indisponible. Décideur :Consulter,Approuver,remplir motif/référence et confirmer indépendance.','Auto-approbation interdite ;décision indépendante enregistrée,version figée. À vérifier reste À vérifier pour chaque régime.'),
 ('PA-CAT05','Ventiler sans mélanger les régimes','Rubrique du jeu,v1 consultable ;hypothèses non légales.','Montants0.00,300.00,500.00,800.01 ;voir calculs indépendants du jeu.','Détail >Aperçu pédagogique ;saisir chaque montant et Simuler la ventilation.','Pour800.01 :IR exonéré500.00/soumis300.01 ;CNSS exonéré300.00/soumis500.01 ;AMO exonéré0.00/soumis800.01. Simulation explicitement non validée ;aucun net calculé.'),
 ('PA-CAT06','Refuser un cumul supposé','Préparateur,catalogue et nouvelle rubrique CUMUL_FICTIF889.','Copie du jeu avec code CUMUL_FICTIF889 ;unité IR annuel,CNSS mensuel,AMO inchangée.','Créer puis consulter ;simuler800.01.','Fractions IR/CNSS laissées inconnues avec alerte de cumul/éligibilité ;aucun plafond mensuel/annuel appliqué isolément par erreur.'),
 ('PA-CAT07','Conserver les versions et dates','Version1 approuvée et date de recette antérieure2027-01-01.','Nouvelle version :libellé Prime FUTURE FICTIVE889,début2027-01-01,motif Version future fictive889 ;autres données conservées.','Proposer nouvelle version,faire approuver indépendamment ;consulter les dates2026-12-31 puis2027-01-01. Si date déjà passée,utiliser une année future adaptée.','Ancienne version applicable avant l’effet,nouvelle ensuite. Ancien contenu inchangé. Nouvelle date passée ou égale à la dernière approuvée refusée.'),
 ('PA-CAT08','Refuser doublons et entrées invalides','Copie de recette et rubrique existante.','Même code ;aperçu NaN,Infinity,-1,0.001 ;code invalide espace ;formule libre non proposée.','Tenter deuxième création avec même code puis les montants invalides ;consigner les refus du navigateur ouAPI sans les contourner en production.','Aucun doublon ni montant non fini/négatif/précision perdue. API refuse aussi booléens etflottants ;aucune formule utilisateur exécutée.'),
 ('PA-CAT09','Qualifier une règle avec droit dédié','Expert compétent désigné sur copie ;aucun taux réel utilisé par ce test.','Sur une nouvelle proposition fictive :IR Validé,texte TEXTE FICTIF889,article ARTICLE FICTIF889,URL officielle CGI2026,empreinte a répétée64fois.','Essayer sans références :refus. Avec références :décideur sans droit dédié ne peut approuver. Administrateur accorde Qualifier les règles réglementaires de paie ;expert indépendant contrôle puis confirme expressément.','Droit dédié et attestation nécessaires. Les références du scénario sont fictives et ne constituent aucune règle légale validée ;aucune vérification automatique du PDF ou duhash déclarés revendiquée.'),
 ('PA-CAT10','Révoquer et isoler les sociétés','Deux sociétés et utilisateur légitimement autorisé sur la seconde.','Révocation rémunération du préparateur ;motif Fin accès fictif889.','Révoquer,puis Actualiser ;changer de société et vérifier listes/détails. Révoquer aussi le droit expert avant une nouvelle décision réglementaire.','Données/actions privées retirées ;API refuse les anciennes URL. SociétéB ne voit aucune rubriqueA ;droit expert révoqué interdit l’approbation correspondante.'),
 ('PA-CAT11','Vérifier mapping,incompatibilités et absence de preuve','Préparateur sur copie.','Code AUTRE_FICTIVE889,incompatibilité INCONNUE ;puis auto-incompatibilité AUTRE_FICTIVE889 ;compte9999999999.','Tenter créations successives avec ces valeurs ;puis choisir les références réelles de rubriques déjà créées pour la même société.','Inconnues/auto-incompatibilités/mauvais compte refusés sans création résiduelle. Le compte de charge peut rester vide à ce stade. Les pièces attendues sont des types déclarés,leur contrôle sur variables relève du lot suivant.'),
 ('PA-CAT12','Contrôler concurrence et séparation comptable','Deux sessions sur copie ;comptable légitime pour comparaison.','Même dernière version ouverte dans deux sessions,propositions différentes ;soldes et lignes comptables avant lot.','Enregistrer première nouvelle version,puis tenter avec la révision périmée de l’autre ;comparer versions,journal et soldes.','Conflit explicite,pas d’écrasement ;aucune écriture,facture,règlement,cotisation ou bulletin créé. Les tests SQL isolés vérifient aussi immutabilité et migration rejouée avec données.')
]

def generer():
    jeu={'attention':'Exclusivement fictif,ne pas utiliser pour calculer une paie réelle','proposition':JEU,'URL_CGI':'https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf','calculs_independants':[]}
    from decimal import Decimal
    for s in ['0.00','300.00','500.00','800.01']:
        m=Decimal(s);jeu['calculs_independants'].append({'montant':s,'IR_soumis':format(max(Decimal(0),m-Decimal(500)),'.2f'),'CNSS_soumis':format(max(Decimal(0),m-Decimal(300)),'.2f'),'AMO_soumis':s})
    (D/'JEU_CATALOGUE_PAIE_889.json').write_text(json.dumps(jeu,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet();font='Helvetica'
    if Path('C:/Windows/Fonts/arial.ttf').exists():pdfmetrics.registerFont(TTFont('Arial889','C:/Windows/Fonts/arial.ttf'));font='Arial889'
    for st in styles.byName.values():st.fontName=font
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda s,style='BodyText':Paragraph(escape(str(s)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Complément Paie :catalogue des éléments889','Heading1'),p('12cas à effectuer après le cahier Personnel887. Tous les statuts humains sont Non testé. Catalogue et aperçu pédagogique seulement ;variables,bulletins,calculs fiscaux et sociaux définitifs à suivre. Production non validée.'),p('Préparation et saisie exacte','Heading1'),p('Suivre CATALOGUE_PAIE_889.md pour installation sur copie,habilitations et fonctionnement. Le JSON joint contient tous les champs de la première rubrique ;les trois régimes sont renseignés séparément. Les comptes fictifs préparateur/validateur/lecteur et leurs secrets sont décrits dans le cahier Personnel887. Ne jamais employer ces secrets en production.'),p(json.dumps(JEU,ensure_ascii=False,indent=2)),PageBreak()]
    wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('Catalogue');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures attendues','Fiscalité attendue','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,objectif,pre,donnees,actions,attendu in CAS:
        ecriture='Aucune écriture ni paiement ;comparer journal et soldes avant/après.';fiscal='Aucune liquidation fiscale/sociale ;règles chiffrées de recette fictives.';controle='Société,droits,séparation des acteurs,dates,absence d’arrondi implicite et historique.'
        story+=[p(ident+' — '+objectif,'Heading2')]
        for t,v in [('Prérequis',pre),('Données',donnees),('Actions',actions),('Attendu',attendu),('Écritures',ecriture),('Fiscalité',fiscal),('Contrôles',controle),('Preuve','Capture de la saisie et du résultat/refus ;identifiant version et acteur.'),('Statut','Non testé ;remplir résultat réel,anomalies etobservations dans Excel.')]:story.append(p(t+' : '+v))
        story.append(Spacer(1,12));w.append([ident,objectif,pre,donnees,actions,attendu,ecriture,fiscal,controle,'Non testé','','','','Capture et IDversion à conserver'])
    pdf=D/'RECETTE_CATALOGUE_PAIE_889.pdf';SimpleDocTemplate(str(pdf),leftMargin=1.7*cm,rightMargin=1.7*cm,title='HisabPro catalogue de paie889').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    for i in range(2,14):w.row_dimensions[i].height=140
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J13')
    for row in [['HISABPRO —CATALOGUE PAIE889'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(Catalogue!J2:J13,"{statut}")'])
    s.append(['Cas',12]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=50;s.column_dimensions['B'].width=25
    chart=BarChart();chart.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);chart.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(chart,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    def aplatir(obj,prefixe=''):
        for k,v in obj.items():
            chemin=prefixe+k
            if isinstance(v,dict):yield from aplatir(v,chemin+'.')
            else:yield [chemin,', '.join(map(str,v)) if isinstance(v,list) else '' if v is None else str(v)]
    for ligne in aplatir(JEU):d.append(ligne)
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for i in range(2,d.max_row+1):d.row_dimensions[i].height=36
    x=D/'SUIVI_CATALOGUE_PAIE_889.xlsx';wb.save(x)
    text='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in text for c in CAS) and '\u25a0' not in text
    relu=load_workbook(x);assert relu['Catalogue'].max_row==13 and all(relu['Catalogue'].cell(i,10).value=='Non testé' for i in range(2,14))
    print(json.dumps({'cas':12,'pages':len(PdfReader(pdf).pages),'feuilles':relu.sheetnames,'statuts':'Tous Non testé'},ensure_ascii=False))

if __name__=='__main__':generer()
