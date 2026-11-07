# Journal — contrôle des options AV, des libellés et des dates

Lot `JOURNAUX-AV-AUDIT-20261008-272`.

## État réellement constaté

Le dépôt courant contient **un seul** élément `AV — Avoirs` dans `JOURNAUX` (`src/data/donnees.js`). Le filtre du Journal le parcourt une fois. Le formulaire d'écriture utilise le même référentiel, réparti entre journaux standards et spéciaux ; AV est uniquement standard. Les codes sont définis dans le modèle backend ; aucune liste de journaux personnalisés par société n'est utilisée par ces deux contrôles actuels.

Le Journal affiche une ligne par mouvement. La date et le code journal sont des cellules fusionnées sur les lignes d'une même écriture. Le libellé présenté est celui de la ligne lorsqu'il apporte une information, sinon celui de l'écriture. L'affichage ne préfixe pas automatiquement ce libellé d'un second mot « Avoir ».

**Conclusion limitée à la version testée :** les deux anciens signalements « deux AV — Avoirs » et répétition du mot « Avoir » ne sont pas reproduits. Aucun correctif applicatif, suppression, fusion de journal ni changement de code/libellé historique n'est appliqué. Deux écritures d'avoir distinctes restent deux écritures distinctes ; elles ne sont pas un doublon du référentiel.

La présentation actuelle de la date est la colonne Date, fusionnée verticalement, et non un titre de carte. Aucune refonte esthétique n'est effectuée sans référence visuelle exploitable.

## Scénario réellement exécuté

Deux parcours Edge headless **1365 et 390 px**, application/API réelles et PostgreSQL nonce. Une nouvelle société fictive et deux clients distincts sont créés par l'API. Deux factures ventes de 100 HT + 20 TVA = 120 TTC et 200 HT + 40 TVA = 240 TTC sont validées/comptabilisées. Chacune possède son propre avoir complet, sans retour physique, créé depuis ses lignes sources, comptabilisé puis validé.

Oracle indépendant :

- Factures : débit 3421 de 120/240, crédits 7111 de 100/200 et 4455 de 20/40.
- Avoirs : débits 7111 de 100/200 et 4455 de 20/40, crédits 3421 de 120/240.
- Ensemble : **4 écritures définitives, 12 lignes, débit = crédit = 720 MAD**.
- Filtre AV seul : **2 écritures distinctes, 6 mouvements, débit = crédit = 360 MAD**.

Dans le navigateur :

1. Le bouton `AV — Avoirs` est présent une seule fois et utilisé par un clic natif.
2. Six lignes comptables AV sont affichées, indépendamment de la ligne de total.
3. Chacun des deux avoirs possède sa référence distincte et une seule cellule date fusionnée sur ses trois mouvements, ainsi qu'un seul badge AV par écriture.
4. Les libellés des six mouvements sont identiques à ceux de leurs sources comptables ; aucun préfixe supplémentaire n'est ajouté.
5. Le formulaire Nouvelle écriture est ouvert ; son sélecteur natif contient un seul AV et aucun code dupliqué. AV est sélectionné réellement puis le formulaire est annulé sans sauvegarde. Les autres codes distincts sont toujours présents.
6. Les snapshots finaux des IDs, dates, journaux, références, libellés, validation, comptes, montants et auxiliaires sont identiques à ceux pris avant la consultation. Aucune requête UI de création/modification/suppression d'écriture n'est émise.

## Commandes et résultats

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_journaux_avoirs_isole.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_avoir_retour_isole.py Test/test_e2e_ecriture_erreurs_isole.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_journaux_avoirs_isole.py
```

Première cible : **1 failed en 28,11 s**. Le nouveau test comptait toutes les lignes `tbody` et attendait six, alors que la page contient six mouvements plus une ligne de total. Le sélecteur est corrigé uniquement dans ce test neuf pour compter les mouvements, avec contrôle séparé du total. L'oracle financier et le code applicatif restent inchangés ; le cas mobile n'avait pas été exécuté dans ce run arrêté par `-x`.

Cible finale : **2 passed en 28,10 s, exit 0**, desktop et mobile réellement exécutés, aucun test ignoré. Compilation Python du test : **exit 0**. Les 25 avertissements Pydantic/Starlette existants ne sont pas des tests ignorés.

Connexes : **3 passed en 54,74 s, exit 0**, aucun échec, erreur ou test ignoré. Le retour/avoir client avec contrepassation et les deux parcours de création d'écriture avec vrais refus API restent réussis. La fixture E2E compile réellement l'application React ; aucun fichier applicatif n'étant modifié, aucun build supplémentaire de modification frontend n'est requis pour ce lot.

## Limites et reprise

La recette automatisée de la version locale est validée pour la cible. Elle ne démontre pas l'état d'une ancienne installation, d'un cache navigateur ou des données utilisateur. Si le doublon est encore visible chez l'utilisateur, conserver une capture et la version exacte avant tout diagnostic supplémentaire ; ne pas supprimer/fusionner ses écritures pour faire disparaître un affichage.

Aucune base PostgreSQL réelle et aucune donnée comptable réelle ne sont utilisées. La recette utilisateur reste à effectuer.

Fichiers différentiels exacts :

- `Test/test_e2e_journaux_avoirs_isole.py`
- `Test/rapport_e2e_journaux_avoirs_isole.md`

`src/pages/Journal.jsx` et le référentiel sont inchangés et doivent être exclus du ZIP. L'agent principal assure le journal et la vérification du ZIP différentiel.
