# HisabPro — fin de développement hors RH/paie

Ce document borne la prochaine version de recette. Il ne remplace pas la
roadmap complète et ne transforme pas les fonctions partielles en fonctions
terminées. Aucun nouveau module n’est ajouté pendant cette stabilisation.

## Clôture des points qui empêchaient de figer cette candidate

| ID | Action finie à réaliser | Critère de sortie | État |
|---|---|---|---|
| FIN-01 | Séparer les factures achat/vente dans le cycle commercial ; fiabiliser les cinq listes concernées | Tests Edge/API avec deux sens, refus PostgreSQL réels, reprise, vrai vide, exercice retardé,102factures et dépendance facture de réception client | Terminé673 :28tests réussis en189,81s ; recouvert dans la campagne675 |
| FIN-02 | Exécuter une campagne commune sur les sources applicatives figées | Aucun échec/erreur/ignoré dans les cas sélectionnés ; empreintes identiques avant/après et témoins comptables/documents conservés | Terminé675 :312réussites en1424,85s ;382sources et témoins de trois sociétés préservés |
| FIN-03 | Vérifier installation vierge et livraison | Chaîne102 sur bac jetable, aucun SQL historique réécrit ; ZIP différentiel listé, CRC et manifeste vérifiés ; journal et limites à jour | Terminé675 :93SQL/29rejeux, build9,48s,106fichiers protégés et63archives antérieures contrôlés ; cible réelle distincte |

Ces trois points forment la liste technique de cette stabilisation. Un défaut
d’intégrité, de sécurité ou empêchant un parcours inclus suspend sa sortie
et doit être corrigé avant de la qualifier. Une amélioration de présentation,
un nouveau module ou une nouvelle variante facultative est reporté, avec sa
limite visible, au lieu de relancer une série indéfinie de développements.
Cette liste ne signifie pas qu’un audit exhaustif aurait prouvé l’absence
de tout autre défaut.

## Ce qui fonctionne déjà, sans être une recette humaine validée

Le dépôt contient les parcours de création de société, exercices, tiers et
articles ; devis, commandes, livraisons/réceptions et factures ; validation,
écritures, règlements et lettrage ; banques et rapprochement ; stock,
immobilisations, inventaire, clôture et à-nouveaux ; états et exports.
Les preuves ont des périmètres précis, conservés dans la matrice et les
rapports de tests. La campagne commune de cette stabilisation doit les
compléter sur le code figé ; elle ne prévalide pas tous les cas possibles.

Les guides, cahiers, jeux chiffrés et suivis existent. Les résultats humains
restent vierges :17dans le guide courant et12dans l’annexe documentaire RAS.

## Limites qui ne seront pas masquées pour annoncer une fin

| Élément | Ce qui manque réellement | Conséquence |
|---|---|---|
| LIA-09B | Référentiel officiel exhaustif du millésime applicable | Les codesT1… restent une présentation interne ; la liasse officielle exhaustive n’est pas livrée |
| LIA-09C | Schéma et codifications XML/EDI officiels applicables | Aucun export présenté comme prêt pour SIMPL-IS |
| LIA-09F | Modèles administratifs applicables aux rémunérations des tiers | Déclaration complète non développée ; distincte de la paie |
| LIA-09G | Textes, situations et modèles applicables à la taxe professionnelle et annexes | Déclaration complète non développée |
| LIA-09A / FEC historique | Justificatifs et qualifications certains des données réelles | Anomalies conservées ; aucune réparation arbitraire des écritures définitives |
| CPT-12 | Décision métier sur la réouverture d’un exercice définitivement clôturé | Protection maintenue ; réouverture annuelle non ajoutée |
| Fiscalité partielle | Qualification réelle des dossiers, déclaration/versement/imputation RAS complets et autres limites détaillées dans la matrice | Une capture ou un document joint ne prouve ni dépôt, ni versement, ni crédit imputable |
| Liasse seule et sociétés liées | Périmètres partiels décrits par09D et633/635 | Pas de journal créé par une balance importée ; pas de réplication générale des paiements/avoirs/livraisons ni consolidation fiscale |
| RH/paie | Périmètre différé par l’utilisateur | Aucun travail RH/paie dans cette stabilisation |

Il s’agit de limites de livraison, pas d’un classement définitif hors roadmap.
Une version de recette exploitable et une application couvrant toute la
roadmap sont deux jalons distincts. Le second ne peut pas être annoncé avec
ces éléments encore absents ou partiels.

## Ce qui reste nécessaire après la stabilisation technique

1. **Recette utilisateur à effectuer** sur les jeux fictifs, avec résultats
   réels et preuves. Le point6 réservé au retour de l’utilisateur reste différé.
2. **Installation et exploitation cibles à qualifier** : rôles, secrets,
   migrations déjà appliquées, sauvegarde/restauration et fonctionnement du
   dossier cible. Aucun test n’est lancé ici sur le PostgreSQL réel.
3. **Décision de mise en production** après ces validations. Une réussite
   automatisée ne valide ni les données réelles ni la conformité réglementaire.

## État de clôture de la stabilisation

Les trois points de stabilisation sont terminés dans le périmètre testé.
Les312cas de la campagne commune675 passent sans échec/erreur/ignoré ; les
empreintes et témoins sont préservés. Le CLI d’installation garde son statut
de runtime partiel, distinct du banc applicatif102 des parcours fonctionnels.
Les sources restent figées ; aucun nouveau module n’a été ajouté.

Les statuts globaux restent16terminé,47partiel,3absent,4bloqué. Leur découpage
de roadmap n’est pas reclassé par la fermeture de la stabilisation.
Développement de cette stabilisation terminé ; développement global partiel.
Tests automatisés validés dans les périmètres décrits ; recette utilisateur
à effectuer et production non validée. RH/paie et point6 humain différés.
[Bilan final et ZIPs](RAPPORT_STABILISATION_HORS_RH_20261020.md).

Références : [matrice fonctionnelle](MATRICE_COUVERTURE_HISABPRO.md),
[registre des anomalies](REGISTRE_ANOMALIES_HISABPRO.md),
[dernier bilan antérieur645–671](RAPPORT_SESSION_20261019_645_671.md),
[mode d’emploi Word](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx) et
[point d’entrée des cahiers](../recette/PAR_OU_COMMENCER_20261019.md).
