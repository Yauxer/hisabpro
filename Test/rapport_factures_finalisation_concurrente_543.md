# Lot543 — finalisation concurrente des factures

## Défaut reproduit et cause

Deux demandes simultanées sur la même facture provoquaient200/500, en vente
et en achat, pour la validation d'un brouillon comme pour la conversion d'une
proforma. La seconde requête avait lu l'ancien état puis tentait de mettre à
jour le numéro et les snapshots après que la première avait rendu la facture
définitive. La trace montre le refus de `hisabpro_guard_facture_validee()` sur
`UPDATE factures SET numero, compte_tiers_snapshot, societe_snapshot_json`.

Ce refus protégeait la facture ; le lot ne prétend pas qu'un double mouvement
de stock a été constaté avant correction. Le problème prouvé est la seconde
demande fondée sur un état périmé, qui aboutissait à une erreur500.

## Correction minimale

La lecture initiale des deux endpoints utilise `populate_existing()` et
`FOR UPDATE OF factures` avant les contrôles de statut. Le verrou ne vise que
le parent, malgré les chargements joints des lignes/échéances. Après le premier
commit, la seconde demande relit l'état réel et suit le contrat déjà existant :

- Validation répétée d'un brouillon :200, même numéro, sans nouvelle mutation.
- Conversion d'une proforma déjà convertie :400, sans nouvelle mutation.

Aucun trigger, numéro historique, écriture définitive, calcul, règle de stock,
migration ou permission n'est modifié. L'erreur SQL n'est pas simplement
interceptée pour masquer la cause.

## Tests réellement exécutés

- Avant correction : **4échecs,29avertissements,46.48s**,code1 ; quatre200/500.
- Diagnostic ciblé :1échec/3désélectionnés,22.31s ; représentation tronquée de
  la trace dans l'assertion. Trace complète ensuite :1échec/3désélectionnés,
  23.37s, même défaut et cause SQL identifiée. Aucun succès revendiqué.
- Après correction : **4 réussites, 29 avertissements, 34.21 s**, code0.
- Consolidation finale : **356 réussites, 29 avertissements, 751.93 s**, code0.
  `Test/run_unit_tests.py Test/test_consolidation_factures543_isole.py -ra`.
  Les356cas comprennent les352précédents et les4nouveaux ; les cas ciblés ne
  sont pas additionnés une seconde fois.
- Connexes externes : **247 réussites, 29 avertissements, 183.29 s**, code0.
  Les25fichiers et la commande sont décrits dans le [rapport538](rapport_factures_comptabilisation_concurrence_538.md).
  Deux commandes sur les mêmes sources figées : **603 exécutions réussies**,
  aucun échec/erreur/ignoré. Les anciennes qualifications restent historiques.
  Le wrapper LOGIN est distingué des tests de calcul pur et anciens bacs
  propriétaires. Restauration098 :74tables, source préservée, cibles supprimées,
  trois fonctions098 identiques. Trois Python du lot compilés,98SQL et115guides
  inchangés. Les sources frontend sont identiques au build5409.03s.

Commande ciblée : `Test/run_unit_tests.py
Test/test_finalisation_facture_concurrente_isole.py -ra`,
`PYTHON_DOTENV_DISABLED=1`.

Quatre parcours HTTP réels : brouillon/proforma et vente/achat, avec un article
stockable fictif au stock initial2. Un verrou PostgreSQL natif sur
`lignes_facture` retient la première requête pendant que la deuxième arrive.
Après finalisation, un seul numéro définitif et un seul mouvement sont attendus,
stock1 pour la vente ou3 pour l'achat. Une nouvelle répétition ne doit modifier
aucune table métier. Chaque parcours enchaîne comptabilisation de120MAD,
validation de l'écriture et export FEC200. Aucun mock métier.

## Limites et livraison

PostgreSQL nonce temporaire uniquement, API sous rôle LOGIN non propriétaire.
Les montants et quantités sont fictifs ; aucun chiffre réel n'est réparé.
Les séquences et protections historiques restent intactes. Les taux utilisés
dans les fixtures ne constituent pas une qualification fiscale nouvelle.
Frontend inchangé depuis540 ; buildVite540 historique9.03s, aucune nouvelle
compilation frontend revendiquée pour ce changement backend.

Copier `hisabpro-backend/routers/factures.py`543 puis redémarrer l'API.
Aucune migration nouvelle. Recette utilisateur sur l'installation réelle à
effectuer ; production et conformité non déclarées validées. Le point6 soumis
au retour humain reste réservé.
