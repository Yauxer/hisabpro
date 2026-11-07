# Conserver une copie figée d’une facture — lot923

Dans **Factures**, ouvrir une facture de vente validée. En bas du détail, le panneau **Copie PDF conservée** permet de conserver les octets du PDF produit par HisabPro. Le logo incorporé au PDF est conservé avec le document. Une facture non soldée peut aussi être conservée : cette opération ne vaut pas preuve de paiement.

1. Déplier **Conserver une copie figée**.
2. Renseigner le motif et confirmer la conservation de ce PDF.
3. Cliquer **Conserver ce PDF**. La date, l’identifiant de l’auteur, le motif, la taille et l’empreinte SHA-256 apparaissent immédiatement.
4. Utiliser **Télécharger la copie conservée**. Après rechargement de la page, le même bouton restitue exactement les mêmes octets, sans recalculer le PDF.

Une seule copie est conservée par société et facture. Un double clic ou une nouvelle requête restitue la copie existante et son motif initial. Aucun bouton ne permet de la remplacer ou de la supprimer. Les règlements, avoirs et consultations restent disponibles selon les droits habituels. La conservation ne crée ni écriture comptable ni nouveau statut commercial « archivée ».

Les administrateurs et comptables peuvent constituer la copie ; les utilisateurs en consultation peuvent lire ses informations et la télécharger. L’isolation par société et la révocation des accès s’appliquent aussi à ce document.

## Installation et sauvegarde

Appliquer **125_factures_copies_conservees.sql** sur une copie isolée de l’installation existante, avec contrôle d’erreur, avant la recette. Cette migration ajoute une table et des garde-fous ; elle ne réécrit aucune facture, écriture ou migration ancienne. Elle peut être rejouée. Aucun modèle ORM ne tente de créer cette table avant la migration.

Sans125, le détail signale que la conservation n’est pas installée, et le téléchargement habituel du PDF continue de fonctionner. Aucun accès au PostgreSQL habituel n’a été effectué pendant le développement.

Les PDF sont stockés en base, limités à10Mo chacun, et inclus dans la sauvegarde PostgreSQL. Prévoir l’espace et la politique de sauvegarde/conservation de l’entreprise. La restauration du nouveau document est testée séparément sur une seconde cible éphémère, avec contrôle des octets, empreintes, métadonnées et droits.

## Périmètre exact

- Factures de **vente validées** uniquement ; brouillons et proformas refusés.
- Les factures d’achat ne sont pas couvertes : leur original est le document du fournisseur, et non le PDF interne produit par HisabPro.
- La date conservée est celle de cette opération ; elle n’est pas présentée comme la date d’émission historique du fichier ni comme un horodatage tiers.
- Empreinte et garde-fous internes ne constituent pas une signature électronique, une certification d’archivage légal ou une garantie contre un administrateur PostgreSQL capable de désactiver les protections.
- La copie de facture est distincte de l’archive fiscale annuelle et du livre d’inventaire.

[RecettePDF](RECETTE_CONSERVATION_FACTURES_923.pdf) · [Classeur de suivi](SUIVI_CONSERVATION_FACTURES_923.xlsx) · [Données exactes](JEU_CONSERVATION_FACTURES_923.json).

Cette livraison ajoute un parcours à la fiche historique **HP-FAC-013** ; elle ne remplit pas les résultats humains des anciens cahiers. La recette utilisateur et les vérifications du futur environnement restent à effectuer.

## Navigation après validation dans le Journal

Le lot corrige aussi une anomalie reproduite pendant la non-régression : après **Valider les brouillons**, le message de succès pouvait apparaître dans une alerte JavaScript après le départ vers un autre écran et bloquer la navigation. Le résultat s’affiche maintenant dans le Journal, avec un bouton pour le fermer. La confirmation préalable à la validation reste présente, et le bouton est indisponible pendant le traitement. Les erreurs ou refus sont signalés dans la page ; aucune écriture refusée n’est rendue définitive par ce changement d’interface.

Le PDF et le classeur joints comprennent deux cas supplémentaires **JRN923-01/02** pour vérifier le message, les montants et la navigation immédiate. Cette correction vise la cause reproduite ; elle ne démontre pas que tous les anciens ralentissements ont la même origine.
