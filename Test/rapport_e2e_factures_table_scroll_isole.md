# Hauteur et défilement de la liste des factures — 8 octobre 2026

Le parcours d'acompte fournisseur 252 a révélé un défaut réel en viewport 390 × 1000 px : les KPI et filtres empilés consomment toute la hauteur ; le conteneur du tableau se réduit à zéro dans le flex, tandis que son parent masque le dépassement vertical. Le clic natif de validation est intercepté par la carte, même après le défilement automatique de Playwright. Le défilement horizontal fonctionne ; aucune colonne ne doit être masquée pour contourner le défaut.

La correction minimale concerne uniquement `Factures.module.css` : autoriser le scroll vertical du contenu, préserver le masquage horizontal du parent et garantir une base et une hauteur minimale de 240 px à la zone de tableau. Les deux règles ont été appliquées après le dégel explicite de l'agent principal, à la reprise de 17:52 UTC ; aucune source applicative n'a changé pendant la globale précédente. Aucun état, compte ou donnée métier ne change.

Le test indépendant prépare une nouvelle société et une facture brouillon fictive par API. Oracle indépendant : 100 MAD HT, TVA 20 MAD, TTC 120 MAD. Il vérifie que les KPI et les filtres restent présents, que le tableau conserve une hauteur réelle non nulle et que le clic natif « Valider définitivement » fonctionne. La référence et les montants doivent rester exacts, avec un numéro définitif et aucune écriture créée par la validation seule. Viewports : 390 × 1000, 1365 × 600 et 1365 × 1000. API, Edge et PostgreSQL nonce réels ; aucune réponse métier fabriquée, aucun clic forcé ou style injecté.

## Résultats réellement exécutés

Avant correction, deux preuves ciblées 390 × 1000 px échouent : **1 failed, 2 deselected en 19,45 s**, puis **1 failed, 2 deselected en 19,31 s** avec log sauvegardé dans `.codex-tests/factures_scroll_253_avant.log`. Le tableau mesuré a `clientHeight=0`, `scrollHeight=126`, `clientWidth=112` et `scrollWidth=1037`. Le test échoue sur la hauteur nulle, sans clic forcé ni injection de style.

Après correction : **3 passed en 24,39 s**, zéro échec et zéro test ignoré, pour les trois viewports. Chaque cas conserve les KPI/filtres, mesure une hauteur réelle positive, valide la facture par clic natif puis relit la référence et les montants dans la vraie API/base nonce. La validation seule ne crée aucune écriture.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_factures_table_scroll_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_factures_table_scroll_isole.py Test/test_e2e_acompte_fournisseur_isole.py
npm run build
```

Compilation Python : exit 0. Build Vite : **138 modules, exit 0 en 4,42 s**, avec les avertissements existants sur XLSX et la taille des chunks.

Connexes réellement exécutés :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_facturation_isole.py Test/test_e2e_factures_ca_dates_isole.py Test/test_factures_periode.py Test/test_fact4_facturation_robuste.py -x
```

Résultat : **13 passed en 72,43 s**, zéro échec et zéro test ignoré. Les recettes navigateur achat/vente et CA par dates utilisent la vraie API/PostgreSQL nonce ; les tests de calculs et contrôles connexes conservent leurs propres fixtures. La recette fournisseur 252 franchit aussi sur mobile la validation/comptabilisation de facture, l'imputation et le règlement ; elle révèle ensuite un autre défaut de hauteur dans la page Lettrage. Ce défaut distinct n'est pas masqué ni présenté comme validé par la présente correction ; il est documenté dans son rapport et signalé pour un lot séparé.

Aucune donnée utilisateur réelle n'est utilisée. La recette utilisateur sur ses documents reste à effectuer. Ce lot corrige la liste des factures, sans refonte générale de la navigation mobile.
