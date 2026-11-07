# Acompte, imputation et solde — recette connectée

Exécution locale du 7 octobre 2026, PostgreSQL éphémère isolé et navigateur Edge, sans base réelle ni mocks des routes métier.

Commande : `Test/run_unit_tests.py Test/test_e2e_acompte_imputation_isole.py Test/test_fact8_echeanciers_acomptes.py Test/test_factG_acomptes_avoirs.py --tb=short --show-capture=no`.

Résultat final : **28 réussis, aucun échec ni test ignoré, 26,85 secondes**. Les avertissements existants concernent Pydantic et python_multipart.

Parcours réel : acompte bancaire de 400 MAD, facture de 1 200 MAD, imputation de 400 MAD, règlement du solde de 800 MAD, validation des quatre écritures et lettrage des trois lignes client. Compte d'acomptes soldé, banque à 1 200 MAD, seconde imputation refusée et sources relues. Neuf tests API isolés vérifient aussi le rejet des montants non finis et booléens sans mutation.

Corrections minimales : une échéance vide est transmise comme null ; les actions de tableau disposent d'une surface cliquable et d'un nom accessible, même sans police d'icônes. L'assertion de montant accepte le format monétaire 800,00 sans changer le produit.

Essais intermédiaires échoués explicitement : bouton sans hauteur puis comparaison textuelle 800/800.00 ; corrigés avant l'exécution finale. PostgreSQL réel et recette utilisateur non exécutés.
