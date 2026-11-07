# Lot 557 — Réouverture administrative des périodes

L'implémentation existante couvre la réouverture d'une période d'un exercice
non définitivement clôturé. Aucun nouveau mécanisme de réouverture annuelle
n'a été ajouté. La qualification CPT-11 peut passer à « terminé » dans ce
périmètre précis ; recette utilisateur et mise en production restent distinctes.

## Tests natifs réellement exécutés

Six scénarios : **6 réussis, 29 avertissements, 42,79 s**.

- L'administrateur ferme janvier puis le rouvre : saisie refusée pendant la
  fermeture, permise après réouverture ; une écriture déjà validée reste intacte
  et non modifiable. Un nouveau brouillon empêche la fermeture du mois.
- Comptable et Consultation seule : réouverture individuelle ou globale
  refusée 403, sans modification du calendrier ou des écritures.
- Deux changements de statut correctement historisés avec acteur et motif.
  L'audit append-only ne peut pas être modifié par le rôle SQL applicatif.
- Après clôture annuelle réelle, réouverture individuelle/globale refusée 423.
  Une tentative SQL sous LOGIN applicatif est aussi refusée par le trigger.
  Les pièces antérieures, la clôture et les à-nouveaux sont préservés.
- Une autre société reste indépendante et peut ouvrir ses propres périodes.
- Edge390 : fermeture puis réouverture par l'administrateur, rafraîchissement
  immédiat et état conservé après rechargement. Lecteur : commandes désactivées.

La CM 3 000 MAD du laboratoire existant explique le résultat de clôture -3 000.
Ce jeu fictif ne constitue pas la qualification d'un régime fiscal réel.

## Consolidation et lisibilité mobile

Une seule application PostgreSQL nonce098 exécute les sept modèles d'inventaire,
les refus sans mutation, les aperçus et ces scénarios de calendrier :
**37 réussis, 29 avertissements, 86,78 s, code 0**.
Les suites se recouvrent : ne pas additionner les résultats pour compter des
fonctionnalités. Aucun mock métier, aucune connexion à la base utilisateur.

L'aperçu mobile de555 a aussi été ajusté : largeur des trois colonnes fixée,
intitulés pouvant revenir à la ligne, montants espacés. Les deux montants sont
lisibles à390px sans déplacement horizontal pour le cas testé1 200,13 MAD.
Assertion de largeur et capture finale inspectée. Les grands montants gardent
un conteneur à défilement si nécessaire.

Build Vite : **réussi en6,35 s**, avertissement de taille conservé.
Aucune migration ou donnée existante modifiée. RH/paie restent différées.

Prochaine étape : qualification fiscale sur la copie officielle CGI2026 TGR,
puis développement indépendant des formats déclaratifs encore indisponibles.
