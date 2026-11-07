# HISABPRO — Préparation annuelle des ventes

Version 2 du 12 octobre 2026. Complément au guide principal. Recette fictive, sans résultat utilisateur prévalidé.

Ce document explique le nouvel onglet Comptabilité → Liasse fiscale → Préparation ventes. Il fournit un jeu réduit permettant de vérifier les pièces retenues, les identités historiques et les exports CSV, Excel et PDF. La préparation est interne : le formulaire officiel DGI reste à qualifier. Les écritures manuelles et les ventes absentes de la facturation ne sont pas comprises dans ces totaux documentaires.

Le fichier GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx décrit la création de société, les exercices, les factures et les avoirs. Le classeur ANNEXE_RECETTE_VENTES.xlsx contient sept cas à renseigner avec les résultats réellement observés.

## 01 Préparer le dossier fictif

Utiliser un environnement de recette séparé et une société fictive vierge nommée RECETTE VENTES 418 SARL. Se connecter comme administrateur. Créer ou vérifier l'exercice 2026 du 01/01/2026 au 31/12/2026. Ce profil réduit conserve les pièces commerciales sans demander leur comptabilisation ; la préparation devra donc signaler les pièces non comptabilisées. La lecture et l'export n'ajoutent aucune écriture.

Toutes les données ci-dessous sont fictives. Le taux de TVA de 20 % est une donnée de laboratoire, pas une qualification générale des opérations. Les références RVT418-F1/F2 permettent de retrouver les pièces ; relever les numéros internes effectivement attribués à leur validation.

| Réf. | Donnée à saisir | Montant | Résultat attendu |
|---|---|---|---|
| T1 | Client : CLIENT RECETTE VENTES 418 ; ICE 001234567890123 ; IF 12345678 | Sans objet | Identité reprise dans les pièces lors de leur validation |
| F1 | Vente du 15/01/2026 ; référence RVT418-F1 ; description SERVICE RECETTE 418 ; quantité 1 ; prix unitaire 100 ; TVA 20 % | HT 100 ; TVA 20 ; TTC 120 | Facture définitive ; numéro interne généré |
| F2 | Vente du 15/01/2026 ; même client ; référence RVT418-F2 ; même description ; quantité 1 ; prix unitaire 200 ; TVA 20 % | HT 200 ; TVA 40 ; TTC 240 | Deuxième facture définitive |
| A1 | Avoir sur F1 du 15/03/2026 ; motif CORRECTION FICTIVE 418 ; quantité concernée 0,30 ; retour de stock décoché | HT 30 ; TVA 6 ; TTC 36 | Avoir actif à sa propre date, présenté avec signe négatif |

Remises, escompte, emballage, transport et RAS restent à zéro dans ce profil. Aucune saisie d'article stockable n'est nécessaire : utiliser une description de prestation libre. Aucune réception ou quantité de stock ne doit être générée par cette recette documentaire.

## 02 Créer les trois pièces

1. Dans Clients / Fournisseurs, créer CLIENT RECETTE VENTES 418 de type Client avec l'ICE et l'IF du tableau.

2. Dans Factures, choisir Nouvelle facture puis Vente. Saisir F1 selon le tableau. Enregistrer en brouillon, puis utiliser Valider définitivement. Relever son numéro interne. La génération de son écriture reste une action distincte dans ce profil réduit.

3. Répéter avec F2, en saisissant explicitement le prix unitaire 200. Vérifier TTC 240 et relever le numéro interne de cette deuxième pièce.

4. Ouvrir le détail de F1 puis Créer un avoir. Saisir la date 15/03/2026 et le motif du tableau. Sélectionner la ligne SERVICE RECETTE 418, saisir 0,30 dans Quantité concernée et décocher le retour de stock. Vérifier HT 30, TVA 6 et TTC 36 avant de créer l'avoir. Relever son numéro.

5. Vérifier dans les listes que les trois pièces existent. Conserver une capture de leurs numéros et montants avant de préparer les ventes. Une facture restée brouillon ne sera pas retenue.

## 03 Préparer, lire et exporter

1. Choisir l'exercice 2026 dans le sélecteur supérieur, puis Comptabilité → Liasse fiscale → Préparation ventes.

2. Cliquer Préparer les ventes. La période doit être 2026-01-01 → 2026-12-31 et le nombre de pièces retenues doit être 3. Les montants attendus sont HT commercial signé 270,00 et TTC signé 324,00. La TVA signée est 54,00.

3. Lire les deux factures et l'avoir : l'avoir doit porter sa date du 15/03/2026 et des valeurs −30,00 / −6,00 / −36,00. Déplier Périmètre et méthode de calcul pour distinguer les totaux documentaires du chiffre d'affaires comptable. Le diagnostic Pièce non comptabilisée est attendu dans ce profil.

4. Cliquer Exporter les ventes CSV. Ouvrir le fichier VENTES_PREPARATION_INTERNE_2026.csv dans Excel en choisissant UTF-8 et le séparateur point-virgule. Importer les colonnes ICE / IF comme texte pour conserver leurs zéros initiaux. Le fichier contient le périmètre, la période, une empreinte, les trois sources et le total complet 270,00 / 54,00 / 324,00.

5. Cliquer Exporter les ventes Excel. Ouvrir VENTES_PREPARATION_INTERNE_2026.xlsx : la feuille Synthèse contient la société, la période, l'empreinte et les totaux ; Sources contient les trois pièces. Les ICE / IF sont du texte, avec leurs zéros initiaux. Les montants ordinaires sont numériques ; un montant dépassant la précision d'Excel reste un texte exact.

6. Cliquer Exporter les ventes PDF. Ouvrir VENTES_PREPARATION_INTERNE_2026.pdf : vérifier les trois pièces, les identités figées, les totaux et l'empreinte. Le titre indique PRÉPARATION INTERNE DES VENTES ; ce document ne constitue pas une déclaration fiscale.

7. Le CSV correspond à l'aperçu affiché. Les exports Excel/PDF relisent les sources et vérifient son empreinte : si elles ont changé, le téléchargement est refusé avec une invitation à actualiser. Cliquer Actualiser les ventes, comparer le nouveau relevé puis exporter à nouveau. Après un changement de société ou d'exercice, une réponse d'export tardive ne doit pas déclencher de téléchargement. La préparation reste extérieure aux archives de liasse et à leur ancien PDF ou classeur consolidé.

Calcul indépendant : 100 + 200 − 30 = 270 ; 20 + 40 − 6 = 54 ; 120 + 240 − 36 = 324. Ce calcul ne constitue ni un résultat fiscal ni une déclaration de TVA.

## 04 Vérifications complémentaires

VP-001 — Pièces et exclusions : vérifier les trois sources du profil. Dans une variante du dossier, une facture brouillon, une proforma et une pièce annulée ne doivent pas entrer dans le total ; leurs exclusions sont comptées. Les achats restent hors de ce relevé de ventes.

VP-002 — CSV, Excel et PDF : comparer chaque numéro, date, identité et montant avec l'écran, puis les trois totaux indépendants. Vérifier la société, la période et l'empreinte. Conserver les trois fichiers comme preuves. Variante : ajouter une quatrième facture fictive définitive de HT 100 / TVA 20 / TTC 120 après avoir préparé l'aperçu. Un export Excel/PDF de l'ancien aperçu doit être refusé. Actualiser : retrouver quatre pièces et HT 370 / TVA 74 / TTC 444, puis exporter. Utiliser un dossier séparé pour cette variante afin de conserver le profil principal de trois pièces.

VP-003 — Identité figée : modifier uniquement l'ICE de la fiche CLIENT RECETTE VENTES 418 en 009876543210987 après la création des trois pièces. Actualiser la préparation. L'ICE des trois pièces historiques doit rester 001234567890123. Les montants et numéros doivent rester identiques.

VP-004 — Exercice : créer un exercice 2025 vide, du 01/01/2025 au 31/12/2025, dans ce dossier réduit. Le sélectionner et préparer les ventes. Aucune des pièces 2026 ne doit apparaître. Un zéro dans ce relevé signifie absence de pièces documentaires retenues, pas chiffre d'affaires comptable certifié. Revenir en 2026 : retrouver les trois sources.

VP-005 — Société : dans une autre société fictive vierge, sélectionner son exercice 2026 et préparer les ventes. Les sources de RECETTE VENTES 418 SARL ne doivent jamais apparaître. Revenir à la première société : retrouver son seul dossier.

VP-006 — Consultation : créer un utilisateur fictif de rôle Lecture, se connecter avec ce compte dans la première société et consulter/exporter la préparation. Vérifier la conservation des pièces et du Journal ; ce flux ne crée aucune écriture.

VP-007 — Historiques inconnus : cas technique nécessitant un jeu historique synthétique préparé par un technicien sur base isolée. Les tests livrés constituent ces sources sans désactiver les protections. Une pièce dont le montant est inconnu doit rester visible avec À vérifier ; le total complet reste inconnu et la partie certaine est séparée. L'état normal des pièces ne doit pas être modifié pour masquer un contrôle. Ce cas est hors de la séquence manuelle principale.

## 05 Consigner la recette et les limites

Dans ANNEXE_RECETTE_VENTES.xlsx, compléter Résultat réel, Anomalies et Preuves, puis choisir le statut. Les sept cas sont initialement Non testé : les tests automatisés exécutés ne remplissent jamais la recette humaine à votre place. Captures attendues : liste des trois pièces, tableau de préparation, CSV / Excel / PDF téléchargés, refus d'export obsolète et contrôle de l'identité figée.

Développement : préparation interne et trois exports disponibles ; 09E reste partiel. Tests automatisés : les preuves sont dans Test/rapport_preparation_ventes_418.md, Test/rapport_exports_ventes_423.md et la nouvelle consolidation de session. Recette utilisateur : à effectuer. Production : non validée. Restent la qualification du formulaire officiel, le rapprochement au chiffre d'affaires comptable et les ventilations fiscales exhaustives. Aucun XML/EDI n'est fourni par cet onglet.

Le dossier annuel complet, la comptabilisation et la clôture restent couverts par leurs parcours du guide principal. Ce profil réduit de trois pièces ne remplace pas la recette annuelle complète. Le point 6 reste en attente du retour utilisateur.
