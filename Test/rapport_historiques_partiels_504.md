# Lot504 — Amortissements partiels et écarts historiques

Ce lot ajoute une recette réelle aux fonctions existantes, sans nouvelle
modification du produit : les cinq scénarios passent avec la correction503.
Il distingue la dotation de N de l'amortissement cumulé repris à l'ouverture.

## Jeu fictif et résultats attendus

Bien10000MAD mis en service au01/01/N−2, linéaire5ans. Ouverture théorique4000,
dotation annuelle N2000, cumul à la clôture6000, VNC4000.
Les éventuelles valeurs historiques différentes sont préparées sur brouillon
fictif avant validation ; les pièces définitives sont ensuite conservées intactes.

| Cumul repris | Dotation N initiale | Correction N attendue | Écart cumulé restant | Clôture |
|---:|---:|---:|---:|---|
|4000|500|+1500|0|acceptée|
|4000|3000|−1000|0|acceptée|
|4000|2000|aucune|0|acceptée|
|3000|1000|+1000|+1000|refusée|
|5000|1000|+1000|−1000|refusée|

Un complément débite61935 et crédite28355. Une correction d'excès débite28355
et crédite61935. L'assistant ne corrige que N : les insuffisances ou excès
antérieurs ne sont ni absorbés dans N, ni masqués par une réécriture d'ouverture.
La contrepartie4481 de reprise est choisie explicitement dans ce laboratoire ;
elle n'est pas présentée comme la contrepartie d'une situation réelle inconnue.

Chaque scénario vérifie le diagnostic, les montants/sens des lignes, la présence
d'une seule AM et au plus une correction, l'absence d'effet d'un rejeu et
l'intégrité des sources. Les deux refus de clôture conservent toutes les tables
métier, à l'exception de l'audit de refus ajouté normalement.

Pour les trois cas rapprochés : clôture avec résultat net−5000 (dotation2000 et
CM3000 déjà appliquée par le laboratoire), FEC exportable et trois PDF du livre
réellement téléchargés et lus avec `pypdf`. Le snapshot expose cumul6000/VNC4000,
le PDF contient le matériel et ces montants. Cela ne valide pas la fiscalité
d'une entreprise réelle ni le graphisme du document.

## Tests exécutés

Ciblés : **5réussites,29avertissements,34,43s**, code0.

Qualification finale : **101réussites,29avertissements,321.00s**, code0,
aucun échec/erreur/ignoré. Sources figées vérifiées par empreintes.
Restauration :74tables, source préservée et cibles supprimées ; fonctions098,
refus409 et reprise conservés. Invariants0 :pièces déséquilibrées, montants
non finis et définitives sans numéro/date.98SQL/115guides inchangés.
Deux nouveaux fichiers Python compilés ; six Python dans le cumulatif503/504.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_reprises503_isole.py Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py Test/test_patch05c_reconciliation_historique.py Test/test_patch05d1_reconciliation_amortissements.py Test/test_patch05_livre_inventaire.py Test/test_e2e_cloture_isole.py -ra
```

Le regroupement conserve les oracles501/499/497/495/493, les scénarios503 et504,
les parcours Edge existants, la restauration098 et l'ancien parcours de clôture
sans098. Les passages successifs ne sont pas additionnés comme des cas distincts.

## Limites et reprise

PostgreSQL temporaire gardé par nonce et compte applicatif limité uniquement.
Pas de base réelle ni nouvelle migration, pas de modification des115guides ou
du point6 réservé au retour humain. Frontend inchangé, aucun build Vite requis.
La recette visuelle de l'assistant503 et les justificatifs restent à contrôler.
Ces cinq scénarios n'épuisent pas les variantes dégressives, cessions en cours
de période ou historiques multi-exercices.

Prochaine étape : qualifier la continuité sur deux clôtures décalées successives
et les cessions en cours de période ; poursuivre ensuite les autres risques
de concurrence sur stocks et paramètres fiscaux, sans rejouer les lots livrés.
