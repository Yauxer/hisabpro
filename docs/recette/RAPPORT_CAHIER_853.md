# HisabPro — dotation unique et valeur résiduelle

Les fiches NEG027 et NEG028 sont exécutées dans Edge sur ordinateur et mobile avec API réelle et PostgreSQL natif éphémère. Le sous-parcours reprend les formulaires du cahier :capital200000MAD,acquisition informatique24000MAD HT,TVA4800MAD,paiement28800MAD et dotation2025de4800MAD. Les écritures et leurs comptes sont comparés au jeu source ;aucune donnée réelle n'est utilisée.

NEG027 :la dotation est produite depuis le plan puis validée au Journal. Le bilan2025 détaille24000MAD brut,4800MAD amortis et19200MAD net. Une seconde génération unitaire reçoit409. La génération par lot depuis Immobilisations et celle de Clôture ne produisent aucune nouvelle dotation. Une seule pièce définitive demeure,débit61935/crédit28355 pour4800MAD. Le registre,les tiers,les exercices et les quatre écritures du sous-parcours restent identiques. Les huit tests connexes PostgreSQL vérifient également les demandes simultanées et les verrous de génération.

NEG028 :le formulaire Nouvelle immobilisation est rempli avec un coût HT1000MAD et une valeur résiduelle1001MAD. La TVA de la copie est entièrement récupérable,le coût d'entrée est donc1000MAD. La requête réelle répond400 et l'interface affiche le motif de dépassement. Le même corps envoyé directement à l'API est refusé400. Aucun nouvel actif,tiers,exercice ou mouvement comptable n'est ajouté. Le registre et les écritures définitives existantes restent conservés.

Contrôle positif :le même formulaire accepte ensuite une immobilisation1000MAD avec valeur résiduelle0. Le registre contient bien cette seconde copie et toutes les écritures définitives antérieures restent intactes. Ce contrôle distingue le refus de la relation numérique incorrecte d'un formulaire qui serait entièrement bloqué.

Résultats finaux :deux parcours Edge réussis et huit tests de concurrence PostgreSQL réussis. Les résultats exacts et durées sont joints aux JUnit et PREUVE_CAHIER853.json. Aucun correctif produit,migration ou nouveau calcul comptable/fiscal n'a été nécessaire ;aucun nouveau build frontend n'est revendiqué. Les tests Python ajoutés sont compilés et les462empreintes de la candidate849 restent inchangées.

Le suivi atteint172fiches automatiquement réussies,5partielles,85nonqualifiées individuellement et10bloquées à la source. Les70statuts fonctionnels globaux restent inchangés. Les variantes de cession/prorata,pièces historiques et réserves réglementaires ne sont pas effacées. Les résultats ne valent ni recette humaine ni production validée.

Prochaine étape indépendante :vérifier les derniers cas UX de comptabilité/facturation et mettre en évidence les réserves qui nécessitent l'environnement cible ou une décision humaine. RH/paie et formats de dépôt restent différés. Aucun PostgreSQL utilisateur ni donnée comptable réelle touché.
