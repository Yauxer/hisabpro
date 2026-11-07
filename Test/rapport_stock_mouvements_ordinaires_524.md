# Lot524 — Mouvements ordinaires compatibles avec les inventaires

## Régression reproduite et correction

Le lot518 prenait une exclusion trop large pour tous les mouvements d'un
exercice. Deux mouvements ordinaires pouvaient alors se refuser409 alors que
le moteur savait déjà les sérialiser par article. Trois tests PostgreSQL
historiques inchangés (CMUP avec objets ORM anciens, deuxième sortie
insuffisante, idempotence simultanée) ont reproduit cette régression.
Un nouveau scénario API avec deux articles distincts l'a confirmée de manière
déterministe pendant une attente native d'insertion.

Le verrou de coordination est désormais partagé pour les mouvements
ordinaires, avec les verrous d'article existants toujours actifs. Les endpoints
de comptage et de comptabilisation conservent leur verrou exclusif ; la clôture
conserve son exclusion sur l'exercice. Une photographie/génération ne peut donc
pas se glisser au milieu des mouvements, sans empêcher deux mouvements
ordinaires de travailler normalement. Deux fichiers produit modifiés.

Aucun ancien test modifié pour accepter la régression. Aucun calcul de CMUP,
quantité ou fiscalité changé, aucune migration et aucune donnée réelle touchée.

## Preuves API/PostgreSQL et périmètre

- Deux corrections sur deux articles distincts sont réellement observées
  simultanément en attente dans `pg_stat_activity`. Elles terminent toutes
  deux200, avec stocks0→5 et0→7.
- Pendant ces deux transactions, comptage, génération et clôture refusent409 ;
  les sources restent intactes. Le comptage5×20+7×20=240 est ensuite accepté,
  sa régularisation validée, puis clôture−2760 et FEC effectifs.
- Les trois scénarios historiques restent inchangés : recalcul depuis l'article
  relu, refus de sortie insuffisante selon le contrôle métier et absence de
  double mouvement pour une même clé d'idempotence.
- Le module PostgreSQL historique complet est également repris après correction,
  ainsi que les protections518/510, pour vérifier la compatibilité ensemble.

Les quantités et montants sont fictifs. La CM3000 existante est conservée ;
aucune qualification fiscale d'une entreprise réelle n'est déduite.

Avant correction : **4échecs,29avertissements,43,40s**, code1 : trois cas
historiques et le nouveau scénario API. Cette régression est attribuée au
verrou trop large du lot518, sans la présenter comme préexistante.

Qualification ciblée : **29réussites,29avertissements,117,07s**, code0 :
15tests du module PostgreSQL132 inchangé, le nouveau scénario API et13tests
de protections518/510. Les trois scénarios historiques défaillants passent
sans modification de leurs attentes. Pas d'addition des passages successifs.

Qualification finale : **401réussites,29avertissements,655.97s**, code0,
aucun échec/erreur/ignoré :385oracles522,15tests PostgreSQL132 et1nouveau cas.
Scénarios du wrapper principal sous rôle LOGIN non propriétaire PostgreSQL18.3,
sources figées vérifiées ; Edge ordinateur/mobile, vente/achat,
factures→règlements→lettrage, PDF/XLSX/impression, fiscalité et clôtures inclus.

Restauration098 :74tables, source préservée, cibles supprimées, trois fonctions
identiques et refus409/reprise conservés. Invariants comptables0 : pièces
déséquilibrées, montants non finis, définitives sans numéro/date.
Quatre Python du lot et32du cumulatif compilés ;98SQL/115guides,
main/models/AGENTS, Journal522 et autres sources produit inchangés.
Frontend inchangé.

Commande : liste de la consolidation522 avec
`Test/test_consolidation_stock524_isole.py` comme wrapper et ajout du module
`Test/test_session132_operations_postgres.py`, avec `-ra` via
`Test/run_unit_tests.py`.


## Installation et limites

Installer ensemble `services/exercice_verrou_service.py` et
`services/stock_movement_service.py` à jour524, puis redémarrer l'API.
Le cumulatif contient ces versions corrigées ; ne pas les remplacer ensuite
par celles d'un ancien ZIP518. Aucune nouvelle migration.

La concurrence sur un même article reste protégée par son verrou de ligne.
Un comptage, une génération ou une clôture en cours peuvent encore refuser un
mouvement409 ; la reprise après achèvement reste normale. Les opérations
directes hors moteur/endpoints, les dates d'exercice modifiées simultanément
et la validité d'un inventaire devenu ancien demandent leurs propres contrôles.
Recette utilisateur, production et point6 humain restent en attente.
