# Réceptions partielles avec stock au BR — lot 280

Recette réelle du 9 octobre 2026 UTC. Deux nouveaux fichiers uniquement :
`Test/test_e2e_cycle_achat_reception_partielle_isole.py` et ce rapport.
Aucun correctif applicatif, aucune migration et aucune donnée réelle modifiés.

## Règle existante observée

La société autorise déjà `stock_declencheur_achat=br` via PATCH `/api/societe/moi`.
Ce réglage est appliqué par cette API réelle, puis sa réponse est vérifiée, pour
chaque société fictive. Le moteur commercial déclenche une entrée de stock quand
le BR passe au statut `livre`, à partir de la quantité reçue. Le moteur facture
ne répète pas ce mouvement lorsque ce réglage vaut `br`.

Le reliquat BC est calculé par identifiant de ligne source. Il permet une première
réception d'une unité sur quatre, puis une deuxième des trois unités restantes.
Les livraisons actives, y compris les quantités portées sur un BR préparé, alimentent
ce suivi existant ; ce lot ne change ni cette règle ni une réservation de stock.

## Données exactes et oracle indépendant

Une société fictive et un fournisseur rattaché au compte 4411 sont créés par
authentification/API réelles dans PostgreSQL nonce. Un article stockable commence
à zéro, prix d'achat 500 MAD HT et TVA 20 %, compte achat 6111.
Un BC de quatre unités est préparé par API : HT 2 000, TVA 400, TTC 2 400 MAD.

Dans Edge, le premier BR reçoit une unité ; le second en reçoit trois.
Chacun donne sa propre facture fournisseur brouillon. La référence fournisseur
et la qualification charge / déductible 100 % sont saisies explicitement dans
l'éditeur navigateur du lot 275 avant validation. Le PATCH navigateur et les
valeurs persistées sont vérifiés. Le taux et la qualification sont des données
de recette choisies, pas une nouvelle affirmation de droit fiscal à déduction.

| Phase | Stock après réception | HT facture | TVA | TTC |
|---|---:|---:|---:|---:|
| BR 1 : une unité | 1 | 500 | 100 | 600 |
| BR 2 : trois unités | 4 | 1 500 | 300 | 1 800 |
| Total | 4 | 2 000 | 400 | 2 400 |

Deux écritures sont générées puis validées dans le Journal. Leur cumul réellement
contrôlé vaut D6111 = 2 000, D34552 = 400, C4411 = 2 400 MAD. Chaque écriture est
équilibrée ; le total débit = total crédit = 2 400 MAD. Les lignes fournisseur
conservent le vrai tiers et son snapshot auxiliaire du jeu fictif.

## Contrôles navigateur/API/PostgreSQL exécutés

- Edge headless bureau 1 365 px et mobile 390 px, sans clic forcé.
- BC → Réceptionner : quantité préremplie 4, remplacée par 1. Deuxième ouverture :
  quantité restante préremplie 3, reçue intégralement.
- Chaque BR : Marquer en cours, Marquer réceptionné, puis Facturer depuis ce BR.
- Après chaque préparation BR, aucun mouvement supplémentaire avant confirmation.
  Après réception, stocks 0 → 1 puis 1 → 4, exactement deux entrées 1 et 3.
- Source stock `bon_reception`, identifiants exacts du BR et de sa ligne, coût
  unitaire 500 et clé d'idempotence. Ni validation facture, ni comptabilisation,
  ni refus de conversion, ni rechargement ne crée un troisième mouvement.
- Reliquat BC : 3 après première réception, 0 après seconde, quantités reçues 1/4.
  Une demande de quatre après la première réception est refusée 400 ; une nouvelle
  conversion après réception complète est refusée 400.
- Chaque facture conserve les liens techniques à la même ligne BC et à sa propre
  ligne BR, l'article et la quantité réelle 1 ou 3. Chaque BR conserve son facture_id.
- Double conversion de chacun des BR en facture : 409. Double comptabilisation
  de chacune des factures : 409. Exactement un BC, deux BR, deux factures et deux
  écritures subsistent.
- Toutes les colonnes persistées des écritures validées sont comparées avant/après
  les refus. La première écriture reste identique pendant le deuxième cycle.
- Les deux factures apparaissent dans Cycle commercial → Achat → Factures,
  puis encore après rechargement ; intégrité des écritures et stock final revérifiés.
- Aucune erreur JavaScript ni réponse 5xx observée dans les parcours finaux.

## Commandes et résultats réels

Depuis la racine, avec les fixtures PostgreSQL éphémères gardées par répertoire
et nonce ; aucun PostgreSQL utilisateur, aucun processus utilisateur modifié :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_e2e_cycle_achat_reception_partielle_isole.py -x
```

- Première exécution : session 90764, sortie 1, **1 failed**, 25 avertissements,
  **37,98 s**. Préparation du cas négatif incorrecte : le payload de dépassement
  du reliquat omettait la description obligatoire ; 422 avant le garde-fou métier
  attendu à 400. Le premier BR et l'entrée 0 → 1 étaient déjà réussis. Correction
  de ce payload test uniquement, aucune modification applicative.
- Deuxième exécution : session 82439, sortie 0, **2 passed**, 25 avertissements,
  **36,27 s**. Puis renforcement de la comparaison des écritures déjà validées.
- Version finale ciblée et tests connexes :

```powershell
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_e2e_cycle_achat_reception_partielle_isole.py Test/test_e2e_cycle_achat_isole.py Test/test_e2e_facture_achat_tva_edition_isole.py
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 -m py_compile Test/test_e2e_cycle_achat_reception_partielle_isole.py
```

Session 70995, sortie 0 : **6 passed**, 25 avertissements, **96,79 s** : deux
réceptions partielles, deux cycles stock à facture et deux éditions TVA achat.
Compilation Python terminée, sortie 0. Avertissements multipart et configuration
Pydantic existants. Aucun build supplémentaire nécessaire pour ce lot de tests
seulement ; le build applicatif précédent est documenté séparément au lot 275.

## Limites et suite

Le BC initial et le paramètre de déclenchement du stock sont préparés par l'API,
les réceptions et factures ensuite par le navigateur. Une facture par BR est
testée ; le découpage d'un seul BR en plusieurs factures ne l'est pas ici.
Les retours de BR, annulations, ventes, paiements/lettrage, exports et permissions
inter-sociétés ne sont pas ajoutés à ce scénario. Le test n'a pas pour effet
de modifier l'historique réel ou de certifier le traitement réglementaire.
Une suite indépendante possible est la facturation partielle d'un même BR,
avec les mêmes contrôles d'absence de double entrée stock et de conservation
des pièces définitives.

## Prolongement distinct — lot 283, 9 octobre 2026

Les sections précédentes conservent la recette livrée au lot 280. Le lot 283
étend les mêmes deux fichiers après dégel explicite, sans recopier le scénario
BC/BR ni modifier le code applicatif. Il ajoute les paiements séparés des deux
factures et leur lettrage commun. Les anciennes limites paiement/lettrage du
lot 280 sont levées pour ce scénario précis, sans étendre les autres limites.

### Diagnostic mobile et limite de la suite globale précédente

La suite globale 278 exécutée par l'agent principal a terminé en erreur :
2 575 tests réussis et quatre échecs. Son XML, consulté ici dans
`.codex-tests/global_20261009_1404.xml`, porte 2 579 tests, quatre échecs,
zéro erreur de setup, zéro ignoré et durée XML 2 079,317 s. Le cas mobile de ce
fichier affiche uniquement `Locator.inner_text: Timeout 20000ms exceeded` dans
le bloc de diagnostic, masquant l'exception initiale. Le rapport court de cette
exécution ne permet pas d'en établir la cause métier ou navigateur.

Le diagnostic est désormais best-effort : lecture du body bornée à deux secondes,
échec secondaire capturé, puis l'exception initiale est réémise. Aucune assertion,
attente fonctionnelle ni règle applicative n'est assouplie. Avant l'extension,
le cas mobile existant a été réellement relancé seul : **1 passed**, 25
avertissements, **21,90 s**, session 51212, sortie 0. L'échec initial n'est donc
pas reproduit isolément ; **sa cause reste inconnue**. Ce lot corrige le masquage
du diagnostic, sans prétendre corriger une cause de l'échec global non démontrée.
Une nouvelle suite globale reste nécessaire et est suivie séparément par le
principal ; ces tests ciblés ne la remplacent pas.

### Oracle complémentaire et contrôles exécutés

Après les deux factures déjà validées, le navigateur ouvre successivement
Factures → Payer le fournisseur pour la pièce de 600 MAD puis celle de 1 800 MAD.
Le montant prérempli et le `facture_id` de chaque règlement sont contrôlés.
Le mode existant de virement génère deux écritures, D4411/C5141 = 600 puis 1 800.
Chaque situation de facture confirme son total réglé et un solde nul.

Les deux écritures de paiement sont ensuite validées dans le Journal. Il reste
quatre écritures définitives / dix lignes ; cumul débit = crédit = **4 800 MAD**.
Soldes débit moins crédit réellement vérifiés : 6111 = 2 000, 34552 = 400,
4411 = 0, 5141 = −2 400 MAD. Ces chiffres sont la somme indépendante des deux
achats et des deux règlements ; aucun avoir, escompte, acompte ou RAS ajouté.

Dans Lettrage, compte 4411 et même tiers réel : les quatre lignes sont sélectionnées
et lettrées par un seul code `AAA`. Débits et crédits fournisseurs se compensent
à 2 400 MAD. Après rechargement, les quatre lignes restent lettrées et le code
est vérifié en PostgreSQL pour chaque ligne. Toutes les colonnes persistées des
écritures et de leurs lignes restent identiques avant/après lettrage. Les deux
écritures d'achat restent également identiques pendant les règlements.

Le stock reste strictement à quatre unités et les seuls mouvements restent les
deux entrées issues des BR. Tous les contrôles de reliquat, double conversion,
double comptabilisation, liens sources et intégrité du lot 280 sont conservés.
Les deux largeurs réelles Edge 1 365 / 390 px exécutent ce parcours jusqu'au bout,
sans erreur JavaScript ni 5xx observée.

### Commandes et résultats de cette extension

Avec `PYTHON_DOTENV_DISABLED=1`, depuis la racine :

```powershell
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py 'Test/test_e2e_cycle_achat_reception_partielle_isole.py::test_cycle_reception_partielle_stock_br[390]' -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_e2e_cycle_achat_reception_partielle_isole.py -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_e2e_cycle_achat_reception_partielle_isole.py Test/test_e2e_avoir_fournisseur_isole.py Test/test_e2e_acompte_fournisseur_isole.py Test/test_e2e_facture_achat_tva_edition_isole.py
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 -m py_compile Test/test_e2e_cycle_achat_reception_partielle_isole.py
```

- Reproduction avant extension : session 51212, sortie 0, 1 passed / 25
  avertissements / 21,90 s, détaillée ci-dessus.
- Extension bureau/mobile : session 84185, sortie 0, **2 passed**, 25
  avertissements, **33,67 s**.
- Ciblés et connexes finaux : session 69656, sortie 0, **8 passed**, 25
  avertissements, **118,89 s** : deux réceptions partielles réglées/lettrées,
  deux avoirs fournisseurs, deux acomptes fournisseurs et deux éditions TVA.
- Compilation Python : sortie 0. Aucun build supplémentaire, puisqu'aucune source
  frontend ou backend n'a changé dans ce lot.

Les scénarios restent isolés et fictifs. Aucun PostgreSQL réel, aucune réparation
historique, aucun nouveau régime fiscal ou taux et aucune recette utilisateur
officiellement validée ne sont impliqués.
