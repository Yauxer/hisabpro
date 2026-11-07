# Lot514 — Déficits historiques partagés entre exercices

## Cause et correction minimale

Le verrou annuel512 ne couvrait pas le stock global des déficits : une saisie
historique pouvait changer ce stock pendant une clôture ou une confirmation.
Deux imputations portant sur deux exercices différents pouvaient lire le même
disponible, puis la seconde échouer500 dans le contrôle SQL d'épuisement.
Le contrôle SQL existant empêche l'excès ; il n'est pas supprimé ni contourné.

Un verrou transactionnel non bloquant par société protège maintenant ce stock :
partagé pendant clôture/calcul fiscal annuel, exclusif avant toute lecture des
six opérations de déficits (ajout, modification, suppression, génération,
confirmation ou annulation d'imputation). Le verrou du stock précède celui de
l'exercice. Plusieurs lectures peuvent coexister, les autres sociétés restent
disponibles. Un conflit renvoie409 avant calcul ou modification.

Aucune migration, règle de report, durée, ventilation ni formule fiscale
modifiée. Les protections existantes des déficits déjà imputés restent actives.
Il s'agit d'une protection des opérations concurrentes : ce lot n'ajoute pas
une interdiction permanente de saisie historique après clôture ou confirmation.

## Tests API et PostgreSQL réellement exécutés

- Six croisements : clôture/confirmation en cours puis ajout, modification ou
  suppression du stock. Refus409, stock initial conservé et impôt cohérent.
- Deux croisements inverses : ajout non encore confirmé puis clôture ou
  confirmation. Refus409, puis reprise réussie après enregistrement.
- Deux exercices bénéficiaires20000 et un seul déficit1000 fourni explicitement :
  première imputation1000 acceptée, seconde409. Après achèvement, seconde
  proposition0 ; consommation totale1000, une seule imputation conservée.
  Modification/suppression du déficit utilisé toujours refusées409.
- Isolation entre sociétés, échec pour doublon sans modification des tables
  métier et libération du verrou permettant ensuite la clôture.
- Perte fictive2000 : déficit calculé2000, annulation d'imputation possible,
  clôture−5000 avec la CM3000 déjà existante, non neutralisée pour le test.

Les montants sont des hypothèses fictives de laboratoire, sans qualification
réglementaire d'un dossier réel.

Premier passage :11échecs,29avertissements,41,66s, code1. Neuf échecs de
concurrence/contrat non implémenté ; deux jeux de test violaient la chronologie
du journal en saisissant une pièce début décembre après le capital validé fin
décembre. Dates corrigées au31décembre, contrôle métier intact.
Deuxième passage avant correctif : **10échecs/1réussite,29avertissements,
42,53s**, code1 : le scénario d'imputations entre exercices atteint alors
effectivement la course et l'erreur500 de contrôle du solde.

Qualification ciblée : **91réussites,29avertissements,84,51s**, code0 :11cas514,11cas512 et69régressions fiscales. Aucun passage successif additionné comme cas distinct.

Qualification finale : **256réussites,29avertissements,493.36s**, code0,
aucun échec/erreur/ignoré :245oracles précédents et11cas514.
Parcours Edge fiscal, inventaires desktop/mobile, clôtures et restauration098
conservés. Sources figées vérifiées ;74tables restaurées, source préservée,
cibles supprimées, trois fonctions098 identiques et refus409/reprise intacts.
Invariants comptables0 : pièces déséquilibrées, montants non finis,
définitives sans numéro/date. Cinq Python du lot et20du cumulatif compilés ;
98SQL/115guides, main/models/AGENTS et calculs de stock/exercices intacts.

Commande : même liste que la qualification512, en remplaçant uniquement
`Test/test_consolidation_fiscal512_isole.py` par
`Test/test_consolidation_deficits514_isole.py`, avec `-ra` via
`Test/run_unit_tests.py`.


## Installation, preuves et limites

Installer ensemble `routers/fiscalite.py`, `routers/cloture.py` et
`services/exercice_verrou_service.py` à jour514, puis redémarrer l'API.
Aucune modification de base réelle ni nouvelle migration. Aucun déficit réel
n'est ajouté ou requalifié. Une saisie historique ou un changement déjà achevé
reste soumis aux contrôles métier existants ; une correction fiscale après
clôture exige toujours un examen distinct et traçable.

Les lectures d'aperçu isolées, règlements CSS et écritures directes SQL/Python
ne sont pas inclus dans cette garantie de concurrence. Les oracles512 et
précédents doivent rester verts ; recette utilisateur, production et point6
restent en attente.
