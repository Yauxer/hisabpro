# Lot 260 — BC/BL, totaux finis avant mutation

## Anomalies reproduites réellement

API authentifiée et PostgreSQL nonce uniquement, sans donnée réelle :

- BC créé avec quantité `1e308`, PU HT `10` : HTTP 500 après persistance. **1 échec en 20,19 s**, session 23405.
- BC modifié avec les mêmes valeurs, vente et achat : HTTP 500 après remplacement des lignes et persistance de la note.
- BL créé avec ces valeurs, vente et achat : HTTP 201 et données persistées ; la lecture de la liste devient HTTP 500. Ces deux défauts ne sont pas présentés comme un HTTP 500 à la création du BL.

La seconde commande de preuve donne **4 échecs, 29 désélectionnés en 20,67 s**, session 28950. Les snapshots montrent les mutations dans ces échecs. Aucun test ignoré ou échoué n’est déclaré réussi.

## Correction minimale

Un garde commun dans `schemas.py` contrôle les requêtes `BonCommandeCreate`, `BonCommandeUpdate` fournissant des lignes et `BonLivraisonCreate`. Il vérifie le produit brut, les deux remises successives, le rabais par quantité, le net avant son plancher zéro, puis HT/TVA/TTC et les sommes. Une opération intermédiaire infinie/NaN n’est pas masquée par une remise ou par le plancher zéro. Le rabais ordinaire conduisant à un net négatif fini reste autorisé avec le comportement existant à zéro.

Pour le BL, la quantité prévue et la quantité effectivement livrée sont vérifiées séparément : aucune substitution d’une quantité livrée nulle par la prévue dans les totaux. Exemple vérifié : prévue 2, livrée 0 → HT facturable 0 ; prévue 2, livrée 1 → HT facturable 67 pour PU100/remises10 % puis20 %/rabais5.

Le taux effectif suit la qualification existante, sans règle fiscale nouvelle ni montant maximal arbitraire. Les sorties historiques `LigneBCOut` et `LigneBLOut` ne sont pas durcies. `BonLivraisonUpdate` ne permet pas de modifier les lignes dans le contrat existant : aucun champ ou comportement nouveau ajouté. Notes seules et `lignes: null` du BC conservent le contrat antérieur.

## Commandes et résultats

Python du dépôt : `hisabpro-backend/.venv/Scripts/python.exe`, `PYTHON_DOTENV_DISABLED=1`. Le garde-fou de fixture vérifie la cible PG nonce avant toute opération.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_bc_bl_totaux_finis.py -x
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_bc_bl_totaux_finis.py -k 'lignes0 and (bc_patch or bl_create)'
```

Preuves avant correction : résultats d’échec décrits ci-dessus.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_bc_bl_totaux_finis.py Test/test_documents_valeurs_finies.py Test/test_devis_totaux_finis.py
```

Après correction : **148 tests réussis en 77,34 s**, 25 avertissements de dépendances existants, session 56940, code 0. Parmi eux, 33 nouveaux cas BC/BL : vente/achat, création et modification BC, création BL, cinq types de débordement, remise/rabais, gratuité, fractions, quantité livrée zéro et lecture de la liste. Chaque refus compare articles, mouvements, bons/lignes, écritures/lignes avant/après sans mutation. Les 115 tests connexes couvrent les saisies commerciales finies et les totaux de devis du lot 254.

Après ajout d’une assertion pure sur le rabais ordinaire à net négatif fini : `... Test/test_bc_bl_totaux_finis.py -k bornes_representatives` → **1 réussite, 32 désélectionnés en 1,09 s**, 25 avertissements, code 0.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile hisabpro-backend/schemas.py Test/test_bc_bl_totaux_finis.py
```

Compilation : code 0.

## Limites et reprise

Pas de test navigateur supplémentaire dans ce lot API. Les anciens bons comportant déjà des opérations non finies ne sont ni réécrits ni artificiellement corrigés. Les montants des factures suivent un calcul Decimal distinct, hors de ce lot.

Une limite d’export extrême reste identifiée par lecture du code : le PDF BC calcule la TVA par `ht * taux / 100`, tandis que le JSON utilise `ht * (taux / 100)` ; la première expression peut déborder pour un HT très grand alors que le résultat mathématique est fini. Ce PDF extrême n’a pas été validé ici ; traiter séparément la stabilité de ses calculs sans inventer de plafond métier. Les sommes extrêmes de quantités gratuites dans les tableaux de reliquat restent aussi à examiner séparément.

Prochaine étape : correction indépendante des totaux de factures et, si nécessaire, export PDF extrême, puis consolidation globale.
