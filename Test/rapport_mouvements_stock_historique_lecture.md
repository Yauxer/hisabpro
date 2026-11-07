# Lot333 — lecture des mouvements de stock historiques

La route existante `GET /api/articles/{id}/mouvements` exposait directement
les trois quantités historiques. Les valeurs non finies provoquaient une
réponse500 lors de la sérialisation JSON ; NULL échouait en validation.

Seul `MouvementStockOut` change : quantité, stock avant et stock après sont
nullable en sortie, avec `nombres_diagnostics`. Les valeurs finies signées,
zéro, fractions et grandes valeurs sont préservées. Les saisies, le moteur,
les métadonnées, le tri et la limite50 ne changent pas. Aucun coût ajouté
au contrat ; aucune modification de l'objet ORM.

## Tests exécutés

Toutes les commandes passent par `Test/run_unit_tests.py`, avec
`PYTHON_DOTENV_DISABLED=1`. Les imports purs utilisent SQLite mémoire ;
les appels HTTP utilisent exclusivement l'application complète et un
PostgreSQL éphémère avec URL/dossier/nonce vérifiés.

Baseline : **32 échecs, code1**, XML42,828s. Les traces de la vraie API sont
conservées dans `.codex-tests/mouvements_333_api_echec_*.log`. Deux cas
initialement préparés ne pouvaient pas être insérés : la contrainte réelle
`ck_mouvements_stock_quantite_positive_06c` refuse quantité0 et -Inf.

Premier run après correction : **42 réussis, 2 échecs, code1**, XML44,436s.
Ces deux échecs portent sur cette préparation incompatible avec la contrainte.
Le banc a été corrigé pour **tester son refus et le rollback**, sans supprimer
ni contourner la contrainte. NULL et booléens restent des tests de projection
pure, car les colonnes PostgreSQL sont NOT NULL.

Commande finale :

```text
python -X utf8 Test/run_unit_tests.py
 Test/test_mouvements_stock_historique_lecture.py
 Test/test_patch06b_stock_ledger.py Test/test_patch069_stock_services.py
 -q --tb=short --junitxml=.codex-tests/mouvements_333_final.xml
```

**45 réussis, 0 échec/erreur/ignoré, 25 avertissements, code0**, XML40,328s.
33 nouveaux cas, dont huit lectures API non finies, une lecture API signée/zéro
et deux refus PostgreSQL ; quatre tests06B et huit tests069 connexes inchangés.
Compilation du schéma et du test : code0.

Les photographies articles/mouvements/écritures/lignes restent identiques après
GET. L'autre société reçoit404. Aucun montant, justificatif ou écriture réelle
n'a été réparé.

## Limites

Aucun consommateur de cette route n'a été trouvé dans `src`. L'onglet
« Mouvements & CMUP » utilise un autre service, traité au lot334. Ce lot API
ne prétend donc pas valider cette interface. Aucune migration ou base réelle
modifiée ; recette utilisateur distincte.
