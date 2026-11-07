# Lot501 — Clôture avec correction d'amortissement seule

Le point A-499-CLOTURE est confirmé : une correction RECON-AMORT validée2000,
égale à la dotation attendue, reste refusée comme manquante parce que le
contrôle recherche uniquement une référence AM classique.
Avant correction :1échec/2réussites,29avertissements en30,47s.

Le contrôle conserve son comportement pour les AM classiques et reconnaît
désormais une correction seule lorsque la charge nette réellement enregistrée
est exactement égale à la dotation attendue. La recherche est déterministe :
société, exercice comptable et référence RECON-AMORT-exercice-immobilisation
exacts ; somme débit-crédit des lignes de classe6. La seule présence d'une
référence ne suffit pas. Aucun montant, compte ni écriture n'est créé ou modifié
pour rendre le contrôle vert. Les autres contrôles de clôture restent actifs.

## Tests exécutés

- Ciblés corrigés :3réussis,29avertissements en28,94s.
- Extension5cas :5réussis,29avertissements en34,23s, aucun échec/erreur/ignoré.

Société fictive :capital1000, acquisition10000HT/TVA2000, correction2000 au lieu
d'une AM classique. Après validation préalable, la clôture doit aboutir avec
résultat avant impôt-2000, CM existante du laboratoire3000, résultat net-5000,
à-nouveaux et FEC exportable. Il reste exactement une correction et zéro AM
supplémentaire ; toutes les pièces originales restent identiques.

Les cas1000 et3000 sont préparés sur brouillon fictif **avant** leur unique
validation, jamais par modification d'une pièce définitive. La clôture reste
refusée400 ; aucune table métier ne change, la trace de refus est conservée.
Une correction d'une autre société ou d'un autre exercice, même avec référence
ressemblante, ne fait pas disparaître une dotation manquante.

Commande finale :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_correction501_isole.py Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py Test/test_patch05c_reconciliation_historique.py Test/test_patch05d1_reconciliation_amortissements.py Test/test_e2e_cloture_isole.py -ra
```

**88exécutions réussies,29avertissements en285.49s**,0échec/erreur/ignoré.
Les5cas501 sont regroupés avec les oracles499/497/495/493, les tests purs,
les parcours Edge immobilisations/vente/achat/règlement/lettrage/clôture,
restauration098 et ancien E2E de clôture sans098. Les passages successifs ne sont
pas additionnés et les mêmes parcours dans deux configurations ne sont pas
présentés comme des cas métier distincts.

Restauration :74tables/quatre pièces/données/schéma/ACL/séquences/FEC conservés,
fonctions098 et refus409/reprise disponibles ; source préservée,cibles nettoyées.
Invariants0 :pièce déséquilibrée,montant non fini,définitive sans numéro/date.
Sources/fonctions/ACL inchangées pendant les tests ;3Python compilés,
98SQL et115guides intacts.

## Installation et limites

Installer `routers/cloture.py` avec les fichiers497/499 puis redémarrer l'API.
Aucune migration supplémentaire ni réparation de données réelles. Les montants
du laboratoire ne prouvent pas la fiscalité d'une entreprise réelle ; les
paramètres fiscaux et justificatifs doivent être qualifiés séparément.

Le point de reprise499 est corrigé pour cette correction exacte seule. Cela
ne valide pas toutes les variantes d'historiques, années décalées, reclassements
ou reprises d'ouverture. Les insuffisances/excès restent visibles, aucun
ajustement automatique ne les masque. Frontend inchangé, pas de nouveau build
Vite ; recette humaine/production et point6 en attente.98SQL/115guides intacts.
