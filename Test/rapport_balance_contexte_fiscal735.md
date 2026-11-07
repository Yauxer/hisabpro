# Contexte fiscal externe735 — rapport de validation

Quatre rubriques internes CM/CSS/crédits/acomptes, explicitement sourcées,
versions immuables, droits, référence B12 et exports PDF/Excel/ZIP avec logo.
Une case ou une liste vide reste inconnue ; néant ne fabrique pas de zéro.
Crédits600 dont150 déjà imputés et450 restants ; comparaison aux150 déclarés
côté acomptes, écart0. Variante149,99 : écart−0,01 et alerte. Versement1000
et crédit antérieur100 distincts, CSS0 explicite séparée. Aucun impôt dû ou
solde final calculé, aucune qualification normative déduite.

Le contrôle B12 conservé est copié pour mémoire (1460 dans le jeu). Une nouvelle
version B12 au taux déclaré10 donne730 ; le contexte conserve1460 avec alerte
jusqu’à sa conservation explicite. Anciennes versions et autres compléments
inchangés ; aucune écriture/liquidation/paiement confirmé.

## Tests réellement exécutés

460connexes réussis758,61s et2annuels33,95s ;0échec/erreur/ignoré. Ciblés34API/purs76,02s,8Edge+restauration191,63s,1Edge B12 supplémentaire48,49s(8non sélectionnés). Reprise733:4réussis107,39s. Campagnes recouvrantes non additionnées. Build7,23s code0,1180SHA figés,110SQL/bootstrap/modèles et7moteurs fiscaux inchangés. Restauration104/83tables/cinqfichiers. Guide Word/PDF8pages,Excel5feuilles,huitcas humains Non testé.

Les460cas couvrent le nouveau contexte, les compléments antérieurs, la recette
intégrée733, les moteurs purs historiques et la restauration. Les résultats
ciblés sont recouverts par cette campagne et ne s’additionnent pas. Les2annuels
vérifient séparément le parcours bancaire/connecté et la cohabitation des
balances ; la preuve historique719 est sauvegardée puis restaurée.

L’API est exécutée sous LOGIN non propriétaire dans un cluster PostgreSQL
nonce104, jamais sur la base réelle. Les tests purs et certains historiques
PDF utilisent leur banc unitaire/SQLite existant ; ils ne remplacent pas une
validation PostgreSQL. Le navigateur Edge effectue les vraies requêtes ; seules
les réponses réellement obtenues sont retenues pour les cas de retard.

Sauvegarde/restauration :83tables/cinqfichiers, octets/ACL/séquences/versions,
justificatifs et logos comparés ; cible jetable nettoyée et source préservée.
Aucune migration ajoutée. Les7moteurs fiscaux et110fichiers SQL/bootstrap/modèles
protégés sont inchangés. Compilation des11Python du lot à la livraison.
Avertissements existants :30dépréciations dans les campagnes ; build signale
le volume des chunks et l’import XLSX mixte, sans échec.

## Documents et limites

[Mode d’emploi](../docs/LIASSE_BALANCES_CONTEXTE_FISCAL_735.md),
[Word](../docs/recette/MODE_EMPLOI_CONTEXTE_FISCAL_735.docx),
[PDF](../docs/recette/MODE_EMPLOI_CONTEXTE_FISCAL_735.pdf),
[Excel](../docs/recette/MODE_EMPLOI_CONTEXTE_FISCAL_735.xlsx).
Les8cas humains restent Non testé ; résultat réel/anomalies/preuves vierges.
Mobile390, PDF export et pages du cahier inspectés ; Office non ouvert.

[Sources et réserve](../docs/audit/SOURCES_CONTEXTE_FISCAL_20261022_735.md) :
CGI officiel non récupéré intégralement (MEF timeout,DGI405), donc aucune
nouvelle règle de liquidation/EDI codée. Les tests ne valident pas les
qualifications fiscales, la recette utilisateur ou la mise en production.
RH/paie etpoint6 humain différés. Suite indépendante : sélecteur d’articles
commercial, erreurs de chargement et faux résultats de recherche.
