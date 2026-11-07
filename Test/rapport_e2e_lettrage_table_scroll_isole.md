# Hauteur de la liste du lettrage après sélection — 8 octobre 2026

Le parcours fournisseur 252, repris après correction de la liste des factures, révèle un second défaut mobile réel. Le tableau de lettrage est comprimé par les filtres et les actions ; l'apparition de la barre de sélection après une première case cochée réduit encore sa hauteur. L'en-tête fixe intercepte le clic natif sur la case suivante. Le run complet a donné 1 passed et 1 failed en 56,25 s, sans clic forcé ; la capture fictive est `.codex-tests/acompte_fournisseur_390_fe3c3fe1.png`.

La correction minimale concerne uniquement le CSS de cette page : défilement vertical du contenu et base/hauteur minimale de 240 px pour la carte du tableau. Aucun filtre, indicateur, champ ou ligne n'est masqué. Les règles de sélection, de lettrage et les écritures validées restent inchangées.

Le test indépendant utilise trois écritures synthétiques équilibrées et validées par la vraie API, dans une société/fournisseur et une base PostgreSQL nonce. Il ne simule pas une facture réelle : les trois mouvements 4411 sont crédit 1 200, débit 400 et débit 800, avec contreparties explicites en 5141. Oracle indépendant : débit et crédit du collectif 1 200 chacun, solde nul, code AAA sur les trois lignes. Les références, montants, dates et auxiliaires d'origine restent inchangés après lettrage.

Viewports exécutés : 390 × 1000, 1365 × 600 et 1365 × 1000. La hauteur utile est mesurée avant et après apparition de la barre de sélection ; elle doit être supérieure à la hauteur de l'en-tête. Chaque case est cochée nativement, le lettrage est effectué puis relu après rafraîchissement. Aucune réponse API inventée, style injecté, changement de viewport en cours ou clic forcé.

## Tests exécutés

Avant correction : **1 failed, 2 deselected en 23,35 s** sur le cas mobile. Hauteur du tableau avant sélection : 237 px ; après première sélection : 25 px, alors que l'en-tête mesure 33 px. La preuve est sauvegardée dans `.codex-tests/lettrage_scroll_257_avant.log`. Le test échoue sur une vraie contrainte géométrique du corps visible, sans contourner le clic ni modifier un montant.

Après correction : **3 passed en 33,76 s**, zéro échec et zéro test ignoré. Les trois viewports permettent la sélection native des trois lignes, le lettrage AAA et sa persistance après rechargement ; les dates, références, montants et auxiliaires d'origine sont identiques avant/après.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_lettrage_table_scroll_isole.py -k 390 -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_lettrage_table_scroll_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_lettrage_table_scroll_isole.py Test/test_e2e_acompte_fournisseur_isole.py
npm run build
```

Compilation Python : exit 0. Build Vite : **138 modules, exit 0 en 5,65 s**, avec les avertissements XLSX et taille des chunks existants.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_acompte_fournisseur_isole.py Test/test_e2e_acompte_imputation_isole.py Test/test_e2e_lettrage_concurrence_isole.py -x
```

Résultat final de reprise et connexes : **13 passed en 106,24 s**, zéro échec et zéro test ignoré. Les deux parcours fournisseur (1365 et 390 px) atteignent le lettrage AAA avec quatre écritures et neuf lignes inchangées ; le cycle client existant et les refus de montants non finis restent valides. Le test de réponse GET tardive reste réussi. La recette 252 est donc débloquée après les corrections distinctes 253 et 257 ; son oracle financier n'a pas changé.

Aucune donnée utilisateur réelle n'est concernée. Ce lot corrige la hauteur/scroll de la page de lettrage, sans changer les règles d'imputation, de lettrage ou la navigation mobile générale. La recette utilisateur reste à effectuer.
