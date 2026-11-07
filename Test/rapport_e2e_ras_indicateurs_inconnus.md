# RAS : indicateurs et balance âgée indéterminables

Lot : `RAS-INDICATEURS-INTERFACE-20261009-297`.

## Périmètre

Le pilotage commercial distingue un montant connu de zéro et un montant indéterminable. Lorsque le serveur signale une RAS historique invalide, l'encours, le retard et le taux concernés affichent « À vérifier », avec la référence de la facture et le diagnostic. Le chiffre d'affaires et les achats connus restent affichés.

La balance âgée conserve la facture indéterminable dans le domaine clients ou fournisseurs. Son solde, ses tranches et les totaux du domaine affichent « À vérifier ». Les fichiers CSV et Excel gardent ces nombres vides et ajoutent un diagnostic explicite ; le PDF utilise le moteur serveur du lot 296. Les exports normaux conservent leurs dix colonnes. Aucun calcul comptable ni taux fiscal n'est modifié. Les autres balances et la gestion des dates du lot 266 sont conservées.

## Banc et oracles

FastAPI réelle, PostgreSQL temporaire avec garde de nom et de connexion, Edge sans données réseau simulées. Deux largeurs : 1365 et 390 pixels. Chaque cas utilise une nouvelle société fictive et des tiers fictifs ; aucun PostgreSQL réel ni processus utilisateur n'est utilisé.

Scénario normal : vente de 1 000 HT + 200 TVA, achat de 500 HT + 100 TVA, aucun règlement. Encours clients 1 200, fournisseurs 600 ; taux de recouvrement 0 %. Les exports CSV, Excel et PDF sont réellement téléchargés et ouverts.

Scénario historique incomplet : une facture fictive supplémentaire de 1 000 HT + 200 TVA par domaine, avec une RAS NaN préparée uniquement dans le laboratoire avant fixation de l'état validé. Les références fournisseurs requises sont renseignées. Le chiffre d'affaires attendu est 2 000 HT, les achats 1 500 HT. Les deux domaines d'encours sont indéterminables. Les factures restent visibles et leurs nombres exportés ne deviennent jamais zéro.

Les cinq tables factures, lignes de facture, écritures, lignes d'écriture et règlements sont photographiées avant et après le parcours ; leurs lignes restent strictement identiques. Aucun règlement ni écriture n'est créé dans le parcours de consultation.

## Résultats exécutés ici

Commande ciblée :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_ras_indicateurs_inconnus_isole.py -x --tb=short
```

- Premier essai : 2 réussis, 1 échoué, arrêt au premier échec, 43,97 s. La préparation de la facture historique d'achat omettait sa référence fournisseur ; le trigger l'a refusée avant la recette du cas. Seul le nouveau jeu fictif a été complété, sans modifier le contrôle ni les données déjà validées.
- Relance finale : **4 réussis**, 25 avertissements de dépendances, **45,82 s**, code de sortie 0.
- Build frontend exécuté : `npm.cmd run build`, code de sortie 0, 138 modules, 4,67 s. Avertissements existants de regroupement des bundles.

Commande connexe :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_balances_exports_isole.py Test/test_e2e_balances_dates_contexte_isole.py Test/test_fact10_dashboard_commercial.py -x --tb=short
```

Résultat connexe : **13 réussis**, 25 avertissements de dépendances, **78,69 s**, code de sortie 0. Il comprend les quatre parcours d'exports des balances, les trois parcours de dates et contexte, ainsi que six contrôles du dashboard. Compilation du nouveau fichier : `python -X utf8 -m py_compile Test/test_e2e_ras_indicateurs_inconnus_isole.py`, code de sortie 0. Aucun fichier applicatif n'a changé depuis le build réussi. Les résultats du backend 296 sont rapportés séparément par son agent ; ils ne remplacent pas les quatre recettes exécutées ici.

## Limites

La RAS historique comptabilisée ne constitue pas une attestation. Les anomalies sont visibles et conservées, sans réparation automatique. Ce lot ne capture pas de RAS effective et n'active pas de nouvelle règle fiscale. La recette utilisateur sur son installation reste à effectuer ; aucune donnée de cette installation n'a été consultée ou modifiée.
