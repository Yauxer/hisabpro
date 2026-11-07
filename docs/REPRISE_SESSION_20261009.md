# HisabPro — reprise du 9 octobre 2026

Cette livraison reprend les lots interrompus, sans réappliquer les anciennes
corrections. Le dépôt courant contient déjà les changements décrits ci-dessous.

## Résultat technique

- Globale finale réellement exécutée : **2 582 réussites, aucun échec, aucune
  erreur ni test ignoré**, code retour 0, en **2 024,18 secondes**.
- Les 32 avertissements existants sont conservés dans le rapport.
- **625 empreintes** de sources et tests identiques avant/après.
- La première globale reste documentée : 2 575 réussites et quatre échecs.
  Trois supports simulés d'édition ont été complétés. L'échec mobile initial
  n'a pas été reproduit ; son diagnostic préserve désormais l'exception originale.
- Les recettes PostgreSQL utilisent uniquement les clusters isolés contrôlés
  par les fixtures. Aucun PostgreSQL réel ni donnée comptable réelle utilisé.

La [preuve globale finale](../Test/rapport_non_regression_globale_20261009_finale.md)
précise la commande et le périmètre. Le
[journal complet](../CODEX_PROGRESS.md) conserve les résultats intermédiaires.

## Principaux changements de la reprise

- Filtres de dates préservés à l'arrivée tardive du contexte dans les balances,
  le grand livre et le rapprochement bancaire ; anciennes réponses bancaires
  écartées quand société, compte ou période changent.
- Montants des nouvelles requêtes Articles contrôlés avant mutation ; frais
  d'emballage et transport facultatifs exposés dans leur formulaire.
- Aperçu des libellés selon le préfixe et l'exercice, sauvegarde des paramètres
  Fiscalité accessible et qualification TVA des achats éditable en brouillon.
- Filtre des clients/fournisseurs par délai, combiné aux filtres existants,
  avec traitement explicite des valeurs inconnues.
- Recette connectée des achats partiels jusqu'aux deux paiements et au lettrage :
  deux BR de 1 et 3 unités, factures/règlements de 600 et 1 800 MAD, quatre
  écritures/dix lignes, débit = crédit = 4 800 MAD, fournisseur soldé, stock 4.

Ces chiffres sont ceux de sociétés fictives de laboratoire. Ils ne constituent
pas une qualification fiscale ou une correction des données de l'utilisateur.

## Recette utilisateur à effectuer

Les nouveaux cas restent tous **Non testé** pour la recette utilisateur :

- Corrections de formulaires et de dates, huit cas :
  [PDF](recette/ANNEXE_RECETTE_CORRECTIONS_20261009.pdf),
  [Excel de suivi](recette/ANNEXE_RECETTE_CORRECTIONS_20261009.xlsx).
- Achats partiels, paiements et lettrage, deux cas :
  [PDF](recette/ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.pdf),
  [Excel de suivi](recette/ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.xlsx).

Ces annexes complètent le cahier annuel existant ; leurs sociétés fictives
indépendantes ne doivent pas être ajoutées à son oracle annuel. Suivre les
prérequis et consigner le résultat réel, les anomalies et les preuves dans Excel.

## Utiliser le cumulatif

Le fichier de livraison est
`HisabPro_Session_20261009_1404_Cumulatif_Verifie.zip`.
Il contient les versions effectivement livrées de cette reprise, avec le journal
et le manifeste. C'est un **différentiel**, sans projet complet, environnement,
cache, secret ni dump.

Pour une autre copie, le prérequis est une version déjà à jour **jusqu'au lot
265**. Le correctif de démarrage GRH 229 et le bilan détaillé 256 font partie de
ce socle antérieur ; ils ne sont pas réembarqués dans ce cumulatif.
Sur le dépôt courant, les modifications sont déjà intégrées.

Lire le [guide de mise à jour](MISE_A_JOUR_REPRISE_20261009.md) avant transfert :
comparer les changements locaux, préserver la configuration et tester d'abord
sur une copie isolée. Les lots de cette reprise n'ajoutent pas de migration SQL.
Les anciens mécanismes de démarrage peuvent cependant exécuter du DDL selon
la configuration ; cette note n'autorise aucune opération sur une base réelle.

## État et prochaine reprise

La [checklist](audit/CHECKLIST_UTILISATEUR_20261007.md) compte 40 demandes
terminées, 30 partielles, deux absentes et une bloquée. La
[matrice générale](audit/MATRICE_COUVERTURE_HISABPRO.md) conserve les périmètres
et preuves, avec 15 fonctions terminées, 46 partielles, cinq absentes et quatre
bloquées. Développement global partiel, tests de cette version validés,
recette utilisateur à effectuer, mise en production non validée.

Reprendre la **RAS sur les règlements partiels** depuis l'audit 208 et le code
présent. Vérifier d'abord les qualifications, événements générateurs et pièces
officielles ; reproduire ensuite le comportement sur une société fictive isolée.
Le premier règlement ne suffit pas, à lui seul, à justifier une retenue totale.
Ne pas assimiler une estimation documentaire à une retenue effectivement opérée.

La paie définitive reste limitée par la confirmation des parts et conditions
CNSS ; l'XML/EDI reste conditionné au schéma officiel applicable. Les justificatifs
FEC/ETIC et autres anomalies historiques demeurent visibles dans le
[registre](audit/REGISTRE_ANOMALIES_HISABPRO.md). Aucune certification officielle
ni validation réglementaire automatique n'est revendiquée.
