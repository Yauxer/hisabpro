# Bilan de session — Personnel & Paie897–905

## Complément final905

Après la consolidation903,un nouveau scénario API/PostgreSQL isolé a préparé12mois réels de données fictives,avec variables approuvées,bruts etsocial sélectionnés.1cas réussi en42.57s :328cas distincts enunion avec901,soit221unitaires/85API-SQL-restauration/22Edge,sansnouvellecampagnecomplète328. Produit519empreintes inchangé,aucun nouveaubuild oumigration. Sommes mensuelles salariales4248.00 etpatronales6144.00MAD ;anciens snapshots etcomptabilité conservés. Aucun IRmensuel,net ouclôture de paie inventé. Les sections327ci-dessous conservent la chronologie901/903 ;105cas humains toujours Non testé. [Résultats905](RESULTATS_ANNEE_SOCIALE_905.md).

Session du28/10/2026, reprise depuis le produit895. Les lots889/891/893 déjà présents n’ont pas été réimplémentés. Le dépôt a été contrôlé par empreintes, car ce répertoire n’est pas un dépôt Git. Aucun commit ni push.

## Fonctions ajoutées

| Lot | Résultat concret | Livraison différentielle |
|---|---|---|
| 897 | Référentiel des branches sociales par société/régime, taux exacts, assiettes/plafonds propres, versions datées, qualification indépendante et double couverture bloquée ; écran04 | [ZIP897](../../HisabPro_897_Paie_Referentiel_Social.zip) |
| 899 | Calcul social pédagogique relié à un brut conservé, exclusions avant plafond, cumul mensuel par rubrique, résultats par salarié/branche/payeur, sources courantes et snapshots immuables ; parcours03→04 | [ZIP899](../../HisabPro_899_Paie_Calcul_Social_Connecte.zip) |
| 901 | Contrôle annuel du barème généralIR2026 sur RNI déclaré, réduction familiale confirmée, inconnus explicites et sources conservées ; écran05 | [ZIP901](../../HisabPro_901_Paie_Controle_IR_Annuel.zip) |
| 903 | Bilan, procédure d’installation sur copie, vérificateur documentaire portable et reprise3C2 ; aucun changement produit | ZIP documentaire et cumul final de session |

Les rubriques01 à05 de la sidebar sont accessibles dans leur périmètre décrit.06 à09 restent À venir. Aucune paie définitive n’est annoncée par cette navigation.

## Qualification réellement exécutée

La dernière campagne porte sur le produit901 : **327 cas distincts réussis**,221unitaires/source,84API/SQL/restauration PostgreSQL natif isolé,22Edge/API/PG. Aucun échec, erreur ou test ignoré dans cette campagne. Les campagnes230 du lot897 et277 du lot899 recouvrent ces cas ; elles ne sont pas additionnées.

Build final :208modules, code0,10.52s. Compilation :14fichiers Python modifiés dans901. Restauration native :95tables, schéma/données/séquences/ACL identiques, contrôle des snapshots du brut/social/IR avec rôle runtime limité et véritable modification de prédicat détectée. Source conservée, seconde cible temporaire supprimée. Les résultats et tentatives antérieures sont conservés dans [la preuve901](../../Test/PREUVE_PAIE_901.json) et les rapports897/899/901.

Deux parcours par nouvel écran,1440/390, ont été exécutés dans Edge avec API et base isolées. Captures mobiles du référentiel, de la liste sociale et du résultat fiscal inspectées ; absence de débordement horizontal contrôlée. Le premier échec897 concernait une attente403 erronée sur une route inexistante ; corrigé404/405 sans changement du produit, puis requalifié. Il n’est pas effacé de la chronologie.

Le produit courant comporte519empreintes dans `Test/CANDIDAT_PAIE_901.json`. Les migrations antérieures n’ont pas été réécrites ;116/117/118 sont additives et ont été rejouées avec conservation des données de test. Les archives livrées antérieurement restent immuables ; leurs SHA/CRC et les différentiels finaux sont vérifiés avant livraison.

## Recette utilisateur disponible

Le [mode d’emploi](MODE_EMPLOI_PERSONNEL_PAIE.md) référence sept ensembles PDF/Excel, **105cas humains**, dont18 nouveaux dans cette session. Les données et calculs indépendants sont fournis. Tous les statuts initiaux sont **Non testé** ; aucun résultat humain n’est déduit des tests automatisés.

Les lignes longues des classeurs897/899/901 ont été agrandies pour garder les consignes lisibles. Les PDF historiques897/899 ont été conservés identiques à leurs ZIPs. Le vérificateur `Test/verifier_cahiers_paie903.py` lit les IDs/statuts, compare aux PDF et contrôle les liens locaux, sans modifier les résultats saisis. Son exécution de livraison est consignée dans `Test/PREUVE_CAHIERS_PAIE_903.json` ; elle ne valide pas la recette humaine ni le calcul des formules dans un logiciel Excel réel.

## Statuts à distinguer

| Statut | État |
|---|---|
| Développement terminé | Oui pour les sous-étapes897/899/901 décrites, pas pour la paie complète |
| Tests automatisés validés | Oui pour les327cas du produit901 et les restaurations isolées correspondantes |
| Recette utilisateur à effectuer | Oui, sur copie, avec les105cas et leurs preuves |
| Prêt pour mise en production | Non : qualification, installation/exploitation et développements restants |

Aucune connexion à la base habituelle de l’utilisateur, aucun `.env`, clé réelle ou donnée comptable réelle utilisé par les tests. Aucun taux social légal n’est activé par défaut. Le contrôle annuel901 conserve un résultat mathématique avant arrondis de liquidation ; les champs montant à déclarer, retenue mensuelle et net restent inconnus.

## Prochaine tâche exacte

Poursuivre **3C2 : assiette fiscale et IR mensuel reliés aux sources**, selon [le point de reprise](REPRISE_IR_MENSUEL_3C2_903.md). Distinguer traitementsIR des rubriques, frais professionnels, déductibilité des cotisations, cumuls, éligibilité familiale et arrondis. Les cas sociaux complexes et leurs preuves restent à qualifier ; net, bulletins, paiements, comptabilisation, déclarations et archivage de paie suivent dans le master.

Avant de reprendre, vérifier le journal et les519empreintes ; ne pas relancer les étapes terminées. Le [guide d’installation sur copie](INSTALLATION_COPIE_PAIE_116_118.md) explique l’ordre116→117→118 sans action sur la base réelle.

Le cumul différentiel de cette exécution est `HisabPro_Session_20261028_Paie_897_905.zip`. Le cumul historique depuis871 est conservé séparément ; il ne faut pas le confondre avec le seul différentiel de cette session. Aucun projet complet, cache, environnement, dump ou clé privée n’est inclus.
