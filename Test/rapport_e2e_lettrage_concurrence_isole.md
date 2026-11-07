# Chargements concurrents du lettrage — 8 octobre 2026

Le parcours annuel connecté a révélé qu'une réponse client 3421 tardive pouvait remplacer les lignes fournisseurs 4411 après un changement rapide de filtre. L'écran conservait alors le filtre fournisseurs et affichait des tiers clients. Les montants comptables n'étaient pas modifiés ; le défaut concerne l'état affiché et la sélection d'auxiliaires.

Le test spécifique utilise Microsoft Edge, FastAPI et PostgreSQL éphémère. Il retient une vraie réponse HTTP client obtenue par `route.fetch()`, rend une vraie réponse fournisseur, puis libère la réponse client conservée. Aucun corps JSON, montant ou statut métier n'est inventé. Cette instrumentation contrôle exclusivement l'ordre de livraison réseau afin de reproduire la concurrence.

Commande :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_lettrage_concurrence_isole.py -x
```

Les deux premiers runs de préparation ont échoué avant la vérification de la course : mauvaise URL d'interception `/lignes` au lieu de `/comptable` (33,30 s), puis sélecteur de texte trouvant une option cachée au lieu de la cellule du tableau (33,25 s). Les corrections portent uniquement sur le test.

Troisième run avant correction : **un échec réel en 17,84 secondes**. La sélection est toujours 4411 après libération de la réponse client tardive, mais le tableau affiche la facture client de 1 200 MAD et son règlement de 400 MAD au compte 3421. La réponse fournisseur avait auparavant été affichée et les deux réponses HTTP réelles avaient été vérifiées distinctes. Le défaut est ainsi reproduit de façon déterministe. Les résultats après correction restent à consigner.

Aucune base réelle utilisée. Les données et règles de lettrage ne sont pas modifiées pour contourner cette anomalie.

## Correction et tests après correction

`Lettrage.jsx` conserve le scope compte/exercice courant et une version de chargement. Une ancienne closure ne peut plus lancer un refresh pour un scope abandonné. Les réponses, erreurs et fins de chargement ne modifient l'état que si leur scope et leur version restent courants. Le cleanup invalide les requêtes lors d'un changement ou du démontage.

Le même test strict est **réussi en 17,41 s**, exit 0, sur Edge / FastAPI / PostgreSQL éphémère. La réponse client tardive ne remplace plus les lignes fournisseurs et le snapshot comptable reste inchangé. `py_compile` du test : exit 0. `npm run build` : exit 0, 139 modules, 5,88 s ; avertissements existants de taille de bundle et d'import SheetJS mixte.

Commande connexe : `python -X utf8 Test/run_unit_tests.py Test/test_e2e_facturation_isole.py -x`, avec `PYTHON_DOTENV_DISABLED=1`. Les deux cycles achat/vente, validation, règlement et lettrage sont **réussis en 26,59 s**, exit 0, sur Edge / FastAPI / PostgreSQL éphémère.

La reprise annuelle attend la livraison différentielle vérifiée de ce correctif. Ce test ne revendique ni recette utilisateur complète ni validation réglementaire.
