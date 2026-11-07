# Consolidation globale 391 — 11 octobre 2026

Sur les sources finales de la session précédente, avant les nouveautés392/393/398 : 3283 tests exécutés, 3282 réussis, un échec, zéro ignoré/erreur, 33 avertissements, 4251,60s. Échec : délai de navigation de15s vers dashboard lors de la connexion Edge, dans le test de date locale Europe/Paris1365. Aucune modification pour masquer cet échec.

Reprise isolée de tout le fichier de date locale : 8 réussis, zéro échec/erreur/ignoré, 39,345s. L'échec global n'est pas reproductible dans cette reprise ; la globale initiale demeure explicitement en échec. Les703 empreintes sources/SQL/tests/configurations/assets sont identiques avant et après. La cause du délai ponctuel reste non démontrée ; surveiller une prochaine globale.

Preuves locales : `.codex-tests/consolidation391_globale.{log,xml,exit,sources.json}`, `.codex-tests/consolidation391_reprise_date.xml`. Ces caches ne sont pas livrés.

Tests PostgreSQL nonce et Edge uniquement. Aucun accès au PostgreSQL réel ni modification des données réelles. La reprise isolée ne remplace pas une nouvelle globale après les nouveaux lots bancaires. Point6 en attente de l'utilisateur.
