# Validation définitive — montants historiques, lot344

## Cause et reproductions réelles

Le contrôle partagé des montants représentables était utilisé à la création
et à l’édition, mais pas avant la validation définitive normale ou la
conversion d’une proforma. Certaines sources non finies pouvaient en outre
être masquées par les bornes `max(...,0)` du calcul existant.

Baseline prix :16échecs/12réussites,25avertissements,58,35s,code1 ; XML
28tests,16failures,0errors,0skipped,58,330s. Les seize cas portent sur achat/
vente, brouillon/proforma et prixNaN/+Inf/-Inf/1e308. Les témoins prix0/100 et
accès inter-société passent déjà. Sur ces seize tentatives, six renvoient500
sans persistance ; **dix renvoient200 et modifient effectivement facture,
lignes et séquence de numérotation**, photographies SQL nonce à l’appui.
Cela concerne notamment des proformas devenues définitives avec prix invalide.

Baseline supplémentaire :30échecs,28désélectionnés,25avertissements,
55,86s,code1 ; XML30tests,30failures,0errors,0skipped,55,837s. Quantité,
remise, rabais, transportHT et escompte historiques NaN/+Inf/-Inf sont testés
sur les deux voies de validation. Les journaux originaux500 et photos de
la première baseline sont conservés dans `.codex-tests/validation344_*`.

## Correction minimale

La garde partagée `_verifier_montants_representables` qualifie maintenant
les sources monétaires finies avant le moteur existant : cinq champs
monétaires du pied de facture et cinq champs par ligne. Les optionnelsNULL
gardent leur traitement antérieur ; les taux non utilisés ne sont pas
transformés en champs obligatoires. Les sources sont contrôlées avant que
des bornes ou compensations arithmétiques puissent masquer un non-fini.

Le contrôle existant des totaux et montants affichés reste inchangé. Les
erreurs numériques deviennent422 par la garde partagée. Celle-ci est
appelée avant les changements de date/snapshots, la réservation définitive,
les mouvements de stock et le passage à l’état validé, pour les deux routes.
La réponse idempotente d’une facture déjà validée reste antérieure à cette
garde : aucune réécriture ou réparation d’ancien document définitif.

Pas de nouveau barème, formule TVA/CMUP, taux fiscal, champ justificatif
obligatoire ou migration. Les valeurs connues restent calculées par le
moteur d’origine.

## Tests

Compilation des deux fichiers Python modifiés/ajoutés :code0.
Les58nouveaux cas utilisent l’API réelle et PostgreSQL éphémère vérifié
par URL/dossier/nonce. Photographies de factures/lignes/stocks/écritures,
séquences de facturation, exercices et périodes avant/après les refus.
**Sélection finale :91réussis,0échec/erreur/ignoré,25avertissements,
170,78s,code0.** XML `validation344_final.xml` relu. Les calculs TVA et les
contrôles structurels de facturation connexes passent, ainsi que les parcours
Edge réels facture achat/vente jusqu’au règlement/lettrage et éditionTVA achat.
Les58nouveaux cas confirment les refus422 sans changement des photos SQL,
la conservation des prix connus0/100 et les refus404 inter-société.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_validation_facture_montants_historiques_postgres.py Test/test_patch02b_tva_service.py Test/test_fact4_facturation_robuste.py Test/test_conform1_tva_frais.py Test/test_e2e_facturation_isole.py Test/test_e2e_facture_achat_tva_edition_isole.py --tb=short --junitxml=.codex-tests/validation344_final.xml
```

Les684empreintes sont stables pendant/après cette sélection ; seuls
`factures.py` et le nouveau test diffèrent de343.
`PYTHON_DOTENV_DISABLED=1` ; aucun PostgreSQL utilisateur, fichier `.env`
ou donnée comptable réelle utilisé. Aucun test de concurrence PostgreSQL
supplémentaire n’est revendiqué.

## Limites

Les données historiques définitives invalides restent à traiter séparément,
avec leurs justificatifs et leur piste d’audit. Ce lot empêche les nouvelles
validations invalides ; il ne répare pas des pièces antérieures. La recette
partenaire et l’ergonomie du refus sur l’installation utilisateur restent
distinctes. La consolidation336 et les sélections341/343 sont des preuves
antérieures, non additionnées au résultat de ce lot.
