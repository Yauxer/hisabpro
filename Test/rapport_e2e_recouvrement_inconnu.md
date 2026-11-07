# Recouvrement : soldes historiques indéterminés

Lot 295 — 9 octobre 2026. Périmètre : interface Situation financière et recouvrement, test navigateur isolé, présent rapport. Aucun calcul fiscal, taux, règle de comptabilisation ou historique comptable modifié.

## Anomalie reproduite

L’API du lot 291 conserve un diagnostic lorsqu’un taux de RAS historique est invalide : imputation et reste dû sont `null`, statut `indetermine`, agrégats concernés marqués `calcul_incomplet`. La page transformait ces valeurs en zéro, affichait notamment « 0,00 MAD », « null facture ouverte » et « 0.0 % ». Le filtre par défaut « Toutes les ouvertes » masquait également la pièce parce que JavaScript compare `null <= 0.01` comme vrai.

Avant correction, la nouvelle recette réelle Edge a échoué sur l’absence de « À vérifier » dans le KPI, après vérification des valeurs nulles de l’API : **1 échec en 30,72 s**, avec arrêt au premier échec. Commande :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_recouvrement_inconnu_isole.py -x --tb=short
```

## Correction minimale

`src/pages/SituationFinanciere.jsx` distingue un nombre fini d’un montant indéterminable. Les KPI, la position nette, l’ancienneté, la balance âgée et les cellules concernées affichent « À vérifier ». Les pourcentages, nombres de pièces et ventilations inconnus ne sont plus présentés comme nuls. Une notice signale les calculs incomplets ; le diagnostic de RAS est visible sur la ligne de facture.

La pièce indéterminée reste présente dans le filtre par défaut, sans être classée comme réglée et sans proposer une relance chiffrée. L’export CSV distingue également « À vérifier » d’un véritable zéro et ajoute le diagnostic. Les valeurs connues restent numériques avec virgule décimale. Les filtres explicites par statut ou montant conservent leur fonction ; cette correction ne qualifie pas les pièces inconnues comme impayées ou échues.

## Tests réellement exécutés

La fixture existante installe PostgreSQL et l’application dans un environnement nonce isolé. Deux sociétés fictives sont créées par API. Dans la première, une facture normale de 1 000 HT + 200 TVA conserve un reste dû de 1 200 ; le taux de RAS estimé ne constitue pas un règlement. Une seconde pièce historique fictive reçoit `NaN` pendant qu’elle est encore brouillon, avant son passage simultané à l’état validé. Aucun trigger n’est désactivé, aucune pièce déjà définitive n’est réécrite.

Les tests Edge aux largeurs **1 365 et 390 pixels** vérifient le KPI indéterminé, la présence de la facture sous le filtre par défaut, les trois mentions « À vérifier », le diagnostic, l’absence de bouton Relancer, la facture normale, la balance âgée et les CSV réellement téléchargés et ouverts. L’autre société ne reçoit aucune de ces factures. Les snapshots de factures, règlements, écritures et lignes d’écriture sont identiques avant et après toutes les lectures.

Première exécution après correction, aux largeurs initiales 1 440/820 : **2 tests réussis en 28,64 s**. Puis renforcement du sélecteur KPI et du snapshot des lignes, et remplacement des largeurs par 1 365/390. Validation finale :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_recouvrement_inconnu_isole.py Test/test_e2e_recouvrement_isole.py Test/test_fact7_recouvrement.py Test/test_recouvrement_promesse_montants.py --tb=short
```

**34 tests réussis en 76,95 s ; aucun test ignoré ; sortie 0.** Les 25 avertissements concernent les dépréciations existantes Pydantic et python-multipart.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_recouvrement_inconnu_isole.py
npm run build
```

Compilation Python : sortie 0. Build Vite : sortie 0, **138 modules, 8,96 s**, avec les avertissements existants de taille de bundle et d’import XLSX mixte.

## Limites et reprise

Aucun accès à PostgreSQL réel ni redémarrage de l’application de l’utilisateur. Les vérifications navigateur sont automatisées sur l’application isolée ; la recette utilisateur reste à effectuer. Ce lot rend le diagnostic visible, sans réparer les historiques ni valider l’applicabilité fiscale d’une retenue. La capture explicite d’une retenue et les autres écrans sont des lots distincts. Le journal et le ZIP différentiel sont gérés par l’agent principal.
