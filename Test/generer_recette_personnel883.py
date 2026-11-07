"""Cahier Personnel consolidé :43cas humains distincts des résultats automatisés."""
from pathlib import Path
from decimal import Decimal
from html import escape
import json,re
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart,Reference
from openpyxl.workbook.properties import CalcProperties
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
from generer_recette_personnel879 import CAS as C879,prose as prose_base
from generer_recette_personnel881 import CAS as C881

R=Path(__file__).resolve().parents[1];D=R/'docs/personnel-paie'

def prose(texte):
    texte=prose_base(texte)
    texte=re.sub(r'\b(effet|début|fin|entrée|révision|schéma|scénario|base|version|installer|consolidée|au|en|le|après|avant|à|puis)(?=\d)',r'\1 ',texte)
    return re.sub(r'(\d)(cas|pages|feuilles|MAD)\b',r'\1 \2',texte)

SOC=[
 ('PP-SOC01','Distinguer entrée et début du contrat','Copie,protection,préparateur/validateur sous capacités explicites.',
  'P004 ;Hassan FICTIF883 ;poste Test social ;entrée15/12/2025 ;sans compte utilisateur confirmé ;ATTEST-P004 ;motif Création fictive P004. Aucun salaire connu.',
  'Créer le brouillon en ouvrant les informations facultatives ;soumettre puis faire approuver l’identité par le second compte.',
  'Date absente de la racine avant décision,puis15/12/2025 ;aucune date de contrat automatiquement renseignée.'),
 ('PP-SOC02','Approuver trois régimes déclarés','P004 identité approuvée ;capacité identifiants sensibles des deux acteurs.',
  'CDI ;début et effet01/01/2026 ;pas de fin ;AMO-FICTIVE-P004 ;RETRAITE-FICTIVE-P004 ;MUTUELLE-FICTIVE-P004 ;CONTRAT-P004 ;motif Contrat fictif P004.',
  'Consulter au31/12/2026 ;proposer Contrat avec ces valeurs ;enregistrer,soumettre et faire approuver avec CTRL-P004.',
  'Trois libellés présents après approbation,entrée15/12/2025 distincte du contrat01/01/2026. Pas de salaire déduit.'),
 ('PP-SOC03','Version future et effacement explicite','P004 contrat approuvé,sans rémunération future approuvée.',
  'Nouvelle version CDI effet01/01/2027,début01/01/2026 ;AMO-FUTURE-P004 ;retraite conservée ;mutuelle effacée ;AVENANT-P004 ;motif Évolution fictive P004.',
  'Proposer le contrat à cette date ;vérifier les valeurs préremplies ;vider mutuelle explicitement ;soumettre,faire approuver,comparer31/12/2026 et01/01/2027.',
  'Anciennes valeurs conservées en2026 ;AMO nouvelle,retraite conservée,mutuelle À confirmer en2027. Aucune non-affiliation déduite du vide.'),
 ('PP-SOC04','Révoquer les lectures sensibles','P004 avec régimes ;administrateur distinct.',
  'Droit Consulter les identifiants sensibles ;motif Révocation fictive P004.',
  'Administrateur :révoquer ;gestionnaire :Actualiser ;ouvrir fiche,demandes et historique ;consulter autre société de test si disponible.',
  'Libellés et motifs/références sensibles masqués ;aucune valeur récupérée par société étrangère. Aucune suppression de version.'),
 ('PP-SOC05','Ne pas reprendre les régimes d’un CDD expiré','Créer/approuver P005,Nadia CDD FICTIVE883,sans compte,entrée01/01/2026 ;ATTEST-P005 ;motif Création fictive P005.',
  'CDD début/effet01/01/2026,fin31/12/2026 ;AMO-CDD-FICTIVE-P005 ;autres régimes inconnus ;CONTRAT-P005. Nouveau CDI début/effet01/01/2027.',
  'Approuver le CDD ;sélectionner ensuite la consultation01/01/2027 AVANT de proposer le CDI ;laisser les régimes inconnus vides ;enregistrer et consulter la demande.',
  'Le nouveau contrat ne présume pas l’AMO de l’ancien CDD. L’ancien régime reste seulement dans sa version historique.'),
 ('PP-SOC06','Préserver une rémunération future approuvée','P001 :base9876,54 au01/01/2027 déjà approuvée par le scénario879 ;dossier pas encore sorti à la date consultée.',
  'Nouveau contrat CDI effet01/01/2027,début01/01/2026 ;REF-CONFLIT-P001 ;motif Contrôle cohérence fictif.',
  'Proposer cette nouvelle version de contrat ;observer le refus ;recharger et consulter la rémunération au01/01/2027.',
  '409 expliqué car le salaire serait détaché de son contrat ;9876,54 conservé. Examiner une régularisation contrôlée,ne pas changer les dates pour contourner.'),
]

def normaliser(c,domaine):
    ident,obj,pre,donnees,actions,attendu=c
    return dict(id=ident,module=domaine,objectif=prose(obj),prerequis=prose(pre),donnees=prose(donnees),actions=prose(actions),attendu=prose(attendu),
      ecritures='Aucune écriture administrative ;grand livre et pièces fictives conservés.',fiscalite='Aucun impôt ou cotisation calculé par ce parcours.',
      controle='Société,rôle,capacités,révision,dates,indépendance et absence de valeur inventée.',preuve='Capture/référence de demande et résultat réel à enregistrer.',automatisation='Voir PREUVE_PERSONNEL_PAIE_883.json ;appréciation humaine séparée.')

def generer():
    preuve=json.loads((R/'Test/PREUVE_PERSONNEL_PAIE_883.json').read_text(encoding='utf8'));assert all(x['statut']=='reussi' for x in preuve['resultats_distincts'])
    cas=[dict(c) for c in C879]+[normaliser(c,'Profil_Personnel') for c in C881]+[normaliser(c,'Regimes_sociaux') for c in SOC]
    assert len(cas)==43 and len({x['id'] for x in cas})==43
    # Les instructions actuelles remplacent le périmètre historique du pilote.
    for c in cas:
        for k,v in c.items():
            if isinstance(v,str) and k not in ('id','automatisation'):c[k]=prose(v)
        c['prerequis']=prose(c['prerequis'].replace('schéma 108','schéma 110'))
        if c['id']=='PP-003':c['donnees']+=' Préparateur/validateur peuvent être Personnel seul après109 ;administrateur séparé pour habilitations.'
        if c['id']=='PP-002':c['prerequis']='Compte administrateur/comptable légitime ;le profil Personnel seul ne voit pas le lien historique.'
    (D/'CAS_RECETTE_PERSONNEL_883.json').write_text(json.dumps(cas,ensure_ascii=False,indent=2),encoding='utf8')
    jeu=json.loads((D/'JEU_DONNEES_PERSONNEL_879.json').read_text(encoding='utf8'))
    jeu['complements_883']={'P004':'Hassan FICTIF883,entrée2025-12-15,CDI2026-01-01,trois régimes fictifs,salaire inconnu.',
      'P005':'Nadia CDD FICTIVE883,entrée2026-01-01,CDD2026-01-01 à2026-12-31,AMO fictive,salaire inconnu.',
      'attention':'Ne pas convertir les deux salaires inconnus en zéro ni présenter la somme des trois bases connues comme une paie globale complète.'}
    jeu['personnel_complementaire']=[{'matricule':m,'nom':n,'poste':poste,'date_entree_connue':entree,'beneficiaire_sans_compte_confirme':True,
      'reference_beneficiaire':'ATTEST-'+m,'contrat':typ,'date_debut':'2026-01-01','date_effet':'2026-01-01','date_fin':fin,'salaire_base':None}
      for m,n,poste,entree,typ,fin in [('P004','Hassan FICTIF883','Test social','2025-12-15','CDI',None),('P005','Nadia CDD FICTIVE883',None,'2026-01-01','CDD','2026-12-31')]]
    assert Decimal(jeu['calculs_independants']['somme_bases_initiales'])==sum(Decimal(x['salaire_base']) for x in jeu['salaries'])
    (D/'JEU_DONNEES_PERSONNEL_883.json').write_text(json.dumps(jeu,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet();font='Helvetica'
    if Path('C:/Windows/Fonts/arial.ttf').exists():pdfmetrics.registerFont(TTFont('Arial883','C:/Windows/Fonts/arial.ttf'));font='Arial883'
    for st in styles.byName.values():st.fontName=font
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;styles['BodyText'].spaceAfter=6
    def p(t,style='BodyText'):return Paragraph(escape(prose(t)).replace('\n','<br/>'),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Personnel / RH — édition consolidée883','Heading1'),
      p('43cas et données exactes ;version28/10/2026. Tests automatisés :'+str(preuve['nombre_distinct'])+' cas distincts qualifiés. Recette humaine :à effectuer. Production :non validée.'),
      p('Disponibles :dossiers,coordonnées,date d’entrée connue,contrats,salaires contractuels versionnés,approbations,sorties,historique,habilitations et profil Personnel seul,régimes sociaux déclarés. Aucune paie calculée,affiliation,déclaration ou écriture comptable née de l’administration.'),
      p('Limite réelleD05 :RIB et pièces sécurisées non collectés avant choix de l’hébergement des clés,rotation,sauvegarde/restauration et conservation. Le Lot1 complet reste partiel sur ce point ;le pilote disponible est testable sans le contourner.'),
      p('Préparer une copie','Heading1'),p('Sur une copie restaurable,installer105 à110 avec le rôle migrateur. Déployer le code actuel sur toutes les instances avant attribution du rôle Personnel et saisie de régimes ;ne pas revenir à une version qui les ignore. Aucun déploiement réel n’a été réalisé ici.'),
      p('Administrateur :Paramètres >Utilisateurs,créer deux comptes distincts avec rôle Personnel seul. Dans Personnel >Habilitations,accorder les capacités du scénario ;activer volontairement la protection. Ne pas donner un rôle comptable à une personne qui doit uniquement gérer le personnel.'),
      p('Comptes fictifs exacts à créer :Préparateur FICTIF883,preparateur.rh883@example.com,secret Prepa-Fictif-883! ;Validateur FICTIF883,validateur.rh883@example.com,secret Valide-Fictif-883! ;Lecteur FICTIF883,lecteur.rh883@example.com,secret Lecteur-Fictif-883! (identité/historique seulement). Rôle Personnel seul pour ces trois comptes. Utiliser uniquement sur copie isolée.'),
      p('Compte préparateur :identité,rémunération,identifiants sensibles,proposer,soumettre,historique. Compte validateur :lectures utiles,approuver,historique. Les attestations d’indépendance et références de pièces demandent un contrôle humain.'),
      p('L’espace historique est réservé aux autres profils autorisés ;pour un profil Personnel,se limiter au nouvel espace. Le contexte de conditions se règle par date,indépendamment de l’exercice comptable. Mon compte permet de changer son mot de passe.'),PageBreak(),p('Données à saisir','Heading1')]
    lib={'matricule':'Matricule','nom':'Nom complet','poste':'Poste','email':'E-mail','telephone':'Téléphone','numero_cnss':'CNSS fictif','situation_familiale':'Situation familiale (code)',
      'nb_enfants':'Enfants','personnes_charge_ir':'Personnes à charge IR','reference_beneficiaire':'Référence rattachement','salaire_base':'Base mensuelle MAD'}
    for sal in jeu['salaries']:
        story.extend([p(sal['matricule']+' — '+sal['nom'],'Heading2'),Table([[p(v),p(sal[k])] for k,v in lib.items()],colWidths=[6*cm,10*cm],style=TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.lightgrey)])),
          p('Choisir explicitement absence de compte utilisateur et cocher sa confirmation. CDI début/effet01/01/2026,aucune fin,périodicité Mensuelle. Valeurs inconnues laissées vides,références/motifs fournis par les cas.')])
    story.extend([p('Codes familiaux :marie= Marié(e),celiba= Célibataire,divorce= Divorcé(e). Les données sociales/fiscales sont fictives et non déclarables. Calcul indépendant des trois bases initiales :23000,10MAD ;après hausse P001 au01/01/2027 :23876,54MAD. Ce n’est pas un net à payer ni une liquidation fiscale.'),
      p('P004/P005 sont décrits intégralement dans PP-SOC01/05 ;aucun salaire n’y est attesté. Aucun RIB ni pièce réelle n’est nécessaire à ce cahier.'),PageBreak()])
    for c in cas:
        story.append(p(c['id']+' — '+c['objectif'],'Heading2'))
        for titre,k in [('Module','module'),('Prérequis','prerequis'),('Saisie exacte','donnees'),('Actions','actions'),('Attendu','attendu'),('Écritures','ecritures'),('Fiscalité','fiscalite'),('Contrôles','controle'),('Preuve','preuve')]:story.append(p(titre+' : '+c[k]))
        story.append(p('Statut humain :Non testé. Renseigner résultat réel,anomalie,observation et capture dans Excel. Couverture automatique :'+c['automatisation']));story.append(Spacer(1,10))
    def pied(canvas,doc):
        canvas.setFont(font,8);canvas.drawString(1.7*cm,1.1*cm,'HisabPro · Personnel · Recette fictive · 28/10/2026');canvas.drawRightString(19.3*cm,1.1*cm,str(doc.page))
    pdf=D/'CAHIER_RECETTE_PERSONNEL_HISABPRO_883.pdf';SimpleDocTemplate(str(pdf),title='HisabPro —cahier Personnel43cas',leftMargin=1.7*cm,rightMargin=1.7*cm).build(story,onFirstPage=pied,onLaterPages=pied)
    wb=Workbook();s=wb.active;s.title='Synthese';wb.calculation=CalcProperties(fullCalcOnLoad=True)
    headers=['ID','Module','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut humain','Résultat réel','Anomalies','Observations','Preuve attendue','Preuve/capture','Couverture automatisée']
    domaines=list(dict.fromkeys(c['module'] for c in cas));lignes=[]
    for domaine in domaines:
        w=wb.create_sheet(domaine);w.append(headers)
        for c in [x for x in cas if x['module']==domaine]:w.append([c[k] for k in ['id','module','objectif','prerequis','donnees','actions','attendu','ecritures','fiscalite','controle']]+['Non testé','','','',c['preuve'],'',c['automatisation']])
        w.freeze_panes='D2';w.auto_filter.ref=w.dimensions
        for col in w.columns:w.column_dimensions[col[0].column_letter].width=35
        for row in w:
            for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
        for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='185FA5')
        for i in range(2,w.max_row+1):w.row_dimensions[i].height=130
        dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add(f'K2:K{w.max_row}');lignes.append((domaine,w.max_row))
    for row in [['HISABPRO —PERSONNEL :RECETTE CONSOLIDÉE883'],['Les résultats automatisés ne remplissent pas les statuts humains.'],['Tests automatisés distincts',preuve['nombre_distinct']],['Production','Non validée'],['Statut humain','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,'='+'+'.join(f'COUNTIF(\'{nom}\'!K2:K{fin},"{statut}")' for nom,fin in lignes)])
    s.append(['Nombre de cas',len(cas)]);s.append(['Progression','=IFERROR(B7/B10,0)']);s['B11'].number_format='0%';s.column_dimensions['A'].width=85;s.column_dimensions['B'].width=25
    chart=BarChart();chart.title='Recette humaine';chart.add_data(Reference(s,min_col=2,min_row=5,max_row=9),titles_from_data=True);chart.set_categories(Reference(s,min_col=1,min_row=6,max_row=9));s.add_chart(chart,'A14')
    w=wb.create_sheet('Jeu_de_donnees');cles=list(jeu['salaries'][0])+['date_entree_connue','date_fin'];w.append(cles)
    for sal in jeu['salaries']+jeu['personnel_complementaire']:w.append([sal.get(k) for k in cles])
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=26
    w.freeze_panes='C2';xlsx=D/'SUIVI_RECETTE_PERSONNEL_883.xlsx';wb.save(xlsx)
    relu=load_workbook(xlsx);assert sum(relu[n].max_row-1 for n,_ in lignes)==43
    assert all(relu[n].cell(i,11).value=='Non testé' for n,fin in lignes for i in range(2,fin+1))
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c['id'] in texte for c in cas) and '\u25a0' not in texte
    print(json.dumps({'cas':43,'pages':len(PdfReader(pdf).pages),'feuilles':relu.sheetnames,'human':'Tous Non testé','formules':'recalcul à ouverture Excel'},ensure_ascii=False))

if __name__=='__main__':generer()
