# Revue ciblée loi 9-88, comptabilité électronique et HisabPro

Date : 8 octobre 2026. Lot REVUE-LOI-988-20261008, demande AUG20-04.

**Résultat : revue technique partielle ; rapprochement réglementaire article
par article bloqué par l'accès incomplet aux textes officiels.** Les protections
et tests déjà présents ne sont pas réimplémentés. Aucun code, taux, document
comptable ou donnée réelle n'est modifié. Ce document ne délivre ni certification,
ni homologation, ni avis juridique de conformité.

## Ce qui était déjà documenté

Le [manuel du système comptable](../MANUEL_SYSTEME_COMPTABLE_HISABPRO.md)
décrit déjà validation, numérotation, contrepassation, périodes, clôture, FEC,
ETIC et archivage. Il distingue la présence d'une migration de son application
effective. Les [procédures d'exploitation](../EXPLOITATION_HISABPRO.md)
documentent séparation des environnements et sauvegarde/restauration.

Les migrations 038, 052, 053 et leurs tests sont présentes. La migration 052
porte notamment sur l'affectation du résultat et les états ; elle n'est pas une
preuve exhaustive de la loi 9-88. Les compléments 072–079 couvrent intégrité,
archives, auxiliaires et permissions. Les rapports techniques récents ci-dessous
suffisent à reprendre ces contrôles sans recommencer un audit validé.

## Sources et accès réellement vérifiés

Les consultations suivantes ont eu lieu pendant cette revue. Un résultat indexé
prouve seulement le contenu effectivement visible dans ce résultat ; il ne
remplace pas la lecture complète du fichier.

| Référence | Source institutionnelle exacte | Accès et portée |
|---|---|---|
| S1 | [AMDIE : texte annoncé de la loi 9-88](https://amdie.gov.ma/wp-content/uploads/2024/01/Obligations-comptables-commercants.pdf) | Index officiel lisible : intitulé, promulgation et début de l'article premier, mention de la modification 44-03. PDF direct : HTTP 403 via outil web puis requête Python ; variante www également 403. Articles complets non obtenus. |
| S2 | [MEF/CNC : normes adoptées](https://www.finances.gov.ma/fr/Nos-metiers/Pages/cnc-normes.aspx) | Catalogue officiel indexé : Avis 24, CGNC tomes I/II et avis d'application de la loi 9-88 identifiés. Ouverture web et requête Python : timeout. Tomes et dispositions exactes non lus sur l'hébergement ministériel. |
| S3 | [MEF : annonce Avis 24/25, 14 juin 2023](https://www.finances.gov.ma/fr/Pages/detail-actualite.aspx?fiche=6558) | Index officiel lisible. L'annonce présente deux articles et une annexe portant sur définition, critères du logiciel et informations/format FEC. Ouverture directe : timeout. Elle ne fournit pas la liste complète des critères et champs. |
| S4 | [SGG : BO 6344-bis, rapport institutionnel 2015](https://www.sgg.gov.ma/Portals/0/BO/2015/BO_6344-bis_Fr.pdf) | Passage indexé lisible d'un rapport de contrôle : référence à l'article 4 pour le manuel de procédures d'une entreprise examinée. Ce rapport n'est pas le texte consolidé actuel de la loi ni une détermination de son application à toutes les sociétés HisabPro. |

Le [scan Avis 24 hébergé par l'OEC régional](https://oecrsk.ma/docs/finance-compta/avis%2024%20CNC%20traitement%20informatique.pdf)
est accessible comme PDF de sept pages. Il reste un document candidat hébergé
hors du ministère : son authenticité, sa version applicable et sa concordance
avec une publication officielle n'ont pas été établies ici. Il n'est donc pas
utilisé pour déclarer une obligation ou une conformité. Aucun résumé de cabinet,
plateforme de cours ou site commercial ne sert de support normatif à cette revue.

Le CGNC, l'Avis 24 et la loi 9-88 ont des objets distincts ; leur référencement
ne valide ni les tableaux DGI, ni un schéma EDI/SIMPL, ni une procédure de dépôt.

## Comparaison ciblée : preuves et écarts

La colonne « disposition » attribue un article uniquement si sa référence est
effectivement identifiable dans la source consultée. Les autres références
restent à établir à partir du texte officiel complet. Les statuts portent sur
la **revue demandée**, jamais sur une conformité légale certifiée.

| ID / point à rapprocher | Disposition / source exacte | Preuve existante dans le dépôt | Tests et preuve la plus récente consultée | Écart et statut |
|---|---|---|---|---|
| N01 — Champ d'application de la tenue comptable | S1, article premier : début seulement ; reste de l'article non lu | Modèles société/exercice, plan par société ; services/exercices_service.py et plan_comptable.py | Tests patch055 ; manuel décrivant les périmètres | **bloqué** : consolidation applicable et éventuelles exceptions à vérifier ; ne pas étendre automatiquement une contrainte à tous les profils. |
| N02 — Chronologie et numérotation | S1, article exact non vérifié ; S3 annonce des critères informatiques sans les détailler | 018_numero_ecriture_a_validation.sql ; routers/ecritures.py, _verifier_chronologie_validation ; contrôle séquences/chronologie dans fec_service.py | test_patch07c2_numero_validation.py : assertions statiques ; test_patch07c1_fec_avis24.py : contrôles purs ; consolidation globale historique citée ci-dessous | **partiel** : preuves techniques présentes ; correspondance normative exacte et traitement des pièces tardives à vérifier. Ordre commercial de création et date comptable sont distincts. |
| N03 — Validation, irréversibilité, correction | S3, annexe annoncée mais dispositions exactes non obtenues sur le MEF | 038 et 072 : protection des lignes définitives, équilibre différé, refus de montants non finis ; contrepassation dans ecritures.py | test_compta3_avis24_durcissement.py et tests PostgreSQL du dépôt ; les tests statiques seuls ne prouvent pas les ACL installées | **partiel** : comportement produit vérifiable ; rapprochement aux clauses ministérielles non terminé. Une contrepassation conserve l'original ; ne pas modifier un validé pour effacer un contrôle. |
| N04 — Piste d'audit et périodes | S3, critère exact à confirmer ; pas d'article de loi attribué par mémoire | 013/036/038 et production_audit_service.py ; périodes auditées ; clôture annuelle définitive et réouverture mensuelle contrôlée | Tests audit/periodes ; manuel du système ; contrôles runtime documentés dans rapport_runtime_permissions_postgres.md | **partiel** : couverture technique existante ; exhaustivité des événements, exploitation et séparation migrateur/runtime restent à vérifier sur le déploiement. |
| N05 — Justificatifs et lien vers l'opération | S1/S3 : disposition complète non accessible | EcritureJustificatif, référence/date de pièce ; piece_fec et diagnostics REFERENCE_PIECE_MANQUANTE ; récupération exacte et compléments séparés | test_compta4_justificatifs_fec.py ; tests113/122 ; matrice LIA-FEC | **partiel** : contrôles et lien technique présents ; justificatifs réels manquants toujours visibles. Aucune date, référence, échéance ou identité ne peut être inventée. |
| N06 — Journal, grand livre et restitution | S1/S2 : article et paragraphes complets non vérifiés | ecritures.py, états et exports ; source des libellés comptes société ; journal et grand livre | ZIP217 : 13 pytest et 5 Node, résultats historiques de matrice ; exports de balances213/216 | **partiel** : restitution testée techniquement ; présentation légale complète et formalités éventuelles à rapprocher au texte applicable. |
| N07 — Inventaire et livre d'inventaire | S1/S2 : articles non lus ; aucune exigence exacte déclarée | routers/inventaire.py ; livre_inventaire_service.py/PDF ; instantanés de bilan/CPC et migration074 | rapport_archives_comptables_immutables_postgres.md : 13 PG réussis, 21,32 s et33 connexes ; tests livre/inventaire présents | **partiel** : instantanés et immutabilité testés ; inventaire physique, justificatifs, périmètre annuel et formalités restent une validation humaine distincte. |
| N08 — États et clôture annuelle | S1/S2 : dispositions exactes à confirmer | liasse_service.py, clôture, à-nouveaux ; bilan/CPC/ESG/financement/ETIC ; données extra-comptables explicitement saisies | Matrice CPT-10/CPT-13 : scénario annuel réduit224 ; rapport_e2e_archive_liasse_isole.md : 1 Edge, 20,10 s, dossier fictif | **partiel** : scénario réduit exécuté ; exhaustivité, image fidèle et pièces du dossier réel ne sont pas déduites d'un test automatique. |
| N09 — Manuel et organisation de l'entreprise | S4, référence à l'article 4 dans un rapport institutionnel ; texte consolidé non confirmé | Manuel système et procédures d'exploitation présents | Lecture documentaire effective pendant cette revue ; aucun nouvel essai métier | **partiel** : documentation du logiciel disponible ; ce manuel ne décrit pas automatiquement l'organisation propre de chaque entreprise. Seuils/conditions actuels à confirmer avant tout champ obligatoire. |
| N10 — Conservation durable des données et pièces | S1 : durée et article non vérifiés ici ; S3 ne fournit pas les modalités intégrales | Archives JSON/SHA, migrations073/074 ; ops/postgres_sauvegarde.py et procédures | Rapport073 : 5 PG, 53,99 s ; rapport074 : 13 PG, 21,32 s ; test_session132_sauvegarde_postgres.py présent | **partiel** : intégrité interne et banc de restauration présents ; politique de durée légale, pièces externes, médias, contrôles de lisibilité et restauration de production non établis. Le ZIP n'est pas une sauvegarde comptable. |
| N11 — Format électronique et FEC | S3 confirme l'objet du FEC, sans fournir son annexe complète ; S2 référence l'avis | fec_service.py : entêtes, dates, montants, brouillons, séquences et justificatifs ; contrôles distincts des états | Tests07c1/099/113/122 ; noms des tests « officiels » ne valent pas preuve normative ; rapport09A conserve des anomalies historiques | **bloqué** pour la revue normative exhaustive : confronter chaque champ et format à l'annexe officielle applicable avant de conclure. Un FEC techniquement exportable ne suffit pas à valider un dépôt. |

## Résultats historiques et contrôles de cette revue

Les résultats numériques dans la table proviennent de rapports déjà présents,
lus pendant cette revue. Ils ne sont pas présentés comme de nouveaux essais.
Le [rapport global du8 octobre](../../Test/rapport_non_regression_globale_20261008.md)
rapporte 2060 réussis, 1233,35 s, exit 0, pour les sources figées **avant** les
nouveaux lots paie 226 et suivants ; ce chiffre ne valide pas la version actuelle
ni la réglementation. Les suites ciblées recouvrent cette collecte et ne sont
pas additionnées.

Cette étape exécute seulement recherches du dépôt, lecture des preuves,
consultations web et contrôle documentaire des chemins/statuts. Aucun nouveau
test métier, accès PostgreSQL réel, modification comptable, migration réelle
ou test navigateur n'est revendiqué. Les refus403 et timeouts sont des échecs
d'accès aux sources, pas des textes lus ou tests réussis.

## Reprise proposée

1. Obtenir la version officielle complète applicable de la loi 9-88 et de ses
   modifications, ainsi que l'annexe Avis 24 et les tomes CGNC pertinents, avec
   provenance, date et version. L'article premier visible ne suffit pas.
2. Remplacer les dispositions « non vérifiées » par leurs articles/paragraphes
   exacts, puis confronter les preuves déjà disponibles sans réappliquer les
   protections installées. Identifier séparément les formalités de l'entreprise.
3. Vérifier une conservation opérationnelle des pièces et archives : politique
   de durée, sauvegardes, restauration isolée, lisibilité et séparation des
   privilèges. L'immutabilité SQL ne prouve pas cette organisation.
4. Maintenir les anomalies historiques FEC/ETIC jusqu'à justificatif ou décision
   humaine traçable. Poursuivre les autres travaux indépendants des sources
   momentanément inaccessibles.

La demande de comparaison exhaustive reste ouverte. Les statuts « développement
terminé », « tests automatisés validés », « recette utilisateur à effectuer » et
« prêt pour mise en production » demeurent distincts.
