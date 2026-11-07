# Captures TVA, états, IS et lettrage — lot587

Deux parcours ont été exécutés sur sociétés fictives, vraie API et PostgreSQL
nonce099 sous LOGIN limité ; le lettrage utilise réellement Edge, en1440px
pour la vente et390px pour l'achat. Aucun changement du produit dans ce lot.

## Données et oracles indépendants

Chaque société dispose d'un apport fictif10000,00 MAD en banque. Facture de
service : HT1000,00, TVA200,00, TTC1200,00. Deux règlements réels de525,00,
chacun rapproché d'une quote-part600,00 et d'une capture guidée75,00.
Les conditions du calcul sont des déclarations fictives de laboratoire.
Les comptes de destination employés par le banc sont des choix techniques,
pas une affectation comptable imposée ni une nouvelle qualification fiscale.

| Contrôle | Vente | Achat |
|---|---:|---:|
|CPC courant, avant éventuelle comptabilisationIS|1000,00|-1000,00|
|Total bilan après premier paiement|11200,00|9675,00|
|Total après sa capture TVA|11200,00|9675,00|
|Total après deuxième paiement et capture|11200,00|9150,00|
|Total après annulation du deuxième paiement/capture|11200,00|9675,00|

La capture reclasse des postes du bilan sans modifier le CPC. Le paiement
d'achat diminue l'actif et le passif, contrairement à l'encaissement client
qui reclasse la créance en banque. Les deux bilans restent équilibrés.
Les calculs, acomptes, crédits et liquidationIS sont identiques avant/après
capture, lettrage et annulation : aucun crédit fiscalIS ou acompte n'est créé
par la retenue TVA. Cela ne valide pas l'applicabilité d'un régime fiscal.

Après paiement complet :6écritures/13lignes, débit=crédit=12400,00 MAD,
calculé indépendamment :10000+1200+525+75+525+75. Cinq lignes auxiliaires
sont lettrées dans Edge, codeAAA : facture1200 contre trésorerie1050 et
retenues150. Le solde opérationnel est nul.

Vente : contrepassation directe après lettrage, selon le comportement existant,
sans réécriture du groupe initial. Achat : délettrage préalable dans Edge,
avec confirmation réelle, puis contrepassation. Après annulation :17lignes,
débit=crédit=13000,00 ; solde de facture600,00, capture active validée75,00
et annulée75,00. Les lignes et en-têtes des six écritures initiales sont
identiques aux originaux ; les contrepassations sont des écritures distinctes.

## Exécutions

- Premier prototype :2échecs,29avertissements,39,43s. L'oracle supposait à tort
  un bilan achat invariant lors d'un paiement et un refus409 à l'annulation
  lettrée. Analyse du comportement existant ; scénario financé et oracles
  corrigés, aucune règle métier imposée pour satisfaire le test.
- Deuxième exécution :1réussi/1échoué,29avertissements,60,67s. Le test achat
  n'acceptait pas la confirmation native de délettrage ; timeout sans POST.
- Finale :**2réussis,29avertissements,40,63s, code0**, avec confirmationAAA
  effectivement acceptée et vérifiée. Aucun test ignoré ou interrompu dans
  cette exécution. Compilation Python du fichier ajoutée à la livraison.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_ras_tva_coherence_isole.py -ra
```

Ces2parcours complètent les137tests consolidés585 ; ils ne les remplacent pas.
La déclarationTVA, l'imputation de retenueTVA et son reversement restent hors
de cette qualification. Aucune base réelle ou écriture historique touchée,
aucune recette humaine validée. Prochaine étape : sources et modèles officiels
de la déclaration, puis autres lots hors RH/paie.
