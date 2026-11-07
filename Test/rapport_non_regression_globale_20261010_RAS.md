# Non-régression RAS — 10 octobre 2026 — lot300

## Exécution du principal, sources figées

Commande réellement lancée vers01:24UTC, depuis la racine :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test -vv --tb=short --junitxml=.codex-tests/global_RAS_20261010_0058.xml
```

Le lanceur conserve stdout/stderr, XML et code retour sous `.codex-tests`.
Les645empreintes applicatives et de tests ont été enregistrées avant la
commande. Aucun code source ni test n'est modifié pendant cette exécution.
Le rapport Markdown et le journal sont hors de ce périmètre figé.

Les fixtures PostgreSQL créent exclusivement leurs clusters éphémères nonce.
Le runner désactive dotenv et exclut le test historique de séquences qui
viserait une installation réelle. Aucun PostgreSQL utilisateur n'est testé.

## Résultat final — échec conservé

Commande terminée vers02:04UTC pendant l'interruption de quota. Le principal
a récupéré les preuves à08:14UTC : **2627réussis, 12échecs, 0erreur,
0ignoré, 32avertissements ; code retour1**, sur2639cas collectés.

Résumé pytest exact : `12 failed, 2627 passed, 32 warnings in 2386.05s (0:39:46)`.
Le XML confirme2639cas et12échecs. Contrôle réel après commande :
**645empreintes avant/après identiques**, aucun fichier ajouté ou supprimé
dans le périmètre source figé. Log, XML et code retour sont conservés ;
ils ne sont pas remplacés par une relance ultérieure.

## Échecs observés et diagnostic

- `test_e2e_avoir_fournisseur_isole.py` : deux largeurs1365/390.
- `test_e2e_avoir_retour_isole.py` : un parcours retour/annulation.
- `test_e2e_cloture_isole.py` : un parcours clôture.
- `test_e2e_factures_ca_dates_isole.py` : deux fenêtres100/101.
- `test_e2e_journaux_avoirs_isole.py` : deux largeurs1365/390.
- `test_fact6_avoirs_retours.py` : une recette.
- `test_session132_operations_postgres.py` : un parcours API.
- `test_session133_cloture_postgres.py` : deux casFalse/True.

Les traces API et recette montrent `NameError: name 'societe_id' is not
defined`, dans `avoirs.py`, `_credit_excedentaire_avoir`, ligne143.
La recherche de capture RAS utilise un identifiant non défini dans cette
fonction. Les préparations de clôture échouent lors de la création de l'avoir,
avant le parcours de clôture ; aucune course de réponses frontend n'est
établie par cet échec. Les hypothèses de synchronisation émises avant la
disponibilité des traces ne constituent pas un diagnostic validé.

La correction et ses nouveaux tests sont un lot distinct309. Une réussite
ciblée après correction ne transforme jamais cette globale300 en succès.

## Limites

La globale286 verte porte sur la version antérieure et ne remplace pas
cette exécution. Les suites ciblées qui se recouvrent ne sont pas additionnées.
La recette utilisateur, le déploiement sur PostgreSQL réel et la conformité
réglementaire restent distincts des résultats automatisés.
