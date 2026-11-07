# Bancs frais et reprise bancaire —414

Les trois échecs concernés de la globale411 sont réellement reproduits :3échecs/12réussites sur15cas,1,85s. Aucun code produit modifié.

L'ancien contrôle de frais exigeait un libellé source disparu après404. Il vérifie désormais le vrai modèle Pydantic TransitionIn :rejet de négatif/NaN/Inf/−Inf/booléen/fraction de centime et acceptation de null/zéro/0,01/10,01/chaîne exacte. Le contrôle de plafond et la borne UI sont conservés ;les tests API connexes vérifient la mutation réelle et sa conservation en cas de refus.

Le banc AST083 compilait uniquement la reprise de solde,sans sa nouvelle fonction de qualification des montants. La dépendance réelle et math sont désormais chargés par ce banc. Les soldes attendus500/480,la priorité du relevé,l'isolation société/compte et la distinction annuel/adjacent restent identiques. SQLite est uniquement le banc unitaire de calcul ;les comportements PostgreSQL ont été vérifiés distinctement sur bases nonce.

Après correction :39tests réussis,zéroéchec/erreur/ignoré,68,33s,code0 :deux fichiers corrigés,frais API et relevés historiques API/Edge. Compilation Python des fichiers modifiés code0. Aucun PostgreSQL réel ni donnée comptable réelle. La globale411 demeure conservée en échec ;une nouvelle globale finale reste nécessaire. Recette humaine etpoint6 en attente.
