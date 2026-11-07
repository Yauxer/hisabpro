# Lot538 — comptabilisation concurrente des factures

## Anomalie reproduite et correction

Deux requêtes simultanées `POST /api/factures/{id}/comptabiliser` lisaient
`est_comptabilisee=false` avant que la première ait terminé. Chacune créait
une pièce : deux réponses200 et deux écritures pour la même facture,
en vente comme en achat. Le refus409 existant ne protégeait que les requêtes
successives.

La lecture initiale de la facture utilise maintenant `FOR UPDATE` et
`populate_existing()`, avant les contrôles existants. La deuxième transaction
attend le premier commit, relit l'indicateur et reçoit le refus409 déjà prévu.
Aucun calcul, montant, schéma, migration ou format de document ne change.
L'avoir était déjà protégé par un verrou de ligne ; aucun changement dans
`avoirs.py`.

## Tests réellement exécutés

- Avant correction : **2échecs/2réussites,29avertissements,57.26s**,code1.
  Les deux factures renvoient200/200 ; les deux avoirs renvoient200/409.
- Après correction : **4réussites,29avertissements,38.56s**,code0.
- Consolidation : **344réussites,29avertissements,1040.12s**,code0.
  Commande : `Test/run_unit_tests.py Test/test_consolidation_factures538_isole.py -ra`.
  Aucune désélection, aucun échec/erreur/ignoré.
- Connexes externes : **247réussites,29avertissements,225.81s**,code0.
  Liste de25fichiers identique à la qualification externe534 : restauration098
  à froid, immobilisations, clôture, stocks, fiscalité et montants non finis.
  Deux commandes distinctes sur les mêmes sources figées : **591exécutions**,
  sans additionner les quatre cas ciblés déjà inclus dans la consolidation.
  Les fixtures de calcul pur et les anciens bacs propriétaires restent
  distincts de la consolidation LOGIN non propriétaire. Restauration :74tables,
  source préservée, cibles de test supprimées, trois fonctions098 identiques.
  Les98SQL et115guides restent intacts ; trois Python du lot compilés.

Commande ciblée : `Test/run_unit_tests.py
Test/test_facture_comptabilisation_concurrente_isole.py -ra`.

Les quatre cas croisent vente/achat et facture/avoir. Le test bloque la
première insertion avec un vrai verrou PostgreSQL sur `lignes_ecriture`, puis
envoie la deuxième demande HTTP avant de libérer le verrou. Aucun mock métier.
Il exige une seule pièce, débit=crédit=120MAD pour la facture,60MAD pour un
avoir de moitié, auxiliaire du tiers exact, validation réelle de la pièce et
export FEC200. Dans les cas d'avoirs, la facture d'origine est définitive et
son contenu et son audit doivent rester identiques.

Ces montants sont des données fictives de test et ne fixent aucune règle
fiscale nouvelle.

La qualification externe utilise les25fichiers suivants comme arguments de
`Test/run_unit_tests.py`, suivis de `-ra`, avec `PYTHON_DOTENV_DISABLED=1`.
Le runner interdit la suite historique de séquences sur base externe ; les
fixtures PostgreSQL de cette liste créent leur propre cible isolée.

```text
Test/test_restauration_journal098_isole.py
Test/test_patch03_immobilisations.py
Test/test_immobilisations_fin_plan.py
Test/test_patch05c_reconciliation_historique.py
Test/test_patch05d1_reconciliation_amortissements.py
Test/test_patch05_livre_inventaire.py
Test/test_e2e_cloture_isole.py
Test/test_inventaire_comptage_complet.py
Test/test_inventaire_nombres_historique_postgres.py
Test/test_patch08_1_fiscalite_is.py
Test/test_patch08_2_retraitements_fiscaux.py
Test/test_patch08_3_deficits_fiscaux.py
Test/test_patch08_4_cotisation_minimale.py
Test/test_patch08_5_acomptes_liquidation.py
Test/test_patch08_6_css_credits.py
Test/test_patch092_liquidation_reference_acomptes.py
Test/test_patch094_liquidation_snapshot_detail.py
Test/test_e2e_fiscalite_is_isole.py
Test/test_stock_integrite_mouvements.py
Test/test_patch06c_stock_engine.py
Test/test_patch06b_stock_ledger.py
Test/test_patch06_stock_cloture.py
Test/test_patch07c2_numero_validation.py
Test/test_session133_ecritures_montants.py
Test/test_session132_operations_postgres.py
```

## Limites et reprise

Exécution exclusivement sur un cluster PostgreSQL local temporaire, marqué
par nonce, port distinct de5432, rôle API non propriétaire. Aucune donnée
comptable réelle utilisée ou réparée. Les doublons historiques éventuels
doivent faire l'objet d'une analyse distincte et traçable ; ce lot ne les
supprime pas.

Frontend inchangé. Vérification visuelle sur l'installation utilisateur
encore à effectuer ; la recette utilisateur, la conformité réglementaire et
la mise en production ne sont pas déclarées validées. Le point6 soumis au
retour humain reste en attente.
