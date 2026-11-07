# Libellés des comptes historiques — 8 octobre 2026

Le plan actif était déjà chargé par Layout et respectait les libellés
personnalisés. Le défaut concernait les comptes désactivés : absents du cache
d'affichage, ils perdaient leur intitulé dans le journal, le grand livre et CSV.

La lecture conserve désormais tous les comptes de la société, avec leur libellé
exact. Le cache v1 est étendu de manière compatible ; chaque lecture vérifie
la clé utilisateur/société du jeton courant. Le plan utilisé pour sélectionner
un nouveau compte reste limité aux actifs. Les snapshots auxiliaires, libellés
d'opération et écritures définitives ne sont pas modifiés.

## Commandes réellement exécutées par le principal après reprise

`python -X utf8 Test/run_unit_tests.py Test/test_e2e_libelles_comptes_isole.py Test/test_patch064_plan_comptable_rapide.py Test/test_session132_admin_plan_navigateur.py Test/test_session132_admin_plan_lecture.py --tb=short --show-capture=no`

**13 réussis, 0 échec, 0 ignoré, 34,37 s**, 26 avertissements existants de
dépréciation Pydantic/python-multipart. Le nouveau scénario utilise Edge,
FastAPI et un PostgreSQL éphémère réellement connecté : écritures validées
120/100/20, désactivation via PATCH administrateur, passage société A → B → A,
journal, grand livre et six CSV vérifiés. Les écritures, lignes et snapshots
auxiliaires avant/après lecture restent identiques. Les anciens tests navigateur
des erreurs de chargement du plan utilisent des réponses simulées ; ils ne sont
pas présentés comme des tests métier connectés.

`node --test Test/test_plan_lecture_comptes.mjs` : **5 réussis, 0 ignoré,
138,54 ms**. Cache complet et ancien v1, isolation utilisateur/société,
déconnexion, exclusion des inactifs de la sélection et actualisation d'un
libellé inactif.

Compilation des deux tests Python modifiés : **OK**. Build final exécuté par
l'agent avant interruption : **139 modules, 5,40 s, OK** ; avertissements
XLSX/bundle déjà connus. Son E2E initial avait réussi en 27,21 s ; les connexes
lancés au moment du quota n'avaient pas de sortie récupérée et ont été repris
par le principal. Aucun résultat interrompu n'est compté comme réussi.

## Limites

Aucun PostgreSQL réel ni donnée comptable réelle utilisés. Les libellés du
compte reflètent le plan de la société ; les libellés auxiliaires historiques
figés restent séparés. La recette utilisateur reste à effectuer. Prochaine
étape : suite globale sur les sources stabilisées, couverture et cumulatif.
