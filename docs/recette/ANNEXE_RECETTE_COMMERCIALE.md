# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

## Annexe commerciale — alertes et documents client

Annexe commerciale : alertes de stock des devis et documents reçus du client. Cinq cas, quatre Non testé et un Bloqué. Aucun résultat utilisateur prévalidé. Données exclusivement fictives ; suivre les cas dans l’ordre sur un dossier de recette. Stock physique actuel indicatif, sans réservation ni promesse de disponibilité future. Cette annexe complète les cahiers annuel et GRH sans les modifier.

## Jeu de données

- **societe** : Société fictive déjà créée selon le cahier annuel ; ne pas utiliser un dossier réel.
- **exercice** : 2026-01-01 au 2026-12-31, ouvert ; sélectionner 2026 dans le bandeau.
- **date_devis** : 2026-10-08
- **client** : CLIENT COMMERCIAL RECETTE ; type Client ; délai de paiement 30 jours.
- **article_physique** : COM-STOCK-001 ; désignation Produit commercial fictif ; stockable Oui ; unité unité ; stock initial 5 ; prix achat HT 8.00 ; prix vente HT 10.00 ; TVA 20 %.
- **service** : COM-SERV-001 ; désignation Service commercial fictif ; stockable Non ; prix achat HT 0.00 ; prix vente HT 10.00 ; TVA 20 % ; stock initial 0.
- **remises** : Remise, remise2, rabais, emballage, transport et escompte : zéro ; aucune consignation.
- **lecteur** : lecteur.com.recette@example.com ; nom Lecteur commercial fictif ; rôle lecture ; mot de passe temporaire RecetteCOM2026! ; société de recette uniquement.
- **societe_b** : COM AUTRE RECETTE FICTIVE 2026, créée comme variante du cahier annuel ; exercice 2026 ouvert ; aucune pièce commerciale de la société A.
- **pdf_fictif** : BR-CLIENT-RECETTE.pdf : texte BON DE RÉCEPTION FICTIF — REC-COM-001 ; date 08/10/2026 ; produit COM-STOCK-001 : 2 unités ; service COM-SERV-001 : 1 ; SANS SIGNATURE AUTHENTIQUE. Créer ce texte dans un traitement de texte puis Exporter PDF.
- **png_fictif** : BR-CLIENT-RECETTE.png : dans Paint ou équivalent écrire REC-COM-001 — IMAGE FICTIVE, puis Enregistrer sous PNG. Ne pas utiliser une pièce réelle.

## COM-001 — Créer un devis à approvisionner avec cumul des lignes

**module** : Devis

**prerequis** : Administrateur connecté à la société fictive du cahier annuel, exercice 2026 ouvert. Créer les deux articles et le client avec les valeurs exactes du Jeu de données, uniquement s’ils sont absents. Stock du produit confirmé à 5 avant COM-001. Aucun autre document n’utilise ces codes. Références légales du dossier reprises du cahier annuel, sans inventer une identification réelle.

**donnees** : 08/10/2026 ; CLIENT COMMERCIAL RECETTE ; ligne1 COM-STOCK-001 quantité3, ligne2 même article quantité3, ligne3 COM-SERV-001 quantité1 ; PU HT10 chacune ; remises0 ; TVA20. Note REC-COM-001.

**actions** : Photographier Articles (stock5) et Journal. Ouvrir Cycle commercial → Vente → Devis → Nouveau devis. Choisir le client ; sélectionner le produit dans la première ligne, saisir Qté3. Cliquer Ajouter, sélectionner encore ce même article, Qté3. Ajouter le service, Qté1. Vérifier PU HT10/TVA20 sur chaque ligne, saisir la note. Lire le diagnostic puis Créer le devis. Noter son numéro réel dans Observations ; recharger puis consulter le devis.

**attendu** : Produit demandé6, stock physique5, manque1 : alerte indicative. Service sans alerte de rupture. Création autorisée ; HT70,00 / TVA14,00 / TTC84,00 MAD. Stock5 inchangé, aucune réservation ni nouvelle écriture.

**ecritures** : Aucune nouvelle écriture et aucune modification d’écriture existante par les actions de ce cas ; comparer le journal avant/après.

**fiscal** : Totaux documentaires au taux saisi 20 % ; aucune facture, TVA déclarée ni liquidation fiscale créée par le devis ou les pièces jointes.

**controles** : Comparer société/exercice actifs, stock et journal avant/après ; relever les numéros effectivement générés, sans imposer un préfixe.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Captures du formulaire avec les trois lignes, alerte et totaux ; liste après création/rechargement ; stock et journal avant/après.

**observations** : À renseigner pendant la recette.


## COM-002 — Modifier le devis et relire la disponibilité

**module** : Devis

**prerequis** : Administrateur connecté à la société fictive du cahier annuel, exercice 2026 ouvert. Créer les deux articles et le client avec les valeurs exactes du Jeu de données, uniquement s’ils sont absents. Stock du produit confirmé à 5 avant COM-001. Aucun autre document n’utilise ces codes. Références légales du dossier reprises du cahier annuel, sans inventer une identification réelle.

**donnees** : Même devis COM-001 ; deux lignes du produit quantité1 chacune ; service quantité1 ; tous PU HT10 et TVA20 ; note REC-COM-002.

**actions** : Dans Vente → Devis, repérer le numéro enregistré en COM-001. Cliquer son action Modifier (crayon). Changer seulement les deux quantités produit3→1 et la note. Vérifier le diagnostic puis Enregistrer. Consulter à nouveau le devis, puis recharger la page et rouvrir Modifier.

**attendu** : Produit demandé2 pour stock5, disponible ; service toujours sans alerte. HT30,00 / TVA6,00 / TTC36,00 MAD. Quantités/note persistées, données actualisées ; stock5 inchangé et aucune nouvelle écriture.

**ecritures** : Aucune nouvelle écriture et aucune modification d’écriture existante par les actions de ce cas ; comparer le journal avant/après.

**fiscal** : Totaux documentaires au taux saisi 20 % ; aucune facture, TVA déclarée ni liquidation fiscale créée par le devis ou les pièces jointes.

**controles** : Comparer société/exercice actifs, stock et journal avant/après ; relever les numéros effectivement générés, sans imposer un préfixe.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Formulaire modifié, consultation/rechargement et total36,00 ; stock5 et journal inchangés.

**observations** : À renseigner pendant la recette.


## COM-003 — Attacher des documents externes au BL préparé sans impact métier

**module** : Documents client

**prerequis** : Administrateur connecté à la société fictive du cahier annuel, exercice 2026 ouvert. Créer les deux articles et le client avec les valeurs exactes du Jeu de données, uniquement s’ils sont absents. Stock du produit confirmé à 5 avant COM-001. Aucun autre document n’utilise ces codes. Références légales du dossier reprises du cahier annuel, sans inventer une identification réelle.

**donnees** : Devis modifié COM-002 ; PDF BR-CLIENT-RECETTE.pdf et PNG BR-CLIENT-RECETTE.png préparés comme indiqué dans le Jeu de données.

**actions** : Vente → Devis : Marquer accepté, puis Créer BC. Confirmer Créer la commande avec les lignes1+1+1. Noter le numéro réel du BC. Dans Bons de commande, action Créer un bon de livraison sur le reliquat ; conserver toutes les quantités et Créer le bon de livraison. Noter son numéro. Laisser le BL en préparation : ne cliquer ni confirmer expédition/remise, ni créer facture. Photographier statutBL, stock et Journal à cet instant. Ouvrir Réception client, repérer ce BL, cliquer Documents reçus du client. Joindre un fichier : choisir le PDF, puis répéter avec le PNG. Télécharger chaque pièce, ouvrir et comparer son contenu avec l’original. Fermer et recharger puis rouvrir les documents. Comparer les captures avant/après dépôt, en utilisant comme référence l’instant suivant la création du BL.

**attendu** : PDF et PNG présents et relisibles sur le bon BL. Dépôt/relecture ne changent ni statutBL, ni stock, ni écritures. Aucune signature ou réception authentique présumée ; aucun second mouvement de stock créé.

**ecritures** : Aucune nouvelle écriture et aucune modification d’écriture existante par les actions de ce cas ; comparer le journal avant/après.

**fiscal** : Totaux documentaires au taux saisi 20 % ; aucune facture, TVA déclarée ni liquidation fiscale créée par le devis ou les pièces jointes.

**controles** : Comparer société/exercice actifs, stock et journal avant/après ; relever les numéros effectivement générés, sans imposer un préfixe.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Numéros réels devis/BC/BL ; statutBL/stock/journal avant et après dépôt ; liste des deux documents ; téléchargements ouverts.

**observations** : À renseigner pendant la recette.


## COM-004 — Consulter les documents en lecteur et isoler une autre société

**module** : Permissions

**prerequis** : Administrateur connecté à la société fictive du cahier annuel, exercice 2026 ouvert. Créer les deux articles et le client avec les valeurs exactes du Jeu de données, uniquement s’ils sont absents. Stock du produit confirmé à 5 avant COM-001. Aucun autre document n’utilise ces codes. Références légales du dossier reprises du cahier annuel, sans inventer une identification réelle.

**donnees** : Compte lecteur et sociétéB du Jeu de données ; BL et deux documents de COM-003.

**actions** : Administrateur : Paramètres → Utilisateurs, créer le lecteur avec les données exactes. Se déconnecter puis se connecter en lecteur dans A. Cycle commercial → Vente → Réception client → même BL → Documents reçus du client. Télécharger/ouvrir les deux pièces. Vérifier absence du bouton Joindre un fichier et de suppression. Revenir en administrateur, sélectionner/créer la sociétéB selon le cahier annuel. Ouvrir Réception client : le BL de A et ses pièces ne doivent pas figurer. Revenir dans A et vérifier leur présence. Ne pas modifier l’URL pour tenter un accès forcé.

**attendu** : Lecteur consulte/télécharge les pièces sans dépôt ni suppression. B n’affiche pas les documents de A. Retour A restitue les deux pièces et les états métier restent inchangés.

**ecritures** : Aucune nouvelle écriture et aucune modification d’écriture existante par les actions de ce cas ; comparer le journal avant/après.

**fiscal** : Totaux documentaires au taux saisi 20 % ; aucune facture, TVA déclarée ni liquidation fiscale créée par le devis ou les pièces jointes.

**controles** : Comparer société/exercice actifs, stock et journal avant/après ; relever les numéros effectivement générés, sans imposer un préfixe.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Captures lecteur avec liste et absence de dépôt ; fichiers téléchargés ouverts ; écran B puis retour A.

**observations** : À renseigner pendant la recette.


## COM-005 — Distinguer un stock historique inconnu d’un stock nul

**module** : Stock inconnu

**prerequis** : Opérateur requis pour préparer un stock historique NULL uniquement dans un laboratoire nonce isolé. Aucun champ UI ne permet cette préparation ; les succès des tests développeur ne prévalident pas ce cas utilisateur.

**donnees** : Article laboratoire COM-UNKNOWN-001 stockable, stock historique NULL, PU HT 10 / TVA 20 ; devis 08/10/2026 quantité 1, TTC 12,00 ; note REC-COM-005.

**actions** : Après préparation attestée par l’opérateur, rester sur sa base de test isolée. Nouveau devis avec cet article, quantité1. Lire Stock à vérifier, conserver capture puis Créer le devis. Recharger ; vérifier stock inconnu toujours visible et absence de nouvelle écriture. Sans ce laboratoire prêt, laisser Bloqué ; ne pas saisir 0 pour simuler NULL et ne jamais altérer une donnée réelle.

**attendu** : Stock à vérifier, quantité disponible/manquante non déterminable ; aucune présentation d’un zéro connu ou d’une disponibilité certaine. Devis autorisé, HT10,00 / TVA2,00 / TTC12,00 ; historique conservé, aucune réservation.

**ecritures** : Aucune nouvelle écriture et aucune modification d’écriture existante par les actions de ce cas ; comparer le journal avant/après.

**fiscal** : Totaux documentaires au taux saisi 20 % ; aucune facture, TVA déclarée ni liquidation fiscale créée par le devis ou les pièces jointes.

**controles** : Comparer société/exercice actifs, stock et journal avant/après ; relever les numéros effectivement générés, sans imposer un préfixe.

**statut** : Bloqué

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Attestation du périmètre laboratoire, capture Stock à vérifier et création ; historique NULL attesté par opérateur ; journal avant/après.

**observations** : À renseigner pendant la recette.

