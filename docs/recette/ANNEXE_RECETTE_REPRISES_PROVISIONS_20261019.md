# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Annexe — reprises de provisions615/617

Version 1 du 19 octobre 2026. Recette humaine à effectuer ; résultats automatisés distincts.

## Périmètre et précautions de recette

Cette annexe complète le cahier général existant. Elle couvre les reprises liées à une dotation, leurs contrôles et leurs exports. RH/paie restent différées. Utiliser uniquement une base vierge de recette ; aucun dossier réel.

Développement du périmètre615/617 livré. Tests automatisés : rapports 615/617. Recette utilisateur : Non testé. Mise en production : non validée. Ne pas clôturer l’exercice 2025 deS1 dans ce scénario ; aucun impôt n’est calculé ou comptabilisé.

Les montants de risque sont des hypothèses de test, pas des estimations comptables réelles. Référence et date de pièce sont fournies ici pour la preuve ; elles ne deviennent pas obligatoires pour la validation des écritures.

## Jeu de données exact

S1 : RECETTE PROVISIONS615 SARL ; Casablanca ; MAD ; SARL. Email : recette.provisions615@example.com ; mot de passe fictif : RecetteProvisions615!. Lecteur : lecture.provisions615@example.com / LectureProvisions615!.

Identifiants fiscaux laissés vides. Premier exercice 2025 ; calendriers 2025 et2026 civils, périodes ouvertes. Logo fictif : docs/recette/images/LOGO_RECETTE_FICTIF.png.

S2 : RECETTE PROVISIONS CONTROLES615 ; S3 : RECETTE PROVISIONS CHRONO615. Initialisation de chaque société : Compléter le plan CGNC,2025 civil, capitalBQ20000 au 02/01/2025 puis dotation 1000 au 31/12/2025 commeRP-03. Ne pas importer les pièces deS1.

Comptes 5141/1111/6195/1518/7195. Dotation DOSSIER-PV01 — risque fictif de recette,1000. REP-PV01 :400, phase 1 ; REP-PV02 :200, phase 2. Reprises et inverse deS1 tous au 31/12/2025. Motif inverse : Correction fictive de la reprise phase 1.

Le logiciel génère les identifiants/numéros définitifs et les référencesINV/ANN-REPRISE : les relever, sans les inventer ni forcer leur valeur.

## Calcul indépendant des résultats attendus

Calcul en centimes entiers, indépendant du code métier de l’application. Après les deux reprises : résultat avant impôt−400, provision400. Après inverse de 400 : résultat avant impôt−800, provision800, reprise active200, disponible 800.

Journal final :5 pièces/10 lignes, débit=crédit 22000.00 MAD. Actif20000.00=passif20000.00. Aucun paiement, TVA ou impôt ajouté.

| Compte | Libellé de contrôle | Débit net MAD | Crédit net MAD |

|---|---|---|---|

| 1111 | Capital social | 0.00 | 20000.00 |

| 1518 | Autres provisions pour risques | 0.00 | 800.00 |

| 5141 | Banques (solde débiteur) | 20000.00 | 0.00 |

| 6195 | Dotations d'exploitation aux provisions pour risques et charges | 1000.00 | 0.00 |

| 7195 | Reprises sur provisions pour risques et charges | 0.00 | 200.00 |

## RP-01 — Créer le dossier vierge et ses calendriers

Module : Préparation

Prérequis : Application de recette isolée ; migration100 installée séparément par l’administrateur. Aucune société réelle sélectionnée.

Données exactes : Admin Recette Provisions ; RECETTE PROVISIONS615 SARL ; Casablanca ; recette.provisions615@example.com ; RecetteProvisions615! ; premier exercice 2025 ; calendriers civils2025/2026.

Actions dans l’interface : Déconnexion si nécessaire. Créer un compte → renseigner les cinq champs du jeu → créer. Paramètres : choisir SARL/MAD et Premier exercice (année de clôture)2025, enregistrer. Clôture : sélectionner2025, vérifier01/01–31/12 et périodes ouvertes ; conserver2026 civil. Si2025 n’a pas été préparé, Créer un exercice → année2025, début01/01/2025, clôture 31/12/2025 → Créer cet exercice.

Résultat attendu : Société fictive active, administrateur identifié, exercices 2025/2026 présents sans chevauchement. Aucun identifiant fiscal inventé.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Écrans société et Gestion des exercices.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-02 — Préparer les comptes et le logo

Module : Préparation

Prérequis : RP-01 réussi.

Données exactes : Comptes 5141,1111,6195,1518,7195 ; logo docs/recette/images/LOGO_RECETTE_FICTIF.png.

Actions dans l’interface : Plan comptable de la société → Compléter le plan CGNC. Rechercher les cinq comptes et vérifier leurs libellés. Paramètres → Logo de la société → choisir le PNG fictif → enregistrer. Ne pas utiliser un logo ou un dossier réel.

Résultat attendu : Comptes disponibles et logo fictif visible, aucun mouvement comptable.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Plan filtré et aperçu du logo.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-03 — Enregistrer le capital fictif et la dotation

Module : Inventaire

Prérequis : RP-02 réussi ; exercice 2025 actif.

Données exactes : CAP-PV01 ; 02/01/2025 ; BQ ; 20000 MAD. Dotation DOSSIER-PV01 — risque fictif de recette ; 1000 MAD ; 6195/1518.

Actions dans l’interface : Journal → Nouvelle écriture : date comptable et justificatif 02/01/2025, journal BQ, libellé Apport bancaire fictif PV01, référence CAP-PV01. Deux lignes 5141 débit 20000 et1111 crédit 20000 → enregistrer, puis Valider. Clôture 2025 → Ajouter un ajustement → Provision pour risques et charges, libellé/montant/comptes du jeu → Vérifier l’écriture → Créer l’écriture. Journal 2025 : valider uniquement cette nouvelle OD.

Résultat attendu : Deux pièces validées et équilibrées. Source datée 31/12/2025 ; aucune contrepassation automatique. Résultat comptable avant impôt−1000 ; banque 20000 ; provision1000.

Écritures attendues : BQ D5141/C1111 20000 ; OD D6195/C1518 1000.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Deux pièces du Journal avec numéros et dotation de Clôture.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-04 — Vérifier un aperçu sans mutation

Module : Inventaire

Prérequis : RP-03 réussi.

Données exactes : Source DOSSIER-PV01 ; date 31/12/2025 ; montant 400 ; REP-PV01 ; date pièce 31/12/2025 ; Diminution fictive du risque — phase 1.

Actions dans l’interface : Clôture 2025 → Reprises partielles de provisions → sélectionner DOSSIER-PV01. Saisir les cinq champs du jeu. Cliquer Vérifier la reprise, sans créer. Relever dotation 1000, disponible 1000, comptes/libellés et capacité pour cette date.

Résultat attendu : Aperçu OD 2025 : débit 1518 et crédit 7195 pour400. Aucun brouillon supplémentaire au Journal. Créer reste désactivé avant confirmation.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Comparer le nombre de pièces avant/après aperçu ; contrôler1000 de capacité.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Aperçu et nombre de pièces du Journal.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-05 — Créer la réservation de 400

Module : Inventaire

Prérequis : RP-04 réussi ; ne pas changer les données après l’aperçu.

Données exactes : Même demande REP-PV01,400 MAD.

Actions dans l’interface : Contrôler les mouvements et justificatifs fictifs. Cocher J’ai vérifié les mouvements du compte et les justificatifs de la reprise. Cliquer Créer le brouillon de reprise une fois. Rester sur le suivi puis ouvrir le Journal 2025.

Résultat attendu : Suivi mis à jour sans F5 : dotation 1000 ; reprises validées0 ; réservation 400 ; disponible 600. Un seul nouveau brouillon, sans modifier la dotation.

Écritures attendues : Brouillon OD D1518/C7195 400.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Suivi1000/0/400/600 et brouillon REP-PV01.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-06 — Valider la première reprise

Module : Inventaire

Prérequis : RP-05 réussi ; exercice 2025 actif.

Données exactes : REP-PV01 de 400 MAD.

Actions dans l’interface : Journal : ouvrir la pièce REP-PV01, contrôler les deux lignes puis Valider. Revenir dans Clôture → reprises, sélectionner DOSSIER-PV01 et Actualiser les provisions si nécessaire.

Résultat attendu : Reprise validée400 ; réservation 0 ; disponible 600. Montants et source inchangés, numéro définitif conservé.

Écritures attendues : OD définitive D1518/C7195 400.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Pièce définitive et suivi actualisé.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-07 — Ajouter200 et contrôler le premier résultat

Module : Inventaire

Prérequis : RP-06 réussi.

Données exactes : 31/12/2025 ; 200 MAD ; REP-PV02 ; date pièce 31/12/2025 ; Diminution fictive du risque — phase 2.

Actions dans l’interface : Même source : renseigner les données, Vérifier la reprise, confirmer puis créer. Vérifier réservation 200 et disponible 400. Journal 2025 : valider REP-PV02. Liasse fiscale2025 : ouvrir CPC et Bilan.

Résultat attendu : Reprises validées600, disponible 400. CPC avant impôt−400 ; provision au bilan400 ; banque 20000 ; actif=passif20000. Aucun impôt ou retraitement fiscal n’est ajouté dans ce scénario.

Écritures attendues : OD D1518/C7195 200.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Suivi, CPC et bilan2025.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-08 — Préparer l’annulation sans libération anticipée

Module : Inventaire

Prérequis : RP-07 réussi.

Données exactes : Annuler REP-PV01 ; date 31/12/2025 ; motif Correction fictive de la reprise phase 1.

Actions dans l’interface : Suivi → repérer la ligne REP-PV01 de 400 → Annuler la reprise → saisir date/motif → Créer l’inverse de reprise. Ne pas valider l’inverse immédiatement. Consulter le Journal.

Résultat attendu : Original de 400 conservé ; inverse 400 en brouillon. Le disponible reste400, pas800. Le suivi explique la capacité maintenue jusqu’à validation des deux pièces.

Écritures attendues : Inverse brouillon D7195/C1518 400.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Original et inverse présents, suivi avec capacité 400.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-09 — Valider l’inverse et contrôler le résultat final

Module : Inventaire

Prérequis : RP-08 réussi ; seul l’inverse reste en brouillon.

Données exactes : Inverse ANN-REPRISE de REP-PV01 ; 400 MAD ; 31/12/2025.

Actions dans l’interface : Journal 2025 : contrôler puis valider l’inverse. Revenir au suivi, actualiser et sélectionner DOSSIER-PV01. Ouvrir Bilan/CPC depuis Liasse fiscale2025.

Résultat attendu : Reprise active200, réservation 0, disponible 800. REP-PV01 et son inverse restent visibles. Provision finale800 ; CPC avant impôt−800 ; banque 20000 ; actif=passif20000.

Écritures attendues : Inverse définitif D7195/C1518 400. Aucun effacement de l’original.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Deux pièces 400, suivi final1000/200/0/800 et états2025.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-10 — Télécharger le suivi avec logo

Module : Exports

Prérequis : RP-09 réussi ; logo fictif enregistré.

Données exactes : Source DOSSIER-PV01 ; PDF et Excel de suivi.

Actions dans l’interface : Dans le suivi, cliquer Télécharger le suivi PDF puis Télécharger le suivi Excel. Ouvrir les fichiers. Excel : feuilles Synthèse, Reprises, Logo société ; vérifier les deux reprises, référence déclarée, inverse et statut.

Résultat attendu : Identité/logo fictifs dans les deux formats ; dotation 1000, active200, réservations 0, disponible 800. Reprise 400 annulée par inverse validé ; 200 active. Empreinte présente, aucune attestation de déductibilité.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Comparer écran/fichiers ; consigner les noms téléchargés et conserver les fichiers.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : PDF, Excel et captures des cellules/du logo.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-11 — Contrôler le Journal et le FEC final

Module : Exports

Prérequis : RP-09 réussi ; cinq pièces toutes validées ; aucune autre opération dans S1.

Données exactes : Exercice 2025 ; référencesCAP-PV01,INV du dossier,REP-PV01,REP-PV02,ANN-REPRISE.

Actions dans l’interface : Journal : filtrer2025, contrôler cinq pièces et leurs lignes. Exporter le FEC 2025 depuis le module FEC. Ouvrir le fichier sans modifier les montants, comparer les comptes et références au tableau de l’oracle.

Résultat attendu : 5 pièces,10 lignes ; débit=crédit 22000 MAD. Soldes D5141=20000 ; C1111=20000 ; D6195=1000 ; C1518=800 ; C7195=200. Aucun brouillon.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Sommes en centimes, unicité des pièces, références et numéros définitifs.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : FEC et contrôle indépendant des10 lignes.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-12 — Consulter sans commandes de mutation

Module : Permissions

Prérequis : RP-10 réussi ; administrateur S1.

Données exactes : Nom Lecteur Provisions ; lecture.provisions615@example.com ; LectureProvisions615! ; rôle lecture.

Actions dans l’interface : Paramètres → Utilisateurs → Ajouter un utilisateur : saisir nom, adresse et mot de passe du jeu, rôle lecture, Créer le compte. Déconnexion, connexion du lecteur. Clôture 2025 → même source → lire et télécharger PDF/Excel.

Résultat attendu : Suivi800 disponible et exports accessibles. Aucun formulaire Vérifier la reprise ni bouton Annuler la reprise. Source et pièces intactes.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Écran lecteur sans mutations, fichiers téléchargés et contrôle du Journal.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## RP-13 — Séparer les sociétés

Module : Permissions

Prérequis : Administrateur reconnecté à S1 ; conserver ses fichiers finaux.

Données exactes : Nouvelle société RECETTE PROVISIONS CONTROLES615 (S2).

Actions dans l’interface : Sélecteur de société → Nouvelle société → saisir le nomS2 → Créer. Clôture → ouvrir les reprises. Vérifier l’absence du DOSSIER-PV01 deS1. Revenir à S1 et retrouver son suivi800.

Résultat attendu : Aucune source deS1 visible dans S2 ; suivi deS1 inchangé.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Vérifier les noms de sociétés en haut de page et dans les exports.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Deux écrans distincts S1/S2.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## NEG-RP01 — Refuser un dépassement ou une saisie invalide

Module : Négatifs

Prérequis : Administrateur S1, aprèsRP-09.

Données exactes : Source DOSSIER-PV01 ; 31/12/2025 ; montant 800.01 puis0,-1,0.001 ; justificationEssai négatif fictif.

Actions dans l’interface : Essayer successivement ces montants dans Montant de reprise, cliquer Vérifier la reprise lorsque le navigateur le permet. Ne pas forcer les contrôles HTML. Revenir au suivi après chaque essai.

Résultat attendu : 800.01 refusé par capacité ; valeurs nulles/négatives/précision excessive empêchées par formulaire ou API. Disponible 800, aucun nouveau brouillon.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Messages ou contrôle de saisie, nombre de pièces toujours5.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## NEG-RP02 — Refuser une reprise antérieure à la source

Module : Négatifs

Prérequis : S1 aprèsRP-09.

Données exactes : Date 30/12/2025 ; 100 MAD ; justificationEssai de date fictif.

Actions dans l’interface : Saisir les données dans le même panneau, Vérifier la reprise. Relever le refus puis remettre31/12/2025, sans créer.

Résultat attendu : Refus : reprise antérieure à la dotation du31/12/2025 ; disponible 800 et Journal inchangés.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Message de date et suivi800.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## NEG-RP03 — Bloquer une période fermée puis la rouvrir

Module : Négatifs

Prérequis : S1 aprèsRP-11 ; administrateur ; aucune pièce brouillon.

Données exactes : Période Décembre2025 ; demande100 MAD au 31/12/2025.

Actions dans l’interface : Clôture 2025 → Périodes comptables → cliquer la période dont l’action est Fermer Décembre, confirmer. Essayer un aperçu de reprise 100 au 31/12/2025 : relever le refus. Revenir aux périodes et Ouvrir Décembre, confirmer. Réessayer l’aperçu, sans créer.

Résultat attendu : Fermeture bloque l’aperçu ; réouverture administrative rétablit l’aperçu. Aucune reprise ajoutée ni clôture annuelle exécutée ; trace de période conservée.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Période fermée/refus puis période ouverte ; Journal toujours5 pièces.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## NEG-RP04 — Imposer original avant inverse

Module : Négatifs

Prérequis : S2 vierge ; initialiser son plan,2025 et capital commeRP-01 à03. Dotation 1000 libellée DOSSIER-CONTROLE-S2 validée.

Données exactes : Reprise 100 au 31/12/2025 référenceREP-S2 ; annulation même date, motif Annulation brouillon fictif.

Actions dans l’interface : Créer REP-S2 en brouillon, ne pas valider. Depuis le suivi, créer son inverse. Journal 2025 : essayer de valider uniquement l’inverse ; relever le refus. Puis Valider les brouillons pour les deux pièces, après contrôle.

Résultat attendu : Inverse seul refusé ; original et inverse validés ensemble dans le bon ordre. Capacité 1000 libérée uniquement après les deux validations.

Écritures attendues : Brouillon D1518/C7195 100 et inverse D7195/C1518 100 ; effet net0.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Refus de validation isolée, deux numéros définitifs et disponible 1000.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## NEG-RP05 — Respecter la date d’une annulation future

Module : Négatifs

Prérequis : Créer S3 et initialiser plan/capital/dotation 1000commeRP-01 à03, libelléDOSSIER-CHRONO-S3. Calendrier 2026 ouvert.

Données exactes : Reprise 1000 le01/02/2026, référenceREP-CHRONO ; inverse 01/06/2026, motifRisque fictif rétabli en juin ; aperçus600au01/03 puis01/07/2026.

Actions dans l’interface : Dans S3, créer puis valider la reprise 1000. Créer puis valider son inverse de juin. Suivi : disponible final1000. Essayer un aperçu600 en mars : relever le refus ; essayer600 en juillet : contrôler l’aperçu, sans créer. Cette branche ne simule aucune clôture ni à-nouveaux annuels.

Résultat attendu : Mars refusé, capacité 0 à cette date ; juillet autorisé en aperçu avec capacité 1000. Aucun nouveau mouvement600.

Écritures attendues : Reprise 2026 D1518/C7195 1000 ; inversejuin D7195/C1518 1000. Effet net2026nul.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Deux pièces 1000 et les deux résultats d’aperçu.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## NEG-RP06 — Conserver les pièces liées et leurs justificatifs

Module : Négatifs

Prérequis : S1 aprèsRP-11 ; administrateur.

Données exactes : Source DOSSIER-PV01 ; REP-PV01 ; son inverse ; REP-PV02.

Actions dans l’interface : Journal 2025 : consulter chaque pièce, vérifier qu’une pièce définitive ne peut être supprimée ou réécrite. Les corrections liées se font depuis le suivi, pas par contrepassation générique. Ne pas tenter de modifier directement la base. Relever les messages de protection lorsque la commande est proposée.

Résultat attendu : Source/originaux/inverse conservés,5 pièces/10 lignes 22000. Les compléments justificatifs éventuels utilisent le flux append-only existant, sans réécrire les lignes.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Pièces conservées et contrôles/message de protection.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## TECH-RP01 — Rejouer les protections financières et concurrentes

Module : Technique

Prérequis : Développeur sur copie locale isolée ; environnement Python et binaires PostgreSQL de recette disponibles. Jamais la base utilisateur.

Données exactes : Depuis la racine : $env:PYTHON_DOTENV_DISABLED='1' ; .\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_reprises_provisions.py Test/test_reprises_provisions615_isole.py Test/test_reprises_chronologie615_isole.py -q

Actions dans l’interface : Exécuter exactement la commande dans PowerShell. Conserver la sortie et le code retour. Le banc prépare ses propres clusters nonce. Si les binaires/dépendances manquent, noter Bloqué avec la cause ; ne pas substituer un PostgreSQL réel.

Résultat attendu : NaN/infini/booléen refusés, idempotence et concurrence sans double consommation, sociétés/rôles protégés, périodes/clôture gardées, source antérieure intacte. Aucun succès déduit si commande échouée/ignorée.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.

Contrôles : Contrôler société/exercice, nombres et absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner pendant la recette.

Anomalies constatées : À renseigner pendant la recette.

Preuve attendue : Commande, sortie complète, code retour et chemins des preuves du banc.

Preuves réelles : À renseigner pendant la recette.

Observations : Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports 615/617.

## Limites non exécutables et validation humaine

LIM-RP01 — Bloqué : Attribution des mouvements manuels historiques sans lien fiable. Analyse humaine distincte ; aucun rapprochement par libellé supposé.

LIM-RP02 — Bloqué : Déductibilité et qualification fiscale du risque réel. Justificatifs et décision comptable/fiscale à obtenir, aucune attestation automatique.

Une empreinte exportée identifie les données courantes, pas une signature ni une preuve de conformité fiscale. Les mouvements manuels historiques non liés ne sont pas attribués automatiquement.

Excel : renseigner Statut humain, Résultat réel, Anomalies et Preuves. La synthèse se calcule à l’ouverture dans Excel ; son recalcul interactif et la mise en page Word du partenaire restent à vérifier.
