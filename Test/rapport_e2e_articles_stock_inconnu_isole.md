# Interface articles — stock historique inconnu

Lot `ARTICLES-STOCK-INCONNU-INTERFACE-20261008`, 8 octobre 2026.

## Correction minimale

La lecture API du lot 248 conserve un diagnostic et renvoie `null` pour un stock historique absent ou invalide. L'interface distinguait mal cette situation d'un stock nul. La page articles affiche désormais **Stock inconnu** et une valeur **À vérifier**, sans signaler une rupture ni calculer une valeur à zéro. Le champ historique reste vide et en lecture seule avec son diagnostic. Le classement « Stock faible » place d'abord les quantités connues ; une valeur inconnue n'est plus classée comme zéro.

La création conserve son stock initial normal de zéro. Un article stockable de stock zéro reste en rupture ; un service reste non stockable. Une conversion en service d'un ancien article au stock inconnu est refusée avec une explication, afin de préserver la vérification de la source. Aucune règle fiscale, écriture, donnée historique ou route API n'a été modifiée.

## Tests réellement exécutés

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_articles_stock_inconnu_isole.py Test/test_articles_stock_historique_lecture.py --tb=short
```

**10 réussis en 33,47 s**, aucun échec ni test ignoré : un scénario navigateur réel et neuf tests API/schéma connexes. Les avertissements concernent les dépréciations Pydantic et python_multipart existantes.

Le scénario utilise Edge, FastAPI et PostgreSQL temporaires isolés par nonce. Cinq articles fictifs sont créés par API : deux futurs historiques, un stock positif de cinq unités, un stock nul et un service. Après vérification explicite de la cible isolée, seules les deux quantités historiques sont remplacées par `NULL` et `NaN` via SQL dans ce laboratoire. Aucun contrôle ni migration n'est désactivé. Le navigateur vérifie les deux diagnostics, les valeurs indéterminées, les champs vides en lecture seule, le classement, la rupture normale, le service et le stock initial de création. Aucun appel de mutation d'article n'est effectué par cette navigation. Les photographies exactes des tables articles, mouvements de stock et écritures sont identiques avant et après la recette. Aucun échec intermédiaire n'a été rencontré.

```text
npm.cmd run build
```

**OK**, Vite en 5,47 s ; avertissements existants concernant le découpage xlsx et la taille du bundle. Les fichiers de build ne font pas partie du différentiel.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_articles_stock_inconnu_isole.py
```

**OK**, code de sortie 0.

## Limites et livraison

Aucun PostgreSQL réel, répertoire utilisateur de pièces ni serveur utilisateur n'a été utilisé ou modifié. La recette sur les données historiques de l'utilisateur reste à faire : le diagnostic est volontairement conservé jusqu'à vérification de la source, aucune réparation automatique n'est proposée. Ce lot ne traite pas d'autres montants historiques invalides.

Différentiel prévu : `src/pages/Articles.jsx`, `Test/test_e2e_articles_stock_inconnu_isole.py`, ce rapport. Le journal et le ZIP sont préparés et vérifiés par l'agent principal.
