# Patch 113 — diagnostic PostgreSQL ETIC

Contrôle du 6 octobre 2026, société 3, exercice 2026, clôture au 31 décembre.
Les requêtes ont été exécutées dans des transactions `BEGIN READ ONLY`, puis
annulées. Aucune réparation FEC, migration ou mutation de données n'a été lancée.
Ce document décrit les résultats calculés ; il ne constitue pas une validation
des données historiques ni une instruction de réparation comptable.

## Résultats du service réellement utilisé par l'écran

| Section / compte | Solde comptable | Source calculée, échue | Reliquat | Factures éligibles / historiques |
| --- | ---: | ---: | ---: | ---: |
| B6 / 3421 | 161 302,80 | 105 110,80 | 56 192,00 | 34 / 6 |
| B7 / 4411 | 45 960,00 | 33 960,00 | 12 000,00 | 5 / 2 |

Les compteurs incluent les factures soldées. Les deux factures achat historiques
récupérées sont distinctes : id 4, numéro `02`, et id 10, numéro `002`.
Toutes les factures éligibles possèdent une date d'échéance enregistrée ; aucun
échéancier multi-tranches n'est enregistré pour ces factures. Le calcul n'a donc
pas besoin de substituer une échéance supposée de 60 jours.

La source B6 contient toutefois des incohérences historiques décrites ci-dessous,
notamment la facture FA-2026-012. Son montant ne peut donc pas être déclaré
intégralement fiable sans rapprochement comptable complémentaire.

## B7 : décomposition exacte des 12 000 MAD non ventilés

| Mouvement(s) 4411 | Contribution au reliquat | Source retrouvée et raison du blocage |
| --- | ---: | --- |
| AC-2026-0001, 08/05, référence 0001 | 6 000 | Facture id 2 du même jour : TTC 1 440, référence INV-MT-8821, échéance 07/07. Le montant et la référence ne correspondent pas ; son échéance ne peut pas qualifier les 6 000. |
| AC-2026-0002, AC-2026-0003 et AC-2026-0005, 22/05 | 3 600 | Les trois écritures à 1 200 renvoient au seul candidat id 9, numéro 87, échéance 21/07. Deux écritures n'ont aucune référence ; la facture est compatible avec plusieurs écritures et reste exclue par le contrôle d'unicité. Son échéance ne justifie pas trois dettes. |
| AC-2026-0004, référence 02 | 240 | Facture id 4, échéance 21/07, soldée par règlements ids 17 et 18 de 230 et 10 MAD le 02/07. Ces règlements sont non comptabilisés, sans ecriture_id ; aucun débit compensateur n'est présent dans 4411. La source facture est nulle, mais le crédit comptable subsiste. Il faut établir la nature du solde, pas le déclarer impayé. |
| AC-2026-0011, FA-2026-016 | 960 | Facture id 66 : échéance 26/09, snapshot de compte 44110001, alors que l'écriture porte 4411. Le montant existe dans la source 44110001, pas dans la source 4411. Le déplacement automatique entre comptes serait une reclassification non autorisée. |
| AC-2026-0014, 28/08, référence 2026-001 | 1 200 | Aucune facture achat correspondante dans les données disponibles ; aucune échéance déterminable. |
| **Total** | **12 000** | |

AC-2026-0006 (`002`) est maintenant récupérée : 240 MAD restent dus, échéance
enregistrée au 21/07. AC-2026-0007 (720) et AV-2026-0003 (-360) expliquent
360 MAD dus sur FA-2026-ACHAT1, échéance 13/08 ; ils ne contribuent pas au reliquat.
AC-2026-0009 (960) est compensée par AE-2026-0009 (-960) : le règlement/effet
id 29 est rattaché à la facture id 59, référence yomama, échéance 20/07, statut
payé. Cette échéance existe, mais ces mouvements ont un impact net nul sur 4411.

## B6 : décomposition exacte des 56 192 MAD non ventilés

Les contributions ci-dessous sont des écarts entre comptabilité et source facture,
pas des créances supplémentaires à classer en échéances. Les compensations
explicitement identifiées sont prises en compte dans cette décomposition.

| Mouvement(s) / pièce | Contribution au reliquat | Pourquoi une ventilation automatique serait injustifiée |
| --- | ---: | --- |
| VT-2026-0001, référence 2026-002 | 120 | Aucune facture vente de même date, montant et référence. |
| VT-2026-0002, référence 0002 | 12 550 | Facture id 1 de même date et TTC, échéance 07/07, mais numéro FA-2026-001 et référence CMD-2026-045. La référence explicite de l'écriture est incompatible ; aucune association automatique. |
| VT-2026-0003, sans référence | 1 200 | La facture ancienne id 3 du même jour vaut 72, pas 1 200 ; aucune source fiable retrouvée pour cette écriture. |
| VT-2026-0007, référence 56 | 1 440 | Facture correspondante absente. |
| VT-2026-0009, référence 067 | 12 000 | La facture id 13 portant ce numéro vaut 24 000 et correspond à VT-2026-0010, pas à cette écriture de 12 000. |
| VT-2026-0011, référence 234 | 120 | Facture correspondante absente ; ne doit plus être confondue avec la facture 777 de même date et montant. |
| VT-2026-0015 à 0018, références 67, GH1, UP et 55 | 4 800 | Quatre mouvements de 1 200 sans facture correspondante disponible. |
| VT-2026-0031, référence 2026-002 | 4 800 | Facture correspondante absente. |
| VT-2026-0010, facture 067 | 24 000 | Échéance enregistrée 21/07 ; règlement id 13 de 24 000 le 28/06, non comptabilisé, sans écriture liée. La facture est soldée, le débit comptable subsiste. |
| VT-2026-0014, facture 45 | 13 200 | Échéance 02/06 ; règlement id 14 de 13 200 le 28/06 non comptabilisé. Même divergence entre source et comptabilité. |
| VT-2026-0019, FA989 | 2 400 | Échéance 05/08 ; règlements ids 1 et 2 de 2 000 et 400, non comptabilisés. |
| VT-2026-0022, 666665 | 1 200 | Échéance 12/08 ; règlement id 6 de 1 200, non comptabilisé. |
| VT-2026-0023, FA-12 | 1 200 | Échéance 12/08 ; règlements ids 7 et 16 de 1 000 et 200, non comptabilisés. |
| VT-2026-0025, FATEST | 1 200 | Échéance 17/06 ; règlements ids 11 et 12 de 1 000 et 200, non comptabilisés. |
| VT-2026-0020 et 0021, FAAA-2026-001 | 1 900 | Deux écritures de 1 200 pour une facture de 1 200 ; règlement id 5 de 700 non comptabilisé. La source conserve 500 dus, échéance 12/08. L'échéance ne légitime ni le mouvement supplémentaire ni le règlement absent de la comptabilité. |
| VT-2026-0026, TEST-01 | 3 600 | Facture TTC actuel 3 240 contre écriture 3 600 ; trois avoirs de 1 080 chacun, non comptabilisés, ramènent la source à zéro. L'échéance enregistrée 01/09 ne permet pas de qualifier cette divergence comme créance due. |
| VT-2026-0030, FA-testest-1 | 24 | Règlements ids 22 et 23 de 18 et 6 non comptabilisés ; avoir AV-2026-007 de 24 non comptabilisé. Source soldée, débit comptable subsistant. |
| BQ-2026-0001 et 0002 | -3 500 | Crédits clients de 1 500 et 2 000 portant 2026-001 ; aucun règlement enregistré correspondant aux dates et montants. La facture portant ce numéro vaut seulement 60. Affectation à une créance non déterminable. |
| OD-2026-0005 à 0008 avec AE-2026-0001, 0003, 0005 et 0007 | 236 | Impayés des règlements ids 24–27 : principal compensé par les transferts, mais 50 + 40 + 100 + 46 de frais réintégrés au collectif sans échéance propre enregistrée. Les anciennes échéances chèques/effets ne définissent pas celle des frais. |
| Facture FA-2026-012, id 62 | -26 298 | Marquée validée et comptabilisée, échéance 24/09, incluse dans la source ; aucune écriture ayant cette référence ni mouvement 3421 correspondant retrouvé. Les écritures VT-2026-0040 et 0041 concernent FA-2026-013 et 014, déjà comptées séparément. Source supplémentaire sans contrepartie prouvée. |
| **Total** | **56 192** | |

Les avoirs AV-2026-0001 et 0002 sur FA-deez-01 compensent les 2 400 MAD de
VT-2026-0024 : impact net nul. OD-2026-0004 correspond à l'imputation d'acompte
de 500 sur FA-2026-002. Les règlements rejetés ids 30 et 35 ont des échéances
21/07 et 22/07 ; AE-2026-0010/0012 sont compensées par OD-2026-0011/0012,
sans reliquat net supplémentaire. Les règlements BQ-2026-0004/0006/0007/0010/0011
et la retenue OD-2026-0009 compensent leurs factures dans la comparaison.

## Périmètre restant à valider

Les montants ci-dessus concernent 3421 et 4411. Les autres lignes B6/B7 (factures
à établir/non parvenues, comptes État, charges/produits d'avance et dettes sur
immobilisations) restent à examiner séparément ; aucune échéance n'en a été déduite.

Après redémarrage du backend, vérifier l'affichage, les compteurs et la conservation
des ventilations déjà saisies. La confirmation B6/B7 doit rester bloquée tant que
la ventilation complète n'est pas justifiée. Vérifier en particulier les règlements
non comptabilisés, le snapshot 44110001 et la facture FA-2026-012 avant toute
complétion manuelle. Aucune écriture définitive ne doit être retouchée pour faire
coïncider les totaux.
