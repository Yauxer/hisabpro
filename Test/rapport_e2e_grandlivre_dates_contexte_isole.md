# Grand livre : préserver les dates pendant le chargement du contexte

Lot `GRANDLIVRE-DATES-CONTEXTE-20261008-270`, 9 octobre 2026.

## Cause reproduite avant modification

Le contexte exercice était chargé après l'ouverture de la page ; son arrivée déclenchait un effet qui remplaçait systématiquement les dates, même lorsque l'utilisateur avait déjà saisi une période. La reproduction utilise une véritable réponse GET `/api/exercices` retenue puis libérée sans en modifier le corps. Aucun montant ou reporting n'est remplacé.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_grandlivre_dates_contexte_isole.py -k filtre-mars-conserve --tb=short
```

**1 échec réel en 20,91 s**, 2 désélectionnés : CSV mars correct avant libération ; après réception du contexte les dates reviennent à `2026-01-01` / `2026-12-31` au lieu du filtre `2026-03-01` / `2026-03-31`. Il s'agit du défaut attendu, pas d'une erreur de fixture ni d'un test réussi.

## Correction minimale

GrandLivre.jsx mémorise si les dates ont été saisies, avec la portée année/société. L'hydratation tardive du même exercice préserve ce choix. Sans saisie, les bornes réelles restent appliquées ; un changement volontaire d'année ou de société réinitialise les dates. Le chargement du reporting suit aussi l'identité de société et garde son annulation de requêtes obsolètes existante. Aucun calcul, route backend, libellé de compte ou écriture n'est modifié.

## Oracle et tests connectés

Deux écritures fictives sont créées et validées normalement par API : au 5 janvier, débit banque 5141 / crédit capital 1111 de 1 000 MAD ; au 15 mars, débit charge 6111 / crédit banque 5141 de 200 MAD. Pour le grand livre 5141 de mars, le solde initial est **1 000**, le mouvement crédit **200**, le cumul final **800 MAD** ; seul le mouvement de mars doit apparaître dans le CSV. Le CSV complet après hydratation sans saisie contient janvier et mars avec cumul final 800.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_grandlivre_dates_contexte_isole.py --tb=short
```

**3 réussis en 28,41 s**, aucun échec ou test ignoré. Edge → FastAPI → PostgreSQL nonce vérifie : filtre mars et vrais CSV téléchargés avant/après contexte ; initialisation tardive des bornes décalées du 2 janvier au 30 juin sans saisie, puis changement d'exercice vers avril–septembre ; changement vers une seconde société dont la période est février–septembre, son seul mouvement banque de crédit17/cumul-17, sans ligne ou référence de la société A. Les CSV sont ouverts en UTF-8/BOM et analysés avec csv.DictReader et Decimal. Les photographies complètes des tables écritures et lignes restent identiques avant/après navigation et exports. Aucune erreur JavaScript ni réponse500 métier.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_balance_grand_livre_final.py Test/test_e2e_libelles_comptes_isole.py Test/test_patch082_libelles_lignes_ecritures.py Test/test_patch054_journal_conformite_finale.py --tb=short
```

**26 réussis en 25,27 s**, aucun test ignoré : reporting final, lecture connectée des libellés exacts, lignes d'écritures et journal. Les dépréciations Pydantic/python_multipart existantes restent signalées.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_grandlivre_dates_contexte_isole.py
```

**OK**, code de sortie 0.

```text
npm.cmd run build
```

**OK**, Vite en 4,59 s, après stabilisation du lot articles 269. Avertissements existants : import xlsx partagé et taille du bundle. Aucun fichier dist n'est inclus dans ce différentiel.

## Limites

Aucun PostgreSQL réel ni serveur utilisateur utilisé. Les corps HTTP différés ont été lus depuis le laboratoire et restitués sans modification ; seules les polices décoratives externes sont bloquées par le support navigateur existant. Les nouveaux tests portent sur cette course de chargement et la portée du filtre, sans prétendre couvrir tous les parcours du grand livre.

Différentiel : `src/pages/GrandLivre.jsx`, `Test/test_e2e_grandlivre_dates_contexte_isole.py`, ce rapport. Journal et ZIP préparés par l'agent principal.
