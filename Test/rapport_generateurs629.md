# Lot629 — générateurs comptables sous SQL100

109 cas réellement exécutés : 109 réussis, zéro échec, erreur ou ignoré,
137,236 secondes, code retour0. JUnit `.codex-tests/generateurs629.xml`.

Le regroupement conserve les tests et leurs oracles existants, sous la chaîne
SQL100 et le LOGIN applicatif d'un PostgreSQL natif jetable : mutations
concurrentes des immobilisations, mouvements ordinaires de stock, règlements
par tiers, rapprochements ventilés, annulations ventilées, finalisation
concurrente des factures, acomptes clients et fournisseurs. Les parcours
navigateur présents dans ces modules sont exécutés dans Edge.

Une société témoin séparée contient une dotation définitive et une reprise
réservée en brouillon. Le suivi complet et les en-têtes/lignes des deux pièces
sont comparés avant/après toute la suite : inchangés. Les protections des
provisions ne bloquent donc pas les cas ordinaires testés et n'altèrent pas
leurs données. Cela ne représente pas109 fonctionnalités nouvelles ni un total
unique à additionner aux campagnes antérieures.

Commande exécutée :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_consolidation_generateurs629_isole.py -q -x --basetemp=.codex-tests/generateurs629 --junitxml=.codex-tests/generateurs629.xml
```

Compilation Python du regroupement contrôlée. Aucune correction du code métier
n'a été nécessaire pour ces109 cas. Les avertissements Pydantic et réécriture
pytest existants restent visibles ; aucun test ignoré n'a été présenté comme
réussi. Seuls les clusters temporaires des bancs ont été utilisés et nettoyés.
PostgreSQL utilisateur6028 et ses processus enfants sont restés présents.

Installation100 sur la base réelle, recette humaine Word/Excel et production
restent non validées. RH/paie et le point6 de recette humaine restent différés.
Suite : intégrité des livraisons, rapport et cumul de session, puis poursuite
des fonctions horsRH encore partielles/absentes selon la matrice.
