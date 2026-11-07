# Reprise : déclarations B4 après les soldes conservés

Le complément707 conserve les soldes251 et contrôle séparément le brut entier
24/25. Ne pas réappliquer B11/B1 ou ce calcul à partir d’une note historique.
Lire l’état du journal et vérifier la livraison avant toute étape suivante.

La suite prévue est une déclaration documentaire des émetteurs par période et
compte251 réellement présent dans la balance conservée. Une ligne par émetteur
peut porter nom, identifiant facultatif, valeur comptable, capital de l’émetteur,
quote-part, produits reçus et référence de source. Les données absentes restent
inconnues ; aucune identité ou quote-part n’est inférée du compte ou du ratio
valeur comptable/capital. Plusieurs émetteurs peuvent partager un compte251.

Réutiliser la sauvegarde documentaire immuable et le formulaire ETIC existants,
avec catalogue propre et clairement interne pour N/N-1. Empreinte parent, UUID,
société, rôle et rejeu avant contrôle doivent rester protégés. Les champs
facultatifs ne doivent pas devenir obligatoires sans justification. Une ligne
déclarée documentée requiert toutefois un émetteur identifiable et sa source.

Le contrôle doit comparer, par compte et période, la somme des valeurs saisies
au solde251 certain, sans corriger un écart. Une valeur manquante ou une absence
de ligne ne devient pas0. Ne pas sommer les pourcentages d’émetteurs différents.
Ne pas calculer un produit reçu depuis un compte de produits du Journal courant.
Les valeurs et contrôles seront figés dans une nouvelle version, en conservant
le détail brut707 et les autres compléments. Le formulaire doit distinguer les
contrôles conservés du brouillon en cours.

Sans source N-1, garder cette période indisponible et refuser toute déclaration
qui inventerait son rattachement. Les notes B4 contradictoires ou une déclaration
néant malgré un solde251 non nul doivent rester visibles, sans correction
automatique. Valeur comptable et produits nets peuvent être signés si justifiés ;
capital non négatif, pourcentage de0 à100 avec précision explicite.

Prévoir tests Decimal/NaN/infinis, inconnus et écarts de centimes, compte hors
source, absence N-1, multi-société/lecture, rejeu/concurrence, brouillon et contexte
navigateur, exports/logo/manifeste et restauration froide. Les noms du catalogue
interne ne constituent pas un modèle DGI officiellement validé.

Les mouvements B2/B2bis/B3/B5 et les sources fiscales restent une étape séparée ;
ne pas les déduire de la variation entre deux soldes. RH/paie et point6 différés.
