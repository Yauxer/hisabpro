# Diagnostic des sept échecs346 — lot350

Reprise le11octobre2026,08:11UTC, budget jusqu'à10:11UTC.
Journal et dernier cumulatif349 relus :19fichiers/5différentiels,
CRC/union/dernières versions/SHA vérifiés avant nouveau journal.
Le dossier n'est pas un dépôt Git ; aucune réinitialisation ou commit.
Serveurs et PostgreSQL utilisateur inspectés par PID, laissés intacts.

Commande avant correction applicative :
`Test/run_unit_tests.py Test/test_effets_dates_operations.py
Test/test_e2e_ras_capture_isole.py Test/test_e2e_devis_notes_isole.py
-vv --tb=short --junitxml=.codex-tests/diagnostic350_avant.xml`.
Résultat : **27 réussis,25 avertissements,101,49s,code0**. Sept parcours
Edge connectés avec PostgreSQL nonce (RAS5/devis2),20 tests effets ORM.
Cette réussite à heure courante ne remplace pas les sept échecs346.

Causes reproduites séparément : dates navigateur UTC versus locales351
(quatre RAS et huit modales effets échouées avant correction) ; date
future calculée à l'import puis devenue courante352 (deux reproductions).

Le délai de connexion devis n'a pas été reproduit ici. Cause réseau non
établie : aucun retry, délai supplémentaire, assertion assouplie ou
correction spéculative du login. Le test conserve désormais, en cas
d'échec, les méthodes/URL/raisons des requêtes API échouées, les seuls
codes de réponse du login et l'état des processus API qu'il a créés.
Aucun mot de passe, jeton ou corps d'authentification n'est imprimé.

La relance après ajout du diagnostic et corrections351/352 est suivie
dans le rapport351 :63réussis25avertissements201,80s,code0, dont les deux
parcours devis. Compilation du banc devis réussie. Une consolidation
globale distincte reste nécessaire ; la cause de l'incident connexion
reste non établie malgré ces deux réussites.
Aucun PostgreSQL réel ou écriture réelle modifié ; aucune migration.
