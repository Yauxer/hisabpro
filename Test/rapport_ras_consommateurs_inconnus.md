# Consommateurs des soldes RAS inconnus — lot 296

9 octobre 2026. Correctif ciblé des deux consommateurs détectés pendant le lot291 : dashboard commercial et PDF de balance âgée. Aucun taux fiscal, règle d'imputation, migration ou modification des écritures historiques.

## Résultat et contrat

Le dashboard conserve les `null` d'un domaine incomplet pour les encours, retards, taux de recouvrement et nombre de clients en retard. Son résumé ajoute `calcul_incomplet_clients` et `calcul_incomplet_fournisseurs`. Les classements du domaine concerné conservent encours et retard maximal à `null`, accompagnés de `encours_anomalie`. `diagnostics_ras` liste les identifiants, références, domaines et diagnostics source. CA, achats, marges et arrondis des autres montants restent inchangés.

Le PDF de balance âgée continue à être téléchargeable. Une facture indéterminable reste visible avec sa référence et son diagnostic ; ses montants affichent « À vérifier ». Tous les totaux du domaine incomplet affichent également « À vérifier », sans prétendre totaliser uniquement les montants connus. Les autres genres de balances conservent leur moteur et leur présentation ; aucune valeur n'est réparée en base.

## Exécution réelle

Commande avant correction :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_ras_consommateurs_inconnus_postgres.py -x --tb=short
```

Session48364 : **1 échec, 25 avertissements, 22,68 s**. Une facture historique à RAS NaN, dont le recouvrement qualifie le solde d'inconnu, produisait `encours_clients=0` dans le dashboard. L'affichage trompeur est reproduit par une vraie API et un cluster PostgreSQL nonce isolé.

Première reprise après correctif : session77239, **2 échecs, 25 avertissements, 21,76 s**. Les indicateurs étaient corrigés mais l'arrondi final des classements reconvertissait encore leurs encours inconnus en zéro. Cette seconde cause a été corrigée uniquement pour le champ encours, sans modifier la fonction universelle d'arrondi.

Deuxième reprise avec connexes : session9621, **10 réussis, 2 échoués, 25 avertissements, 68,75 s**. Les tests des PDF indéterminables exigeaient une phrase contiguë malgré le retour de ligne de la cellule PDF. Correction du test par normalisation des espaces lors de l'extraction, sans changement de contenu ou d'attente métier.

Commande finale :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_ras_consommateurs_inconnus_postgres.py Test/test_fact10_dashboard_commercial.py Test/test_e2e_balances_exports_isole.py --tb=short
```

Session24231 : **12 réussis, 25 avertissements, 68,58 s, sortie0**.

Compilation des deux services et du test : **sortie0**.

## Couverture et limites

Les deux scénarios API couvrent clients et fournisseurs : facture historique NaN préparée avant son état définitif, diagnostics et montants JSON inconnus, classement, téléchargement du PDF âgé et extraction de sa référence, diagnostic et totaux à vérifier. Une écriture100/100 validée est créée pour le contrôle ; les snapshots de ses écritures et lignes restent strictement identiques après les lectures et exports. La valeur historique NaN demeure inchangée. Le PDF général conserve ses montants100 et ne reçoit pas les avertissements propres à la balance âgée.

Les connexes réexécutent le dashboard et les exports navigateur normaux de balances, incluant les variantes comparative et résultat existantes. L'UX des données inconnues et ses exports Excel/CSV sont traités séparément dans le lot297. Les tests n'accèdent jamais au PostgreSQL réel de l'utilisateur ; aucune certification ou validation réglementaire n'est revendiquée.
