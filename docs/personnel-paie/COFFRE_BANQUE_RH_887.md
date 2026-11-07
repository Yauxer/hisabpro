# Personnel / RH — coffre et banque, livraison 887

Le périmètre Personnel disponible comprend désormais les pièces privées et les coordonnées bancaires chiffrées. Il est prêt pour une recette sur copie isolée ; la recette utilisateur et la mise en production restent à valider. Aucun moteur de paie, virement ou calcul de cotisations n'est ajouté par cette livraison.

## Préparer la copie

Déployer le backend et le frontend actuels sur toutes les instances de recette et appliquer les migrations additives 111 puis 112 après les migrations Personnel antérieures. Ne pas modifier une ancienne migration exécutée. Les tests n'ont contacté aucune base PostgreSQL utilisateur ; ces migrations n'y ont pas été installées.

Suivre le chapitre technique du [cahier de recette](CAHIER_RECETTE_PERSONNEL_HISABPRO_887.pdf) pour créer un trousseau privé **hors dépôt et hors base**, avec `ops/personnel_coffre_cles.py initialiser`, et sa sauvegarde séparée. Définir `PERSONNEL_COFFRE_CLES_FICHIER` avec le chemin absolu du fichier privé. Aucun secret ne doit être envoyé à un tiers ni inclus dans les ZIPs métier. Vérifier les ACL Windows avec l'opérateur d'exploitation ; le programme ne certifie pas ces ACL.

L'administrateur déclare dans **Personnel > Habilitations > Coffre RH** les références approuvées de garde, conservation et sauvegarde/rotation. La déclaration est une attestation humaine, sans durée légale inventée. Avant clés, déclaration, protection et capacités requises, la collecte reste fermée. Les comptes Personnel seuls conservent leur périmètre limité.

## Utiliser les pièces privées

Dans la fiche du salarié, ouvrir **Banque et pièces privées**. Déposer un PDF, PNG ou JPEG de 4 Mio maximum. Le téléchargement est privé, contrôlé par les droits et audité. Le contenu original est restitué exactement ; son nom original n'est pas conservé. Aucun logo n'est ajouté à une pièce justificative originale reçue. Le contrôle de signature/type ne constitue pas un antivirus.

Le préparateur autorisé peut proposer une banque avec date d'effet, coordonnées complètes, référence et motif ; une pièce interne peut être liée. Les coordonnées complètes restent chiffrées : listes, historique et projection courante affichent un masque. Leur lecture explicite nécessite les capacités sensibles et laisse un événement d'audit.

Le préparateur soumet sa demande. Un autre utilisateur autorisé ouvre la décision, consulte explicitement les coordonnées privées, télécharge le justificatif associé si présent, vérifie les pièces et coche sa confirmation bancaire avant approbation. Le serveur contrôle la consultation par le décideur, la confirmation, la séparation des acteurs et la révision. Le téléchargement du justificatif n'est pas attesté automatiquement comme une vérification humaine.

Une approbation future ne remplace la banque courante qu'à sa date d'effet. Aucune écriture comptable ni paiement n'est généré. Une nouvelle banque passe par une nouvelle version approuvée ; les versions et les pièces restent traçables.

## Faire la recette

Le [PDF](CAHIER_RECETTE_PERSONNEL_HISABPRO_887.pdf) et le [classeur Excel](SUIVI_RECETTE_PERSONNEL_887.xlsx) consolident **59 cas**, dont 16 pour le coffre. Tous les statuts humains sont « Non testé ». Le jeu est dans [JEU_DONNEES_PERSONNEL_887.json](JEU_DONNEES_PERSONNEL_887.json) et [jeu887](jeu887/DONNEES_COFFRE_FICTIVES.json). Les justificatifs et coordonnées sont entièrement fictifs, impropres à tout paiement. Un fichier de mauvais type et un fichier dépassant la limite sont fournis pour les refus attendus.

## Sauvegarde, rotation et limites

La restauration testée utilise `pg_dump` puis `pg_restore` vers une deuxième base temporaire : 85 tables, données, schéma, séquences et droits contrôlés. Les pièces et coordonnées bancaires sont restituées avec le trousseau sauvegardé séparément ; elles sont refusées sans clé, puis relisibles après récupération. Cela ne valide pas une infrastructure réelle ou sa sauvegarde distante.

La commande `rotation` sauvegarde le trousseau avant activation et conserve les anciennes clés. Elle change la clé des **nouvelles écritures chiffrées** ; elle ne réchiffre pas les objets historiques. Distribuer les clés nécessaires sur toutes les instances avant activation. Ne pas retirer une ancienne clé encore utilisée. Aucun effacement automatique, réchiffrement historique, procédure de révocation globale ou antivirus intégré n'est livré. Ces opérations exigent une procédure distincte et contrôlée.

L'application ne vérifie pas en ligne la titularité ni la validité bancaire d'un RIB/IBAN. Les données fictives de recette ne présument aucun format bancaire marocain obligatoire. Aucun taux social ou fiscal nouveau n'est introduit et aucune certification officielle n'est revendiquée.

Prochaine étape : recette du Personnel livré et configuration d'exploitation sur copie, puis lots de paie du cahier des charges, avec vérification officielle préalable des règles à implémenter.
