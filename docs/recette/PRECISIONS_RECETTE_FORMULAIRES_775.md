# Précisions pour exécuter le cahier — formulaires775

Ces précisions accompagnent le cahier existant sans modifier les réponses de recette humaine.

- **Tiers** :C-MARCH,F-MARCH,etc. sont des repères du cahier. L’écran n’expose pas de champ code ou notes pour les enregistrer :consigner leur correspondance avec le nom et l’auxiliaire généré dans les preuves. Ne pas imposer ces repères comme codes auxiliaires HisabPro. Les comptes3421/4411/4481 se règlent dans « Paramétrage comptable ».
- **Articles** :prix,TVA,nature stockable et comptes de vente/achat se saisissent dans le formulaire. Les comptes de stock3111/6114 ne sont pas des champs de l’article ;leur vérification reste à effectuer dans le parcours de famille/inventaire. HP-ADM-013 reste partiel dans le suivi automatique.
- **Commande issue du devis** :la note REC-BC01 se saisit maintenant dans « Notes de commande ». Cette option existait côté API ;le champ est ajouté par le lot775.
- **Livraison depuis le BC** :le champ « Date de livraison » existait déjà. Saisir explicitement20/01/2025 pour le scénario principal.
- **Facture depuis le BL** :le nouveau champ « Date de la facture » propose la date du jour ;pour le cahier,saisir20/01/2025 avant création. Il est indépendant de la date du BL. Ensuite,dans Factures → Modifier le brouillon,saisir l’échéance26/01/2025 avant validation. La date de facture ne doit pas être assimilée à son échéance.
- **Exercices** :ne pas recréer2025/2026 s’ils existent déjà. La branche de création conditionnelle n’a pas été rejouée dans le cas HP-ADM-003 du suivi automatique.
- **Mentions des tiers** :les noms du jeu fictif ne constituent pas une identité fiscale complète. Les alertes d’adresse/ICE manquants restent visibles ;ne pas inventer de justificatifs pour les masquer.
- **Millésime** :le scénario reste2025 avec ouverture2026 ;ne pas remplacer automatiquement les années par l’année courante.

Le suivi automatique775 qualifie20fiches complètes et2partielles. Les240fiches non qualifiées individuellement et10bloquées dansla source ne sont pas prévalidées. Les tests techniques connexes sont présentés séparément de la recette humaine.
