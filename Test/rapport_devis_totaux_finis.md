# Lot 254 — Totaux de devis finis avant écriture en base

## Preuves avant correction

Les valeurs individuelles des lignes étaient déjà contrôlées, mais leurs produits et sommes pouvaient devenir infinis. Deux requêtes réelles, API authentifiée et PostgreSQL nonce exclusivement, ont reproduit le défaut avec une quantité `1e308` et un prix unitaire `10` :

- POST `/api/devis` : HTTP 500 après commit ; devis et ligne persistés malgré l’échec de réponse. Test avant correction : **1 échec en 16,10 s**, session 51379.
- PATCH `/api/devis/{id}` sur un devis initialement valide : HTTP 500 après remplacement des lignes et persistance de la note. Test avant correction : **1 échec, 9 désélectionnés en 15,85 s**, session 28125.

Chaque preuve compare les sources avant/après et constate effectivement la mutation. Ces données sont fictives et appartiennent aux clusters nonce créés puis arrêtés par les fixtures ; aucune donnée utilisateur réelle n’a été lue ou réparée.

## Correction minimale

Un contrôle commun dans `schemas.py` vérifie, uniquement sur les requêtes `DevisCreate` et `DevisUpdate` fournissant des lignes, la finitude des montants HT/TVA/TTC de chaque ligne et des sommes HT/TVA/TTC du devis. Il suit les expressions float existantes du routeur, notamment la formule TTC de ligne et le taux effectif nul pour une qualification non taxable. Les calculs de montants et règles TVA existants restent inchangés.

Les dépassements sont refusés par HTTP 422 avant les mutations et la réservation d’un numéro. Aucun plafond arbitraire métier ou taux fiscal nouveau. Les changements de notes sans lignes et les mises à jour avec `lignes: null` restent possibles. Le contrôle n’est pas placé dans `LigneDevisCreate`, dont hérite `LigneDevisOut` : aucune nouvelle règle de lecture historique, aucune réparation silencieuse des anciens montants.

## Vérifications réellement exécutées

Environnement `hisabpro-backend/.venv/Scripts/python.exe`, `PYTHON_DOTENV_DISABLED=1`. La fixture API/PG vérifie le nonce et le répertoire isolé avant utilisation ; PostgreSQL réel de l’utilisateur exclu.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_devis_totaux_finis.py Test/test_documents_valeurs_finies.py Test/test_devis_stock_limites_numeriques.py
```

**127 tests réussis en 79,26 s**, 25 avertissements de dépendances existants, session 95089, code 0. Cette commande contenait 14 tests nouveaux ; un dernier test pur de qualification effective a été ajouté après sa collecte et est couvert par la relance finale ciblée.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_devis_totaux_finis.py
```

Relance finale : **15 tests réussis en 19,66 s**, 25 avertissements, session 29714, code 0 ; le dernier test confirme que le contrôle respecte le taux effectif nul déjà utilisé pour la qualification non taxable. Ce test de schéma ne dispense pas des contrôles TVA supplémentaires de la route.

La couverture vérifie création et modification pour débordement du produit, somme de deux lignes, TTC de ligne et TTC total ; chaque refus conserve les sources. Des devis fractionnaires, gratuits et grands mais finis (`1e308` HT / `1.2e308` TTC) restent créables et modifiables. Les tests connexes conservent les rejets NaN/booléens et les grands cumuls Decimal du diagnostic stock.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile hisabpro-backend/schemas.py Test/test_devis_totaux_finis.py
```

Compilation : code 0.

## Limites et prochaine étape

Pas de validation navigateur supplémentaire dans ce lot API. Les anciens devis dont les produits débordent ne sont pas réécrits ; leur éventuelle anomalie de lecture reste une réparation historique distincte à auditer. La précision float, les arrondis et les règles commerciales restent ceux du produit existant. Cette correction ne prétend pas protéger d’autres types de documents non examinés dans ce lot.

Prochaine étape : inclure les nouveaux cas dans la prochaine consolidation, puis reprendre la recette commerciale fictive.
