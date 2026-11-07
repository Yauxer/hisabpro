# Navigation des états de synthèse

Les liens Bilan, CPC et ETIC ne sont plus dupliqués dans le menu Comptabilité. Le cockpit Liasse fiscale expose T1 Bilan, T2 CPC et T3–T25 ETIC. L'accès à l'éditeur ETIC reste disponible depuis ce cockpit ; les anciennes routes restent compatibles pour les favoris et les exports. Cette étape regroupe la navigation, sans refondre les écrans de saisie ni supprimer des données.

Test réellement exécuté : `Test/run_unit_tests.py Test/test_e2e_navigation_liasse_isole.py --tb=short --show-capture=no` : **1 réussi en 17,07 s**, aucun échec ou test ignoré. Edge, API réelle et PostgreSQL éphémère, authentification réelle. Absence des trois liens de menu vérifiée, onglets Bilan/CPC ouverts et éditeur ETIC atteint depuis la liasse ; pas d'erreur navigateur ou serveur observée.

PostgreSQL réel jamais utilisé ; appréciation visuelle et recette utilisateur restent à effectuer.
