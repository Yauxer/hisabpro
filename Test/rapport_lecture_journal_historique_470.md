# Lecture du Journal et montants historiques invalides — lot 470

Une ancienne ligne de brouillon contenant NaN ou deux montants nuls provoquait
une erreur 500 de sérialisation. Le Journal ignorait ensuite l'erreur de son
contexte et pouvait présenter des totaux à zéro. Le défaut a été reproduit sur
PostgreSQL jetable et dans Edge.

Les trois lectures API (liste, détail et recherche par pièce) valident maintenant
leur projection avant réponse et renvoient un diagnostic 409 avec les écritures
et champs concernés. Aucune ligne n'est omise, aucun montant n'est remplacé et
aucune donnée n'est réparée. Le Journal affiche l'erreur et « Réessayer » ; il
ne présente ni tableau, ni total, ni export comptable issu d'un chargement échoué.
Un filtre API ne portant que sur des données valides conserve son comportement.

**18 tests réussis en 102,24 s**, 29 avertissements, exit 0 : cinq nouveaux cas,
onze cas de capacité numérique et deux parcours de permissions du Journal.
Les API 409, refus de validation 400/422, isolation entre sociétés et originaux
inchangés sont vérifiés. Edge 1440/390 contrôle erreur, absence de faux totaux et
exports, puis nouveau refus 409 au clic « Réessayer ». Aucune erreur JS/HTTP 500
dans ces deux parcours après correction.

La tentative initiale comportait cinq échecs : deux erreurs API 500 et deux
absences d'alerte reproduites ; le dernier cas essayait un montant négatif déjà
interdit par une contrainte SQL. Le banc vérifie désormais ce refus natif 23514
et son rollback, sans contourner la protection pour fabriquer une anomalie.

Commande : `python -X utf8 Test/run_unit_tests.py Test/test_lecture_ecritures_invalides_isole.py Test/test_ecritures_capacite_runtime_isole.py Test/test_e2e_journal_lecture_isole.py -ra`.
Compilation et build final exécutés avant livraison. Les brouillons anormaux
restent volontairement présents dans leur laboratoire négatif, distinct de la
recette positive regroupée ; il ne s'agit pas de données réelles.

La lecture d'un Journal contenant ces anomalies est explicitement bloquée,
elle n'est pas présentée comme une lecture partielle complète. Les autres
consommateurs d'historiques et erreurs de données restent à examiner. Toute
réparation réelle nécessite les sources et une procédure traçable ; aucune
réparation d'écriture définitive n'a été effectuée.
