# HisabPro — lecture seule et séparation des sociétés

Les quatre fiches NEG042 à NEG045 sont exécutées dans Edge, sur ordinateur et mobile, avec API réelle et PostgreSQL natif éphémère. Aucun changement du produit n'est nécessaire pour ces contrôles.

Une société A et une société B disposent chacune d'une écriture définitive fictive de100MAD et d'une facture. La facture B est validée avant export : son propriétaire reçoit200 avec un PDF réel. Il ajoute ACH-01.pdf à son écriture et récupère le fichier intégral. La société A reçoit403 ou404 lors de l'export PDF, d'une tentative de modification de facture B et du téléchargement de la pièce B. Une nouvelle lecture par B confirme le document et les octets du justificatif inchangés.

Un utilisateur lecteur se connecte réellement et consulte les factures, le Journal et l'ETIC. Les boutons de création sont désactivés et l'enregistrement ETIC n'est pas proposé. Des requêtes directes de création de facture et d'écriture ainsi que de modification ETIC sont refusées403. La lecture ETIC reste autorisée200. Les deux témoins comptables, les lignes et les factures restent identiques.

La déconnexion depuis le menu efface le jeton local et ramène au formulaire de connexion, y compris après tentative d'ouverture directe de Factures. Les requêtes sans authentification reçoivent401. Ceci vérifie le cas déconnecté ; ni l'expiration d'un JWT signé ni une révocation serveur du jeton capturé au logout ne sont affirmées.

L'administrateur unique ne peut ni désactiver ni supprimer son propre accès ; sa rétrogradation en lecteur est refusée également400. Il reste administrateur et peut toujours se connecter. Les secrets restent en mémoire et ne sont pas enregistrés dans les preuves.

Les premiers échecs concernent uniquement la construction du témoin : un brouillon n'est pas exportable409 et la réponse partielle de validation ne se compare pas à une lecture complète. Les boutons de création du lecteur sont présents mais désactivés, comportement vérifié après lecture du code. Les preuves d'échec sont conservées ; les assertions finales comparent les lectures canoniques avant/après. Le suivi atteint151fiches réussies,5partielles,106nonqualifiées individuellement et10bloquées à la source. La matrice fonctionnelle70 lignes reste inchangée.

Prochaine étape : verrouillage des écritures définitives et périodes, double comptabilisation, puis cycle annuel complet jusqu'aux à-nouveaux et exports. Ces validations automatiques ne constituent ni une recette humaine ni une autorisation de mise en production.
