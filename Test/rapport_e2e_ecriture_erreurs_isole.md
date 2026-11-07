# Messages d'erreur lors de la saisie comptable — 8 octobre 2026

## Analyse

Le helper partagé `formatErreurAPI` transforme déjà les listes d'erreurs FastAPI en messages comprenant le chemin du champ et son `msg`. `EcrituresContext` utilise ce helper via `ecrituresAPI` ; le formulaire affiche ensuite `Error.message`. La validation des montants du lot 161 est déjà présente : lignes portant un seul sens, débit/crédit strictement positifs au total et écriture équilibrée avant activation du bouton. Ces corrections n'ont pas été réappliquées.

Le champ compte autorise une saisie texte. Deux numéros invalides ABC et DEF permettent de provoquer naturellement deux erreurs Pydantic imbriquées dans `detail`, sans fabriquer de réponse réseau. Cette recette complète la preuve de la checklist JUL19-04 « [Object][Object] » et contrôle le libellé exact des comptes par société.

## Scénarios réels

Deux scénarios Edge indépendants, sociétés fictives A et B, utilisent FastAPI et PostgreSQL éphémère protégé par nonce. Pour chacun, une autre société possède un libellé bancaire différent et une subdivision 51419 privée. Les comptes sont créés/renommés via les routes métier normales.

Le navigateur saisit une écriture équilibrée de 100 MAD avec ABC au débit et DEF au crédit, puis coche « Valider immédiatement ». Le vrai POST est rejeté HTTP 422 avec exactement deux chemins `body/lignes/0/compte` et `body/lignes/1/compte`. Le formulaire reste ouvert, conserve la saisie et affiche « Numéro de compte invalide » pour les deux lignes avec `lignes.0.compte` et `lignes.1.compte`, sans `[object Object]`. Aucune écriture, brouillon ou définitive, n'est créée.

Le remplacement d'ABC par 5141 recharge exactement le libellé bancaire personnalisé de la société connectée. Le champ reste en lecture seule ; le libellé bancaire de l'autre société est absent. Un crédit de 101 face au débit 100 désactive le bouton et aucun POST supplémentaire n'est émis. Les montants n'ont pas été arrondis ou modifiés pour contourner le contrôle.

Enfin, le crédit revient à 100 et le compte 51419 privé à l'autre société est saisi. Le vrai POST renvoie HTTP 400 et le message « Compte(s) absent(s) ou désactivé(s) dans le plan de la société ». Aucun `[object Object]`, aucune création comptable ni import implicite du compte 51419 dans le plan actif n'apparaît. Les contrôles finaux API/PostgreSQL confirment la liste d'écritures vide. Aucune erreur JavaScript ni réponse serveur 500 n'est observée.

## Exécution

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_ecriture_erreurs_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_session133_ecritures_montants.py Test/test_patch082_libelles_lignes_ecritures.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_ecriture_erreurs_isole.py
```

Premier run : **1 échec de préparation en 24,55 s**, aucun POST métier. Le test supposait deux lignes initiales alors que le formulaire en prépare trois ; les lignes vides sont exclues normalement de la soumission. L'assertion du nouveau test est corrigée sans changer l'application.

Run final E2E : **2 réussis en 22,58 s**, exit 0. Compilation Python : exit 0. Les tests connexes de montants/validation API sur PostgreSQL isolé et de libellés via helpers JavaScript sont **réussis : 55 tests en 28,44 s**, exit 0. Le fixture a construit l'application pour les parcours réels ; aucun fichier frontend/backend n'a été modifié pendant la globale.

## Limites

Aucune base réelle utilisée et aucune comptabilité réelle modifiée. Ce lot vérifie les messages 422 sur les comptes, le rejet métier des comptes hors société et le blocage du déséquilibre. Les périodes fermées et les autres erreurs possibles de saisie ne sont pas présentées comme couvertes par ce fichier. La recette utilisateur sur ses propres dossiers reste distincte.
