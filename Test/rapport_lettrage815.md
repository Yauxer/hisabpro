# HisabPro — lettrage annuel et contrôles d’auxiliaires

Les 50 opérations comptables du cahier sont transcrites et validées par API dans une société fictive neuve. La recette du module Lettrage est ensuite réalisée dans Edge, sur ordinateur et mobile. Ce lot ne rejoue pas les formulaires commerciaux, déjà couverts par les parcours annuels précédents ; il vérifie les groupes comptables exacts du jeu et leurs auxiliaires.

Les comptes 3421 de C-MARCH et C-SERVICE, puis 4411 de F-MARCH et F-SERVICE, sont sélectionnés par tiers. Chaque groupe est contrôlé avec débit égal au crédit avant confirmation. Les codes AAA, AAB, AAC et AAD sont attribués, uniques dans la société et composés d’au moins trois lettres. La page est rechargée après chaque groupe ; les codes et dates restent présents. Le FEC de 118 lignes est réellement exporté et les codes des quatre groupes y correspondent.

C-IMPAYE conserve un solde ouvert de 14 400 MAD ; F-CONTROLE conserve 480 MAD, avec les références 02 et 002 distinctes. Ces lignes ne sont pas lettrées. Les écritures définitives et les états comptables restent strictement identiques après le lettrage ; seuls les enregistrements de lettrage prévus par le produit sont ajoutés.

Les cas négatifs utilisent des sociétés de contrôle distinctes, sans modifier les soldes du scénario principal. Un débit client Marchandises de 100 et un crédit client Services de 100 ne peuvent pas être sélectionnés ensemble ; l’API refuse aussi le mélange (400). Un débit de 100 et un crédit de 99 du même tiers affichent un écart de 1, avec bouton de confirmation désactivé ; l’API refuse le déséquilibre (400). Aucun lettrage ni mutation financière n’est créé après ces tentatives.

Quatre parcours finaux et neuf tests connexes réussissent. Les premiers essais échoués sont conservés : le test avait utilisé les repères internes REF-02/REF-002 au lieu des références justificatives 02/002 et attendait les lignes dans la réponse de validation, qui ne les contient pas. La préparation de nouvelles sociétés de test est corrigée ; aucune ancienne écriture n’est réparée ou réécrite. Aucun code produit ni migration n’est modifié.

Le suivi passe à 130 fiches réussies, 4 partielles, 128 non qualifiées individuellement et 10 bloquées par les sources. L’ancien écran vide de Lettrage769 n’a pas été reproduit dans ces parcours ; cela ne prouve pas sa cause ni sa résolution générale. Les 70 statuts fonctionnels restent inchangés. Aucun PostgreSQL utilisateur n’est utilisé. B6/B13 attendent des justificatifs ou une méthode, CM/cession restent partielles, RH/paie et point 6 restent différés. La recette humaine et la conformité réglementaire ne sont pas validées automatiquement.

Pour vérifier : Lettrage → exercice 2025 → Clients (3421) ou Fournisseurs (4411), puis choisir le tiers. Sélectionner uniquement les lignes justifiées d’un groupe équilibré, vérifier le solde de sélection et confirmer. Recharger et contrôler le code. Les lignes des tiers impayés doivent rester ouvertes. Ne pas sélectionner des tiers différents pour équilibrer artificiellement une somme.

Prochaine étape : balance générale et grand livre avant constatation de l’IS, avec comparaison au fichier balance_avant_is_2025.csv et au parcours commercial connecté, puis reprise des variantes restantes.
