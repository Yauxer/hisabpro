# Lot512 — Fiscalité, clôture et confirmation simultanées

## Défauts reproduits et correction

Les paramètres IS et les retraitements pouvaient être modifiés pendant une
clôture qui avait déjà lu leurs anciennes valeurs. Une confirmation de
liquidation pouvait également figer un instantané pendant une modification
acceptée en parallèle. Deux confirmations simultanées pouvaient aboutir à
une erreur500 de contrainte unique.

Le contrôle commun des mutations fiscales prend désormais le verrou partagé
de l'exercice utilisé par la clôture, puis une exclusion transactionnelle
non bloquante propre à la société/exercice fiscal. Un conflit renvoie409 :
la demande peut être répétée après la fin de la première opération.
Les contrôles métier existants restent appliqués après ce verrou.

Aucune nouvelle migration, formule fiscale, qualification d'exonération ou
modification de données historiques. Les références d'acomptes et règlements
déjà autorisés après clôture restent possibles avant confirmation définitive.

## Onze cas API/PostgreSQL réellement exécutés

- Clôture suspendue après lecture des paramètres : modification refusée409,
  résultat final−3000 et comptabilisation IS cohérente.
- Paramètres en cours d'enregistrement : clôture refusée409 puis reprise.
- Création, modification et suppression de retraitements pendant clôture :
  trois refus409, retraitement initial conservé.
- Confirmation/paramètres, paramètres/confirmation, confirmation/confirmation :
  première opération200, seconde409 ; une seule liquidation et concordance
  du paramètre courant avec son instantané10000 ou20000.
- Autre société et autre exercice disponibles.
- Référence et versement d'acompte après clôture toujours autorisés, changement
  d'impôt courant refusé ; écritures comptables inchangées.
- Paramètre incohérent refusé400 puis clôture possible : verrou libéré.

Les montants proviennent d'un laboratoire fictif ; la CM3000 existante reste
active. Ils ne constituent pas une validation réglementaire d'un dossier réel.

Avant correction : **8échecs/3réussites,29avertissements,45,45s**, code1.
Premier passage après correction : **3échecs/8réussites,29avertissements,
41,05s**, code1. Les trois échecs restants concernaient le test : l'instantané
conserve les décimaux sous forme de chaînes exactes, comparées initialement
à des entiers. Comparaison corrigée via Decimal, sans changement produit.

Tests du module et régressions fiscales : **80réussites,29avertissements,
43,18s**, code0 :11nouveaux cas et69tests existants, sans additionner les
passages successifs.

Qualification finale : **245réussites,29avertissements,442.03s**, code0,
aucun échec/erreur/ignoré :164oracles précédents,11cas512,69tests fiscaux
et un parcours Edge fiscal réel (paramètres, retraitements, crédit, acompte,
clôture, confirmation et instantané). Parcours d'inventaire desktop/mobile
et restauration098 conservés. Sources figées vérifiées ;74tables restaurées,
source préservée/cibles supprimées, fonctions098 et refus409/reprise intacts.
Invariants comptables0 : pièces déséquilibrées, montants non finis,
définitives sans numéro/date. Quatre Python du lot et18du cumulatif compilés ;
98SQL/115guides, main/models/AGENTS et calculs de stock/exercices intacts.

Commande : `Test/run_unit_tests.py Test/test_consolidation_fiscal512_isole.py
Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py
Test/test_immobilisations_fin_plan.py Test/test_patch05c_reconciliation_historique.py
Test/test_patch05d1_reconciliation_amortissements.py Test/test_patch05_livre_inventaire.py
Test/test_e2e_cloture_isole.py Test/test_inventaire_comptage_complet.py
Test/test_inventaire_nombres_historique_postgres.py Test/test_patch08_1_fiscalite_is.py
Test/test_patch08_2_retraitements_fiscaux.py Test/test_patch08_3_deficits_fiscaux.py
Test/test_patch08_4_cotisation_minimale.py Test/test_patch08_5_acomptes_liquidation.py
Test/test_patch08_6_css_credits.py Test/test_patch092_liquidation_reference_acomptes.py
Test/test_patch094_liquidation_snapshot_detail.py Test/test_e2e_fiscalite_is_isole.py -ra`.


## Installation et limites

Installer ensemble `routers/fiscalite.py` et
`services/exercice_verrou_service.py` à jour512, puis redémarrer l'API.
Aucune nouvelle migration ni intervention sur PostgreSQL réel.

Ce verrou couvre les mutations appelant le contrôle commun de liquidation :
paramètres, retraitements, opérations annuelles de déficits, acomptes, crédits
et confirmation. Les mutations du stock global des déficits historiques, les
règlements CSS, les lectures isolées et les accès directs SQL/Python restent
hors de cette garantie. Les déficits historiques sont la prochaine analyse.
Recette utilisateur, production et point6 restent à valider séparément.
