"""Guide PDF, données fictives et suivi Excel de recette humaine Personnel."""
from pathlib import Path
from decimal import Decimal
from html import escape
import json,re
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.workbook.properties import CalcProperties
from openpyxl.chart import BarChart,Reference
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1]
D=R/'docs/personnel-paie'
AUTO='test_879_creation_conditions_validation_et_masque_edge'
ADMIN='test_879_administrer_acces_activation_reprise_et_rejet_ui'
CAS=[]

def prose(v):
    return re.sub(r'([;:])(?=\S)',r'\1 ',re.sub(r',(?=[^\d\s])',', ',str(v)))
def cas(id,domaine,objectif,donnees,actions,attendu,controle,auto=AUTO,prerequis='Copie de recette, schéma 108, préparateur et validateur distincts habilités.'):
    CAS.append(dict(id=id,module=domaine,objectif=prose(objectif),prerequis=prose(prerequis),donnees=prose(donnees),actions=prose(actions),
                    attendu=prose(attendu),controle=prose(controle),automatisation=auto,
                    ecritures='Aucune écriture générée ; pièces et lignes existantes inchangées.',
                    fiscalite='Aucun impôt/cotisation calculé ici. Données personnelles conservées sans déduction automatique.',
                    preuve='Capture de l’écran et réponse/statut constaté ; référence de demande si applicable.'))

cas('PP-001','Navigation','Retrouver le module et ses neuf rubriques.','Société : RECETTE PERSONNEL879 — FICTIF.','Ouvrir Personnel & Paie dans la sidebar ; lire les neuf intitulés ; cliquer 01 Personnel.',
    'Personnel accessible ; huit autres rubriques À venir sans lien actif fictif.','Rubrique active, défilement vertical, retour à la liste.')
cas('PP-002','Navigation','Conserver l’espace historique.','Lien Espace historique.','Depuis Personnel, ouvrir Espace historique puis revenir.',
    'Ancienne URL /cnss disponible ; aucune mutation ancienne après activation.','Ne pas utiliser ce lien pour contourner le nouveau circuit.',auto='test_879_reseau_interrompu_reessai_et_navigations')
cas('PP-003','Acces','Accorder les droits explicites.','Préparateur : identité, rémunération, identifiants sensibles, proposer, soumettre, historique. Validateur : identité, rémunération, identifiants sensibles, approuver, historique.',
    'Administrateur : Habilitations > Accorder un droit ; choisir compte, droit, motif RECETTE-FICTIVE879 ; confirmer pour chaque droit.',
    'Droits présents sans changer les rôles globaux ni créer une opération financière.','Vérifier compte par nom ET e-mail. Ne pas attribuer comptable à une personne qui ne doit pas accéder à la comptabilité.',ADMIN)
cas('PP-004','Acces','Activer volontairement la protection.','Motif : Activation de la société fictive879.','Lire les conséquences ; cocher la confirmation ; activer une seule fois.',
    'Protection activée ; anciens formulaires Personnel/absences/avances bloqués, nouvelles API sous habilitations.','Préparer au préalable deux comptes distincts ; aucune activation en production pendant la recette.',ADMIN)
cas('PP-005','Dossiers','Créer trois brouillons sans faux salaire.','Jeu P001/P002/P003 ci-dessous. Aucun salaire saisi à la création.','Créer un salarié ; saisir matricule/nom/poste ; ouvrir les informations facultatives. Compte utilisateur du salarié : Le salarié ne possède pas de compte ; cocher la confirmation. Référence du contrôle : ATTEST-P001 (puis P002/P003). Motif : Création fictive P001 (puis P002/P003). Créer le brouillon. Répéter trois fois.',
    'Trois brouillons, dernier créé en tête. Aucune rémunération approuvée ni paie créée.','Nom, matricule, coordonnées, données connues uniquement. Ne pas remplir un champ inconnu avec 0.')
cas('PP-006','Dossiers','Soumettre l’identité.','Demande initiale P001 ; motif : Identité P001 à contrôler.','Fiche > Consulter la demande > Préparer la soumission ; saisir motif ; Soumettre. Répéter pour P002/P003 avec leur référence.',
    'Demande Soumise ; dossier À valider.','Seul le préparateur soumet ; révision inchangée.')
cas('PP-007','Dossiers','Faire approuver par le second compte.','Référence : CTRL-P001-ID ; motif : Pièce fictive vérifiée.','Avec le validateur : Demandes à traiter ; consulter ; Approuver ; motif/référence ; confirmer indépendance ; confirmer. Répéter pour P002/P003.',
    'Identités Actives, révision 1 ; coordonnées appliquées. Contrat et salaire encore à confirmer.','ACTIF ne veut pas dire paie calculée ou payée.')
cas('PP-008','Dossiers','Contrôler recherche et filtres.','Recherche P002 puis statut Actif.','Rechercher par matricule et nom ; changer statut ; revenir Tous ; tester pagination si nécessaire.',
    'Résultats limités à la société et au filtre ; pas de ligne masquée par débordement global.','Le tri reste du plus récent au plus ancien.')
cas('PP-009','Dossiers','Reprendre une fiche historique sans la reclasser.','Fiche fictive ancienne préparée sur la copie avant protection : matricule HIST879 et salaire historique 10000.00 ; référence ATTEST-HIST879. Si aucune fiche n’existe, noter Bloqué (prérequis) sans modifier un dossier réel.','Reprendre une fiche existante ; sélectionner la fiche ; attester absence de compte ; référence ATTEST-HIST879 ; motif Reprise fictive HIST879 ; créer ; consulter et soumettre ; avec le validateur, rejeter : Complément fictif nécessaire, référence CTRL-HIST879.',
    'Nouvelle extension Brouillon ; ancienne racine et salaire conservés ; rémunération contractuelle non attestée.','Aucune conversion automatique du flottant ni date inventée.',ADMIN)
cas('PP-010','Dossiers','Reproposer après rejet.','Motif du rejet : Complément fictif nécessaire ; nouvelle proposition : Complément reçu.','Après rejet initial, préparer une nouvelle proposition Identité puis la soumettre et l’approuver.',
    'Ancien rejet conservé, nouvelle demande distincte, révision incrémentée.','Historique conservé ; aucun effacement du rejet.',ADMIN)
cas('PP-011','Conditions','Proposer les contrats connus.','P001/P002/P003 : CDI, début et effet 01/01/2026, pas de fin ; références CONTRAT-P001/P002/P003. Motif : Contrat fictif P001 (puis P002/P003).','Fiche > Proposer une modification > Contrat ; saisir dates et justificatif ; enregistrer ; soumettre avec le même motif ; faire approuver par le validateur (référence CTRL-P001-CONTRAT, puis P002/P003).',
    'Contrats approuvés ; révision 2 sur chaque dossier.','Dates à saisir explicitement ; aucune date comptable ou échéance utilisée comme remplacement.')
cas('PP-012','Conditions','Enregistrer trois salaires de base exacts.','P001 : 9000,10 ; P002 : 8000,00 ; P003 : 6000,00 MAD ; périodicité Mensuelle, effet 01/01/2026 ; références REM-P001/P002/P003. Motif : Base contractuelle fictive P001 (puis P002/P003).',
    'À la date de consultation 31/12/2026, proposer Rémunération sur le contrat approuvé ; enregistrer puis soumettre ; second compte approuve.',
    'Montants approuvés identiques ; révision 3. Total indépendant des bases :23000,10 MAD.','Ce total n’est ni net à payer ni coût employeur. Aucun IR, CNSS ou OD déduit de ce contrôle.')
cas('PP-013','Conditions','Proposer une hausse future sans remplacer le présent.','P001 : 9876,54 MAD au 01/01/2027 ; AVENANT-P001-2027 ; motif Hausse fictive P001.','Proposer la hausse à la révision 3 ; avant validation, consulter le 01/01/2027.',
    'Ancienne base 9000,10 encore applicable avant approbation.','Proposition visible séparément, aucun remplacement immédiat.')
cas('PP-014','Conditions','Approuver la hausse et comparer les dates.','Même demande, référence CTRL-P001-AVENANT.','Soumettre, second compte approuve ; consulter 31/12/2026 puis 01/01/2027.',
    '9000,10 puis9876,54 ; ancienne version conservée. Total indépendant de trois bases au 01/01/2027 :23876,54 MAD.','Changer la date de consultation, pas l’exercice comptable pour forcer un montant.')
cas('PP-015','Conditions','Sortir un salarié avec effet futur.','P001 sortie 30/06/2027 ; référence SORTIE-P001 ; motif Départ fictif.','Proposer Sortie puis soumettre et faire approuver ; consulter 29/06 et30/06/2027.',
    'Actif le 29, Sorti le 30 ; dossier conservé ; conditions non complètes pour paie à partir de la sortie.','Statut effectif à cette date, sans calcul des jours payés ou indemnités.')
cas('PP-016','Acces','Masquer les données sensibles.','Lecteur : identité seulement, puis historique si nécessaire.','Se connecter au compte lecteur ; consulter liste, fiche, demandes ; ajouter droit historique et consulter événements.',
    'Rémunération/CNSS/données fiscales masquées ; montants absents des détails/motifs non autorisés.','Ne pas confondre champ masqué et valeur0.',auto='test_879_identite_facultative_pas_de_fuite_ni_conversion')
cas('PP-017','Acces','Révoquer sans imposer une reconnexion.','Droit Consulter les rémunérations du préparateur.','Administrateur : révoquer avec motif ; sur la fiche ouverte : Actualiser.',
    'Montants masqués et aucune ancienne copie conservée dans le détail ouvert.','Le même compte et le même jeton servent au contrôle.')
cas('PP-018','Acces','Vérifier l’isolation de deux sociétés.','Sociétés fictives A/B ; brouillon local non enregistré dans A.','Annuler le formulaire local ; changer de société avec le sélecteur ; consulter Personnel.',
    'Aucun salarié, brouillon ou montant de A dans B ; droits relus pourB.','Ne pas transmettre le formulaire de A avec le jeton de B.',auto='test_879_changement_societe_ne_reprend_pas_donnees_ou_brouillon')
cas('PP-019','Navigation','Vérifier ordinateur et mobile.','Écrans 1440 px puis 390 px.','Ouvrir liste, fiche, modales de création/proposition/validation ; atteindre les boutons ; ouvrir/fermer le menu au clavier.',
    'Pas de débordement horizontal global ; modales défilables ; champs et actions accessibles.','Un tableau large peut défiler dans sa propre zone. L’appréciation ergonomique humaine reste à renseigner.')
cas('PP-020','Acces','Consulter la traçabilité.','P001 après les opérations précédentes.','Ouvrir Historique puis Propositions et décisions ; lire auteurs, dates, révisions et motifs autorisés.',
    'Création, demandes, soumissions, décisions présentes ; anciens montants et références consultables selon droits.','Noms affichés pour les comptes ; préparateur et décideur distingués.')
cas('PP-N01','Negatifs','Refuser le doublon de matricule.','Matricule P001 déjà existant, y compris espaces ASCII de bord.','Essayer de créer un autre salarié avec le même matricule dans A.',
    'Conflit lisible, aucun second dossier. Même matricule permis dans B.','02 et002 restent distincts.',auto='test_877_creation_trois_salaries_sans_fauxzero_et_sans_ecriture')
cas('PP-N02','Negatifs','Refuser l’auto-approbation.','Compte préparateur du dossier.','Après soumission, consulter la demande avec le préparateur.',
    'Pas d’approbation possible ; décision réservée à un autre compte habilité.','L’API refuse également l’auteur/bénéficiaire même administrateur.',auto='test_877_auteur_et_beneficiaire_refuses_memes_admin')
cas('PP-N03','Negatifs','Refuser les montants invalides.','Montant vide, négatif, non numérique ou 9000,101.','Essayer d’enregistrer une rémunération avec ces valeurs.',
    'Saisie refusée, aucune version erronée ni arrondi silencieux.','Erreur lisible ; aucune mention [object Object].',auto='test_877_proposition_monetaires_strictes')
cas('PP-N04','Negatifs','Conserver la première décision en concurrence.','Deux décisions sur la même demande ou modification concurrente du dossier.','Ouvrir deux sessions ; préparer une modification dans la première, faire décider une autre proposition dans la seconde, puis soumettre la première.',
    'Conflit de révision explicite ; aucun écrasement du dossier approuvé.','Recharger et préparer à nouveau ; ne pas contourner la révision.',auto='test_879_conflit_revision_visible_sans_ecraser_dossier')
cas('PP-N05','Negatifs','Refuser une condition contradictoire avec la sortie.','Après sortie P001 : 30/06/2027 : nouvelle rémunération 01/07/2027.',
    'Consulter après sortie ; vérifier absence de nouvelle modification normale ; API de proposition contradictoire refusée.',
    'Dossier sorti conservé ; aucune condition postérieure approuvée.','Une rectification doit faire l’objet d’un examen distinct.',auto='test_877_sortie_future_statut_a_date_et_historique')
cas('PP-N06','Negatifs','Récupérer après une panne réseau.','Interruption temporaire de la connexion au backend de test.','Ouvrir la liste pendant la panne ; rétablir le réseau ; Actualiser.',
    'Message de connexion indisponible puis données réellement rechargées.','Aucun faux succès et pas de nouvelle écriture.',auto='test_879_reseau_interrompu_reessai_et_navigations')
cas('PP-N07','Negatifs','Ne pas inventer un matricule historique.','Fiches historiques sans matricule ou avec doublons.','Ouvrir Reprendre une fiche existante ; observer les choix et messages.',
    'Fiches ambiguës signalées/bloquées, aucune fusion ni numéro inventé.','Les autres fiches/sociétés restent exploitables.',auto='test_879_options_scope_minimal_et_permissions')
cas('PP-N08','Negatifs','Clore une préparation dont le compte a été désactivé.','Préparateur distinct, demande soumise, compte ensuite désactivé par administrateur.','Avec un validateur indépendant : refuser l’approbation puis rejeter avec motif et référence.',
    'Approbation refusée ; rejet tracé possible, préparateur d’origine conservé.','Migration 108 ; aucune réattribution d’auteur.',auto='test_879_rejeter_preparation_compte_desactive_sans_transfert_auteur')
cas('PP-N09','Negatifs','Conserver le grand livre existant.','Une pièce fictive BQ déjà validée : 5141 débit 1000 / 1111 crédit 1000.','Noter pièce et lignes avant le parcours ; effectuer les opérations Personnel ; comparer ensuite.',
    'Même pièce, mêmes lignes et soldes ; aucune écriture issue de la gestion administrative.','Écriture fictive seulement, aucune donnée comptable réelle.',auto='test_877_ecriture_definitive_existante_conservee')


def generer():
    preuve=json.loads((R/'Test/PREUVE_PERSONNEL_PAIE_879.json').read_text(encoding='utf8'))
    assert all(x['statut']=='reussi' for x in preuve['resultats_distincts'])
    D.mkdir(exist_ok=True)
    jeu={'societe':'RECETTE PERSONNEL879 — FICTIF','ville':'Casablanca','devise':'MAD',
      'usage':'Copie isolée uniquement ;données fictives non déclarables.',
      'salaries':[{'matricule':f'P00{i}','nom':nom,'poste':'Poste fictif','email':f'personnel879.p{i}@example.com','telephone':f'TEL-FICTIF-P00{i}',
          'numero_cnss':f'FICTIF-NON-DECLARABLE-P00{i}','situation_familiale':sit,'nb_enfants':n,'personnes_charge_ir':n,
          'beneficiaire_sans_compte_confirme':True,'reference_beneficiaire':f'ATTEST-P00{i}','contrat':'CDI','date_debut':'2026-01-01','date_effet':'2026-01-01',
          'salaire_base':mt,'periodicite':'mensuelle'} for i,(nom,sit,n,mt) in enumerate([
              ('Salma FICTIVE','marie',2,'9000.10'),('Omar FICTIF','celiba',0,'8000.00'),('Nadia FICTIVE','divorce',1,'6000.00')],1)],
      'hausse_p001':{'date_effet':'2027-01-01','montant':'9876.54','reference':'AVENANT-P001-2027'},
      'sortie_p001':'2027-06-30','calculs_independants':{'somme_bases_initiales':format(sum(Decimal(x) for x in ['9000.10','8000.00','6000.00']),'.2f'),
      'somme_bases_apres_hausse':format(sum(Decimal(x) for x in ['9876.54','8000.00','6000.00']),'.2f')},'paie_definitive_autorisee':False}
    (D/'JEU_DONNEES_PERSONNEL_879.json').write_text(json.dumps(jeu,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_RECETTE_PERSONNEL_879.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    police='Helvetica'
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial879','C:/Windows/Fonts/arial.ttf'));police='Arial879'
    styles=getSampleStyleSheet()
    for st in styles.byName.values():st.fontName=police
    styles.add(ParagraphStyle('Texte879',fontName=police,fontSize=9,leading=13,spaceAfter=7))
    styles['Title'].fontSize=20;styles['Title'].leading=25;styles['Title'].textColor=colors.HexColor('#185FA5')
    def p(v,style='Texte879'):return Paragraph(escape(prose(v)).replace('\n','<br/>'),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),Spacer(1,12),p('Personnel / RH — Lot 1 — Livraison 879','Heading1'),
      p('Guide d’utilisation et de vérification sur copie de test. Version du 28 octobre 2026. Les captures sont issues de données fictives isolées ;leurs noms peuvent différer du jeu manuel.'),
      p('Développement du pilote Personnel : livré ; limites de déploiement détaillées en fin de document. Tests automatisés : '+str(preuve['nombre_distinct'])+' cas distincts réussis. Recette utilisateur : à effectuer. Prêt pour production : non validé.'),
      p('Périmètre :dossiers salariés,contrats,conditions de rémunération,propositions et décisions,historique,sorties,accès et navigation. Le calcul de paie,les virements,déclarations et rubriques À venir ne sont pas des fonctionnalités livrées ici.'),
      p('Préparer la copie','Heading1'),p('Installer les migrations 105 → 106 → 107 → 108 avec le rôle migrateur. Préparer une sauvegarde restaurable et deux comptes distincts autorisés. Aucune migration ni donnée réelle n’a été traitée pendant les tests décrits ici.'),
      p('Dans le pilote,les mutations sont réservées aux utilisateurs déjà légitimement administrateurs/comptables et explicitement habilités. Le profil Personnel seul reste une limite de déploiement ;ne pas donner des droits comptables à une personne qui ne doit pas les posséder.'),
      p('Ouvrir Personnel & Paie > 01 Personnel. L’administrateur prépare les droits dans Habilitations,puis active la protection volontairement. Le nouveau circuit bloque les anciens formulaires de mutation ;/cnss demeure accessible pour consultation selon droits.'),
      p('L’approbation doit venir d’un autre compte que le préparateur et le bénéficiaire lié. Les attestations sont des contrôles humains enregistrés ;aucune certification réglementaire ou vérification automatique de pièces n’est revendiquée.'),
      PageBreak(),p('Jeu de données exact','Heading1')]
    etiquettes={'matricule':'Matricule','nom':'Nom complet','poste':'Poste','email':'Adresse e-mail','telephone':'Téléphone',
      'numero_cnss':'Numéro CNSS (fictif)','situation_familiale':'Situation familiale','nb_enfants':'Nombre d’enfants',
      'personnes_charge_ir':'Personnes à charge IR confirmées','beneficiaire_sans_compte_confirme':'Absence de compte utilisateur confirmée',
      'reference_beneficiaire':'Référence du contrôle de rattachement','contrat':'Type de contrat','date_debut':'Début du contrat',
      'date_effet':'Date d’effet','salaire_base':'Base mensuelle en MAD','periodicite':'Périodicité'}
    def affiche(k,v):
        if k=='situation_familiale':return {'marie':'Marié(e)','celiba':'Célibataire','divorce':'Divorcé(e)'}[v]
        if k=='beneficiaire_sans_compte_confirme':return 'Oui — cocher la confirmation'
        if k=='periodicite':return 'Mensuelle'
        if k in ('date_debut','date_effet'):return '/'.join(reversed(v.split('-')))
        if k=='salaire_base':return v.replace('.',',')
        return v
    for index,sal in enumerate(jeu['salaries']):
        if index:story.append(PageBreak())
        story.append(p(sal['matricule']+' — '+sal['nom'],'Heading2'))
        story.append(Table([[p(etiquettes[k]),p(affiche(k,v))] for k,v in sal.items()],colWidths=[6*cm,10*cm],style=TableStyle([
          ('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f3f6fa')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#dddddd'))])))
    story.extend([p('Calcul indépendant :bases mensuelles initiales 23 000,10 MAD ;après hausse P001 : 23 876,54 MAD. Il ne s’agit ni d’un net à payer ni d’une liquidation fiscale.'),
      p('Les champs inconnus restent vides. Les références fictives ATTEST/CONTRAT/REM/CTRL servent seulement à cette recette. Les identifiants internes sont ceux retournés par l’application ;ne pas en inventer.'),PageBreak()])
    for c in CAS:
        story.append(p(c['id']+' — '+c['objectif'],'Heading2'))
        for label,key in [('Module','module'),('Prérequis','prerequis'),('Données à saisir','donnees'),('Actions dans l’interface','actions'),('Résultat attendu','attendu'),
                          ('Écritures attendues','ecritures'),('Impact fiscal','fiscalite'),('Contrôles','controle'),('Preuve attendue','preuve')]:
            story.append(p(label+' : '+c[key]))
        story.append(p('Statut recette humaine :Non testé. Résultat réel,anomalies et observations à renseigner dans le classeur Excel. Couverture automatique associée :'+c['automatisation']))
        story.append(Spacer(1,10))
    story.extend([PageBreak(),p('Repères visuels réels','Heading1')])
    for nom,label in [('879_1440_fiche.png','Fiche sur ordinateur'),('879_390_creation.png','Formulaire mobile,partie basse défilable')]:
        img=D/'preuves'/nom
        if img.exists():
            w,h=ImageReader(str(img)).getSize();largeur=16*cm if w>800 else 6*cm
            story.extend([p(label,'Heading2'),Image(str(img),width=largeur,height=largeur*h/w),Spacer(1,12)])
    story.extend([p('Limites à conserver','Heading1'),p('Les coordonnées bancaires/RIB et leurs règles de chiffrement ne sont pas collectés par ce périmètre. Les rectifications de matricule ou de lien bénéficiaire restent contrôlées et ne sont pas des modifications libres. Les données historiques ambiguës doivent être examinées sans réparation arbitraire.'),
      p('Les paramètres et calculs réglementaires de paie relèvent des lots suivants et exigent leurs sources officielles. Les informations fiscales personnelles sont des données déclarées ;leur saisie ne calcule aucun droit fiscal.'),
      p('En cas de conflit :annuler,recharger le dossier,puis préparer une nouvelle proposition. Un rejet ne supprime pas l’historique. Une préparation dont le compte est désactivé peut être rejetée après 108 ;son approbation demeure interdite.'),
      p('Détails techniques et preuves :Test/PREUVE_PERSONNEL_PAIE_879.json ;rapport de résultats 879. Le cahier de recette comptabilité/facturation déjà présent dans docs/recette reste distinct.')])
    def page(canvas,doc):
        canvas.setFont(police,8);canvas.setFillColor(colors.HexColor('#5a5955'));canvas.drawString(1.7*cm,1.2*cm,'HisabPro · Personnel · Recette sur données fictives');canvas.drawRightString(19.3*cm,1.2*cm,str(doc.page))
    pdf=D/'CAHIER_RECETTE_PERSONNEL_HISABPRO_879.pdf'
    SimpleDocTemplate(str(pdf),rightMargin=1.7*cm,leftMargin=1.7*cm,topMargin=1.7*cm,bottomMargin=1.8*cm,title='Cahier de recette Personnel — HisabPro').build(story,onFirstPage=page,onLaterPages=page)
    wb=Workbook();synth=wb.active;synth.title='Synthese';wb.calculation=CalcProperties(fullCalcOnLoad=True)
    headers=['ID','Module','Objectif','Prérequis','Données exactes','Actions UI','Résultat attendu','Écritures','Impact fiscal','Contrôles','Statut humain','Résultat réel','Anomalies','Observations','Preuve attendue','Preuve/capture','Couverture automatisée']
    lignes=[]
    for domaine in ['Navigation','Acces','Dossiers','Conditions','Negatifs']:
        ws=wb.create_sheet(domaine);ws.append(headers)
        for c in [x for x in CAS if x['module']==domaine]:
            ws.append([c[k] for k in ['id','module','objectif','prerequis','donnees','actions','attendu','ecritures','fiscalite','controle']]+['Non testé','','','',c['preuve'],'',c['automatisation']])
        ws.freeze_panes='D2';ws.auto_filter.ref=ws.dimensions
        dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');dv.errorTitle='Statut de recette';dv.error='Choisir un statut de la liste.';dv.showErrorMessage=True;ws.add_data_validation(dv);dv.add(f'K2:K{ws.max_row}')
        for i in range(1,18):ws.column_dimensions[chr(64+i)].width=15 if i in [1,2,11] else 35
        for row in ws:
            for cell in row:cell.alignment=Alignment(vertical='top',wrap_text=True)
        for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='185FA5')
        for n in range(2,ws.max_row+1):ws.row_dimensions[n].height=130
        for val,col in [('Réussi','EAF3DE'),('Échoué','FCEBEB'),('Bloqué','FAEEDA')]:
            ws.conditional_formatting.add(f'K2:K{ws.max_row}',FormulaRule(formula=[f'K2="{val}"'],fill=PatternFill('solid',fgColor=col)))
        lignes.append((domaine,ws.max_row))
    synth.append(['HISABPRO — PERSONNEL : RECETTE UTILISATEUR'])
    synth.append(['Les résultats humains restent à saisir ;les tests automatiques ne valent pas recette utilisateur.'])
    synth.append(['Tests automatisés exécutés',preuve['nombre_distinct']]);synth.append(['Production','Non validée'])
    synth.append(['Statut humain','Nombre'])
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:
        synth.append([statut,'='+'+'.join(f'COUNTIF(\'{nom}\'!K2:K{fin},"{statut}")' for nom,fin in lignes)])
    synth.append(['Nombre de cas',len(CAS)]);synth.append(['Progression humaine','=IFERROR(B7/B10,0)']);synth['B11'].number_format='0%'
    graphique=BarChart();graphique.title='Résultats de la recette humaine';graphique.y_axis.title='Nombre de cas';graphique.add_data(Reference(synth,min_col=2,min_row=5,max_row=9),titles_from_data=True);graphique.set_categories(Reference(synth,min_col=1,min_row=6,max_row=9));synth.add_chart(graphique,'A14')
    synth.column_dimensions['A'].width=85;synth.column_dimensions['B'].width=25;synth.freeze_panes='A6'
    for cell in synth[1]:cell.font=Font(bold=True,color='185FA5',size=14)
    jeu_ws=wb.create_sheet('Jeu_de_donnees');cles=list(jeu['salaries'][0]);jeu_ws.append([etiquettes[k] for k in cles])
    for sal in jeu['salaries']:jeu_ws.append([affiche(k,sal[k]) for k in cles])
    jeu_ws.freeze_panes='C2'
    for col in jeu_ws.columns:jeu_ws.column_dimensions[col[0].column_letter].width=25
    for cell in jeu_ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='185FA5')
    xlsx=D/'SUIVI_RECETTE_PERSONNEL_879.xlsx';wb.save(xlsx)
    relu=load_workbook(xlsx);assert sum(relu[n].max_row-1 for n,_ in lignes)==len(CAS)
    assert all(relu[n].cell(r,11).value=='Non testé' for n,_ in lignes for r in range(2,relu[n].max_row+1))
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages)
    assert all(c['id'] in texte for c in CAS) and 'FICTIVE' in texte and '\u25a0' not in texte
    print(json.dumps({'cas':len(CAS),'pdf_pages':len(PdfReader(pdf).pages),'feuilles':relu.sheetnames,'humain':'Tous Non testé','formules':'présentes,calcul à l’ouverture Excel'},ensure_ascii=False))

if __name__=='__main__':generer()
