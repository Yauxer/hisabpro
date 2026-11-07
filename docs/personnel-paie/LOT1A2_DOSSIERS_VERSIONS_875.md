# Personnel & Paie — Lot 1A.2 : dossiers et versions

Livraison 875 du 27 octobre 2026. Cette étape fournit les structures PostgreSQL, le contrat des valeurs monétaires et un diagnostic API. Elle ne fournit pas encore les API de création, soumission et approbation : elles relèvent du lot 1A.3. Les écrans et la sidebar relèvent du lot 1B.

## Ce qui change

- Migration additive `106_personnel_dossiers_versions.sql`, après 105. Aucun ancien fichier SQL n'est modifié. Elle ne s'exécute pas au démarrage de l'application.
- Extension des identités `employes` par `personnel_dossiers`, sans changer les anciennes colonnes ni créer une deuxième identité salarié.
- Structures de demandes, versions de contrats, versions de rémunération et événements. Les liens métier portent la société et le salarié ; aucun lien entre deux sociétés n'est admis.
- Montants des nouvelles rémunérations en `numeric(18,2)`. Le contrat Python accepte une chaîne décimale exacte, refuse les flottants, booléens, montants non finis, négatifs ou dépassant deux décimales. La sortie est une chaîne à deux décimales. Exemple : `"9000.10"`.
- Versions approuvées immuables ; contenu soumis figé ; décision indépendante du préparateur et du bénéficiaire lorsqu'il est relié à un utilisateur. Le circuit applicatif complet, ses capacités et le contrôle optimiste de révision restent à construire en 1A.3.
- Événements non modifiables et non supprimables. Les tables et vues nouvelles sont en lecture seule pour le rôle runtime `hisabpro`. Aucune permission applicative d'écriture n'est ouverte par cette livraison.
- Une suppression d'utilisateur référencé par le nouvel historique renvoie un conflit 409 ; sa désactivation reste possible. Un conflit de matricule lié renvoie également 409 depuis les anciens formulaires.

La migration ne crée aucune fiche, aucun contrat, aucune rémunération, aucune habilitation et aucune écriture comptable. Elle ne transforme pas `actif=True` en activation de paie. Les anciennes valeurs flottantes et les dates inconnues restent inchangées.

## Diagnostic disponible dès cette livraison

Avec une session administrateur de la société courante :

`GET /api/employes/securite/preflight-dossiers?limite=50`

Le diagnostic fonctionne avant l'installation de 105/106 sur un schéma historique reconnu. En mode Personnel protégé, les capacités `personnel.lire_identite` et `personnel.audit_lire` sont requises en plus du rôle administrateur et du module actif. Un utilisateur lecture ou comptable reçoit 403, même avec ces deux capacités.

Le résultat contient :

- nombre d'identités de la société courante, y compris archivées ;
- présence des cinq tables nouvelles, colonnes attendues, précision monétaire et clé unique composite de l'employé ;
- matricules manquants et groupes de collisions ;
- dates d'entrée inconnues, dates incohérentes ou non finies et salaires historiques invalides ;
- listes d'identifiants plafonnées par `limite`, de 1 à 100, avec totaux complets et indicateurs de troncature.

Il ne renvoie ni salaire historique, ni numéro CNSS, ni identité d'une autre société. La réponse porte `Cache-Control: no-store`. Aucun fichier de rapport contenant les données utilisateur n'est créé automatiquement.

`schema_versions` vaut `absent`, `partiel`, `incoherent` ou `installe`. Ce diagnostic structurel ne remplace pas la vérification des empreintes de migration, contraintes, privilèges et sauvegardes de l'environnement cible. `historique_atteste` et `activation_paie_autorisee` restent faux : un diagnostic sans collision n'est pas une approbation de paie.

Exemple de lecture : deux employés avec `002` et ` 002` forment une collision. Les références `02`, `002` et `2` restent différentes. Les espaces ASCII de bord sont retirés pour la clé ; la casse, les espaces internes, les espaces insécables et les zéros sont conservés. La normalisation Python et SQL est identique.

Un matricule absent ou ambigu empêche de rattacher cette identité à un nouveau dossier. Il ne bloque pas l'installation de la migration, les autres dossiers ou les autres sociétés. Aucun renommage, choix arbitraire ou fusion ne sont effectués. Les anciens employés sans extension conservent leur comportement historique ; les identités déjà liées sont protégées contre une collision ou un changement de clé par les anciens chemins.

## Périodes des versions

Une version approuvée est applicable à partir de `date_effet`, incluse, jusqu'à la date de la prochaine version approuvée, exclue. Les vues `personnel_remunerations_periodes` et `personnel_contrats_periodes` calculent cette borne avec `lead(date_effet)`. Une proposition non approuvée n'interrompt pas la version courante. Deux versions approuvées du même composant à la même date sont refusées par un index unique, y compris en concurrence.

Exemple synthétique utilisé dans les tests :

| Date de consultation | Salaire de base applicable |
|---|---:|
| 31/12/2026 | 9 000,10 MAD |
| 01/01/2027 | 9 876,54 MAD |

L'ajout de la deuxième version ne réécrit ni le montant ni la date d'effet de la première. La borne de fin calculée est une règle technique de versionnement, pas une date de sortie inventée. Les dates de début/fin du contrat sont des données déclarées distinctes ; la future lecture à date devra aussi les contrôler. Une rémunération approuvée doit déjà référencer un contrat approuvé compatible avec sa date d'effet.

Une correction rétroactive peut modifier la lecture actuelle d'une période ; elle devra être explicitement approuvée et contrôlée par 1A.3. Les futures campagnes devront figer leurs snapshots. Aucune paie définitive ou régularisation rétroactive n'est implémentée ici.

## Installation sur une copie autorisée

1. Vérifier les versions réellement installées et préparer une sauvegarde restaurable. Ne pas utiliser une base utilisateur pour les essais.
2. Déployer les fichiers Python et redémarrer le backend selon sa procédure habituelle. Le nouveau GET de diagnostic est alors disponible sans installation automatique.
3. Examiner le diagnostic de chaque société à reprendre. Conserver les anomalies pour décision humaine ; ne pas convertir ou corriger les données pour obtenir un rapport vert.
4. Avec le rôle migrateur, appliquer **105 puis 106** sur la copie. Le rôle runtime ne doit pas être propriétaire. 106 échoue transactionnellement si 105 est absent. Les tables historiques restent conservées.
5. Rejouer 106, relire le diagnostic et contrôler les données, contraintes et droits. Pour `hisabpro`, les nouvelles tables doivent être lisibles mais ni insérables, ni modifiables, ni supprimables, ni tronquables.
6. Ne pas ouvrir les privilèges de mutation pour contourner les refus : l'API contrôlée et ses tests restent la prochaine étape. L'activation volontaire de la protection suit le [guide 873](LOT1A1_HABILITATIONS_873.md) ; 106 ne l'active pas.

Les tests 875 installent et peuplent ces structures exclusivement sur des clusters natifs temporaires identifiés par nonce. Les versions approuvées utilisées pour contrôler les contraintes SQL sont synthétiques et insérées par le propriétaire de ces clusters ; elles ne constituent pas une API d'approbation livrée.

## Retour applicatif et limites

Conserver les nouvelles tables, les clés et les historiques. Ne pas supprimer 106 ni ses protections comme procédure de retour arrière. Un ancien backend doit être évalué sur copie : il ne doit pas contourner la protection ou transformer un refus SQL en erreur opaque. Une restauration de sauvegarde doit viser une autre cible contrôlée ; aucune restauration sur la source n'est automatique.

Cette étape ne collecte aucun RIB/CIN et ne tranche pas la politique de chiffrement/conservation. Aucun taux fiscal ou social nouveau n'est codé. Le lien bénéficiaire-utilisateur doit être établi par une procédure attestée avant les futures approbations ; une absence de lien ne prouve pas qu'un approbateur n'est pas bénéficiaire.

Développement de cette fondation distinct de : lot 1A complet, recette utilisateur, validation réglementaire et mise en production. Les API métier, leurs révisions, transitions, séparation des tâches, sorties et projections à date sont la prochaine sous-étape.
