# Édition des règlements clients/fournisseurs — 8 octobre 2026

## Preuve et correction

Deux tests Edge réels, JWT/API et PostgreSQL éphémère gardé par nonce :
`Test/run_unit_tests.py Test/test_e2e_reglement_edition_isole.py --tb=short`.
Avant correction : **2 échoués, 25 avertissements, 21,35 s**. L'édition était
déjà présente et rechargeait correctement la liste ; elle n'a pas été recréée.
Le formulaire possédait un état `notes` sans champ pour le modifier. Un PATCH
virement vers chèque client ou effet fournisseur rendait HTTP200 en conservant
`statut=complet` et l'ancienne `date_encaissement=2026-10-06`.

Ajout du champ Commentaire et d'un helper d'état initial partagé création/édition.
Pour les seuls règlements non comptabilisés restés à leur état initial, le mode
et la date suivent exactement le comportement existant à la création : chèque/
effet client en portefeuille sans encaissement, effet fournisseur à payer sans
encaissement, moyens immédiats complets à la date du règlement. Le traitement
historique des chèques fournisseurs demeure inchangé, sans nouvelle affirmation
réglementaire. Aucun montant, taux ou écriture historique n'est réparé.

Une modification financière d'un règlement ayant engagé le cycle bancaire est
refusée409 ; les notes seules restent éditables via le flux API existant. Le
blocage des règlements comptabilisés demeure et le bouton d'annulation existant
propose la contrepassation. Aucune validation automatique ni nouveau droit.

## Résultats réellement exécutés

Premier rerun après correction : deux échecs de test en21,85s, après passage de
l'édition et du retour Soldée ; GET des règlements sans paramètre `exercice`.
Test corrigé puis étendu. Cette exécution n'est pas comptée comme réussie.

```text
PYTHON_DOTENV_DISABLED=1 python -X utf8 Test/run_unit_tests.py Test/test_e2e_reglement_edition_isole.py Test/test_factD_reglements_delais.py Test/test_reglements_montants_finis.py --tb=short
```

**39 réussis, 25 avertissements, 43,57 s**, aucun ignoré : deux cas navigateur
vente/achat et37cas connexes. Chaque scénario utilise facture1200MAD, règlement
initial400, modification600 puis1200. Sont contrôlés : date seule et date
d'encaissement, changement vers moyen différé puis retour immédiat, commentaire
relu dans le formulaire, montant/solde et statut actualisés sans F5, comptabilisation
du règlement, validation explicite de sa pièce par API, refus409 sans mutation,
annulation par interface avec original validé conservé et solde rouvert1200.
Un chèque client non comptabilisé remis à l'encaissement est également protégé
contre PATCH financier ; notes seules acceptées sans changement de montant/statut.

```text
PYTHON_DOTENV_DISABLED=1 python -X utf8 Test/run_unit_tests.py Test/test_fact2_cycle_commercial.py Test/test_factH_audit_final_facturation.py Test/test_patch02c_reglement_date_effective.py --tb=short
```

**25 réussis en0,35s**. Compilation du routeur et du nouveau test : code0.
`npm run build` :139modules, succès en5,00s ; avertissements existants xlsx/chunks.

## Limites

PostgreSQL réel, processus utilisateur et données comptables réelles jamais
utilisés. Les droits, migrations et règles fiscales n'ont pas changé. Les notes
des règlements comptabilisés restent accessibles par l'API existante ; leur
formulaire d'édition financière n'est pas offert. Les cycles bancaires engagés
doivent poursuivre leur action métier ; aucun contournement ni annulation forcée.
Recette utilisateur sur son installation à effectuer après application du ZIP.
