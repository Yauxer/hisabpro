# Articles : diagnostic stock et mesure des mutations — 10 octobre 2026

## Problème démontré

La globale311 conserve **2 734 réussites et 4 échecs**, code1, sur649sources
inchangées. Deux échecs viennent du compteur de requêtes du test articles :
il assimile les POST `/api/devis/diagnostic-stock` à des mutations métier.
Les traces montrent uniquement ces lectures supplémentaires pendant le refus
attendu de l'édition ; aucune erreur JavaScript ni réponse API500.

La route commerciale appelle une photographie indicative du stock sans
création, réservation, mouvement ou écriture. Son utilisation de POST ne
transforme pas cette lecture en une modification de document.

## Correction minimale

Seul `Test/test_e2e_articles_historique_nombres_isole.py` est modifié.
L'observateur distingue exactement le chemin de lecture du stock et continue
de compter les autres POST/PATCH articles, devis, commandes et factures.
Aucun code applicatif, migration ou comportement de stock n'est modifié.

Le test force une actualisation réelle du stock en édition du devis : réponse200,
lecture observée et compteur de mutations inchangé. Il conserve le refus de
sauvegarder des prix/TVA inconnus. Une relecture API vérifie ensuite le devis
et la commande : prix100, TVA20, TTC120 toujours inchangés. Les contrôles de
conservation des nombres historiques, des stocks et des écritures restent
présents sur bureau1365 et mobile390.

## Tests réellement exécutés par le principal

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_articles_historique_nombres_isole.py Test/test_e2e_cycle_achat_reception_partielle_isole.py Test/test_e2e_recouvrement_isole.py --tb=short --junitxml=.codex-tests/e2e_312_1039_final.xml
```

**13 réussis, 0 échec, 0 erreur, 0 ignoré, 25 avertissements ; code0
en140,11s.** Les trois modules passent, y compris les quatre cas qui avaient
échoué dans311. Articles : Node et deux Edge ; réceptions partielles : deux
Edge ; recouvrement : huit tests navigateur/API connexes. Compilation Python
du fichier modifié : code0. Le build139modules du lot310 reste la preuve
frontend pertinente : aucun fichier applicatif n'a changé depuis ce build.

La première relance312 a donné **11 réussites et 2 échecs en124,92s**, code1.
La nouvelle relecture API avait omis le paramètre `exercice` obligatoire :
réponse422. Le test a été corrigé pour utiliser l'exercice du document source,
sans assouplir le contrat de l'API. Cette erreur intermédiaire reste consignée.

La relance diagnostique précédant toute correction avait donné3réussites
en47,34s ; elle n'est pas additionnée à la relance finale ou à la globale.

## Limites conservées

Les deux autres échecs311 sont des délais navigateur avant navigation/login.
Les reprises correspondantes passent sans changement applicatif, mais leur
cause n'est pas établie. Les traces Windows et le résultat échoué311 restent
conservés ; aucune globale ultérieure n'est déclarée verte par addition des
retests. Le registre garde cette surveillance sousLIM-20.

Toutes les API et écritures de laboratoire appartiennent aux fixtures nonce.
Aucun test ne vise le PostgreSQL réel, aucune donnée réelle n'est modifiée.
Recette utilisateur et mise en production restent à valider séparément.
