# Suppression de brouillons : libération du bon document — 534

## Cause et correction

Le Journal recherchait le document source par la seule référence libre, en
essayant successivement facture, avoir puis premier règlement correspondant.
Deux règlements d'une ventilation ont légitimement la même référence bancaire.
Supprimer la pièce du second pouvait donc libérer le premier et laisser le
second marqué comptabilisé alors que sa pièce avait disparu. Une référence
renommée pouvait libérer une facture sans rapport ou empêcher la régénération
du bon règlement. Une pièce manuelle de même référence avait aussi cet effet.

Le correctif reste dans `_liberer_document_source`, `routers/ecritures.py` :

- La source interne sépare facture, avoir et règlement. Une pièce manuelle,
  d'import ou d'une autre origine ne libère aucun de ces documents par texte.
- Pour un règlement, le lien `ecriture_id` est prioritaire, même si la référence
  a changé ou est vide. Seul ce règlement redevient non comptabilisé et perd
  son lien, puis peut être régénéré. Les autres pièces restent inchangées.
- La mise à jour est conditionnée au lien encore présent : une nouvelle
  affectation concurrente ne doit pas être écrasée par une ancienne lecture.
- Un lien partagé par plusieurs règlements est refusé409 sans suppression.
- Une pièce portant l'annulation d'un règlement, ou l'origine d'un règlement
  déjà annulé, est conservée : suppression refusée409.
- Le fallback historique ne concerne que les règlements sans lien, déjà
  marqués comptabilisés, de même date et référence/numéro/clé technique.
  Il doit être unique, avec montant positif fini et totaux débit/crédit
  exactement concordants. Ambiguïté ou incohérence restent visibles409.

Le contrôle des écritures définitives reste inchangé. Aucune migration,
réparation historique, modification de taux ou d'écriture validée.

## Tests exécutés

- Avant correction : 16 échecs, 2 réussites, 29 avertissements, 64,68 s,
  code1. Les deux cas déjà corrects supprimaient la pièce du premier règlement.
- Après correction initiale : 18 réussites, 29 avertissements, 51,63 s,
  code0. Suppression suivie d'une nouvelle comptabilisation vérifiée.
- Extension de huit scénarios historiques : 6 réussites, 2 échecs,
  18 désélectionnés, 29 avertissements, 38,99 s. La source historique de60
  ne devait pas libérer le règlement de120 ; garde exacte ajoutée.
- Qualification ciblée finale : **26 réussites, 29 avertissements, 67,85 s**, code0.
- Qualification connexe : **323 réussites,
  29 avertissements, 1032.02 s**, code0. Aucun échec/erreur/ignoré.
  Commande : `Test/run_unit_tests.py Test/test_consolidation_liberation534_isole.py
  -k "recette530 or annulation532 or liberation534" -ra`.
  Le filtre correspond aussi au nom du fichier liberation534 : les323cas du
  wrapper ont réellement été exécutés, sans désélection (169précédents et154
  cas de règlements/annulations/libération). Aucun décompte de154seulement.
  Sources figées, ACL inchangées ; trois Python du lot et neuf du cumulatif
  compilés, 98 migrations et 115 guides de recette inchangés. Frontend inchangé.

Qualification externe distincte : **247 réussites, 29 avertissements,
231.50 s**, code0. Restauration098 à froid, immobilisations, livre d'inventaire,
fiscalité, clôtures, stock et montants NaN/non finis inclus. Les fixtures
historiques propriétaires et tests de calcul pur restent distingués du wrapper
principal LOGIN ; aucune qualification sur base réelle. Deux commandes sur les
mêmes sources figées :323+247=570exécutions réussies, sans présenter ce nombre
comme des fonctionnalités distinctes ni comme un unique lancement pytest.
Restauration :74tables, source préservée, cibles supprimées, trois fonctions098
identiques et refus409/reprise conservés.

Les 26 cas couvrent vente/achat, premier/second règlement d'une ventilation,
référence commune, renommage et collisions avec numéro de facture ou clé
REG d'un autre règlement ; pièces manuelles ; correction associée à une
annulation ; lien dupliqué ; historique unique/ambigu/montant incompatible
et origine annulée. Les négatifs comparent les tables métier avant/après.

Le wrapper ajoute ces cas aux recettes530/532, sous LOGIN PostgreSQL non
propriétaire, avec parcours réels de validation, lettrage, rapprochement,
captures RAS et annulations collectives dans Edge. Campagnes non additionnées.

## Installation et limites

Installer `routers/ecritures.py`534 après530/532, ou utiliser le cumulatif,
puis redémarrer l'API. Aucune migration supplémentaire. Ne pas décocher
manuellement un indicateur comptable pour forcer une régénération.

Clusters nonce uniquement, données fictives, aucune connexion à la base réelle.
Les sources inconnues et les ambiguïtés historiques ne sont pas devinées.
Le rattachement des factures fournisseurs par référence externe et les autres
générateurs sont des contrôles distincts à poursuivre ; ce lot ne prétend pas
résoudre tous les anciens liens documentaires. Recette utilisateur, production
et point6 humain restent en attente.
