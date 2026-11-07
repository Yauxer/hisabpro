# Articles — frais d'emballage et de transport

Lot `ARTICLES-FRAIS-INTERFACE-20261008-269`.

## Analyse et périmètre

Le modèle, les schémas et les routes Article possèdent déjà `frais_emballage` et `frais_transport`, montants HT par unité. Le formulaire ne les affichait pas et ne les envoyait pas. Leur création/édition est exposée par deux champs facultatifs reprenant la DA/FormUX existante. Les valeurs stockées sont reprises à l'ouverture de la fiche. Les champs vides prennent le défaut explicite 0 déjà existant ; aucune nouvelle donnée obligatoire n'est ajoutée.

La validation locale vérifie la finité et le signe des prix, frais, taux, seuil et stock initial concerné, au lieu de ramener un montant non fini à zéro. La validité `badInput` des inputs number est également vérifiée : un navigateur peut exposer une saisie exponentielle hors capacité comme un champ vide. Le plafond TVA 0..100 préexistant est conservé ; aucun nouveau plafond monétaire n'est ajouté. Les aperçus TTC/marge n'affichent pas de résultat non fini.

Le stock actuel en édition reste en lecture seule, y compris un historique inconnu. Il n'est jamais envoyé dans le PATCH ; aucune correction de stock ni écriture comptable ne découle d'une modification de frais.

**Limite explicite :** ces montants de fiche ne sont pas copiés ni taxés automatiquement dans un document. L'utilisateur les reporte dans les frais du document selon les quantités et renseigne ses modes/qualifications. Le formulaire indique « Montants HT par unité, à reporter dans les frais du document selon la quantité. ».

## Tests

Deux parcours réellement exécutés dans Edge 1365 / 390 px, FastAPI et PostgreSQL nonce :

- Création d'une fiche avec prix de vente 100 HT, achat 60 HT, emballage 2,50 HT/unité, transport 7,25 HT/unité et stock initial 0.
- Refus local d'un emballage négatif et de `1e309` dans le transport, les deux prix, le seuil et le stock initial : message explicite et aucune requête de création/édition.
- Édition des frais à 3,75 et 8,50, puis réouverture depuis la liste mise à jour, sans F5 : valeurs persistées et relues aussi par le vrai GET liste.
- Création avec frais vides : défauts 0 acceptés, aucun champ ajouté obligatoire.
- Article historique fictif dont le stock est NULL, préparé exclusivement dans la base nonce avant la connexion : affichage inconnu/lecture seule, édition d'emballage 1,25 → 1,75, stock exclu du PATCH et NULL conservé.
- Vérification DB finale : stock du nouvel article 0, historique NULL, **0 mouvement de stock et 0 écriture comptable** pour la société du scénario.

Les deux premiers runs ont échoué sur des erreurs de préparation du nouveau test, conservées ici explicitement :

1. **1 failed en 41,89 s** : le test cherchait « Stock historique » tandis que l'interface affiche le diagnostic API existant « Stock physique inconnu ou invalide : vérifier la source historique. ». Les contrôles locaux et le CRUD des frais avaient déjà franchi leurs assertions. Seul ce sélecteur est corrigé.
2. **1 failed en 22,86 s** : la vérification finale utilisait un GET article par identifiant inexistant. La route de lecture existante est le GET liste. Le test est corrigé pour vérifier le HTTP 200 de cette route puis retrouver l'identifiant concerné, sans ajout de route ni modification d'oracle.

Le cas mobile n'était pas exécuté dans ces deux runs arrêtés par `-x`. Aucun de ces échecs n'est déclaré réussi rétroactivement.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_articles_frais_isole.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_articles_stock_inconnu_isole.py Test/test_articles_archivage_navigateur.py Test/test_patch069_stock_services.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_articles_frais_isole.py
npm run build
```

Résultats finaux :

- Ciblés : **2 passed en 25,75 s, exit 0**, desktop et mobile réellement exécutés sur l'API/PostgreSQL nonce.
- Connexes : **11 passed en 26,35 s, exit 0**. Le stock historique inconnu est testé contre l'API/PostgreSQL réels isolés ; les deux anciens cas d'archivage navigateur utilisent leurs réponses synthétiques existantes, et les autres tests de services/stock sont les tests unitaires existants. Ce groupe n'est pas présenté comme 11 recettes PostgreSQL connectées.
- Compilation Python : **exit 0**.
- Build Vite : **138 modules, 4,63 s, exit 0**. Avertissements XLSX et taille des chunks existants.

Aucun échec, erreur ou test ignoré dans les deux commandes finales. Les avertissements Pydantic/Starlette existants restent présents. Le schéma API 268 stable est utilisé sans modification de schéma ni backend dans le présent lot ; ses tests exécutés par l'agent principal ne sont pas comptés comme des commandes exécutées ici.

## Fichiers différentiels

- `src/pages/Articles.jsx`
- `Test/test_e2e_articles_frais_isole.py`
- `Test/rapport_e2e_articles_frais_isole.md`

Journal et ZIP vérifié : agent principal uniquement. Recette utilisateur et installation réelle restant à vérifier ; aucune donnée ou base réelle n'est utilisée ici.
