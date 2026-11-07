# HisabPro — acquisition, paiement et amortissement du cahier

Les cas HP-IMM-001/002/003 ont été exécutés dans Edge à1440et390pixels, sur PostgreSQL temporaire natif protégé par nonce. Aucune base réelle utilisée. Les montants et comptes attendus proviennent du jeu de données existant, sans ajout de règle fiscale.

Dans chaque nouvelle société fictive : capital200000 saisi au Journal, puis matériel informatique IMMO-01 acquis et mis en service le01/01/2025 pour24000HT,TVA4800, payé28800 le même jour sur5141. AcquisitionAC2355/34551/4481 etpaiementBQ4481/5141 générés par le formulaire ; fournisseur etauxiliaire4481,dates de pièce etréférences conservés. Chaque écriture est ensuite validée par le Journal.

Plan linéaire5ans : dotation2025 de4800, générée par le bouton de la ligne2025 puis validée. Bilan : brut24000, amortissements4800, net19200 avec détail235. Dans ce sous-parcours uniquement : bilan195200, résultat-4800 ;4écritures définitives/9lignes, débit=crédit262400, dette4481soldée. Aucune assimilation aux résultats annuels complets du cahier.

La seconde génération individuelle est refusée409 ; la génération annuelle ignore correctement la dotation déjà comptabilisée, sans nouvelle écriture. Les écritures définitives initiales sont conservées à l'identique après dotation et tentatives de doublon. Le registre reste correct après rechargement. Il affiche les valeurs théoriques à la date du jour, distinctes du plan etdu bilan2025 ; cette date est maintenant indiquée.

Tests ciblés finaux :2réussis. Tests connexes acquisition/amortissement etcession différée :2réussis. Aucun ignoré. Les8échecs initiaux conservés correspondent au script de test :libellé ambigu Immobilisation, comparaison chaîne/Decimal lecture du plan avant chargement etconfusion entre registre courant etbilan2025. Les assertions ont été corrigées etla date des valeurs théoriques rendue visible. Build Vite réussi. La date des valeurs théoriques est désormais visible au registre ; aucun calcul ni migration modifié.

Le suivi comporte35fiches qualifiées,227nonqualifiées individuellement et10bloquées dans la source. Les réponses humaines restent inchangées. À poursuivre :variante exacte de cession2026, puis raccord chronologique des autres opérations annuelles dans une société neuve. Incident historique de rechargement Lettrage769 encore ouvert. RH/paie etpoint6 restent différés ;recette humaine,conformité réglementaire etproduction nonvalidées.
