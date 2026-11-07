# HisabPro — identité littérale et logo dans les PDF

La fiche SEC007 est exécutée sur une société fictive, dans Edge sur ordinateur et mobile, avec API réelle et PostgreSQL natif éphémère. La raison sociale est exactement Atlas <SARL> & associés. Une image PNG fictive est configurée comme logo. Une facture client de1200MAD TTC, validée et comptabilisée, porte la référence Réf <PIECE> & 857.

La page Paramètres restitue la raison sociale littérale. Depuis le détail de facture, le bouton Télécharger PDF produit un véritable fichier. Le PDF est ouvert par pypdf :le texte contient les chevrons,le symbole& et les accents,ainsi que la référence exacte. Le document comporte une image incorporée. Un second export direct par API est vérifié de la même manière. Le test ne compare pas les octets de deux générations indépendantes,dont les métadonnées peuvent différer ;chaque empreinte est conservée séparément.

Les écritures comptables et le profil de société,logo compris,restent identiques avant et après les exports. Les13tests connexes vérifient notamment les formats de logo acceptés,les images invalides,les tailles et le titre/pied de page de liasse avec identité littérale. Ils sont distincts des deux parcours connectés PostgreSQL et ne sont pas présentés comme13tests de base de données.

Résultats finaux :deux parcours connectés et13tests connexes réussis. Aucun correctif produit,migration ou nouvelle règle fiscale nécessaire ;aucun nouveau build revendiqué. Ce contrôle porte sur la facture et les exports couverts par les tests connexes,il n'affirme pas une qualification exhaustive de toutes les pièces ou une conformité officielle.

Le suivi atteint175fiches automatiquement réussies,5partielles,82nonqualifiées individuellement et10bloquées à la source. Les70statuts globaux restent inchangés. Prochaine étape :erreur réseau et rétablissement puis changement de société avec formulaire non enregistré. Les réserves de méthode,justificatifs,recette utilisateur et production restent visibles. Aucun PostgreSQL utilisateur ni donnée réelle utilisé ;RH/paie etEDI différés.
