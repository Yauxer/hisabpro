# HisabPro — crédits d'avoir et retours excessifs

Les fiches NEG014, NEG015 et NEG016 sont exécutées sur ordinateur et mobile dans Edge avec API réelle et PostgreSQL natif éphémère. La copie utilise les valeurs exactes des scénarios :100unités vendues à250MAD HT, TVA20%, facture30000MAD soldée, avoir de10unités donnant3000MAD de crédit. Le stock initial200unités est enregistré au01/01/2025 avant la vente ; aucun mouvement réel ou historique n'est redaté.

NEG016 : le formulaire de retour refuse101unités pour100facturées, puis l'API refuse également409 avec le motif quantité supérieure à la quantité facturée. Journal, stock, mouvements, factures, règlements et avoirs restent identiques. Le même formulaire accepte ensuite10unités. La comptabilisation porte le stock de100 à110 et laisse3000MAD de crédit libre sur la facture déjà payée.

NEG014 : le formulaire d'imputation ne propose pas la facture du client Impayé. Une requête directe vers cette facture reçoit422 avec le motif même tiers, alors que le crédit existe et que la facture cible a un solde ouvert. Aucun crédit ni paiement n'est déplacé et les états restent identiques.

NEG015 : la facture cible du bon client dispose d'un solde12000MAD, supérieur à la demande3001MAD ; c'est bien le plafond du crédit3000 qui doit bloquer. Le formulaire refuse le dépassement et l'API retourne409 Crédit disponible insuffisant. Les mêmes états restent identiques. L'imputation exacte3000 est ensuite acceptée, consomme le crédit et laisse9000MAD sur la cible, sans nouveau mouvement de stock.

Les préconditions sont préparées par API ; les formulaires et refus sont réellement parcourus dans le navigateur. Aucun résultat attendu n'est injecté dans le produit. Les39tests connexes des acomptes/avoirs ont été exécutés au lot843 pendant cette reprise et restent applicables à la candidate inchangée ; ils ne sont ni réexécutés ni additionnés à nouveau ici. Aucun nouveau build n'est nécessaire, le produit est inchangé.

Le suivi atteint163fiches automatiquement réussies,5partielles,94nonqualifiées individuellement et10bloquées à la source. Les70statuts fonctionnels globaux restent inchangés. Les documents841 restent des preuves historiques, les réserves de méthode et justificatifs ne sont pas effacées et aucune production ou recette humaine n'est validée.

Prochaine étape indépendante : contrôles négatifs des effets, frais et dates bancaires, puis rapprochement et immobilisations. RH/paie et dépôt fiscal restent différés. Aucun PostgreSQL utilisateur ni donnée réelle touché.
