# Règlements : comptabilisation et sources concurrentes — 530

## Problèmes reproduits et correction

Sur une application réelle sous LOGIN PostgreSQL non propriétaire, deux
comptabilisations simultanées pouvaient produire deux pièces pour le même
règlement. Une modification du montant pendant la génération pouvait laisser
un règlement de 60 avec une écriture de 120 ; une suppression concurrente
provoquait une erreur 500. Les contrôles lisaient le règlement sans verrou.

`routers/commercial.py` verrouille et recharge maintenant le règlement avant
de comptabiliser, modifier ou supprimer. L'annulation utilise le même verrou
et recharge aussi l'objet. La seconde comptabilisation conserve le refus 400
existant ; modification/suppression après comptabilisation restent refusées
409. Une modification antérieure est relue, une suppression antérieure donne
404. Un règlement annulé sans comptabilisation est explicitement refusé 409.

L'annulation révélait également une erreur 500 sous les permissions prévues
en production : le `FOR UPDATE` sur `ras_reglement_captures` exigeait le droit
UPDATE, volontairement absent de ce registre immuable. Le seul appelant
d'`annuler_capture` détient déjà le verrou du règlement, également utilisé
par la création d'une capture. La lecture du registre utilise cette
sérialisation existante, sans verrou sur la capture ni élargissement des
permissions. Les contraintes d'unicité et de conservation SQL restent actives.

Aucun schéma, taux, calcul fiscal ou historique comptable n'est modifié.

## Tests exécutés et oracles

- Reprise 528 avant modification : 12 réussites, 29 avertissements, 56,81 s.
- Avant correction : 14 échecs, 29 avertissements, 65,72 s, code 1.
  Les cas d'annulation étaient arrêtés par l'erreur de permissions RAS ;
  ils ne constituaient pas encore une preuve du refus d'un règlement annulé.
- Après le seul verrouillage : 10 réussites, 4 échecs, 29 avertissements,
  73,27 s. Les quatre erreurs restantes identifient exactement la lecture RAS.
- Après les deux corrections : 16 réussites, 29 avertissements, 77,92 s,
  code 0. Aucun échec, erreur ou cas ignoré.
- Qualification connexe : **110 réussites, 169 désélectionnés,
  29 avertissements, 231.03 s**, code 0. Commande :
  `Test/run_unit_tests.py Test/test_consolidation_reglements530_isole.py -k recette530 -ra`.
  Les 169 cas non sélectionnés ne sont pas déclarés exécutés dans cette commande.
  Sources figées et ACL identiques contrôlées par le wrapper.
  Quatre Python compilés ; 98 migrations et 115 guides de recette inchangés.
  Frontend inchangé, aucun build supplémentaire requis pour ce lot backend.

Les seize nouveaux cas utilisent des transactions PostgreSQL natives et
`pg_stat_activity` pour observer la requête retenue. Ils couvrent vente et
achat, les deux ordres génération/mutation, suppression et annulation,
ainsi que deux annulations simultanées avec capture RAS.

Pour chaque sens, deux factures de 120 et 240 reçoivent une ventilation de
240 (120/120), puis un complément de 120. Une seule pièce par règlement,
cinq pièces équilibrées, cinq lignes collectives avec tiers réel, validation,
lettrage RCA et rapprochement du relevé de 240 sont contrôlés. Le FEC est
réellement exporté. Les hypothèses TVA 20 % et RAS 10 % proviennent des jeux
fictifs existants, sans qualification réglementaire nouvelle.

Avec une capture de 30 associée à un règlement de 400 sur une facture de
1200, deux demandes d'annulation retrouvent la même correction. Une seule
annulation de capture et une correction par pièce d'origine ; solde revenu
à 1200 et retenue active à zéro. UPDATE/DELETE/TRUNCATE restent absents des
droits applicatifs sur les deux tables du registre RAS.

Le wrapper ajoute les tests existants de ventilation, rapprochement,
captures RAS, annulation collective et annulation après pointage dans Edge,
sous la même application 098 avec LOGIN SQL non propriétaire. Le numéro de
tests exécutés n'est pas un nombre de fonctionnalités et les campagnes
successives ne sont pas additionnées.

## Installation et limites

Installer `routers/commercial.py` et `services/ras_reglement_service.py`, puis
redémarrer l'API. Aucune migration supplémentaire. Ne pas élargir les droits
UPDATE du registre RAS pour contourner une erreur de lecture.

Uniquement des clusters éphémères marqués par nonce, données fictives et ports
loopback dédiés. Aucune connexion au PostgreSQL réel de l'utilisateur.
Les tests ne réparent aucune pièce historique. Les autres générateurs,
accès SQL directs et identités historiques de sources restent des périmètres
distincts. Recette utilisateur, mise en production et point 6 humain restent
en attente. XML/EDI officiel toujours conditionné aux spécifications officielles.
