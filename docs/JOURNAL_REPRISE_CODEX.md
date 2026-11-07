# Journal actif de développement HisabPro

Le fichier de reprise est **CODEX_PROGRESS.md** à la racine. Son historique
reste conservé. Les entrées « Journal actif » enregistrent le début d'un lot,
ses points de reprise, les commandes/tests, ses limites et sa livraison.

À chaque session, Codex lit AGENTS.md et le suivi, vérifie le dépôt, puis consulte :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/journal_codex.py etat
```

Exemple de consignation, exécuté depuis la racine du projet :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/journal_codex.py debut LOT-EXEMPLE --objectif "Corriger le contrôle ciblé" --fichiers src/composant.jsx --prochaine "Analyser le composant et ses tests"
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/journal_codex.py point LOT-EXEMPLE --fait "Correction enregistrée" --tests "Tests à exécuter ; commande précise à noter" --prochaine "Lancer les tests ciblés"
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/journal_codex.py interruption LOT-EXEMPLE --prochaine "Vérifier le résultat de la commande interrompue puis reprendre les tests"
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/journal_codex.py point LOT-EXEMPLE --tests "Résultats réellement obtenus" --limites "Validations PostgreSQL réel / navigateur restantes" --prochaine "Créer et lister le ZIP différentiel"
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/journal_codex.py fin LOT-EXEMPLE --zip livraison.zip --prochaine "Étape suivante ou recette utilisateur"
```

Un point peut reprendre une étape interrompue. Une fin exige un ZIP existant,
non vide, dont le CRC est vérifié. Une étape terminée conserve son historique :
ses compléments sont consignés sous un nouvel identifiant.

Pour une livraison avec `Test/livrer_session132.py`, ajouter `--etape LOT-EXEMPLE`
et `--prochaine "Prochaine action exacte"`. Le livreur vérifie d'abord le ZIP,
termine l'étape dans le journal puis inclut ce reçu final dans l'archive. Il
n'est alors pas nécessaire d'appeler `journal_codex.py fin` séparément.

Les informations sont écrites sur disque à chaque appel. Codex doit effectuer
ces appels à chaque transition du travail : l'outil ne devine pas les actions
ni les résultats des tests. Les marqueurs JSON servent à relire automatiquement
les étapes incomplètes ; les entrées lisibles servent à l'utilisateur.

Ne jamais enregistrer mots de passe, secrets, chaînes de connexion complètes
ni données comptables réelles sensibles. Les résultats historiques rapportés
doivent porter cette mention jusqu'à vérification lors de la reprise.
