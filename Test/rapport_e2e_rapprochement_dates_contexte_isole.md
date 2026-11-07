# Rapprochement bancaire — dates, réponses tardives et sociétés

Lot `RAPPROCHEMENT-DATES-CONTEXTE-20261008-274`.

## Analyse et correction

Deux causes sont reproduites par l'agent principal avant correction :

- L'arrivée tardive du contexte exercice remplaçait les dates de mars saisies par les bornes annuelles, même si l'année n'avait pas changé.
- Une vraie lecture annuelle initiale de la situation bancaire, reçue après une lecture de mars, pouvait remplacer les mouvements courants et faire réapparaître la ligne de capital de janvier sous des filtres de mars.

La correction de `src/pages/RapprochementBancaire.jsx` est réalisée par l'agent principal : portée société/année et indicateur de saisie pour conserver un filtre manuel du même exercice ; initialisation des bornes réelles sans saisie et réinitialisation lors d'un changement de portée. Les lectures de situation sont protégées par leur version et leur portée (société, compte, dates), y compris données, erreurs, fin de chargement et cleanup. Une callback d'une ancienne portée ne relance pas une lecture qui annulerait la lecture courante. Les comptes bancaires sont rechargés pour la société avec annulation des réponses devenues obsolètes.

La règle préexistante d'initialisation de la date d'une nouvelle opération au début de l'exercice est conservée. Son parcours de saisie n'est pas modifié ni déclaré couvert par ces tests de consultation. Aucun calcul comptable, règle de pointage, solde confirmé, écriture définitive ou migration n'est modifié par les compléments de recette.

## Résultats obtenus par l'agent principal

Ces commandes et résultats sont **rapportés par l'agent principal**, et non exécutés par l'agent chargé des compléments :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_rapprochement_dates_contexte_isole.py --tb=short
```

- Avant correction : **2 failed en 25,08 s**, dates écrasées par le contexte tardif.
- Essai intermédiaire : **1 passed en 21,86 s**, mais retenue réseau trop large ; ce résultat ne démontre pas la protection contre une ancienne lecture annuelle et n'est pas utilisé comme preuve de correction de cette course.
- Reproduction avec retenue strictement annuelle **01-01 / 12-31**, en laissant la vraie requête mars aboutir : **1 failed en 28,94 s**, réapparition de `CAP-GL-DATES`.
- Après correction, premiers deux cas : **2 passed en 27,42 s**.

Les réponses retardées proviennent de `route.fetch()` sur l'API et le PostgreSQL isolés. Les corps, montants et mouvements ne sont jamais remplacés par un JSON synthétique.

## Compléments réellement exécutés ici

Les deux cas principaux sont conservés et rejoués, avec snapshots étendus. Deux nouveaux cas couvrent les bornes sans saisie, le changement d'année et la société/banque. Les fixtures sûres et le jeu fictif de la recette Grand livre 270 sont réutilisés sans modification des fichiers partagés.

Oracle indépendant de la société A : capital bancaire 1 000 en janvier, charge et crédit bancaire 200 en mars. Le solde comptable final est **800 MAD** ; le filtre mars contient uniquement `MARS-GL-DATES`, jamais `CAP-GL-DATES`.

Quatre cas :

1. Contexte exercice réel retenu puis libéré : mars est conservé et les mouvements/solde 800 restent cohérents.
2. Situation annuelle initiale réelle retenue, requête mars laissée aboutir, puis libération de l'annuelle : mars, son seul mouvement et le solde 800 restent visibles.
3. Sans saisie manuelle, arrivée tardive des bornes d'exercice **01-02 / 06-30** : les bornes sont initialisées correctement. Un relevé et un état fictifs préexistants sont lus sans modification. Le changement volontaire d'année via le sélecteur réel applique **04-01 / 09-30** et ne présente plus les mouvements de l'ancien exercice.
4. Changement réel de société par le sélecteur et son rechargement natif : la société B applique **02-01 / 09-30**, contient sa seule charge de **17 MAD**, crédit banque 17 et solde bancaire comptable **−17 MAD**. Les mouvements A disparaissent. La banque A en 5149 est absente ; la banque B en 5148 apparaît avec son libellé réel. Une sélection native de 5148 puis de 5141 confirme la séparation des lectures et le retour au mouvement B/solde −17.

Les photos DB comprennent l'intégralité des lignes des tables `ecritures`, `lignes_ecriture`, `rapprochement_lignes`, `rapprochement_etats` et `comptes_bancaires`. Elles restent identiques avant/après consultation. Les nouveaux cas contrôlent également l'absence de requêtes UI de mutation du rapprochement. Les relevés/états et banques supplémentaires sont des prérequis fictifs créés par API avant les snapshots, exclusivement dans le cluster nonce.

Commandes exécutées ici :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_rapprochement_dates_contexte_isole.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_rapprochement_isole.py Test/test_patch083_soldes_rapprochement.py Test/test_session133_releve_import.py Test/test_session133_releve_import_navigateur.py Test/test_rapprochement_integrite_archives.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_rapprochement_dates_contexte_isole.py
```

Ciblés : **4 passed en 31,27 s, exit 0**, aucun échec, erreur ou test ignoré. Compilation Python du test : **exit 0**. Les 25 avertissements Pydantic/Starlette existants ne sont pas des tests ignorés.

La dernière commande connexe avant l'interruption a terminé en **48 passed, 1 failed en 35,30 s, exit 1**. L'échec du premier cas d'import navigateur provenait du banc synthétique existant : il montait la page sans ModulesProvider et ne fournissait que le contexte exercice. Le composant utilise désormais le contexte société ; cette absence empêchait son rendu avant le bouton Import. Le reste de cette commande après le premier échec n'était pas exécuté à cause de `-x`.

À la reprise du **9 octobre 2026**, l'agent principal autorise et consigne l'extension à `Test/test_session133_releve_import_navigateur.py`. Une seule ligne de plugin esbuild fournit le contexte société fictif du banc, comme son contexte exercice existant. Les données de relevé, dates, montants, requêtes attendues et assertions métier restent inchangés. Ce banc reste explicitement synthétique et n'est pas présenté comme une validation PostgreSQL.

Reprise finale réellement exécutée ici :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_rapprochement_dates_contexte_isole.py Test/test_e2e_rapprochement_isole.py Test/test_patch083_soldes_rapprochement.py Test/test_session133_releve_import.py Test/test_session133_releve_import_navigateur.py Test/test_rapprochement_integrite_archives.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_rapprochement_dates_contexte_isole.py Test/test_session133_releve_import_navigateur.py
```

**77 passed en 83,75 s, exit 0**, aucun échec, erreur ou test ignoré. Ce total inclut les **4 nouvelles recettes Edge/API/PostgreSQL réellement isolées**, la recette bancaire connectée existante, les cinq anciens cas d'import navigateur sur leur support synthétique et les autres tests de soldes/import/intégrité selon leurs fixtures. Il ne signifie pas 77 parcours PostgreSQL connectés. Les snapshots étendus restent immuables dans les quatre nouveaux cas.

Compilation Python finale des deux tests modifiés : **exit 0**. Le build partagé avec le lot 275, exécuté par l'agent backend puis rapporté au principal, a terminé : **exit 0, 138 modules, 7,07 s**. Il inclut la source 274 stabilisée ; aucun build concurrent sur `dist`. Les avertissements XLSX et taille du bundle restent présents. La fixture E2E compile réellement l'application React pour chaque module. Cette précision documentaire est livrée dans le lot de couverture 276 ; l'archive 274 demeure intacte.

## Limites et livraison

Aucune base réelle, aucun relevé utilisateur et aucune écriture comptable réelle ne sont utilisés. La recette utilisateur reste à effectuer. Les tests ne déclarent pas un rapprochement terminé, n'inventent pas un solde de relevé et n'activent aucun pointage automatiquement.

Fichiers différentiels du lot :

- `src/pages/RapprochementBancaire.jsx` — correction par l'agent principal.
- `Test/test_e2e_rapprochement_dates_contexte_isole.py` — preuves initiales du principal, compléments par l'agent de recette.
- `Test/rapport_e2e_rapprochement_dates_contexte_isole.md`.
- `Test/test_session133_releve_import_navigateur.py` — adaptation du contexte société du banc synthétique existant, assertions métier inchangées.

L'agent principal assure le journal et le ZIP différentiel vérifié. Prochaine action : consolider la suite globale sur les sources stabilisées.
