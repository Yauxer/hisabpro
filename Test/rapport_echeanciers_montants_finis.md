# Échéanciers : refus des montants non finis

Le contrôle métier arrondissait `float(montant)` puis comparait le total au TTC. NaN traverse les comparaisons : la requête PUT réelle finissait en erreur500 après tentative de remplacement de l'échéancier fictif. Le schéma acceptait également Infinity et les booléens.

Correction minimale : `montant_echeance_fini` partagé entre le schéma d'entrée et la normalisation métier. Il refuse les booléens, conversions invalides et montants non finis ou non positifs. Le TTC de référence est également contrôlé avant comparaison. Les règles existantes d'arrondi, de tri, de total contractuel et de gel après imputation restent appliquées.

Tests réellement exécutés :

- Avant correction : 11 échecs,13 réussis,4désélectionnés en0,90s pour schémas/service ; PUT NaN réel :1échec en14,05s, réponse500.
- Après correction : **28 réussis en18,14s**, dont4PUT réels sur PostgreSQL éphémère. Chaque refus422 conserve exactement la facture, ses lignes et son échéancier existant ; GET reste200 avec total1200.
- Connexes fact8/recouvrement/ETIC échéances etEdge connecté : **44 réussis en31,60s**.
- Compilation des deux fichiers Python produit et du test : code de sortie0.

La ventilation399,75/800,25 sur TTC1200 reste valide. Aucune donnée réelle ni connexion au PostgreSQL utilisateur. Les échéanciers historiques éventuellement invalides ne sont pas réparés automatiquement.
