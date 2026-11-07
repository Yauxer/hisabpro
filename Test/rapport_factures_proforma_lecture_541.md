# Lot541 — statut proforma conservé dans les réponses API

## Cause et changement

La recette navigateur540 a trouvé deux commandes « Modifier le brouillon »
pour un brouillon et une proforma, au lieu d'une commande propre à chaque
document. La création stockait bien `est_proforma=true`, mais `FactureOut`
ne déclarait pas ce champ. FastAPI le supprimait de la réponse de création
et de la liste (`FactureLectureOut` hérite de ce schéma). Le frontend ne
pouvait donc plus reconnaître la proforma ni proposer sa conversion.

Correction d'une ligne : déclaration de `est_proforma` dans le schéma de
sortie, booléen optionnel avec le même repli que les autres indicateurs.
Le champ existe déjà en base ; aucune migration, aucune déduction depuis le
préfixe du numéro, aucun changement des règles de conversion, validation,
stock ou comptabilisation. Les valeurs historiques nulles restent lisibles.

## Tests exécutés

- Avant correction : **2échecs,29avertissements,35.69s**,code1.
  Dès la création de la facture ordinaire, le booléen attendu est absent.
- Après correction : **2réussites,29avertissements,30.61s**,code0.
- Connexes : **18réussites,28avertissements,69.53s**,code0.
  `Test/run_unit_tests.py Test/test_patch062_validation_snapshots.py
  Test/test_factures_suppression_postgres.py
  Test/test_e2e_factures_erreur_lecture_isole.py -ra`.
  Les tests de calcul/SQLite historiques sont distingués des parcours natifs
  PostgreSQL et Edge. Aucun échec/erreur/ignoré dans ces deux commandes.
  Deux Python du lot compilés,98SQL et115guides inchangés.

Commande ciblée : `Test/run_unit_tests.py
Test/test_factures_proforma_lecture_isole.py -ra`, `PYTHON_DOTENV_DISABLED=1`.

Deux parcours API vente/achat : création ordinaire/proforma, liste JSON,
téléchargement du PDF portant PROFORMA, refus400 de validation/comptabilisation
avant conversion, tables métier inchangées par la lecture et les refus,
conversion existante en facture définitive120MAD, relecture du statut false,
seconde conversion refusée400 sans mutation, comptabilisation, validation de
l'écriture et export FEC200. Toutes les données sont fictives.

## Limites et reprise

Exclusivement PostgreSQL nonce temporaire, rôle API non propriétaire.
Aucune donnée réelle ni écriture définitive modifiée. La sérialisation peut
maintenant restituer le statut au navigateur ; les six tests visuels du lot540
doivent encore être repris, sans masquer leurs échecs initiaux.
Ce lot ne prétend pas qualifier la concurrence de conversion de proformas.
Recette utilisateur et production non validées, point6 humain en attente.

Installer `hisabpro-backend/schemas.py`, puis redémarrer l'API.
Le ZIP est indépendant de la correction d'affichage des permissions540.
