# Personnel / RH883 — régimes déclarés et limites restantes

## Utilisation

Dans **Créer un salarié → Coordonnées et informations personnelles**, renseigner éventuellement la **Date d’entrée connue**. La valeur est proposée puis appliquée après approbation ; une date inconnue reste vide. Elle n’est jamais copiée du début du contrat ou de la date de création. Sur une reprise historique, la date déjà connue reste conservée.

Dans la fiche, sélectionner d’abord **Consulter les conditions au**, puis **Proposer une modification → Contrat**. Avec la capacité **Consulter les identifiants sensibles**, renseigner les noms attestés des régimes AMO, retraite et mutuelle. Aucun de ces trois champs n’est obligatoire ; ne saisir ni numéro bancaire ni donnée médicale.

Les valeurs font partie de la version du contrat : proposition, soumission et décision indépendante, référence du justificatif et motif. Elles apparaissent dans la fiche à leur date d’effet après approbation. Les versions précédentes restent conservées. Une affiliation, un taux, une exonération ou un droit n’est jamais calculé à partir du texte saisi.

Les valeurs connues omises dans une nouvelle proposition sont reprises uniquement depuis un contrat **applicable à la date d’effet proposée**. Un contrat expiré ne permet pas de présumer celles du suivant. Effacer explicitement une valeur connue produit une valeur à confirmer, sans inventer une non-affiliation. Les champs affichés dans le formulaire sont à contrôler avant soumission.

Un lecteur sans capacité sensible ne récupère ni les libellés ni les motifs/références pouvant les divulguer dans les demandes et l’historique. Les préparateurs/décideurs doivent conserver cette capacité pour traiter un contrat qui contient ces valeurs ; une omission ne permet pas de les effacer silencieusement.

## Cohérence avec la rémunération

Une rémunération approuvée est liée à une version de contrat. Le nouveau contrat ne reprend pas automatiquement un salaire. Si des rémunérations déjà approuvées à partir de sa date seraient détachées, la proposition/décision est refusée avec409 ; leur régularisation demande un examen distinct. **Ne pas déplacer artificiellement la date du contrat pour contourner ce contrôle.**

En l’absence de ce conflit, une nouvelle version de contrat demande ensuite ses conditions de rémunération explicitement approuvées. Une valeur non attestée reste **À confirmer**. Le circuit ne génère aucune écriture comptable, paie ou dette du seul fait de l’administration du dossier.

## Installation

Après105–109, déployer le code883 sur **toutes les instances** puis appliquer110 avec le rôle migrateur. Tant que110 manque, les flux anciens sans régime restent utilisables ; une nouvelle saisie de régime répond503 et toute la transaction est annulée. Suspendre les écritures Personnel le temps du déploiement.

110 ajoute trois colonnes nullables et une contrainte de texte non vide quand renseigné. Aucune donnée existante n’est renseignée par défaut ; les vues existantes restent intactes. Le trigger d’immuabilité existant couvre les colonnes nouvelles par comparaison JSON. Les anciennes migrations ne sont pas réécrites.

Ne pas revenir à un ancien backend qui ignore les régimes après leur utilisation : il pourrait créer une version de contrat incomplète. Garder le code compatible ou suspendre les mutations Personnel sous contrôle administratif. Conserver également le confinement du rôle `personnel` introduit par881.

## État exact du Lot1

| Élément | État |
|---|---|
| Dossiers, coordonnées, date connue, contrats/salaires, approbation, historique, sortie | Terminé sur le périmètre disponible |
| Interface ordinateur/mobile, capacités et profil exclusivement Personnel | Terminé, tests isolés exécutés |
| Déclaration des régimes AMO/retraite/mutuelle | Terminée, aucun calcul réglementaire introduit |
| RIB/bancaire et pièces sécurisées | Bloqué pour collecte : cadrageD05 restant |
| Recette utilisateur | À effectuer sur copie ;aucun statut réussi prérempli |
| Production, déploiement et réglementation de paie | Non validés |

Le Lot1 intégral du master reste donc **partiel**. Les absences utiles à la paie relèvent des variables des lots suivants ; un SIRH étendu ne fait pas partie du master.

## BlocageD05 à résoudre

Le [Lot0](LOT0_CONCEPTION.md) demande : **« Hébergement des clés, chiffrement, rotation et durée de conservation des données/pièces de paie. »** L’échéance est **« avant collecte des coordonnées sensibles »**. Le dépôt ne contient pas de décision arrêtée pour ces paramètres ; l’environnement Windows de développement ne prouve pas l’hébergement de production.

Il faut arrêter le lieu de garde des clés, leur accès et sauvegarde séparée, la rotation/restauration, ainsi que la politique de conservation des pièces et son responsable. La cible recommandée à examiner est une gestion des clés hors des tables et archives métier, avec identifiant de version, restauration testée et refus de collecte en l’absence de configuration ;aucun repli en clair.

La future collecte devra protéger les pièces par société/salarié, vérifier type/taille, refuser les URL publiques et masquer les secrets dans les logs, propositions et exports. Aucun fichier sensible réel ni clé de production n’a été créé pendant cette session. Aucune durée légale de conservation n’a été inventée. Le développement indépendant disponible est livré ;cette décision conditionne la fin de la collecte sécurisée du Lot1 avant de poursuivre son usage réel.
