# Listes du cycle commercial

Dans **Facturation → Cycle commercial**, choisir Vente ou Achat puis l’onglet.
Les factures visibles et leur compteur correspondent au cycle choisi. La
lecture parcourt toutes les pages de factures, y compris au-delà de100pièces.
Cela ne change ni les factures, ni leurs montants, ni leur statut.

Devis, Bons de commande, Bons de livraison, Factures et Réception client
disposent de **Actualiser la liste**. Une lecture impossible affiche une
alerte et **Réessayer** ; aucun zéro ou faux message d’absence ne remplace
cette panne. Après rétablissement du service, Réessayer recharge les données
sans F5. Une lecture200 réellement vide conserve son message d’absence.

Pendant un changement d’exercice ou de cycle, les lignes et compteurs
précédents ne sont pas présentés comme ceux du nouveau contexte. Une réponse
retardée de l’ancien contexte est écartée. Le jeton est également contrôlé.
Le renouvellement du jeton et le sélecteur complet de société conservent leurs
propres validations ; ces tests ne constituent pas une recette exhaustive
de toutes les combinaisons d’authentification.

Réception client dépend aussi des factures pour afficher la pièce liée.
Si cette lecture échoue, l’écran l’indique au lieu de supposer qu’aucune
facture n’existe. Les factures brouillon conservent leur règle actuelle de
numérotation : aucun numéro définitif n’est créé par la consultation.

Les boutons et la recherche se replient sur petit écran. Les tableaux
comptables conservent leur défilement horizontal lorsque nécessaire.
Les permissions serveur et la génération des écritures restent inchangées.

Les listes de Règlements et de Réceptions fournisseurs conservent leurs
contrôles distincts des lots663/667. Les autres écrans et les réponses tardives
des opérations de mutation ne sont pas prévalidés par ce contrôle de lecture.
