"""Données et cas RH fictifs ;aucune clé ni connexion de production."""
from pathlib import Path
from html import escape
import hashlib,json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm

R=Path(__file__).resolve().parents[1];D=R/'docs/personnel-paie';J=D/'jeu887'
RIB_A='FICTIF-COORDONNEES-P004-1122';RIB_B='FICTIF-COORDONNEES-P004-3344'

PLAN_EXPLOITATION=[
 'Environnement de recette :copie isolée déjà préparée par l’administrateur,code887 et migrations105 à112. Le backend de recette doit pointer explicitement vers cette copie ;ne pas effectuer ces essais sur lePostgreSQL réel. Aucune connexion ni clé de production n’a été utilisée par les tests fournis.',
 'Windows,exemple de chemins de RECETTE hors dépôt :%LOCALAPPDATA%\\HisabProRecetteRH\\actif\\cles.json et%LOCALAPPDATA%\\HisabProRecetteRH\\sauvegarde\\cles-v1.json. Préparer les deux répertoires privés et vérifier leursACL. En production,le service et les opérateurs doivent seuls accéder aux clés ;prévoir une sauvegarde indépendante réellement restaurable.',
 'Depuis la racine du dépôt,avec lePython du backend :python ops/personnel_coffre_cles.py initialiser --fichier "<chemin-actif-absolu>" --identifiant recette-k1 --sauvegarde "<chemin-sauvegarde-v1-absolu>". Remplacer les deux chemins par ceux du paragraphe précédent. L’outil refuse un fichier existant et n’affiche pas les clés.',
 'Dans la configuration du processus backend de RECETTE,définir PERSONNEL_COFFRE_CLES_FICHIER avec le chemin actif absolu,puis démarrer/reprendre ce serveur de copie. Cette variable contient un chemin,aucune clé. Le fichier de clés reste hors des ZIP et des dumps métier. Ne pas envoyer son contenu àCodex ou à un tiers.',
 'Administrateur >Personnel >Habilitations >Coffre RH :références GARDE-RECETTE-RH887,CONSERVATION-RECETTE-RH887,SAUVEGARDE-ROTATION-RECETTE-RH887 ;motif Déclaration fictive de recette887. La confirmation atteste vos procédures ;elle ne les valide pas automatiquement. Pour un usage réel,utiliser les vraies références approuvées,aucune durée légale n’est présumée.',
 'Rotation des nouvelles écritures :python ops/personnel_coffre_cles.py rotation --fichier "<chemin-actif-absolu>" --identifiant recette-k2 --sauvegarde "<chemin-sauvegarde-v2-neuf-absolu>". Conserver les anciennes clés et sauvegardes ;cette opération ne réchiffre pas les objets historiques. Sur plusieurs instances,distribuer les clés requises à toutes avant activation ou utiliser le trousseau privé partagé selon l’architecture validée.',
 'La perte de clé doit être traitée par restauration depuis la sauvegarde séparée. Les tests887 ont réellement restauré85tables dans une deuxième base temporaire,avecACL et restitution des pièces/banque,puis vérifié le refus sans clé et la récupération après restauration de clé. Aucune restauration réelle n’a été faite chez l’utilisateur.',
 'Limites à conserver :pas de vérification bancaire en ligne ni de validité bancaire des chaînes fictives,pas d’antivirus intégré,pas de paiement automatique,de réchiffrement historique ou de purge automatique. La conservation/effacement doit suivre la politique réelle et une procédure contrôlée. La recette humaine et la production restent à valider.'
]

CAS_COFFRE=[
 ('PP-COF01','Vérifier la fermeture avant configuration','Copie isolée,code887,migrations111/112 ;administrateur.',
  'Aucune clé configurée,aucune politique déclarée pour la société de recette.',
  'Personnel >Habilitations,lire Coffre RH ;ouvrir P004 avec un compte sensible et consulter Banque et pièces privées.',
  'Collecte fermée,aucun dépôt ni banque active par défaut. Aucun droit supplémentaire accordé.'),
 ('PP-COF02','Préparer les clés privées et leur sauvegarde','Opérateur de la copie ;répertoires hors dépôt avec accès privé.',
  'Deux chemins absolus du mode d’emploi ci-dessus ;clé nommée recette-k1 ;sauvegarde neuve cles-v1.json.',
  'Exécuter l’utilitaire initialiser avec ces chemins ;configurer PERSONNEL_COFFRE_CLES_FICHIER sur le serveur de copie ;recharger Habilitations.',
  'Clés Configurées ;aucun secret affiché ou placé dans la base/ZIP. Sans déclaration de politique,collecte encore fermée.'),
 ('PP-COF03','Déclarer les procédures avant collecte','Clés de recette configurées ;administrateur.',
  'Garde GARDE-RECETTE-RH887 ;conservation CONSERVATION-RECETTE-RH887 ;rotation/sauvegarde SAUVEGARDE-ROTATION-RECETTE-RH887 ;motif Déclaration fictive de recette887.',
  'Déclarer la politique du coffre ;saisir les trois références et motif ;cocher la confirmation,puis Enregistrer la déclaration.',
  'Déclaration historisée avec auteur/date. Collecte autorisée seulement si protection,module et capacités sont aussi prêts.'),
 ('PP-COF04','Habiliter sans rôle comptable','Administrateur ;préparateur,validateur et lecteur du scénario initial.',
  'Préparateur/validateur :identité,identifiants sensibles,proposer/soumettre ouapprouver,historique. Lecteur :identité/historique seulement.',
  'Réaccorder le droit sensible révoqué par PP-SOC04 si nécessaire. Garder les rôles Personnel seul ;ouvrir la ficheP004.',
  'Préparateur peut déposer/proposer ;validateur peut consulter/contrôler ;lecteur ne récupère pas les pièces/coordonnées. Aucun accès comptable ajouté.'),
 ('PP-COF05','Déposer et retrouver une pièce intacte','P004 identité approuvée,coffre configuré,préparateur sensible.',
  'jeu887/Justificatif_FICTIF_P004_A.pdf ;catégorie Justificatif bancaire.',
  'P004 >Déposer une pièce privée ;choisir catégorie/fichier ;Chiffrer et déposer ;noter l’identifiant réel affiché. Télécharger cette pièce et l’ouvrir sur la copie.',
  'Pièce visible sansF5,téléchargement piece-personnel-ID.pdf,contenu identique au fichier source. Nom original absent des listes. Déposée ne signifie pas justificatif approuvé.'),
 ('PP-COF06','Proposer la banque sans l’activer','P004 Actif,pièceA déposée ;préparateur.',
  'Effet01/01/2026 ;RIB '+RIB_A+' ;banque Banque FICTIVE de recette ;titulaire Hassan FICTIF883 ;référence REF-RIB-P004-A ;motif Premières coordonnées fictives P004 ;pièceA réelle.',
  'Proposer des coordonnées bancaires,saisir ces valeurs et choisir la pièce par son identifiant retourné ;enregistrer. Ouvrir la demande et la soumettre.',
  'Proposition puis Soumise ;coordonnées approuvées encore À renseigner. Pas de virement,de dette ou d’écriture. Valeur brute absente des listes et demandes par défaut.'),
 ('PP-COF07','Contrôler avec une autre personne','Validateur indépendant sensible ;demandeP004 soumise.',
  'Motif Contrôle fictif P004-A ;référence CTRL-RIB-P004-A ;les deux confirmations manuelles.',
  'Demandes à traiter >Consulter ;Consulter les coordonnées proposées ;Télécharger le justificatif associé ;comparer le texte fictif. Approuver,remplir motif/référence et cocher contrôle bancaire et indépendance ;confirmer.',
  'Consultations tracées,décision par une autre personne et version approuvée. Aucun contrôle du contenu bancaire n’est prétendu automatique.'),
 ('PP-COF08','Consulter puis masquer les valeurs','P004 première banque approuvée ;compte sensible.',
  'Consultation31/12/2026 ;masque attendu ••••1122 ;valeur complète '+RIB_A+'.',
  'Actualiser la fiche ;Consulter les coordonnées approuvées ;vérifier banque/titulaire ;Masquer les coordonnées.',
  'Masque en affichage normal,valeur complète seulement sur action autorisée,puis masquée. Aucun stockage de cette valeur dans localStorage/sessionStorage.'),
 ('PP-COF09','Conserver la banque actuelle avant effet futur','P004 première banque approuvée,aucune sortie contradictoire.',
  'Déposer Justificatif_FICTIF_P004_B.pdf. Nouvelle banque effet01/01/2027,RIB '+RIB_B+' ;même banque/titulaire ;REF-RIB-P004-B ;motif Évolution fictive P004 ;nouvelle pièceB.',
  'Proposer,soumettre et faire approuver avec le second compte et CTRL-RIB-P004-B ;consulter31/12/2026 puis01/01/2027.',
  'Masques1122 puis3344 ;ancienne version conservée,aucun écrasement ni changement de salaire. L’historique est consultable sous droits.'),
 ('PP-COF10','Refuser une copie des coordonnées dans le motif','Préparateur sensible,P004 Actif.',
  'Nouvelle proposition effet01/01/2028,RIB FICTIF-COORDONNEES-P004-5566 ;mettre aussi exactement cette chaîne dans le motif.',
  'Tenter l’enregistrement ;lire le refus,puis annuler la modal. Essayer aussi une valeur masquée ••••1122 comme RIB.',
  'Copie dans motif/refusée et masque refusé ;aucune demande ni valeur bancaire erronée enregistrée. Aucune réémission du secret dans une erreur de validation.'),
 ('PP-COF11','Refuser type trompeur et taille excessive','Préparateur sensible ;coffre ouvert.',
  'jeu887/Type_refuse_FICTIF.pdf,puis jeu887/Trop_grand_FICTIF.pdf (4Mio+1octet).',
  'Tenter de déposer successivement les deux fichiers ;constater les messages ;annuler après chaque essai.',
  'Type contrôlé par contenu malgré extensionPDF ;taille refusée. Aucune nouvelle pièce dans la liste. La limite serveur est également testée automatiquement.'),
 ('PP-COF12','Révoquer et contrôler l’isolation','Administrateur distinct et lecteur Personnel sans capacité sensible.',
  'Droit identifiants sensibles du préparateur ;motif Fin accès privé recette887. DossiersP004/P005 et sociétéB de recette.',
  'Révoquer ;préparateur Actualiser ;vérifier masques et commandes privées absentes. Ouvrir P005 puis sociétéB avec les comptes autorisés ;contrôler les pièces visibles.',
  'Aucune pièce/coordonnée deP004 dans un autre dossier/société ;pas d’auto-approbation sensible. Accès refusé aussi côté serveur ;aucun droit financier implicite.'),
 ('PP-COF13','Récupérer après indisponibilité des clés','Opérateur de la copie ;sauvegarde séparée vérifiée ;aucune manipulation production.',
  'Variable PERSONNEL_COFFRE_CLES_FICHIER temporairement dirigée vers un fichier inexistant sur le seul serveur de copie.',
  'Arrêter le serveur de copie,changer cette variable,puis le reprendre :collecte/restitution refusées. Restaurer le chemin original ou la sauvegarde de clés vérifiée,puis reprendre le serveur. Ne supprimer aucune clé pour ce test.',
  'Refus propre sans contenu privé ;anciennes pièces et banque lisibles après récupération. La base métier seule ne remplace pas les clés.'),
 ('PP-COF14','Faire tourner la clé active avec sauvegarde préalable','Opérateur de recette ;trousseau initial et clés anciennes conservés.',
  'Identifiant recette-k2 ;nouveau chemin de sauvegarde cles-v2.json ;voir commande rotation du mode d’emploi.',
  'Exécuter rotation ;déposer une nouvelle pièce ;vérifier ancien et nouveau téléchargements. Réaccorder la capacité sensible de recette si elle a été révoquée.',
  'Nouvelle clé active,anciennes clés conservées,sauvegarde créée avant activation. Objets existants lisibles. Aucun réchiffrement historique n’est revendiqué.'),
 ('PP-COF15','Restaurer le dossier avec les clés séparées','Technicien et deux environnements temporaires isolés ;jamais la base réelle.',
  'Archive métier de la copie,clé sauvegardée séparément,rôles runtime restreints,pièceA etRIB '+RIB_A+'.',
  'Suivre la procédure d’exploitation validée sur cible vierge isolée ;restaurer schéma/données/ACL,puis les clés ;contrôler pièces/banque et écritures avant/après. Consigner les preuves. Sans environnement technicien,noter Bloqué (prérequis).',
  'Contenus identiques,droits conservés,absence de clés dans dump métier. L’autotest natif887 a réellement vérifié ce parcours sur85tables ;la recette humaine n’est pas prévalidée.'),
 ('PP-COF16','Contrôler la séparation avec la comptabilité','Administrateur/comptable légitime de la copie ;pièce fictive de PP-N09.',
  'Même écriture fictive BQ :5141 débit1000 /1111 crédit1000,et mêmes salaires contractuels connus.',
  'Comparer journal,lignes et soldes aux preuves avant les opérationsCOF ;vérifier historique du dossier et auteurs des décisions.',
  'Aucune écriture ni paiement créé par le coffre ou une approbation bancaire. Les opérations financières des lots suivants restent distinctes.')
]

def preparer_pieces():
    J.mkdir(exist_ok=True);styles=getSampleStyleSheet();info={}
    for code,rib in [('A',RIB_A),('B',RIB_B)]:
        p=J/f'Justificatif_FICTIF_P004_{code}.pdf'
        histoire=[Paragraph('RECETTE HISABPRO — DOCUMENT FICTIF',styles['Title']),Spacer(1,20),
          Paragraph('Justificatif simulé du coffre RH. Cette pièce ne provient d’aucune banque et ne peut pas être utilisée pour un paiement.',styles['BodyText']),Spacer(1,16),
          Table([['Salarié','P004 — Hassan FICTIF883'],['Établissement','Banque FICTIVE de recette'],['Coordonnées de test',rib],['Date d’effet','01/01/2026' if code=='A' else '01/01/2027']],colWidths=[5*cm,12*cm],style=TableStyle([('GRID',(0,0),(-1,-1),.5,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP')])),Spacer(1,20),
          Paragraph('Données entièrement fictives,non déclarables. La chaîne FICTIF sert au test technique et ne représente pas un RIB ou IBAN utilisable.',styles['BodyText'])]
        SimpleDocTemplate(str(p),title='Justificatif fictif coffre RH').build(histoire)
        info[code]={'fichier':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rib_iban_fictif':rib,'titulaire':'Hassan FICTIF883','banque':'Banque FICTIVE de recette','date_effet':'2026-01-01' if code=='A' else '2027-01-01'}
    (J/'Type_refuse_FICTIF.pdf').write_bytes(b'FICHIER FICTIF DE RECETTE :absence de signature PDF.\n')
    (J/'Trop_grand_FICTIF.pdf').write_bytes(b'%PDF-FICTIF\n'+b'X'*(4194305-len(b'%PDF-FICTIF\n')))
    (J/'DONNEES_COFFRE_FICTIVES.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
    return info

if __name__=='__main__':preparer_pieces();print('Pièces de recette fictives préparées ;aucune clé créée.')
