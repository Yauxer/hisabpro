# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Version 1 du 21 octobre 2026

Complément 687 — échéances documentaires des balances importées

Mode d’emploi pour les fonctions disponibles. Sept cas humains Non testé ; aucun résultat humain prérempli. RH/paie et recette utilisateur différées. Production non validée.

## Préparation du laboratoire

Un technicien fournit une base isolée et un compte administrateur fictif. Ne pas utiliser une société ou une base comptable réelle. Aucun SQL supplémentaire requis : la chaîne 071 des préparations immuables doit déjà être présente. Les tests techniques récents utilisent un schéma 103 isolé.

La ventilation est documentée à la date de fin de la période conservée ; la personne chargée de la recette choisit les montants du jeu, sans transformer une date de facture en échéance. Les champs vides restent inconnus ; zéro n’est conservé que s’il est saisi. Les analyses complémentaires peuvent se recouper : ne pas les additionner.

## Calculs attendus indépendants

Balance fictive : 8000 de créances 3421 + 1000 en banque 5141 = 9000 actif ; 6000 capital 1111 + 3000 dettes 4411 = 9000 passif ; aucun compte de résultat, CPC 0. Après la première ventilation : 2000 + 1000 = 3000 qualifiés sur 8000, reliquat 5000. Dette : 1000 + 1000 + 1000 = 3000, reliquat 0. Chaque complément crée une version documentaire, zéro écriture.

## BAL687-01 — Créer la préparation de base

Prérequis : Base isolée fictive, administrateur et application fournis par le technicien ; cas précédents terminés.

Données exactes : RECETTE ECHEANCES 687 SARL ; MAD ; exercice 2026 ouvert, du 01/01 au 31/12 ; BALANCE_FICTIVE_ECHEANCES687.csv.

Actions dans l’interface : Créer cette société distincte et vérifier les quatre comptes du CSV dans son plan. Comptabilité → Liasse fiscale → Importer N / N-1 : joindre le CSV en Balance N, sans N-1 ; Contrôler et préparer puis Conserver une nouvelle version. Relever version 1 et empreinte.

Résultat attendu : 4 comptes ; D=C 9000 MAD ; actif/passif 9000 ; CPC 0 ; N-1 indisponible. Version 1 créée sans écriture.

Écritures attendues : Aucune écriture ; le Journal de cette société reste vide.

Impact fiscal : Aucune liquidation, déclaration ou preuve de dépôt créée.

Contrôles : Comparer les montants et les versions ; conserver la capture/export indiqué.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture d’écran et fichiers exportés lorsqu’indiqués.

Preuve réelle : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL687-02 — Vérifier les inconnus initiaux

Prérequis : Base isolée fictive, administrateur et application fournis par le technicien ; cas précédents terminés.

Données exactes : Version 1 ; créance 3421=8000 ; dette 4411=3000.

Actions dans l’interface : Ouvrir Compléter les échéances documentaires des balances. Choisir B6 ·3421 puis B7 ·4411 dans Compte à documenter. Examiner les sept champs.

Résultat attendu : Champs vides/Inconnu ; reliquats 8000 et 3000. Aucun classement automatique en échues ; aucun tiers ni calendrier supposé.

Écritures attendues : Aucune écriture ; le Journal de cette société reste vide.

Impact fiscal : Aucune liquidation, déclaration ou preuve de dépôt créée.

Contrôles : Comparer les montants et les versions ; conserver la capture/export indiqué.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture d’écran et fichiers exportés lorsqu’indiqués.

Preuve réelle : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL687-03 — Conserver la partie certaine des créances

Prérequis : Base isolée fictive, administrateur et application fournis par le technicien ; cas précédents terminés.

Données exactes : B6/3421 : Plus d’un an 2000 ; Échues 1000 ; justification ETAT CLIENTS FICTIF687 ; autres champs laissés vides.

Actions dans l’interface : Sélectionner B6 ·3421, saisir les deux montants et la justification. Confirmer les données documentaires puis Conserver les compléments dans une nouvelle version. Ouvrir à nouveau le panneau après sélection automatique de version 2.

Résultat attendu : Version 2 liée à version 1 par empreinte. Total8000, ventilé3000, reliquat 5000. Moins d’un an et analyses complémentaires restent inconnus. Bilan/CPC et sources inchangés.

Écritures attendues : Aucune écriture ; le Journal de cette société reste vide.

Impact fiscal : Aucune liquidation, déclaration ou preuve de dépôt créée.

Contrôles : Comparer les montants et les versions ; conserver la capture/export indiqué.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture d’écran et fichiers exportés lorsqu’indiqués.

Preuve réelle : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL687-04 — Ajouter les échéances des dettes

Prérequis : Base isolée fictive, administrateur et application fournis par le technicien ; cas précédents terminés.

Données exactes : B7/4411 : Plus d’un an 1000 ; Moins d’un an 1000 ; Échues 1000 ; État/organismes publics0 ; justification ETAT FOURNISSEURS FICTIF687.

Actions dans l’interface : Depuis version 2, ouvrir le panneau et choisir B7 ·4411. Saisir les quatre montants indiqués sans remplir les autres analyses ; confirmer puis conserver une nouvelle version.

Résultat attendu : Version 3 ; B7 ventilé 3000/reliquat 0, analyse État=0 explicite ; devises/entreprises liées/effets inconnus. B6 conserve 2000/1000 et reliquat 5000.

Écritures attendues : Aucune écriture ; le Journal de cette société reste vide.

Impact fiscal : Aucune liquidation, déclaration ou preuve de dépôt créée.

Contrôles : Comparer les montants et les versions ; conserver la capture/export indiqué.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture d’écran et fichiers exportés lorsqu’indiqués.

Preuve réelle : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL687-05 — Refuser un dépassement sans perdre la saisie

Prérequis : Base isolée fictive, administrateur et application fournis par le technicien ; cas précédents terminés.

Données exactes : Depuis version 3, B6/3421 : remplacer Échues 1000 par 7000 ; conserver Plus d’un an 2000.

Actions dans l’interface : Saisir7000, confirmer puis tenter de conserver. Lire l’alerte. Revenir à 1000 sans enregistrer une nouvelle version.

Résultat attendu : Rejet : 9000 ventilés dépasseraient le solde 8000. Les champs restent visibles pour correction ; version 3 et le Journal sont inchangés.

Écritures attendues : Aucune écriture ; le Journal de cette société reste vide.

Impact fiscal : Aucune liquidation, déclaration ou preuve de dépôt créée.

Contrôles : Comparer les montants et les versions ; conserver la capture/export indiqué.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture d’écran et fichiers exportés lorsqu’indiqués.

Preuve réelle : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL687-06 — Exporter et vérifier la version 3

Prérequis : Base isolée fictive, administrateur et application fournis par le technicien ; cas précédents terminés.

Données exactes : Version 3 ; logo fictif si fourni par le technicien.

Actions dans l’interface : Fermer le panneau si nécessaire, puis Exporter la préparation Excel et PDF. Ouvrir les fichiers. Comparer les rubriques, sources, version/empreinte, échéances, reliquats, justification et analyses complémentaires.

Résultat attendu : PDF/XLSX cohérents : B6 reliquat 5000, B7 reliquat 0, champs inconnus identifiés. Parent version 2 et son empreinte présents. Aucun document présenté comme ETIC officielle complète ou prêt à déposer. Logo actuel si configuré.

Écritures attendues : Aucune écriture ; le Journal de cette société reste vide.

Impact fiscal : Aucune liquidation, déclaration ou preuve de dépôt créée.

Contrôles : Comparer les montants et les versions ; conserver la capture/export indiqué.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture d’écran et fichiers exportés lorsqu’indiqués.

Preuve réelle : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL687-07 — Préserver les anciennes versions et le rôle Lecture

Prérequis : Base isolée fictive, administrateur et application fournis par le technicien ; cas précédents terminés.

Données exactes : Compte fictif lecture687@example.com, rôleLecture, mot de passe de laboratoire Recette687!2026.

Actions dans l’interface : En administrateur, rouvrir version 1 et vérifier ses champs inconnus, puis version 2 avec B7 encore inconnu. Créer le lecteur indiqué depuis Administration → Utilisateurs. Se connecter avec ce lecteur, choisir version 3, ouvrir le panneau et télécharger les exports.

Résultat attendu : Anciennes versions inchangées. Lecture peut consulter/exporter ; champs désactivés et aucune commande de conservation. Bilan 9000/CPC 0 et Journal vide. Recette humaine toujours à renseigner dans ce classeur.

Écritures attendues : Aucune écriture ; le Journal de cette société reste vide.

Impact fiscal : Aucune liquidation, déclaration ou preuve de dépôt créée.

Contrôles : Comparer les montants et les versions ; conserver la capture/export indiqué.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture d’écran et fichiers exportés lorsqu’indiqués.

Preuve réelle : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## Limites

Le panneau ne constitue pas une ETIC officielle complète. Il ne renseigne ni liquidation, ni tableau de financement, ni modèle DGI, ni annexe EDI. Les soldes de sens inverse restent visibles et non ventilables dans cette préparation. Les sources absentes des anciennes versions ne sont pas reconstituées. Les états et les balances conservés ne sont pas recalculés.
