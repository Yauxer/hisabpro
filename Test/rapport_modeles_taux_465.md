# Modèles : changement de TVA —465

Le changement du taux d'un modèle simple conserve maintenant son montant HT,
que sa ligne principale porte du HT(achat)ou du TTC(client). Le calcul partagé
sert à la saisie, à la détection et au changement de taux. Un taux non fini ou
invalide n'est jamais assimilé à zéro ; le modèle source reste inchangé.

Reproduction avant correctif, avec tiers sélectionné : **1 échec vente et 1 achat
réussi 33,36 s**. La vente conservait 120 sur la ligne client alors que le montant
attendu était 110 pour 100 HTet 10 deTVA. La première tentative du banc omettait
le tiers achat ; ce défaut de prérequis a été corrigé sans changer le produit.

Après correction : **42 réussis 33,53 s**, puis **56 réussis 146,03 s**,29 avertissements,
exit 0. Résultat du second processus récupéré dans son journal après interruption
de quota ; il s'était achevé normalement, aucun succès déduit d'une interruption.

La suite comprend 40 casNode du calcul réel et 16 cas natifs/API/Edge connexes,
notamment les nouveaux modèles 092, la migration rejouée, le cycle des avances,
les achats/ventes validés et le lettrage. Les deux parcours de changement de taux
vérifient 20→10→0→20,100 HTconstant et 120/120 à la validation finale, sur 1440/390 px.

Commande connexe : `python -X utf8 Test/run_unit_tests.py Test/test_modeles_changement_taux.py Test/test_modeles_montants.py Test/test_modeles_avances_runtime_isole.py Test/test_e2e_modeles_taux_isole.py Test/test_e2e_modeles_detection_isole.py Test/test_e2e_modeles_journal_lettrage_isole.py -ra`.

Les taux sont ceux déjà proposés dans l'interface ; les chiffres servent à
tester l'arithmétique, sans qualifier fiscalement une opération réelle. Aucun
taux réglementaire ajouté. Les modèles complexes restent hors recalcul
automatique. Aucun PostgreSQL utilisateur ni mouvement réel modifié.

Utilisation : choisir un modèle achat/vente dans le Journal, saisir le HT, puis
changer « Taux TVA du modèle ». Vérifier les trois lignes avant enregistrement.
Compilation et build final exécutés avant livraison ; recette humaine à faire.
