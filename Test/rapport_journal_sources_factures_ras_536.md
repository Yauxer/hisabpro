# Source des factures et RAS distincte — 536

## Problèmes et correction

Une facture fournisseur est comptabilisée avec sa référence fournisseur,
alors que le Journal ne recherchait que le numéro interne de facture.
Supprimer son brouillon la laissait marquée comptabilisée, sans régénération
possible. Les préfixes AM-/ACQ- étaient aussi interprétés comme une autre
origine malgré une source interne facture.

La suppression d'une pièce de facture pouvait par ailleurs effacer le marqueur
de RAS historique alors que son OD distincte et définitive restait présente.
Enfin, une référence renommée vers celle d'une autre facture pouvait libérer
le mauvais document, même en filtrant société/date/tiers.

Le seul fichier produit modifié est `routers/ecritures.py` :

- La recherche reconnaît numéro interne et référence externe d'achat exacte,
  avec société, date et auxiliaire réel. Aucun choix du premier résultat en
  cas d'ambiguïté ; refus409 sans modification.
- La véritable trace de création de l'écriture dans l'audit013, lorsqu'elle
  existe, fournit la référence d'origine. `baseline_initiale` ne vaut jamais
  création et n'est pas utilisée pour reconstruire le passé.
- Identité/source/date de la trace sont vérifiées ; les auxiliaires courants
  doivent recouper ceux des lignes créées dans la même transaction. Une
  contradiction ou plusieurs créations entraînent409, sans réparer de données.
- Une référence courante renommée, vide ou en collision peut ainsi retrouver
  le bon document grâce à sa création réellement enregistrée. Aucun parsing
  heuristique du libellé ni nouvelle colonne de liaison.
- Les préfixes textuels ne remplacent pas la source interne.
- Seul l'indicateur de comptabilisation de la facture est libéré. Une RAS
  comptabilisée séparément n'est pas annulée par cette suppression.

Les écritures définitives, l'audit et l'OD RAS restent intacts. Aucun taux,
calcul fiscal, schéma ou migration supplémentaire.

## Tests exécutés

- Première campagne : 8 échecs/1réussite,29avertissements,40,79s,code1.
  Sept défauts réels ; un test essayait de créer un doublon chez le même
  fournisseur, déjà correctement refusé409 par l'API. Cette règle est conservée.
- L'ambiguïté est ensuite représentée par deux fournisseurs légitimes de même
  référence et un auxiliaire manquant sur le seul brouillon fictif :
  1échec,8désélectionnés,28,63s,29avertissements,code1.
- Premier correctif :13réussites,29avertissements,45,06s,code0.
- Contrôle complémentaire du renommage vers une facture existante :2échecs,
  13désélectionnés,29avertissements,30,23s. Le texte seul ne suffisait pas.
- Après récupération de l'origine réellement auditée :17réussites,
  29avertissements,49,83s,code0.
- Qualification connexe : **171réussites,169désélectionnés,
  29avertissements,405.77s**,code0. Aucun échec/erreur/ignoré.
  `Test/run_unit_tests.py Test/test_consolidation_factures536_isole.py
  -k "recette530 or annulation532 or test_liberation534_ or test_facture536_" -ra`.
  Les169non sélectionnés ne sont pas déclarés exécutés dans cette commande.
  Trois Python du lot compilés ; sources figées,98SQL/115guides intacts.
  Frontend inchangé ; aucune recette utilisateur ou production déclarée validée.

Vente et achat : suppression/recomptabilisation sans toucher les règlements ;
deux fournisseurs de même référence distingués par leur auxiliaire ; préfixes
AM/ACQ ; ambiguïté et dates contradictoires refusées ; références renommées,
vides ou identiques à une autre facture sans libérer celle-ci.

Le scénario RAS représente explicitement un historique fictif : facture120,
paiement110 et vraie OD de10, ensuite validée. Le marqueur historique est posé
dans le seul laboratoire, sur une facture fictive ; la source de l'OD est
marquée avant sa validation, aucun définitif réécrit. L'OD, ses lignes et son
audit restent identiques après suppression puis recomptabilisation de la
facture ; retenue imputée10 et solde0 conservés. Hypothèses TVA20%/RAS10%
de laboratoire reprises des tests existants, aucune qualification normative.

## Installation et limites

Installer `routers/ecritures.py`536 après530/532/534, ou le cumulatif de session,
puis redémarrer l'API. Aucune nouvelle migration. L'audit013 existant est lu
uniquement, sans droits supplémentaires ni reconstitution de son historique.

Sans véritable création auditée, seuls les critères exacts disponibles sont
utilisés ; les modifications antérieures à l'installation de l'audit ne sont
pas reconstituées. Une origine inconnue/ambiguë ou des auxiliaires/date
contradictoires nécessitent une vérification humaine. Aucune référence de pièce
obligatoire nouvelle pour les écritures manuelles ou leur validation.

Tests sur PostgreSQL nonce uniquement, aucune base réelle. Recette utilisateur,
production et point6 humain restent en attente. Les autres générateurs et
accès directs hors API demeurent des périmètres distincts.
