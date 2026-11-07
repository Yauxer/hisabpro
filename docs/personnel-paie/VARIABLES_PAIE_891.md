# Paie — variables mensuelles, livraison 891

La rubrique **02 · Éléments de paie > Variables mensuelles** permet de préparer, soumettre et approuver des montants rattachés à un salarié et à une période. Elle utilise les contrats, rémunérations et versions de rubriques déjà approuvés. Elle ne produit pas encore de bulletin, de cotisation, d'IR, de net à payer ou d'écriture comptable.

## Installation et accès

Sur une copie isolée disposant du code889 et de la migration113, appliquer la migration additive `114_paie_variables.sql` avec le rôle migrateur, puis déployer le frontend et les backends actuels. Aucun taux, période, salarié ou montant n'est créé automatiquement. Les tests n'ont utilisé aucune base PostgreSQL utilisateur.

Les capacités identité et rémunération sont requises pour les consultations. Le préparateur utilise **Créer et proposer** pour saisir/annuler un brouillon, puis **Soumettre ses demandes**. Le décideur utilise **Approuver ou rejeter**. L'approbateur doit être indépendant du préparateur et du bénéficiaire, même s'il est administrateur. Le droit réglementaire dédié du catalogue ne remplace pas cette indépendance et n'est pas nécessaire pour simplement attester une variable : les règles non qualifiées restent non qualifiées.

L'historique et les références de sources/justificatifs sont réservés au préparateur, à l'approbateur ou à une personne habilitée à l'audit. Un lecteur de rémunération sans ces droits voit le montant, mais pas ces motifs et références. La révocation des droits et les changements de société sont contrôlés par le serveur.

## Saisir

Ouvrir **Variables mensuelles**, choisir le mois puis **Saisir une variable**. Renseigner séparément la période et la date d'effet réelle, dans ce mois. La date n'est pas déduite d'une échéance comptable.

Les listes récupèrent les conditions à cette date ; rechercher le salarié et le code de rubrique, puis cliquer **Rechercher les conditions applicables** si nécessaire. Chaque liste est limitée à30 résultats : affiner la recherche pour retrouver une valeur au-delà. Les dossiers sans contrat/rémunération approuvés ne sont pas sélectionnables ; le backend refuse aussi la saisie directe. Aucun salaire historique manquant n'est remplacé par zéro.

Choisir le salarié et une rubrique approuvée applicable. Le mode de saisie vient de cette version de rubrique :

- **Montant exact** : saisir une valeur positive ou nulle avec deux décimales maximum, par exemple `800.01`.
- **Quantité × taux** : saisir les deux valeurs exactes en texte, au plus six décimales. Le produit est arrondi **une fois à la ligne**, au centime, avec `ROUND_HALF_UP` : `3 × 0.335 = 1.005`, soit `1.01 MAD`. Cette politique technique ne prétend pas être une règle légale universelle de paie.

Les valeurs NaN/non finies, négatives, flottantes JSON ou ambiguës sont refusées. Une retenue est saisie positivement dans une rubrique de nature Retenue ; aucun signe négatif ne doit servir à contourner la qualification de la rubrique. L'impact sur le brut et le net sera déterminé par les moteurs ultérieurs.

Renseigner une référence pour chaque type de justificatif attendu et une référence de source stable. Les références sont déclarées : leur présence n'atteste pas automatiquement l'existence ou la validité d'une pièce externe. Le décideur doit contrôler les documents correspondants. Enregistrer crée un **Brouillon**, sans dette ni écriture.

## Contrôler les doublons et cumuls

Un élément mensuel ne peut apparaître qu'une fois par salarié/mois/rubrique parmi les brouillons, soumis et approuvés. Un élément annuel ne peut apparaître qu'une fois par salarié/année/rubrique. Un élément ponctuel peut apparaître plusieurs fois, avec des références de sources distinctes ; une même source ne peut pas être dupliquée dans le mois.

Une incompatibilité déclarée dans l'une des deux rubriques empêche leur coexistence pour le même salarié et le même mois, dans les deux sens. Les demandes rejetées ou brouillons annulés ne bloquent plus une correction, tout en restant dans l'historique.

## Soumettre et décider

Le préparateur consulte la variable, puis **Soumettre la variable ID**, avec motif. Il ne peut ni soumettre le brouillon d'une autre personne ni approuver sa propre variable. Une autre personne autorisée consulte le détail, les sources et justificatifs, puis approuve ou rejette avec motif et référence du contrôle. L'approbation exige les confirmations d'indépendance et de vérification des pièces.

Le serveur vérifie de nouveau les sources approuvées à la date d'effet. Si un contrat, salaire ou version de rubrique a changé entre préparation et décision, la variable n'est pas silencieusement recalculée : il faut annuler le brouillon ou rejeter la demande, puis créer une nouvelle proposition traçable. Un préparateur désactivé empêche l'approbation ; le rejet reste possible pour conserver son attribution d'origine.

Une variable approuvée est figée. Les nouvelles étapes de paie exploiteront ses données et références ; une correction financière ultérieure devra suivre le circuit de régularisation prévu. Les demandes concurrentes ou répétées ne créent pas deux décisions.

## Recette et chiffres

Utiliser le salarié **P001 — Salma FICTIVE** du cahier887, salaire contractuel de novembre2026 **9 000,10MAD**, et la rubrique **PRIME_FICTIVE889** du cahier889. Période `2026-11`, effet `2026-11-15`, montant `800.01`, source `VAR-P001-NOV2026-01`, motif `Variable fictive de recette891` ; références `ATTEST-P001-NOV2026` et `MISSION-P001-NOV2026` pour les deux types attendus. Faire soumettre puis approuver indépendamment. Le montant reste800,01MAD ;aucun net n'est calculé.

Le [complément PDF](RECETTE_VARIABLES_PAIE_891.pdf), le [classeur](SUIVI_VARIABLES_PAIE_891.xlsx) et le [jeu exact](JEU_VARIABLES_PAIE_891.json) décrivent les autres essais. Les données et montants sont exclusivement fictifs ; tous les statuts humains restent Non testé.

## Limites à garder visibles

Les variables et leur approbation ne valident pas les assiettes, exonérations, cotisations ou retenues fiscales. Le paramétrage de pourcentages, SMIG, conditions réglementaires complexes et cumuls d'exonérations reste à compléter avant paie définitive. Le verrouillage des périodes par les campagnes sera raccordé au lot3 ; il n'est pas présenté comme livré ici. Une période de paie ne se confond pas avec un exercice comptable.

Les snapshots des variables approuvées restent figés si une règle future est ajoutée ensuite. Le moteur de campagne devra contrôler la cohérence des sources avant calcul définitif, plutôt que modifier ces snapshots. Les bulletins, paiements, déclarations et OD de paie restent les lots suivants. Recette utilisateur et production non validées.
