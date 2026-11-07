# ACL de suppression des brouillons — 079

Le manifeste limité077 permet le cycle direct facturation/règlement. DELETE API d'un brouillon requiert également le détachement des liens de sources ; les UPDATE sur BC/BL, même sans ligne liée, échouaient sous le rôle applicatif non propriétaire.

Migration additive079 : droits UPDATE uniquement sur `facture_id/statut` du BC etdu devis, `facture_id` du BL etdu mouvement de stock. Elle n'ajoute aucun UPDATE sur une table entière, ne modifie aucune ligne et ne remplace pas077.

Après application deux fois sur PostgreSQL éphémère, l'API réelle supprime brouillon etproforma (204), tout en refusant la facture définitive (409). UPDATE des autres colonnes BC/BL/devis reste refusé42501. Les droits globaux avant/après079 sont identiques.

Tests finaux078/079 etconnexes fact4/factH : **36réussis en26,10s**, dont7ACL079 ; compilation0. Première exécution35réussis/1échec25,63s : assertion du test présumant l'absence UPDATE historique sur stock. La migration012 accorde déjà ce droit ; le test compare donc l'ACL avant/après sans prétendre la révoquer. Cette limite reste visible, aucune permission nouvelle sur `quantite` n'est ajoutée.

Aucun PostgreSQL réel, aucune donnée réelle ni déploiement. 077–079 forment le complément du parcours runtime testé ; les autres modules et la normalisation des anciens droits larges restent des travaux distincts.
