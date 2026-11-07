# Attente de connexion E2E —416

Le rejeu isolé des deux cas liste vide échoués dans411 réussit sans modification :2passes24,51s. La ressource exacte ou la cause du délai original n'est donc pas identifiée. Ce résultat n'efface pas l'échec411.

Un mécanisme correspondant a ensuite été reproduit sans mock de l'API :une image témoin décorative reste volontairement en attente,mais le vrai login est envoyé et le dashboard est atteint. L'ancien helper attend implicitement l'événement load et les deux tests échouent26,81s. Le helper attend maintenant DOMContentLoaded,la présence du main et la navigation authentifiée,avec le même timeout. Les deux tests contrôlés passent avec statut réel200,token navigateur utilisé surAPI réelle etdocument encore interactive tant que l'image est retenue. Seule cette image artificielle est retenue ;authentification,API etPGnonce restent réels.

Les huit lectures factures inconnues/vides et les deux parcours administration sont également rejoués. Cette correction du banc ne constitue pas une correction applicative ni la preuve de la cause exacte de l'ancien délai. Compilation Python code0.


connexion416_apres :12réussis,85.066s,zéroéchec/erreur/ignoré

Aucun PostgreSQL réel ni donnée comptable réelle. Globale411 en échec conservée ;nouvelle globale finale à exécuter. Recette utilisateur etpoint6 en attente.
