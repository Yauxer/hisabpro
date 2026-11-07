# Lot518 — Mouvements de stock pendant clôture et inventaire

## Défaut reproduit et correction minimale

Le comptage et la comptabilisation étaient protégés par les lots508/510,
mais le moteur central des mouvements ne prenait pas leur verrou. Une
correction de stock pouvait être acceptée pendant une clôture ayant déjà lu
l'inventaire. Une clôture, un comptage ou une génération pouvait aussi
commencer pendant l'enregistrement d'un mouvement direct.

La vérification de période du moteur prend désormais, sur PostgreSQL,
le verrou transactionnel existant du stock, partagé avec la clôture et
exclusif entre opérations de stock. L'exercice est trouvé depuis les dates
paramétrées, puis relu avant les contrôles métier existants. Un conflit
renvoie409, sans nouvelle mutation. Une tentative peut être reprise après
l'achèvement de la première.

Une seule fonction produit modifiée ; aucun calcul de quantité, CMUP,
coût, compte comptable, fiscalité ou migration changé. Les contrôles de
chronologie, période fermée, stock négatif et idempotence sont conservés.
SQLite reste utilisé uniquement par les tests de logique métier pure ;
la concurrence est exercée sur PostgreSQL natif isolé.

## Sept scénarios API et PostgreSQL

- Clôture suspendue après lecture du stock : correction refusée409,
  photographies/mouvements/articles inchangés ; clôture−3000 dans le jeu
  initial à stock nul. Après clôture, autre correction refusée et tables
  métier conservées.
- Mouvement en cours puis clôture, comptage ou comptabilisation : trois
  refus409. Après enregistrement, comptage5×20=100, régularisation100 validée,
  clôture−2900 et export FEC effectifs.
- Régularisation100 en cours puis correction10unités : correction409 ;
  une seule régularisation, validation et clôture−2900.
- Exercice décalé juillet N−1/juin N : date décembre N−1 protégée par la clé
  de l'exercice N, sans confusion avec l'année civile ; autre société libre.
- Date antérieure au dernier mouvement refusée, tables métier conservées,
  puis correction valide possible : absence de verrou résiduel.

Les montants sont fictifs. La CM3000 déjà présente reste active ; ces chiffres
ne qualifient aucun dossier réel.

Avant correctif : **6échecs/1réussite,29avertissements,37,70s**, code1.
Après écriture de la correction, la première commande de tests a été refusée
avant exécution : revue automatique indisponible pour limite d'utilisation.
Elle ne constitue donc aucun résultat de test. Reprise avec journal et
processus vérifiés ; aucun ancien test relancé pendant qu'il tournait encore.

Qualification ciblée : **46réussites,29avertissements,46,07s**, code0 :
7cas natifs PostgreSQL et39régressions de logique métier, moteur, ledger et
intégrité. Aucun passage successif additionné comme cas distinct.

Qualification finale : **312réussites,29avertissements,635.32s**, code0,
aucun échec/erreur/ignoré :256oracles précédents,10parcours commerce/logos,
7cas518 et39tests moteur/ledger/intégrité. Tous sont exécutés dans cette
commande après modification du moteur central. Rôle LOGIN non propriétaire,
PostgreSQL18.3 et sources figées vérifiés ; parcours Edge ordinateur/mobile,
téléchargements PDF/XLSX et impressions inclus.

Restauration098 :74tables, source préservée, cibles supprimées, trois fonctions
identiques et refus409/reprise conservés. Invariants comptables0 : pièces
déséquilibrées, montants non finis, définitives sans numéro/date.
Trois Python du lot et24du cumulatif compilés ;98SQL/115guides,
main/models/AGENTS, services de calcul du stock et des exercices intacts.
Frontend inchangé ; build516 précédent conservé, sans le déclarer réexécuté.

Commande : liste complète de la consolidation514, en remplaçant son wrapper
par `Test/test_consolidation_mouvements518_isole.py` et en ajoutant
`Test/test_stock_integrite_mouvements.py`, `Test/test_patch06c_stock_engine.py`
et `Test/test_patch06b_stock_ledger.py`, avec `-ra` via `Test/run_unit_tests.py`.


## Installation et limites

Installer `services/stock_movement_service.py` à jour518 sur la version516,
qui fournit `services/exercice_verrou_service.py`. Le ZIP cumulatif contient
ces dépendances. Redémarrer l'API ; aucune nouvelle migration ou intervention
sur la base réelle. Aucun mouvement ancien n'est réécrit.

Cette protection concerne les opérations concurrentes passant par le moteur.
Elle n'invente pas une photographie d'inventaire ni une réparation d'historique.
La validité d'un inventaire devenu ancien après de nouveaux mouvements
successifs reste un contrôle métier distinct. SQL/Python directs hors moteur,
dates d'exercices modifiées simultanément, recette utilisateur et production
ne sont pas validés par ce lot. Point6 humain conservé en attente.
