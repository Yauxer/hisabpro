# Balance comparative — dates et arrivée tardive du contexte exercice

Lot `BALANCES-DATES-CONTEXTE-20261008-266`, exécuté le 8 octobre 2026 UTC.

## Anomalie et preuve avant correction

La globale historique post263 a exécuté 2 344 cas : **2 343 réussis et un échec**, en 2 504,64 s. Dans `test_resultat_comparative_dates_n1_variations_et_exports_reels`, le fichier Excel comparatif portait les périodes annuelles 2026/2025 alors que mars avait été saisi. Les reprises isolée (un succès en 30,51 s) et du module entier (quatre succès en 47,93 s) n'avaient pas reproduit l'écart et ne constituaient pas une correction.

La nouvelle preuve retient les réponses **réelles** de `GET /api/exercices`, obtenues par `route.fetch()` sur FastAPI/PostgreSQL isolé. Aucun corps JSON, montant, exercice ou statut n'est remplacé. Avant leur libération, les vraies balances N/N-1 sont chargées ; l'utilisateur saisit mars et télécharge un Excel comparatif dont la période mars est vérifiée. Après libération des mêmes réponses, l'exercice sélectionné reste 2026 mais les dates reviennent à **2026-01-01 / 2026-12-31**.

Commande avant correction applicative :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_balances_dates_contexte_isole.py -x --tb=short
```

**1 failed en 44,32 s, exit 1**. Le premier cas échoue sur la conservation de `2026-03-01` ; la sortie affiche les deux bornes annuelles. Le second cas n'est pas exécuté à cause de `-x`.

Cause confirmée : dans `Balances.jsx`, l'effet de synchronisation dépendait des bornes de l'exercice et les appliquait sans condition. `ExerciceContext` commence avec `exercice=null`, puis son GET tardif fournit les bornes réelles. Cette arrivée de métadonnées écrasait un filtre manuel déjà saisi pour la même année. Le problème est une réinitialisation des dates, sans modification des calculs de balance ou du moteur d'export.

## Correction minimale

Seul `src/pages/Balances.jsx` est modifié côté application. Une référence conserve la portée société/année et indique si l'utilisateur a saisi une date. L'arrivée tardive des bornes pour cette même portée conserve le filtre manuel. Sans saisie, les bornes réelles sont toujours initialisées ; un changement volontaire d'année ou de société connue réinitialise le choix. La première résolution de la société de `null` à son identifiant n'est pas assimilée à un changement de société.

La société fait également partie des dépendances de chargement des rapports et de leur annulation. Aucun calcul, compte, migration, montant, écriture validée ou assertion des tests existants n'est modifié.

## Recette exécutée après correction

Les tests utilisent Edge headless, l'application React compilée, FastAPI et le cluster PostgreSQL nonce contrôlé par la fixture existante. Le stockage et les bases utilisateur ne sont jamais utilisés. La synchronisation du navigateur attend les véritables événements/éléments de contexte ; aucune attente arbitraire de plusieurs secondes ni clic forcé n'est utilisé pour obtenir le résultat.

Trois nouveaux cas :

1. **Filtre manuel de mars conservé** malgré le GET exercices tardif. XLSX et PDF conservent la période N/N-1. Les mouvements attendus restent charge 500 MAD et produit créditeur 1 000 MAD. Le changement volontaire via le sélecteur d'exercice réel remplace ensuite mars par les bornes 04-01 / 09-30 de l'autre exercice.
2. **Absence de saisie manuelle** : les bornes réelles 01-02 / 06-30 de l'exercice fictif arrivent tardivement et remplacent correctement les bornes calendaires provisoires. Un changement volontaire d'exercice initialise ensuite 04-01 / 09-30.
3. **Changement réel de société** par le sélecteur existant, POST de changement et rechargement natif. La société B utilise 02-01 / 09-30 ; son Excel et son PDF contiennent sa seule identité et ses mouvements fictifs de 17 MAD, sans le capital de A. La portée précédente et son filtre de mars ne sont pas conservés chez B.

Les snapshots des lignes comptables avant/après sont identiques, y compris pour les deux sociétés du troisième cas. Les mutations de préparation créent uniquement des exercices et opérations fictifs dans la base isolée.

Premier run après correction : **2 passed en 26,32 s, exit 0** (les deux cas relatifs à l'arrivée tardive, avant ajout du cas société).

Run final ciblé et connexe :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_balances_dates_contexte_isole.py Test/test_e2e_balances_exports_isole.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_balances_dates_contexte_isole.py
npm run build
```

**7 passed en 65,47 s, exit 0**, aucun échec, erreur ou test ignoré. Les trois nouveaux cas et les quatre cas existants couvrent les cinq exports de balance, les libellés société, l'isolement de lecture, les variations numériques et les dates N-1 du 29 février. Les 25 avertissements Pydantic/Starlette préexistants ne sont pas des tests ignorés.

Compilation Python : **exit 0**. Build Vite : **138 modules, exit 0, 6,65 s** ; avertissements de regroupement XLSX et de taille des chunks existants.

## Limites et livraison

Tests automatisés locaux validés pour ce correctif. La globale historique en échec reste identifiée comme telle ; ce rapport ne la requalifie pas en réussite. La nouvelle globale complète après correction relève de la consolidation de session.

La recette utilisateur sur son installation reste à effectuer. Aucun PostgreSQL réel, document ou donnée comptable réelle n'a été modifié. Aucune conformité réglementaire ou certification n'est affirmée.

Fichiers différentiels exacts :

- `src/pages/Balances.jsx`
- `Test/test_e2e_balances_dates_contexte_isole.py`
- `Test/rapport_e2e_balances_dates_contexte_isole.md`

L'agent principal consigne les résultats, prépare et vérifie le ZIP différentiel. Prochaine étape : reprendre le parcours fournisseur avec avoir/retour, règlement et lettrage après livraison du présent lot.
