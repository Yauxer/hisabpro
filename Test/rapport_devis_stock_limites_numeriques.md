# Lot 251 — Quantités du diagnostic stock représentables

## Anomalie prouvée et correction minimale

Une vraie requête authentifiée `POST /api/devis/diagnostic-stock` avec quantité texte `1e1000000`, sur PostgreSQL nonce isolé, retournait **HTTP 500**, au lieu du refus HTTP 422 attendu. L’exposant était accepté par le champ Decimal de la requête, puis dépassait l’exposant maximal du contexte lors du cumul. Aucun exposant susceptible d’entraîner une allocation plus importante n’a été testé.

Le champ individuel `quantite` utilise désormais la représentation float des lignes commerciales. Son validateur examine d’abord le Decimal source : nombre fini positif ou nul, booléen refusé. La conversion doit être finie et ne doit pas transformer un nombre non nul en zéro. Un vrai zéro est canonisé en 0.0, y compris une notation à exposant extrême. Ces bornes décrivent la représentation technique des quantités, sans inventer une quantité maximale métier.

Le service du lot 241 reste inchangé : cumul Decimal exact et sortie texte si le cumul dépasse la représentation JSON numérique finie. Deux lignes à `1e308` restent autorisées ; quantité cumulée exacte `2e308` et manque exact `2 × 10^308 − 5`, rendus en texte. Aucun blocage des devis, réservation, mouvement de stock ou nouvelle règle fiscale introduit.

## Tests réellement exécutés

Environnement : `hisabpro-backend/.venv/Scripts/python.exe`, `PYTHON_DOTENV_DISABLED=1`. Fixture réelle API/JWT/PostgreSQL nonce du lot 241, cible vérifiée par le garde-fou d’isolation ; aucun PostgreSQL utilisateur ni donnée réelle.

Avant correction :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py -q Test/test_devis_stock_limites_numeriques.py -k non_representable -x
```

**1 échec**, arrêt au premier cas : `1e1000000` donne HTTP 500. Session 14840 achevée avec code 1.

Après correction :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py -q Test/test_devis_stock_limites_numeriques.py Test/test_devis_stock_diagnostic.py
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile hisabpro-backend/routers/commercial.py Test/test_devis_stock_limites_numeriques.py
```

**35 tests réussis** (13 nouveaux et 22 connexes), session 72664 achevée avec code 0 ; 25 avertissements de dépendances préexistants. Compilation : code 0.

Les nouvelles requêtes réelles vérifient HTTP 422 pour dépassement `1e1000000`, sous-flux `1e-1000000`, booléens, NaN, infinis et valeur négative ; HTTP 200 pour zéro, zéro à exposant extrême, `1e308` et la quantité subnormale représentable `5e-324`. Le cumul de deux grandes lignes conserve son exactitude. Chaque cas compare les tables articles, mouvements, devis/lignes et écritures avant/après : aucune mutation.

## Limites et reprise

La précision individuelle reste celle du float des documents commerciaux ; les chiffres supplémentaires d’une chaîne décimale sont donc arrondis à cette représentation. Le cumul est exact sur ces valeurs individuelles représentables. Aucun test navigateur supplémentaire dans ce lot API ; la recette commerciale utilisateur reste à effectuer. Aucun accès à PostgreSQL réel n’est nécessaire ou autorisé pendant cette session.

Prochaine étape : inclure ces 13 nouveaux tests dans la consolidation finale et suivre le cahier commercial fictif livré au lot 247.
