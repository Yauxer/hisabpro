# Recette E2E connectée — Immobilisations

Date d'exécution : 7 octobre 2026. Fichier : `Test/test_e2e_immobilisations_isole.py`.

## Environnement et périmètre

Navigateur Edge headless, application React complète, FastAPI et cluster PostgreSQL
éphémère avec migrations du banc existant. Société, compte utilisateur et trois
exercices exclusivement fictifs. Aucun appel API simulé, aucune utilisation du
PostgreSQL réel, aucune lecture de `.env` et aucune donnée historique modifiée.

Les exercices vont de l'année courante moins trois à l'année courante moins un
(2023–2025 lors de cette exécution). L'acquisition est saisie dans l'interface,
les dotations sont générées depuis le détail et les quatre écritures sont
validées dans le Journal, exercice par exercice.

## Données et contrôles exécutés

Bien « Serveur fictif E2E », catégorie Matériel informatique, acquis et mis en
service le 1er janvier du premier exercice ; prix HT 10 000 MAD, amortissement
linéaire trois ans, valeur résiduelle nulle. TVA 20 %, récupération 100 % :
configuration disponible de l'application pour ce scénario, sans affirmation
de règle fiscale obligatoire.

| Contrôle | Résultat attendu vérifié |
|---|---|
| Acquisition UI et rafraîchissement du registre | Brut 10 000 ; TVA récupérable 2 000 ; dette TTC 12 000 |
| Écriture AC initialement brouillon | D2355 10 000 ; D34551 2 000 ; C4481 12 000 |
| Première dotation | 3 333,33 ; cumul 3 333,33 ; VNC 6 666,67 |
| Deuxième dotation | 3 333,33 ; cumul 6 666,66 ; VNC 3 333,34 |
| Dernière dotation et centime résiduel | 3 333,34 ; cumul 10 000 ; VNC 0 |
| Trois écritures AM | D61935 / C28355 pour chaque dotation |
| Validation depuis le Journal | Quatre écritures validées et équilibrées sur trois exercices |
| Cohérence comptable finale | Brut D2355 10 000 moins amortissement C28355 10 000 = VNC 0 |
| Registre et détail après rechargement | Bien actif, cumul 10 000, VNC 0, plan persisté |
| Nouvelle génération annuelle | Zéro génération, une immobilisation ignorée, total zéro |
| Intégrité après relance/rechargement | Identifiants, comptes, débits et crédits des lignes validées inchangés |
| Erreurs du navigateur / HTTP serveur | Aucune erreur JavaScript ni réponse serveur en erreur |

La VNC et le cumul affichés au registre sont calculés à la date du jour par le
service existant ; avant comptabilisation ils représentent le plan théorique.
La concordance avec les écritures définitives est contrôlée après génération
et validation de toutes les dotations. Le test ne confond pas ces deux étapes.

## Anomalie et correction produit

Première exécution : échec réel, 42,78 s. Le module utilisait une URL locale
`http://localhost:8000` indépendante de `VITE_API_URL` : l'interface affichait
« Failed to fetch » face au serveur isolé configuré. L'agent principal a corrigé
`Immobilisations.jsx` pour utiliser `API_BASE` partagé. Aucun reroutage de test
ni mock n'a masqué l'anomalie.

Deuxième exécution : échec du sélecteur de test en 39,68 s après acquisition et
trois dotations réussies. Le libellé « Exercice actif » appartient aux paramètres
et n'est pas présent dans le Journal. Le test cible maintenant le sélecteur
d'exercice réel du layout. Le tableau imbriqué est ciblé explicitement.

## Commandes réellement exécutées

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_immobilisations_isole.py -x
```

Exécution finale : **1 passed, 25 warnings in 26.13s**, code retour 0. Les
avertissements concernent les dépréciations Pydantic et python_multipart.

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_immobilisations_fin_plan.py Test/test_patch03_immobilisations.py
```

**13 passed in 0.14s**, code retour 0. `test_patch03_immobilisations.py` ne
contient pas de cas collecté par pytest : sa fonction `run()` a donc été
exécutée séparément, avec environnement mémoire pour les imports.

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -c "import os,sys,runpy; os.environ['DATABASE_URL']='sqlite+pysqlite:///:memory:'; sys.path.insert(0,'hisabpro-backend'); runpy.run_path('Test/test_patch03_immobilisations.py',run_name='__main__')"
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile Test/test_e2e_immobilisations_isole.py
```

Script : **OK — 6 tests Immobilisations Patch 03**, code retour 0. Compilation :
code retour 0. Ces six scénarios purs ne constituent pas une validation PostgreSQL.
La validation PostgreSQL connectée est apportée par l'E2E ci-dessus.

## Limites

Ce lot couvre acquisition, plan achevé, comptabilisation et idempotence.
Cession, rebut, paiement d'acquisition, réconciliation historique et permissions
ne sont pas exercés par ce nouveau scénario. La recette utilisateur visuelle et
la validation réglementaire ne sont pas déclarées acquises. Aucun contrôle sur
la base réelle de l'utilisateur n'a été lancé.
