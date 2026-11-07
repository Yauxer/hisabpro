# HisabPro — fiscalité documentée, clôture et ouverture du cahier

Le parcours annuel de 50 opérations a été prolongé jusqu'à la clôture 2025 et l'ouverture 2026, dans Edge sur ordinateur et mobile (1440/390) et PostgreSQL natif temporaire protégé par nonce. Aucune base utilisateur et aucune écriture réelle utilisées.

L'IS comptabilisé était 23 420,25 alors que le calcul fiscal, avant confirmation des provisions du scénario, donnait 22 807,75. La clôture était correctement bloquée. Les deux réintégrations explicitement prévues dans les notes fictives ont été saisies dans Résultat fiscal / IS : 1 500 sur 61955 et 2 000 sur 61964, catégorie Provisions. L'amende 500 était déjà automatique et n'a pas été doublée. Les réintégrations atteignent 4 000, le bénéfice fiscal 133 830 et l'IS 23 420,25. Ces hypothèses ne sont pas généralisées à toutes les provisions réelles.

Le crédit PPRF 200 a été saisi avec date 30/11/2025, référence INT-PPRF et déjà imputé aux acomptes 0. Aucun produit ni règlement n'a été recréé dans le Journal. Le solde est 23 220,25. Les acomptes 2025 sont Non applicable/premier exercice ;la CSS sans référence 2024 reste explicitement Référence manquante.

CM :base 170 500, calcul proportionnel 426,25, minimum 3 000 observé avant paramétrage. L'exonération du seul scénario fictif a été cochée avec la justification prévue par son cahier. La CM du scénario devient 0. La fiche CM reste partielle :la variation nonexonérée a été observée avant paramétrage, pas sur une copie dédiée ;aucune qualification réglementaire réelle n'est validée.

Après ces saisies, stock, immobilisation, équilibre et IS sont cohérents. Le contrôle FEC ne comporte aucun blocage, avec un avertissement conservé. Le bouton Clôturer est utilisé :résultat 106 409,75, exercice 2025 et ses périodes verrouillés. Les à-nouveaux2026 sont validés et équilibrés à 343 810 MAD de chaque côté, avec 1191 créditeur 106 409,75. Tous les comptes reportés sont comparés au calcul indépendant du jeu de données.

Les deux contrepassations de CCA/FNP sont retrouvées dans l'écran Contrepassations d'ouverture 2026 puis validées au Journal. Les 50 écritures définitives d'origine restent identiques. Une nouvelle écriture 2025 est refusée 423 ;une seconde clôture est refusée. La liquidation 2025 est ensuite confirmée, relue après rechargement et figée : IS 23 420,25, crédit 200, solde 23 220,25. Les tentatives de seconde confirmation et d'ajout de crédit après gel sont refusées 409.

Deux nouveaux parcours et trois tests connexes de fiscalité/clôture ont réussi, sans ignoré. Aucun code produit ni migration modifié dans ce lot. Les preuves contiennent les résultats, contrôles réels et captures. La recette humaine, la conformité réglementaire et la mise en production ne sont pas validées par ces tests.

Le suivi compte 72 fiches réussies,2 partielles,188 nonqualifiées individuellement et10 bloquées dans la source. Les anciens cahiers et réponses humaines sont conservés. Cession 787 partielle, incident Lettrage 769 ouvert, RH/paie et point 6 différés. Prochaine étape :contrôler les 12 mois de TVA et leurs impressions, les paiements 2026 puis les acomptes et CSS issus de la liquidation 2025 confirmée.
