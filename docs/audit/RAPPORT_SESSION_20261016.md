# HisabPro — logos, modèles et recette connectée

Reprise du 16 octobre 2026 à 00 h 30 Europe/Paris, soit le 15 octobre 22 h 30 UTC,
après interruption de quota. Le dépôt, le journal intégral et les processus ont
été vérifiés ; aucun test n'était encore en cours. Les lots 462–464 déjà livrés
n'ont pas été réappliqués. Leur baseline précède les modifications demandées
sur les logos et le catalogue ; le cumulatif de reprise en conservera toutes
les versions finales. Aucun dépôt Git local, commit ou push.

## Changements livrés et contrôlés

| Lot | Résultat | Vérifications ciblées réellement exécutées |
|---|---|---|
|462| Logos des PDF comptables/fiscaux et exports ventes PDF/XLSX ; snapshot logo de liasse neuf |51 réussis,66,25 s ; deux sociétés et images réelles via API |
|463| Trois classeurs navigateur avec feuille logo ; course avant identité corrigée |13 réussis,98,33 s ; téléchargements Edge 1440/390 et lecture openpyxl |
|464| Cinq modèles d'avances personnel, choix des modèles ambigus et saisie SA |21 réussis,110,58 s ; rejeu 092,8 écritures/17 lignes,D=C 19500,FEC |
|465| HT conservé au changement de taux ; taux non fini refusé |56 réussis,146,03 s ; Node et Edge achat/vente |
|466| Logos des impressions Journal/TVA |4 réussis,65,44 s ; huit PDF issus du moteur Edge |
|467| Identités et libellés littéraux dans les champs PDF testés |79 réussis,87,77 s ; image fictive non chargée depuis un texte |
|468| Restauration native avec logos/catalogue |1 réussi,74,71 s ;73 tables,séquences,ACL,pièces,FEC conservés |
|470| Diagnostic 409 d'écritures illisibles et Journal sans faux totaux |18 réussis,102,24 s ; API et Edge 1440/390, données conservées |
|471| Date civile d'un effet, sans blocage lié à l'UTC |9 réussis,119,33 s ; horloge Europe/Paris et instruments annuels |
|472| Droits limités paramètres TVA, retrait SETVAL hérité, refus sur exercice clôturé |6 réussis,117,62 s, restauration de la version finale incluse |
|474| États de lecture de l’accueil et du Grand livre |11 réussis,113,31 s ; alertes/reprise et originaux conservés |
|476| Catalogue Paie : les cinq modèles en sélection réelle |2 réussis,39,85 s ; dix sélections puis annulations, quatre tables inchangées |
|477| Verrou du statut pendant la sauvegarde TVA |33 réussis,122,86 s ; trois scénarios natifs de concurrence inclus |
|478| Qualification regroupée sur les sources finales |143 réussis,423,15 s ; 780 empreintes et ACL inchangées |

Ces suites se recouvrent : leurs nombres ne s'additionnent pas. Les échecs
initiaux, prérequis de banc corrigés et résultats détaillés figurent dans chaque
rapport et dans CODEX_PROGRESS.md. Aucune commande interrompue n'est un succès.

## Qualification sur les sources finales

Résultat final 478 : **143 réussis, zéro échec/erreur/ignoré, 423,15 s**,
29 avertissements, code 0. Les 780 empreintes source sont identiques avant/après
et conformes aux fichiers vérifiés après la commande. API réelle, Edge et
PostgreSQL nonce ; aucun PostgreSQL utilisateur. Les trois compteurs du jeu
positif sont à zéro, les ACL sont conservées.

Le complément de catalogue 476 a ensuite réussi deux parcours en 39,85 s, sur
le même produit inchangé : dix sélections (cinq modèles en 1440 et 390 pixels),
journaux et 100/100 vérifiés, puis annulation sans écriture ni modification
des quatre tables contrôlées. Ces tests ont été exécutés séparément ; ils ne
sont pas présentés comme une unique commande de 145 cas.

La campagne 475 a réussi 140 cas en 394,09 s avant le verrou TVA 477 ; la
qualification 478 la remplace pour les sources finales. La globale historique
3426 n'a pas été rejouée et la recette humaine n'est pas prévalidée.

Première qualification verte 469 : **136 réussis, aucun échec, erreur ou ignoré, en 406,28 s**,
29 avertissements de dépréciation. La première consolidation a obtenu 125 réussites et
deux échecs en 375,47 s. Les deux défauts ont été isolés, reproduits et corrigés :
effet dû aujourd'hui encore considéré futur en UTC, et droits SQL manquants pour
les paramètres TVA. La relance inclut 131 cas positifs sous runtime 093 et cinq cas
de lecture négative dans un autre laboratoire, avec leurs oracles conservés.
Les 134 sources suivies sont restées figées pendant cette commande et leurs
empreintes ont été vérifiées après la sortie 0. ACL inchangées et trois compteurs
à zéro : déséquilibres, montants non finis, définitives sans numéro/date. Le jeu
positif contient 58 sociétés fictives, 99 écritures, 249 lignes, deux clôtures et
26 groupes de lettrage. Les anomalies volontaires des cinq cas négatifs sont
dans un autre laboratoire.

Une relance intermédiaire a obtenu 135 réussites et un échec 405,92 s : le contrôle
ajouté de séquence révélait un SETVAL hérité des anciennes 005/008. Le correctif
ciblé de 093 n'avait pas encore été livré ; les six cas de droits/restauration
ont ensuite réussi 117,62 s avant la dernière relance.

Une autre relance a obtenu 135 réussites et un échec en 418,53 s : le scénario de
téléchargement désactivait le compte avant la fin des lectures initiales. Une
lecture 401 renvoyait donc vers la connexion avant le clic. La synchronisation
du test a été corrigée, avec les mêmes assertions 401/404, message visible,
absence de faux PDF et originaux conservés. Les deux cas ciblés ont réussi en
39,58 s avant les 136 cas finaux. Le ZIP 469 contient cette correction de test et
le regroupement ; les détails sont dans `Test/rapport_consolidation_logos_modeles_469.md`.

## Utilisation et limites

Enregistrer un PNG/JPEG dans Paramètres → Société, puis exporter le document
du module. Le logo occupe la première page PDF ou une feuille d'identité XLSX.
Le Journal et la TVA disposent également d'une identité d'impression. Les
justificatifs importés, formats texte et anciennes archives sans logo sont
conservés. La boîte système d'impression et Excel du partenaire restent à vérifier.

Les modèles se choisissent dans le Journal, catégorie Paie ; ils ne calculent
pas de bulletin et n'autorisent pas une retenue sans justification. Les
migrations 092/093 sont livrées pour application manuelle par l'administrateur,
elles n'ont pas été exécutées sur une base utilisateur. Le diagnostic 409 du
Journal ne répare aucune écriture. Les justificatifs ETIC/FEC manquants, schémas
DGI non obtenus et décisions humaines restent visibles.

Développement global : **partiel**. Tests automatisés : **validés dans les
périmètres détaillés**, dont la qualification finale 143 cas et le complément de catalogue. Recette
utilisateur : **à effectuer**. Production : **non validée**. Point 6 en attente ;
les 115 fichiers de guides/recette sont conservés, sans résultat humain prévalidé.

Le dernier build frontend 474 est réussi en 7,39 s. Le verrou de ligne TVA
477 a réussi 33 cas connexes en 122,86 s, dont trois tests de concurrence natifs
dans les deux ordres et après annulation. Il porte sur une ligne d'exercice
existante ; SQL direct, ligne absente et calcul préalable complet de clôture
ne sont pas qualifiés par ce seul verrou. Aucun taux ou migration ajouté en477.

## Installation et livraisons

Le cumulatif différentiel vise l'état du dépôt avant462, après les livraisons
précédentes déjà intégrées ; il ne contient pas le projet complet. Préférer ce
cumulatif aux extractions successives des ZIPs ci-dessous. Aucun environnement,
cache, fichier .env ou dump n'est fourni. Les anciennes migrations sont intactes.
Appliquer 092/093 manuellement après sauvegarde et contrôle de la connexion ;
le rôle applicatif limité ne sert pas de migrateur. Les commandes et les cinq
contreparties de modèles sont dans `docs/EXPLOITATION_HISABPRO.md`.

Les archives figées ci-dessous restent leurs preuves de livraison. Les rapports
462–468 normalisés pour la lisibilité sont repris en473, sans modifier leurs
résultats ni leurs limites. 473 inclut le présent rapport et les documents de
couverture ; le cumulatif479 en contient les dernières versions.

| Étape | ZIP différentiel |
|---|---|
| 462 | [HisabPro_462_Logos_Exports_PDF_Excel.zip](../../HisabPro_462_Logos_Exports_PDF_Excel.zip) |
| 463 | [HisabPro_463_Logos_Classeurs_Navigateur.zip](../../HisabPro_463_Logos_Classeurs_Navigateur.zip) |
| 464 | [HisabPro_464_Modeles_Avances_Personnel.zip](../../HisabPro_464_Modeles_Avances_Personnel.zip) |
| 465 | [HisabPro_465_Modeles_Changement_TVA.zip](../../HisabPro_465_Modeles_Changement_TVA.zip) |
| 467 | [HisabPro_467_PDF_Textes_Litteraux.zip](../../HisabPro_467_PDF_Textes_Litteraux.zip) |
| 466 | [HisabPro_466_Logos_Impression_Journal_TVA.zip](../../HisabPro_466_Logos_Impression_Journal_TVA.zip) |
| 468 | [HisabPro_468_Restauration_Logos_Modeles.zip](../../HisabPro_468_Restauration_Logos_Modeles.zip) |
| 471 | [HisabPro_471_Effets_Date_Locale.zip](../../HisabPro_471_Effets_Date_Locale.zip) |
| 470 | [HisabPro_470_Journal_Historiques_Invalides.zip](../../HisabPro_470_Journal_Historiques_Invalides.zip) |
| 472 | [HisabPro_472_Parametres_TVA_Droits_Limites.zip](../../HisabPro_472_Parametres_TVA_Droits_Limites.zip) |
| 469 | [HisabPro_469_Recette_Logos_Modeles_Connectee.zip](../../HisabPro_469_Recette_Logos_Modeles_Connectee.zip) |
| 474 | [HisabPro_474_Erreurs_Lecture_Accueil_Grand_Livre.zip](../../HisabPro_474_Erreurs_Lecture_Accueil_Grand_Livre.zip) |
| 475 | [HisabPro_475_Non_Regression_Logos_Lectures.zip](../../HisabPro_475_Non_Regression_Logos_Lectures.zip) |
| 477 | [HisabPro_477_TVA_Verrou_Exercice_Concurrent.zip](../../HisabPro_477_TVA_Verrou_Exercice_Concurrent.zip) |
| 478 | [HisabPro_478_Qualification_Finale_Logos_Modeles.zip](../../HisabPro_478_Qualification_Finale_Logos_Modeles.zip) |
| 476 | [HisabPro_476_Catalogue_Paie_Interface.zip](../../HisabPro_476_Catalogue_Paie_Interface.zip) |
| 473 | `HisabPro_473_Couverture_Logos_Modeles.zip` — documents finaux de couverture |

Prochaine tâche : reprendre les fonctionnalités partielles de la matrice,
notamment le rattachement explicite des avances aux bulletins, sans déduire un
salarié d'un libellé ou récupérer une somme sans justification. Référentiels
fiscaux officiels manquants, ETIC/FEC historiques et point6 restent ouverts.

## Complément480 après le cumulatif479

Les neuf contournements SQL de paramètres clôturés ont été reproduits sous093,
puis corrigés par094 additive. **22réussis78,05s**, sans échec/erreur/ignoré,
29avertissements ; restauration finale distincte **1réussi68,24s**, source
préservée et73tables/schéma/données/séquences/ACL/quatre pièces/FEC conservés.
Les permissions supplémentaires visent deux fonctions invoker, aucun ancien
droit de table n'est élargi. Rejeu sans modification de données. Les prérequis
incorrects du premier banc et les résultats intermédiaires sont explicités
dans `Test/rapport_protection_sql_tva_480.md`.

La143478qualifie runtime093 ;elle n'est pas présentée comme une nouvelle
globale094. Les22cas et la restauration qualifient ce dernier complément.
094contrôle une clôture déjà visible ;SQLdirect concurrent et calcul complet
préalable de clôture restent àqualifier. Aucune donnée comptable réelle ni
ancienne migration modifiée. Les trois migrations092/093/094 restent manuelles,
après sauvegarde etcontrôle de connexion. Point6/115guides toujours inchangés.

ZIP étape : `HisabPro_480_Protection_SQL_Parametres_TVA.zip`.
Dernier cumulatif : `HisabPro_Session_20261016_Logos_Modeles_462_480.zip` ;il
reprend les dernières versions et remplace le cumulatif479 pour cette reprise.
Les limites de production, sources DGI manquantes et recette humaine restent
ouvertes. La prochaine fonctionnalité reste le rattachement explicite des
avances aux bulletins, sans déduction automatique d'un salarié ou d'une somme.
