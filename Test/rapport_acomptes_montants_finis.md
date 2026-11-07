# Acomptes et imputations : montants finis avant commit

Les schémas locaux utilisaient des floats sans contrôle avant coercition. Sur PostgreSQL éphémère, une création d'acompte NaN/Infinity commettait une ligne puis échouait500 à la sérialisation ; une imputation NaN commettait également une ligne. Un booléen était converti en1MAD et accepté.

Correction minimale : validateurs `mode=before` sur montant/taux_tva de `AcompteCreate` etmontant de `ImputerIn`, réutilisant `_nombre_fini` déjà partagé par les lignes commerciales. `None` reste disponible pour l'imputation automatique. Les règles existantes de taux, qualification TVA, montant positif etdisponibilité sont conservées. Aucune requalification fiscale ni réparation d'historique.

Tests réellement exécutés :

- Reproduction fiable après application de041 au banc isolé :9échecs en18,63s, dontles erreurs500 après persistance etles booléens acceptés. Les erreurs antérieures liées au helper HTTPX età la migration manquante du banc ne sont pas des preuves de bugs produit.
- Principal : **49tests unitaires etconnexes réussis en0,81s**, dont30invalides etla compatibilité `None`/valeurs finies.
- Agent : **9API PostgreSQL réelles réussies en18,34s**, unE2E UI désélectionné. Chaque cas renvoie422 etconserve les snapshots acomptes/imputations/écritures.
- Compilation produit ettest : code0.

Les requêtes API se trouvent dans `Test/test_e2e_acompte_imputation_isole.py`, livré avec le lot connecté suivant. Aucun cluster réel ni donnée comptable réelle ; les clusters fictifs de reproduction sont nettoyés. L'anomalie indépendante de date vide du formulaire est traitée dans ce lot UI suivant.
