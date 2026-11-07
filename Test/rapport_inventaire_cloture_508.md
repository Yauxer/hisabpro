# Lot508 — Comptage physique stable pendant la clôture

## Défaut et correction

Le défaut est reproduit dans les deux ordres :

- Une clôture avait déjà contrôlé un stock nul, mais un comptage5×20MAD=100MAD
  était encore accepté pendant ses calculs fiscaux. La clôture pouvait terminer
  sur l'ancienne photographie, sans refléter le nouveau comptage.
- Un comptage nul était en cours, son insertion bloquée par le banc ; la
  clôture était acceptée et le nouveau snapshot pouvait être confirmé ensuite
  sur un exercice désormais clos, même sans variation de quantité.

La validation API du comptage prend désormais un verrou partagé non bloquant
sur la même clé société/exercice que le verrou exclusif de clôture. Il est pris
avant les contrôles de période et conservé jusqu'à la fin de la transaction.
L'exercice est relu après acquisition, pour ne pas conserver son ancien statut
si la clôture vient de terminer. Un conflit donne409 et n'ajoute aucun comptage,
mouvement ou écriture. Les autres sociétés et exercices restent disponibles.
Les valeurs, méthodes de stock, montants et règles fiscales restent inchangés.

Le petit service `exercice_verrou_service.py` utilise les fonctions natives
PostgreSQL déjà employées par la clôture ; aucune nouvelle migration ni fonction
SQL créée. Aucun accès à une base utilisateur.

## Exécutions et preuves

- Premier banc :2échecs/2réussites,29avertissements,63,20s. Un échec était un
  défaut produit ; l'autre venait d'une preuve globale qui tentait de lire la
  table fiscale délibérément verrouillée. Ce SELECT de preuve a été annulé
  uniquement après vérification du dossier/port/nonce du cluster temporaire.
  Le finally et le nettoyage ont abouti. Ce passage n'est pas présenté comme
  deux défauts produit ni comme une réussite.
- Banc corrigé avant code produit :2échecs/2réussites,29avertissements,32,23s.
  Les deux courses produisent200 au lieu du409 attendu.
- Après correction :19réussites,29avertissements,33,08s :4cas PostgreSQL natifs
  et15tests purs de comptage sur SQLite, distingués explicitement.
- Qualification finale : **158réussites,29avertissements,389.17s**, code0,
  aucun échec/erreur/ignoré. Dont les oracles précédents, quatre parcours Edge
  inventaire1365/390px (nombres inconnus refusés et perte40/photographie160),
 25tests historiques et15purs de comptage. Sources figées vérifiées.
  Restauration098 :74tables, source préservée/cibles supprimées, fonctions et
  refus409/reprise intacts. Invariants comptables0 :pièces déséquilibrées,
  montants non finis et définitives sans numéro/date. Quatre Python du lot et
  treize du cumulatif compilés ;98SQL/115guides et main/models/AGENTS intacts.

Le banc utilise de vraies transactions et barrières SQL dans le cluster nonce :
table fiscale pour arrêter la clôture après son contrôle de stock, et table des
inventaires pour arrêter le comptage avant confirmation. Aucun résultat métier
n'est simulé. La preuve pendant la barrière fiscale porte sur articles,
mouvements, comptages, écritures et archives ; les refus métier hors barrière
vérifient toutes les tables, sauf l'audit de refus ajouté normalement.

Après libération : clôture possible avec stock0 et résultat−3000 correspondant
à la CM existante du laboratoire, FEC exportable ; un comptage après clôture
reste refusé. Un comptage invalide libère son verrou. La CM du laboratoire ne
constitue pas une qualification fiscale d'une entreprise réelle.

Commande finale : `Test/run_unit_tests.py Test/test_consolidation_inventaire508_isole.py Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py Test/test_patch05c_reconciliation_historique.py Test/test_patch05d1_reconciliation_amortissements.py Test/test_patch05_livre_inventaire.py Test/test_e2e_cloture_isole.py Test/test_inventaire_comptage_complet.py Test/test_inventaire_nombres_historique_postgres.py -ra`.

## Installation et limites

Installer ensemble `routers/inventaire.py` et le nouveau service, avec les
prérequis de clôture déjà livrés, puis redémarrer l'API. Aucune nouvelle migration
ni modification des comptages historiques. L'utilisateur peut réessayer après
la fin de l'autre transaction ; les périodes clôturées restent protégées.

Ce lot protège la validation de comptage via l'API. Les appels Python directs
au service de snapshot, le SQL arbitraire, les autres mouvements de stock, la
création d'articles et les courses entre deux comptabilisations de stock restent
des périmètres distincts. Les archives existantes sont conservées. Frontend
inchangé ; recette utilisateur, mise en production et point6 non validés.
