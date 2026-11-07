# Factures partiellement payées et échéances

Le tableau de bord, le compteur et le filtre « En retard » des factures utilisent le même calcul calendaire. Les paiements partiels restent dans les alertes jusqu'au solde. L'échéance explicite prime ; à défaut, le délai enregistré est utilisé, y compris zéro. Une facture échue aujourd'hui n'est pas encore en retard. Les documents brouillons, pro forma, annulés ou payés sont exclus.

Commande réellement exécutée : `Test/run_unit_tests.py Test/test_e2e_factures_retard_isole.py Test/test_e2e_recouvrement_isole.py --tb=short --show-capture=no`.

Résultat final : **19 réussis, zéro échec ou ignoré, 48,18 s**. Dix cas exécutent le vrai helper JavaScript avec Node ; un parcours Edge/API/PostgreSQL isolé vérifie facture 1 200 MAD, règlement 400, compteur et filtre retard, alerte d'accueil, puis solde 800 et disparition des alertes. La facture d'échéance du jour reste exclue du retard. Huit tests connexes de recouvrement passent également.

Essais intermédiaires explicitement non validés : fixture tentant de modifier une facture validée correctement refusée par SQL ; GET sans exercice refusé ; date de facture après échéance refusée ; puis neuf erreurs de setup pendant une édition JSX parallèle. Les fixtures ont été corrigées sans contourner ces contrôles. La relance finale sur interface stable passe. Aucune facture définitive ni écriture n'a été modifiée pour préparer les tests.

Build de l'ensemble frontend exécuté par agent sur cet état : 134 modules, 4,61 s, réussi. PostgreSQL réel non utilisé ; recette utilisateur à effectuer.
