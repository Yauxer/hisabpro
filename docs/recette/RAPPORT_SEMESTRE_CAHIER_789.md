# HisabPro — recette connectée de janvier à juin 2025

Un même parcours a été exécuté dans deux sociétés fictives indépendantes, sur ordinateur et mobile (Edge, 1440 et 390 pixels), avec PostgreSQL natif temporaire protégé par nonce. Capital et acquisition sont maintenant raccordés aux opérations commerciales, sans ajout rétroactif dans un journal définitif.

Le parcours comprend : capital 200 000 ; acquisition informatique 24 000 HT et paiement 28 800 ; acomptes et achats de marchandises ; devis, commande, livraison et facturation ; paiements partiels ; lettrage fournisseur ; chèque client, remise et encaissement ; achat de service 12 000 HT et règlement 14 400 ; avoir de retour et imputation du crédit ; seconde vente ; effet fournisseur 14 400 puis paiement ; effet client 10 000, remise et encaissement avec 10 de frais ; acompte client 24 000, facture de service 144 000 TTC, imputation et solde 120 000. Les dates comptables et d'opération sont celles du cahier.

Résultat du scénario au 30/06/2025 :31 écritures définitives,76 lignes, débit=crédit 864300.00 MAD. Tous les comptes et soldes sont rapprochés d'un calcul indépendant à partir du jeu de données source. Le stock reste 60 unités au CMUP 110 ; les services ne génèrent pas de mouvement de stock. Les factures de service, l'effet fournisseur et le reliquat client sont soldés après les opérations prévues.

Les quatre écritures de TVA de janvier, février, mars et juin sont saisies par le formulaire du Journal conformément aux fiches FIS015/016/017/018. Ce contrôle ne remplace pas la recette de la déclaration TVA ni sa qualification réglementaire. Aucun calcul métier attendu n'a été injecté par API pour simuler une comptabilisation automatique.

Tests finaux : deux nouveaux parcours réussis et quatre anciens parcours connexes réussis, sans ignoré. Les échecs initiaux du script restent dans les preuves. Les helpers de tests existants acceptent maintenant un préfixe comptable et des étapes intercalées ; leurs scénarios historiques restent vérifiés. Aucun code produit ni migration modifié dans ce lot ; dernier build frontend réussi au lot 785.

Le suivi individuel passe à 50 fiches réussies,1 partielle,211 nonqualifiées individuellement et10 bloquées dans la source. Les réponses de recette humaine ne sont pas modifiées. La cession 787 reste partielle et sa divergence d'oracle est documentée. Aucun PostgreSQL utilisateur n'a été utilisé.

À poursuivre : opérations de juillet à décembre, impayé et rejet de chèque, inventaire, dotation, ajustements de clôture puis contrôle des résultats annuels. Le scénario actuel ne constitue pas encore l'exercice complet, ni une recette utilisateur ou une validation de mise en production. RH/paie et point 6 restent différés ;incident de rechargement Lettrage 769 toujours ouvert.
