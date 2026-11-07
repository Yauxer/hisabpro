# Chèques, effets et annuels sous LOGIN limité — lot 456

Huit parcours Edge existants sont rejoués avec leurs assertions et oracles
inchangés sur la même application complète 091 et le LOGIN `hisabpro` non
propriétaire. Les anciennes fixtures partielles ne servent pas à cette recette.
Aucune API métier remplacée ; aucune migration rejouée après les pièces.

## Parcours réellement exécutés

- Chèque sur ordinateur et effet sur mobile : facture fictive de 120, remise,
  encaissement avec frais de 10,01, validation, proposition de rapprochement,
  confirmation et lettrage. Banque 109,99, frais 10,01 ; quatre pièces/dix lignes,
  débit = crédit = 480 ; FEC réel et originaux conservés.
- Les deux variantes annuelles 2025 → 2026 : clôture par interface, périodes
  fermées, à-nouveaux et FEC des deux années. L'oracle fiscal de laboratoire
  existant utilise 3 000 d'impôt : résultat avant cet impôt 89,99, après −2 910,01.
  À-nouveaux de 3 020 : 5141 D109,99, 1199 D2 910,01, 4455 C20, 4453 C3 000.
  Pointage conservé en lecture seule, dérapprochement après clôture refusé 409.
  Ces chiffres testent le comportement existant, pas un régime fiscal réel.
- Chèque de 1 200 remis puis rejeté, ordinateur/mobile : créance réouverte,
  virement de remplacement, facture payée, validation et lettrage de quatre
  lignes. Cinq pièces/onze lignes, débit = crédit = 6 000 ; banque 1 200,
  comptes d'attente/client soldés. Lecteur 403 et autre société 404.
- Frais au demi-centime 10,005 : deux refus 422 lisibles dans Edge,
  état et données inchangés.

## Résultats

- Ciblés : **8 réussis en 64,48 s**, 29 avertissements,
  zéro échec/erreur/ignoré (`instruments456_cible.*`).
- Connexes : **79 réussis en 161,82 s**, 29 avertissements,
  zéro échec/erreur/ignoré (`instruments456_connexes.*`). Frais, opérations datées,
  dates navigateur/minuit, identité SQL du lettrage et FEC inclus.
- Compilation Python du nouveau banc : code 0. Aucun changement de produit,
  de migration ou de règle métier ; pas de nouveau build nécessaire.

Les fichiers de preuve sont dans `.codex-tests/`, exclus du ZIP. Les gardes et
assertions du fixture contrôlent l'arrêt de ses processus et la suppression des
seuls répertoires nonce créés. Les suites recouvrantes ne s'additionnent pas.

## Limites et suite

Les frais saisis ne constituent pas un calcul réglementaire ou contractuel
d'escompte automatique. Les autres instruments, banques et variantes annuelles
restent à étendre. Aucun PostgreSQL réel ni donnée réelle utilisé ; installation,
recette utilisateur et production non prévalidées. Point 6 en attente.

Suite : vérifier l'ergonomie du Journal en consultation seule, puis regrouper les
parcours de cette reprise, mettre à jour la couverture et livrer le cumulatif.
