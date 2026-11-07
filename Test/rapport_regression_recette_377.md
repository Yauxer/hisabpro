# Lot377 — clôture et reprise des quatre échecs de la globale373

La globale373 reste une preuve échouée :3235 réussis,4 échecs,0 erreur,0 ignoré. Les corrections ci-dessous ont été vérifiées séparément ; une nouvelle globale est à programmer.

## Cause et correction minimale

Une réponse de clôture2026 arrivée après sélection de2025 remplaçait les données affichées sans remplacer l'année du titre. `Cloture.jsx` protège désormais le chargement par génération, année et jeton ; les trois réponses sont décodées avant publication cohérente. Les réponses obsolètes et leurs erreurs sont ignorées ; aucun calcul comptable ni route de clôture n'est modifié.

Le nouveau test retarde trois vraies réponses API2026, sélectionne2025 puis libère les anciennes réponses. Il contrôle la présence du brouillon2025, ses périodes, le refus de clôturer et l'absence de mutation comptable, sur Edge1365 et390px.

Deux bancs historiques ont été adaptés au menu mobile370 : les tests administratifs chargent les hooks et le routeur réellement utilisés ; le test sans CDN ouvre le menu pour vérifier le bouton visible, puis vérifie sa présence dans le DOM même lorsque le menu se replie. Les assertions métier, les délais de chargement et le blocage CDN sont conservés.

## Commandes réellement exécutées

Python du venv, via `Test/run_unit_tests.py`, avec `PYTHON_DOTENV_DISABLED=1` :

- Reproduction du nouveau test avant correction :1 échec en35,00s, après libération des réponses obsolètes.
- Ancien scénario complet de clôture seul avant correction :1 réussi en32,92s ; ne démontre pas l'absence de course.
- Nouveau test de réponses retardées et `Test/test_e2e_cloture_isole.py` :3 réussis,26 avertissements,60,01s. Clôture, à-nouveaux et verrouillage réellement exécutés sur base jetable.
- Première reprise des bancs :3 réussis,1 échec en41,03s ; puis erreur de collecte par indentation, corrigée et compilée.
- `Test/test_session132_admin_plan_navigateur.py Test/test_e2e_chargement_sans_cdn_isole.py Test/test_navigation_mobile_isole.py` :8 réussis,26 avertissements,78,97s.
- `Test/test_patch04_cloture_service.py Test/test_compta2_cloture_resultat.py` :9 réussis,0,35s.
- Compilation des trois fichiers de tests modifiés/ajoutés :code0.
- `npm run build` :code0,140 modules,9,29s ; avertissements de taille de bundle et d'import XLSX conservés.

Les suites sont distinctes et ne sont pas additionnées à la globale. Preuves XML et captures conservées dans le cache local `.codex-tests` et exclues du ZIP. Aucun PostgreSQL réel ni donnée réelle utilisé ; les tests connectés utilisent exclusivement des bases jetables protégées. La recette humaine et la consolidation globale restent à effectuer.
