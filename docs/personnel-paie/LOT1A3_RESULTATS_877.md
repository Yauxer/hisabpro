# Personnel & Paie — résultats877 et reprise

27 octobre2026. Périmètre : backend du lot1A.3. Interfaces1B et recette d'ensemble1C à suivre.

**262 cas distincts réussis** :124unitaires/contrôles de sources,134API-SQL-bootstrap PostgreSQL natif isolé et4parcours Edge/API/PostgreSQL. Aucun échec, erreur ou cas ignoré dans la sélection finale. Les mêmes identifiants de test relancés ne sont pas recomptés.

| Campagne | Cas | Réussis | Échecs | Erreurs / ignorés | Durée pytest | Code |
|---|---:|---:|---:|---:|---:|---:|
| Reprise875 | 2 | 2 | 0 | 0 / 0 | 36,75s | 0 |
| Contrats unitaires | 31 | 31 | 0 | 0 / 0 | 1,17s | 0 |
| Première API connectée | 42 | 42 | 0 | 0 / 0 | 80,56s | 0 |
| Qualification intermédiaire | 49 | 49 | 0 | 0 / 0 | 134,85s | 0 |
| Conservation initiale | 1 | 0 | 1 | 0 / 0 | 52,67s | 1 |
| Conservation corrigée | 1 | 1 | 0 | 0 / 0 | 40,67s | 0 |
| Non-régression | 212 | 212 | 0 | 0 / 0 | 540,27s | 0 |
| Qualification finale | 50 | 50 | 0 | 0 / 0 | 144,89s | 0 |

Les huit XML sont conservés dans `Test/preuves_personnel877`. La [preuve JSON](../../Test/PREUVE_PERSONNEL_PAIE_877.json) donne les durées JUnit, les identifiants et la famille de chaque cas retenu. La sélection finale réunit exclusivement les50cas de `personnel877_final` et les212cas de `personnel877_connexes`.

L'échec de conservation initial était une erreur du test : la table réelle est `lignes_ecriture`, pas `lignes_ecritures`. Le nom a été corrigé après inspection du modèle, puis le test a réellement réussi. Aucun code de comptabilité n'a été modifié pour ce test.

La revue finale a resserré107 pour ne remplacer que les contraintes d'habilitations connues. Une contrainte locale supplémentaire est désormais un témoin testé et conservé au rejeu. Cette seule source SQL a changé après la non-régression ;107 n'est pas exécuté par les212cas historiques. Leurs fichiers Python et migrations utilisés sont restés identiques. La passe finale50requalifie107, son installation, les API et le témoin comptable sur la dernière version. Aucun nouveau résultat n'est attribué rétroactivement aux anciennes passes.

## Ce qui a été exécuté

- Création de trois salariés fictifs en brouillon, montant historique NULL et ancien indicateur actif faux ; aucun salaire zéro artificiel. Matricules `002`, `02`, `2` distincts, espaces ASCII de bord normalisés, autres caractères préservés.
- Doublon société refusé409, même matricule autorisé dans une autre société, deux créations concurrentes donnent201/409 ; recherche, tri et pagination.
- Soumission par le préparateur seulement, approbation/rejet par un compte distinct, préparateur/bénéficiaire refusés même avec droits d'approbation. Confirmation explicite booléenne, référence et motif contrôlés.
- Droits métier séparés du rôle global, compte lecture toujours non modifiant, révocation effective avec le même jeton, module désactivé, lectures anonymes et objets étrangers refusés. Aucun droit implicite après installation ou activation.
- Proposition de contrat puis salaire exact approuvés ; montant futur non appliqué avant décision, ancien montant conservé après décision. Consultation au31/12/2026 :`9000.10`, au01/01/2027 :`9876.54` ; chaînes décimales dans le JSON.
- Lecture des dossiers, demandes et historique sans récupération des montants/motifs financiers masqués par un lecteur non habilité. Liste des demandes à traiter et filtres disponibles.
- Révision périmée409, rejet possible d'une demande périmée avec révision courante, retour initial au brouillon, nouvelle proposition sans effacer le rejet. Double approbation concurrente :200/409 et un seul événement.
- Conflit de version à date déjà occupée : demande toujours soumise, décision et confirmation annulées, révision et salaire approuvé inchangés ; transaction entière annulée.
- Sortie future, statut filtrable à date, absence de suppression, refus d'une condition postérieure à la sortie ou d'une sortie contredisant une condition future approuvée.
- Reprise historique explicite avec mêmes racines/données, sans convertir le flottant ou supposer une date ; les anciens chemins de modification sont bloqués et la simulation historique ne mélange pas des dossiers contrôlés.
- Upgrade107 sur données106 déjà peuplées, conservation des anciennes colonnes, nouvelles attestations laissées inconnues, rejeu peuplé, contrainte locale conservée, runtime PostgreSQL LOGIN non propriétaire et droits SQL minimaux de mutation.
- Anciennes API/dossiers, valeurs invalides, absences, référentiels, avances et démarrage sur ancien schéma ; contrôles de sources et calculs indicatifs historiques.
- Quatre parcours Edge connectés : masquage/révocation et avances, chacun aux largeurs1440et390. Ce sont des non-régressions des écrans existants, pas une qualification des futurs formulaires1B.
- Une écriture fictive préexistante BQ de1000MAD, deux lignes équilibrées, est validée avant le parcours Personnel ; écriture et lignes définitives identiques après les approbations. Factures, règlements et écritures de la société ne sont ni créés par Personnel ni réécrits.

## Compilation, sources et environnement

**Dix fichiers Python compilés : OK.** Frontend et dépendances inchangés ; **build non relancé pour877**. Le build précédent reste un résultat historique, pas une commande revendiquée ici.

[Candidat877](../../Test/CANDIDAT_PERSONNEL_PAIE_877.json) :472empreintes, quatre sources ajoutées et quatre modifiées depuis875. Les anciens fichiers SQL105/106 et les migrations comptables/fiscales sont conservés. Authentification commune et middleware d'audit réutilisés ; aucun corps confidentiel ajouté aux logs HTTP.

Tests sur clusters PostgreSQL natifs temporaires, marqués par nonce et ports locaux dédiés, avec dotenv désactivé et URL de collecte sentinelle injoignable. Aucun PostgreSQL utilisateur contacté. Aucun SQLite ne remplace la validation native. Données, comptes et pièces de référence sont fictifs et isolés.

## État réel de livraison et limites

Le backend décrit dans le [guideAPI877](LOT1A3_API_PERSONNEL_877.md) est livré et ses tests automatisés pertinents sont réussis. Les installations105–107 sur une copie de l'environnement cible, la sauvegarde restaurable et la recette humaine restent à effectuer. Aucune migration cible n'a été exécutée ici.

Le pilote de mutation est réservé aux utilisateurs déjà légitimement admin/comptable avec capacités explicites. Le profil Personnel seul n'est pas livré. Attestations de bénéficiaire et d'indépendance sont des contrôles humains enregistrés ; l'application ne certifie ni la pièce ni l'identité réelle d'une personne derrière plusieurs comptes. Les rectifications sensibles de lien bénéficiaire/matricule ne sont pas des modifications libres. Une demande préparée par un compte désactivé reste soumise aux contrôles de membre actif hérités de106 ; pas de changement d'auteur silencieux.

État ACTIF d'identité distinct de dossier complet à date ; `paie_definitive_autorisee=false` partout. Aucun moteur, taux légal nouveau, bulletin définitif, paiement, déclaration ou conformité réglementaire n'est validé par cette étape. Les états de synthèse et le grand livre restent alimentés par leurs services existants.

## Prochaine tâche exacte

Lot1B : écrans Personnel liste/création/fiche, propositions et décisions, masques et erreurs lisibles, rafraîchissement après mutation, puis groupe de sidebar **Personnel & Paie** avec les neuf rubriques cadrées au Lot0. Les rubriques futures doivent être signalées comme telles, sans faux écran opérationnel. Garder les anciennes URL pendant la transition. Tester ordinateur et mobile avec API/PostgreSQL connectés ; ne pas ouvrir un moteur de paie dans le même lot.

Développement du backend1A.3 terminé ; tests automatisés de ce périmètre validés ; recette utilisateur à effectuer ; mise en production non validée.
