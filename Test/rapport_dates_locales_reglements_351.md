# Dates locales des règlements et effets — lot351

## Cause et correction minimale

L'annulation de règlement envoyait la date UTC de `toISOString()` ; la
capture RAS utilisait déjà la date locale. À00h30 Europe/Paris, l'annulation
était datée de la veille et refusée422. Les valeurs initiale/maximale des
modales d'effets avaient le même décalage ; à23h30 America/New_York, UTC
était déjà le lendemain. Trois expressions utilisent maintenant
`dateLocaleISO`, fonction métier existante, sans nouvelle règle backend,
modification d'écriture définitive ou migration.

## Reproduction réelle avant correction

- Quatre scénarios RAS complets : vente/achat, Edge1365/390, vraie API et
  PostgreSQL nonce. Seule l'horloge JavaScript est figée à00h30 locale,
  aucun appel métier intercepté. Annulation422 dans les quatre cas.
- Huit modales React d'effets : quatre actions, Europe/Paris00h30 et
  America/New_York23h30. Champ date différent du jour local ; API simulée
  pour ce banc de composant, explicitement distinct du scénario connecté.
- **12 échoués,8 désélectionnés,25 avertissements,89,64s,code1**,
  `dates351_baseline.xml/.log`. Erreur initiale de collecte conservée dans
  `dates351_avant` : argumentaction oublié dans un nouveau test puis ajouté.

## Vérification après correction

Commande réelle : `Test/run_unit_tests.py
Test/test_e2e_dates_locales_reglements_isole.py Test/test_effets_dates_navigateur.py
Test/test_e2e_ras_capture_isole.py Test/test_e2e_devis_notes_isole.py
Test/test_effets_dates_operations.py Test/test_effets_dates_minuit.py
Test/test_ras_capture_reglement_postgres.py -vv --tb=short
--junitxml=.codex-tests/dates351_final.xml`.
**63 réussis,25 avertissements,201,80s,code0**, aucun échec/erreur/ignoré.
Onze parcours Edge connectés : quatre RAS à00h30, cinq RAS existants et
deux devis. Seize tests de modales React avec API simulée ; vingt-deux
tests effets ORM ; quatorze API RAS PostgreSQL nonce. Les quatre parcours
RAS à00h30 vérifient validation, règlement, lettrage/délettrage, annulation,
débit=crédit et conservation des écritures définitives.

Build Vite réel : **code0,5,85s**, avertissement de taille de bundles
supérieure à500kB conservé. Compilation Python des trois tests navigateur
modifiés : code0. Comparaison avec version346 :684→686 sources, seuls
sept fichiers source/test attendus diffèrent (incluant les lots350/352).

La cohérence de date locale est testée ; les fuseaux navigateur et serveur
différents restent soumis aux contrôles métier existants. Recette humaine
à effectuer sur les écrans Règlements/Effets ; aucune base réelle utilisée.
