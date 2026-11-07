"""Complément humain du profil Personnel ;aucun succès de recette prérempli."""
from pathlib import Path
from html import escape
import json
from openpyxl import load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];D=R/'docs/personnel-paie'
CAS=[
 ('PP-PR01','Attribuer le rôle dédié','Administrateur, code881 partout,109 installée.','Nouveau compte fictif personnel881@example.com ;rôle Personnel seul ;mot de passe fictif de recette choisi par l’administrateur.',
  'Paramètres >Utilisateurs :créer le compte avec ce rôle. Lui attribuer ensuite explicitement les capacités de lecture/préparation utiles dans Habilitations.',
  'Aucune capacité automatique ;avant délégation, accès aux dossiers refusé. Le compte ne devient pas comptable.'),
 ('PP-PR02','Préparer et faire approuver avec deux profils Personnel','Deux comptes dédiés habilités ;protection active.','Matricule P881 ;nom Salarié FICTIF881 ;sans compte utilisateur ;ATTEST-P881 ;motif Création fictive881.',
  'Se connecter au premier compte ;créer puis soumettre le dossier. Second compte :Demandes à traiter >Consulter >Approuver ;référence CTRL-P881 et indépendance confirmée.',
  'Dossier Actif ;préparateur et approbateur différents ;aucune écriture comptable.'),
 ('PP-PR03','Vérifier le menu et les URL directes','Compte Personnel connecté.','URL /journal,/factures,/parametres,/cnss.',
  'Observer sidebar puis saisir chaque URL ;revenir au Personnel. Vérifier la même chose à390px de large.',
  'Arrivée au Personnel ;aucun contenu des autres modules. Le serveur refuse aussi les appels API directs avec403.'),
 ('PP-PR04','Révoquer une capacité pendant la session','Compte Personnel autorisé à proposer.','Droit Proposer une modification ;motif Révocation fictive881.',
  'Administrateur :révoquer ce droit. Gestionnaire :Actualiser puis tenter une proposition.',
  'Action masquée/refusée ;les lectures encore autorisées restent disponibles. Pas de reconnexion requise pour le refus serveur.'),
 ('PP-PR05','Vérifier les rôles propres à chaque société','Compte avec accès à deux sociétés fictivesA/B.','Rôle Personnel seul dansB ;rôle propre légitime dansA.',
  'Changer de société ;contrôler le rôle/les menus et les données. AdministrateurB :désactiver l’accès invité ;retester.',
  'Rôle et capacités propres àB ;révocation effective surB ;compte principal dansA conservé.'),
 ('PP-PR06','Changer le rôle sans réutiliser les droits anciens','Administrateur et gestionnaire distincts.','Sur la copie seulement :Comptable puis Personnel seul.',
  'Administrateur :changer le rôle. Garder la même session du gestionnaire ;Actualiser ou recharger une URL.',
  'Le serveur applique immédiatement le rôle en base. Aucun JWT antérieur ne conserve les droits comptables après restriction.'),
 ('PP-PR07','Contrôler l’échec de contexte et le rechargement','Compte dédié connecté, copie isolée.','Backend temporairement indisponible pendant chargement du contexte.',
  'Interrompre seulement la connexion de test puis la rétablir ;Réessayer le contexte Personnel.',
  'Erreur visible ;aucune donnée comptable de repli. Réessai réel après retour du service. Appréciation humaine à renseigner.'),
 ('PP-PR08','Changer son mot de passe sans accès aux paramètres','Compte Personnel connecté.','Ancien secret de ce compte fictif ;nouveau Secret-Fictif-UI881-Renouvele! saisi deux fois.',
  'Mon compte :saisir ancien,nouveau et confirmation ;Modifier mon mot de passe ;Revenir à la connexion puis utiliser le nouveau secret.',
  'Confirmation explicite,anciens jetons invalidés,nouvelle connexion au Personnel et aucun accès comptable ajouté.'),
]

def generer():
    wb=load_workbook(D/'SUIVI_RECETTE_PERSONNEL_879.xlsx');ws=wb.create_sheet('Profil_Personnel');ws.append([c.value for c in wb['Dossiers'][1]])
    for ident,obj,pre,donnees,actions,attendu in CAS:
        ws.append([ident,'Profil Personnel',obj,pre,donnees,actions,attendu,'Aucune écriture','Aucun calcul fiscal',
          'Contrôler rôle effectif,capacité,société et absence de données étrangères.','Non testé','','','','Capture et compte/société utilisés.','','Voir tests881 ;le cas de panne de contexte demande encore sa recette humaine.'])
    ws.freeze_panes='D2';ws.auto_filter.ref=ws.dimensions
    for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=35
    for row in ws:
        for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
    for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
    for i in range(2,len(CAS)+2):ws.row_dimensions[i].height=120
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(dv);dv.add(f'K2:K{len(CAS)+1}')
    synth=wb['Synthese'];synth['A1']='HISABPRO — PERSONNEL : RECETTE879 + PROFIL881';synth['B10']=29+len(CAS)
    for r,statut in zip(range(6,10),['Non testé','Réussi','Échoué','Bloqué']):synth.cell(r,2).value+=f'+COUNTIF(\'Profil_Personnel\'!K2:K{len(CAS)+1},"{statut}")'
    synth['A3']='Tests automatisés881 :voir preuve JSON,aucune équivalence avec recette humaine';synth['B3']=None
    cible=D/'SUIVI_RECETTE_PERSONNEL_881.xlsx';wb.save(cible)
    relu=load_workbook(cible);assert relu['Profil_Personnel'].max_row==len(CAS)+1 and all(relu['Profil_Personnel'].cell(i,11).value=='Non testé' for i in range(2,len(CAS)+2))
    styles=getSampleStyleSheet();font='Helvetica'
    if Path('C:/Windows/Fonts/arial.ttf').exists():pdfmetrics.registerFont(TTFont('Arial881','C:/Windows/Fonts/arial.ttf'));font='Arial881'
    for s in styles.byName.values():s.fontName=font
    def p(t,st='BodyText'):return Paragraph(escape(t),styles[st])
    story=[p('HISABPRO — PERSONNEL SEUL','Title'),p('Complément au cahier de recette879 —livraison881. Les conditions du pilote879 relatives au rôle exclusivement Personnel sont remplacées par ce complément.'),
      p('Déployer le code881 sur toutes les instances,puis109. Aucun compte ni capacité automatiquement attribué. Dans Paramètres >Utilisateurs,choisir Personnel seul ;attribuer ensuite les capacités utiles dans Personnel >Habilitations. Prévoir deux comptes indépendants.'),
      p('Le compte arrive directement au Personnel. Journal,factures,paramètres,ancien espace et fournisseurs de données comptables ne sont pas ouverts à ce profil. Une société où il possède un autre rôle conserve ses propres droits.'),
      p('Recette humaine :à effectuer ;production :non validée. Le PDF879 décrit les autres29cas et les données exactes ;le classeur881 réunit37cas non testés humainement. Les limites RIB/pièces/clés/régimes et calculs de paie restent explicites.')]
    for ident,obj,pre,donnees,actions,attendu in CAS:
        story.extend([Spacer(1,12),p(ident+' — '+obj,'Heading2'),p('Prérequis : '+pre),p('Données : '+donnees),p('Actions : '+actions),p('Attendu : '+attendu),p('Écriture/impact fiscal :aucun. Statut humain :Non testé. Résultat réel,anomalie et capture à renseigner dans Excel.')])
    story.extend([Spacer(1,12),p('Retour arrière :ne pas remettre un backend antérieur à881 en présence de comptes personnel actifs. Conserver le garde ou désactiver explicitement les accès concernés sous contrôle administratif. Ne pas les convertir automatiquement en comptable ou lecture générale.')])
    pdf=D/'COMPLEMENT_RECETTE_PROFIL_PERSONNEL_881.pdf';SimpleDocTemplate(str(pdf),title='HisabPro —Profil Personnel seul881').build(story)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS)
    print(json.dumps({'cas_humains':29+len(CAS),'nouveaux_cas':len(CAS),'pages_complement':len(PdfReader(pdf).pages),'feuilles':relu.sheetnames,'statuts':'Non testé'},ensure_ascii=False))

if __name__=='__main__':generer()
