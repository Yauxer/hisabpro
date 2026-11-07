# HisabPro — décision de recette : facturation et comptabilité

Cette qualification porte sur le parcours principal de facturation et de comptabilité. Elle exclut RH/paie, dépôt fiscal officiel et XML/EDI. Elle ne vaut ni certification ni validation réglementaire automatique.

## Ce qui est démontré

Le cycle annuel connecté repart d'une société fictive : référentiels, devis, commande, livraison, facturation, validation, avoir, règlements, acompte, chèques/effets, lettrage, stock, immobilisation, inventaire, clôture et à-nouveaux. Les contrôles rapprochent les écritures produites aux calculs indépendants du jeu source. Le bilan vaut337 010 MAD, le résultat net106 409,75 MAD, le stock6 600 MAD, l'immobilisation24 000 MAD brut/4 800 MAD amortis/19 200 MAD net, le report2026 est unique et équilibré à343 810 MAD.

Les écritures définitives, périodes fermées et exercice clôturé refusent les mutations interdites. Les doubles requêtes concurrentes ne créent pas une deuxième comptabilisation. Le lecteur, l'accès invité révoqué et une société étrangère sont refusés pour les opérations protégées. Un changement personnel de mot de passe invalide les anciens jetons versionnés et le secret précédent.

Le livre annuel est archivé avec version, auteur, date et SHA-256 ; le PDF est contrôlé et une opération2026 ne change pas le snapshot2025. La sauvegarde/restauration est rejouée sur deux PostgreSQL natifs éphémères distincts : schéma, données, droits, séquences, justificatifs, logos et rendu sont contrôlés. Le banc de restauration104 n'est pas le PostgreSQL de l'utilisateur ; ses données fictives sont distinctes du scénario annuel50opérations.

## Statuts de sortie

- Développement : parcours principal présent ; correction de chargement du calendrier après révocation livrée. Les réserves fonctionnelles ci-dessous restent ouvertes.
- Tests automatisés : campagnes finales et preuves de cette session jointes ; les échecs initiaux restent conservés.
- Recette utilisateur : à effectuer sur une copie isolée, avec le cahier fourni ; aucun succès humain n'est prérempli.
- Mise en production : non validée. Les contrôles d'environnement et réserves doivent être décidés avant ouverture réelle.

## Réserves précises

1. Navigation mobile : un arrêt de chargement de Clôture à15 000 ms est conservé dans recette839_cible, après45 opérations. La passe finale ajoute une trace sans retry ni délai augmenté. Une réussite suivante ne prouve pas la cause ni sa correction ; surveiller les navigations sur l'environnement cible et conserver la trace si récidive.
2. Archivage individuel des factures, fiche FAC013 : non qualifié et bloqué par la source du cahier. L'archivage annuel du livre est une fonctionnalité distincte, désormais testée ; ne pas les confondre.
3. Cession d'immobilisation, IMM004 : variante partielle, différence d'oracle sur le prorata2026 de13,33 MAD ; méthode et traitement fiscal à faire valider avant usage de cette variante. Acquisition et amortissement du scénario annuel sont contrôlés séparément.
4. Délais de paiement FAC017 : suivi et export testés ; qualification fiscale/justificatifs contractuels restent partiels. Aucun calcul d'amende ni dépôt officiel validé ici.
5. Données historiques FEC/ETIC : justificatifs manquants et reliquats B6/B13 restent visibles. Aucun solde ni date n'est inventé pour supprimer un contrôle.
6. Sessions : les JWT historiques sans version gardent leur durée de vie initiale ; prévoir une reconnexion générale avant production. La déconnexion locale est testée, sans prétendre révoquer côté serveur tout jeton déjà capturé.

## Vérifications sur l'environnement cible

Utiliser une copie sauvegardée et isolée du futur environnement : appliquer les migrations prévues dans l'ordre, conserver les migrations déjà exécutées, démarrer avec le rôle PostgreSQL applicatif limité et vérifier les journaux. Contrôler les paramètres de société, droits réels des utilisateurs, origine frontend autorisée, HTTPS, secrets de déploiement et durée des sessions. Rejouer la sauvegarde/restauration vers une cible vierge distincte et vérifier l'accès aux justificatifs et logos ; mesurer le temps de reprise attendu par l'entreprise.

Faire vérifier par le responsable comptable un cycle représentatif de ses opérations, les comptes et auxiliaires, les factures imprimées, la balance, le grand livre, les immobilisations, les contrôles de clôture et les à-nouveaux. Tester le mobile réellement utilisé. Ces vérifications n'autorisent aucune réparation silencieuse d'écritures définitives.

## Où tester et consulter les preuves

Le jeu exact reste docs/recette/jeu_donnees_recette.json, avec les justificatifs et relevés voisins. Le classeur SUIVI_AUTOMATISATION_CAHIER_839.xlsx sépare les résultats automatiques et les fiches encore non qualifiées. Les rapports835,837 et839 décrivent chaque scénario et les échecs conservés. PREUVE_QUALIFICATION_CORE841.json et le manifeste CANDIDAT_FACTURATION_COMPTABILITE_841.json identifient les tests et les empreintes de la candidate.

La prochaine action est une recette utilisateur du périmètre principal sur une copie de l'environnement cible, puis une décision explicite sur les réserves. RH/paie et les formats de dépôt fiscal restent différés. Aucune base réelle n'a été modifiée pendant cette qualification.


Résultats finaux de session : 100 tests réussis, zéro échec/erreur/ignoré dans les campagnes finales sélectionnées. Les essais initiaux échoués sont conservés séparément. Restauration : 83 tables et 8 fichiers, droits et séquences identiques. Navigation ciblée :112 chargements réussis sur ordinateur/mobile, sans retry ni délai augmenté ; aucune cause de l’incident initial affirmée. Build835 réussi ; seuls deux fichiers frontend du produit ont changé dans la session, aucun backend ni migration. Le suivi passe de144 à158 fiches automatiquement réussies ;5 partielles,99 non qualifiées individuellement,10 bloquées. Les70 statuts fonctionnels globaux restent16 terminés,49 partiels,1 absent et4 bloqués. Candidate : 462 empreintes produit, SHA-256 global ad8ad5ce20d93375890c41e2da69d5ed9435b3dd71761ef08d714007ba451a24.
