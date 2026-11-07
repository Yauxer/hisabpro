# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Version 1 du 20 octobre 2026

Complément 677/679/681 — Balances détaillées et rapprochements documentaires RAS

Mode d’emploi et cahier complémentaire. Les 15 cas humains sont Non testé. Résultat réel, anomalies et preuves restent à renseigner. Aucun résultat humain n’est déduit des tests automatisés.

Développement du périmètre décrit disponible ; tests automatisés consignés séparément ; recette utilisateur à effectuer ; production : non validée.

## Préparer la recette

Un technicien fournit une base de test isolée et fait appliquer explicitement la chaîne103. Ne jamais utiliser une société réelle. Les commandes de laboratoire créent leurs propres cibles et ne migrent pas la base utilisateur.

Le technicien prépare le compte administrateur fictif admin683@example.com, mot de passe RecetteHisab683!2026, dans une société initiale LAB ACCUEIL 683. Ce mot de passe publié est réservé au laboratoire. Le lecteur lecture683@example.com sera créé au casRRP683-07 avec le même mot de passe fictif.

Créer deux sociétés distinctes : RECETTE BALANCES 683 SARL et RECETTE RAS 683 SARL. DeviseMAD, exercice 2026du01/01au31/12 ouvert. Conserver les alertes ICE/IF lorsqu’ils ne sont pas fournis ; ne pas inventer de justificatifs réels.

Les CSV fournis ont une feuille logique et les colonnescompte,debit,credit ; ils alimentent uniquement une préparation de balances, jamais le Journal. Le classeur de suivi à plusieurs feuilles n’est pas un fichier de balance à importer.

## Données et calculs indépendants

Calculs en entiers/centimes, sans appel aux services de l’application. Les montants du scénario sont exclusivement fictifs.

BalanceN :13 comptes ; débit=crédit 51000 MAD ; actif brut 50000, amortissements 300, net 49700 ; passif 49700 ; résultat5000. N-1 : actif net 24850, résultat2500.

Immobilisations corporelles : brut 21000, amortissements 300, net 20700, N-1 net 10350. Sous-postes231/232/233/234/235/238 : bruts1000/2000/3000/4000/5000/6000. Ne pas inventer la ventilation des amortissements/net entre ces sous-postes.

Jeu RAS : capital 100000 ; achat10000 HT+2000 TVA=12000 TTC ; quote-part6000dont1000 TVA ; retenue supposée du laboratoire750 ; cash5250. Les qualifications de l’assistant sont des hypothèses documentées du jeu, pas une qualification d’un dossier réel.

Avant pièce de versement :4 pièces/9 lignes, débit=crédit 118000, banque 94750, fournisseur 6000 créditeur,4457 créditeur 750,CPC −10000,bilan 96750.

Après pièce de versement :5 pièces/11 lignes, débit=crédit 118750, banque 94000, fournisseur 6000 créditeur,4457 soldé,CPC −10000,bilan 96000. Les liens300+450 puis le retrait450 ne modifient aucun de ces chiffres.

La capacité documentaire450après retrait ne signifie pas reste à payer450 : la pièce de versement750reste comptabilisée. Le retrait ne contrepassera aucune écriture.

## Comment utiliser les avancées

Depuis Liasse fiscale, conserver la préparation puis consulter son bilan et ses comptes sources. Les exports PDF/XLSX portent la version/empreinte ; le logo et l’identité actuels restent hors empreinte.

Les sous-postes du bilan sont pour mémoire et ne se somment pas une deuxième fois. Sans sourceN-1, les comparatifs sont indisponibles, pas nuls. Le tableau du bilan se défile horizontalement sur mobile sans déplacer toute la page.

Depuis Déclaration TVA ou la Liasse, ouvrir le registre des captures achats, choisir Rapprochement comptable d’un versement, sélectionner une pièce déjà validée et saisir le montant explicite. Les comptes choisis dans le jeu ne sont pas imposés réglementairement.

Le PDF des rapprochements est séparé des exports annuels099. Les pièces, acteurs, empreintes et retraits y restent visibles. Ce document n’est ni un reçu fiscal, ni un bordereau DGI, ni une attestation de droit à imputation.

## Ordre de passage et suivi humain

Exécuter BAL683-01à07 puis RRP683-01à08. Les véritables numéros de pièces sont attribués par l’application : relever ceux affichés, sans supposer un identifiant technique. Le tableau de bord Excel se recalcule à l’ouverture ; ses statuts humains restent vierges de réussite.

## BAL683-01 — Créer la société de balances

Module : Balances

Prérequis : Administrateur et base vierge isolée fournis par le technicien. Application et migration103 préparées sur cette seule cible.

Données exactes : RECETTE BALANCES 683 SARL ; MAD ; exercice 2026 du 01/01 au 31/12.

Actions dans l’interface : Créer une nouvelle société depuis le sélecteur. Vérifier son plan et l’exercice 2026 ouvert. Choisir cette société. Les ICE/IF manquants restent signalés ; ne pas inventer de références réelles.

Résultat attendu : Société distincte, comptes du CSV présents dans son plan, aucune écriture au Journal.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL683-02 — Importer N et N-1

Module : Balances

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : BALANCE_FICTIVE_N_683.csv et BALANCE_FICTIVE_N1_683.csv,13 comptes chacun.

Actions dans l’interface : Comptabilité → Liasse fiscale → Préparer depuis des balances externes → Importer N / N-1. Joindre les deux CSV fournis, puis Contrôler et préparer.

Résultat attendu : Débit=crédit 51000 MAD ; actif/passif 49700 ; CPC 5000 ; N-1 actif 24850 et CPC 2500. Aucune archive fiscale ni écriture créée.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL683-03 — Conserver et rouvrir la version

Module : Balances

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Préparation contrôlée du cas 02.

Actions dans l’interface : Cliquer Conserver une nouvelle version. Relever version 1 et son empreinte. Recharger la page, ouvrir Importer N / N-1 puis sélectionner version 1 dans Préparations conservées, sans joindre les CSV à nouveau.

Résultat attendu : Même version, même empreinte et mêmes totaux. Les fichiers sources normalisés ont été conservés.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL683-04 — Vérifier le détail des immobilisations

Module : Balances

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Corps : brut 21000, amortissements 300, net 20700 ; N-1 net 10350.

Actions dans l’interface : Dans version 1, cliquer Consulter le bilan et les comptes sources. Choisir Actif. Rechercher visuellement les sous-postes231/232/233/234/235/238. Sur mobile, faire défiler horizontalement le tableau pour lire les colonnes de droite.

Résultat attendu : Bruts1000/2000/3000/4000/5000/6000. Les amortissements et nets non ventilés restent Indisponible. Total général brut 50000/amortissements 300/net 49700 ; N-1 net 24850. Ne pas additionner les sous-postes une seconde fois.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL683-05 — Consulter les comptes sources N/N-1

Module : Balances

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Compte 28321 : crédit 300 enN,150 enN-1.

Actions dans l’interface : Dans Comptes sources normalisés, sélectionner N et rechercher28321. Vérifier une seule ligne. Passer à N-1 et rechercher28321 à nouveau. Rechercher9999999999, puis effacer le filtre.

Résultat attendu : Crédit 300 puis 150, aucun compte pour9999999999 ; effacement retrouve13 comptes. Aucun intitulé historique inventé depuis le plan courant.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL683-06 — Exporter la version contrôlée

Module : Balances

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Version 1 et empreinte relevée au cas 03 ; fichier LOGO_FICTIF_683.png fourni.

Actions dans l’interface : Dans les paramètres de la société fictive, importer LOGO_FICTIF_683.png, simple rectangle bleu de test. Revenir à la version 1 de préparation. Cliquer Exporter la préparation Excel puis Exporter la préparation PDF. Ouvrir les documents et comparer version/empreinte, bilans, CPC et balances sources.

Résultat attendu : Exercice 2026/version 1/même empreinte. PDF et Excel montrent le détail et les comptes. Le motif bleu est présent. Le logo/identité actuels sont hors empreinte ; aucune ancienne version n’est réécrite.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## BAL683-07 — Vérifier N-1 absent et préservation de version1

Module : Balances

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Réimporter uniquement BALANCE_FICTIVE_N_683.csv.

Actions dans l’interface : Actualiser la page puis importer seulement N, contrôler et conserver version 2. Consulter le détail et sélectionner N-1. Revenir ensuite à version 1 et réexporter son PDF.

Résultat attendu : Version 2 : N-1 indisponible, jamais supposé nul. Version 1 conserve sa sourceN-1, son empreinte et ses chiffres ; son export porte toujoursv1.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## RRP683-01 — Préparer les quatre pièces sources du jeu

Module : Rapprochements RAS

Prérequis : Société de recette distincte des balances. Qualifications supposées du laboratoire et données JSON complètes ; ne pas utiliser ces faits pour qualifier une opération réelle.

Données exactes : Nouvelle société RECETTE RAS 683 SARL ; capital 100000 ; facture12000 TTC ; cash5250 ; capture750 ; date 19/10/2026.

Actions dans l’interface : Créer la société RAS distincte enMAD, exercice 2026 ouvert, TVA encaissement, prorata du laboratoire100%. Saisir au Journal BQ CAP-RR683 : débit 5141=100000, crédit 1111=100000, puis valider. Créer le fournisseur FOURNISSEUR FICTIF RR683. Créer une facture achat du 19/10/2026 référence FOURN-RR683, service quantité1 prix HT 10000 TVA 20%, charge déductible 100% du laboratoire. Valider la facture, comptabiliser et valider son écriture. Enregistrer un virement5250 référence VIR-RR683 comptabilisé, puis valider sa pièce. Dans le règlement, utiliser l’assistant TVA 117-V-b : payeur personne morale privée assujettie, prestataire personne physique assujettie, listeB oui, aucune exclusion après contrôle dans ce seul jeu, attestation présentée du 01/09/2026 référence ATTESTATION-FICTIVE-RR683 ; quote-part6000 TTC dont1000 TVA ; justification VENTILATION FICTIVE RR683 : 5000 HT + 1000 TVA = 6000 TTC. Choisir 4457, référence RAS-RR683, confirmer et valider l’OD 750.

Résultat attendu : 4 pièces validées/9 lignes ; débit=crédit 118000 ; banque 94750 ; fournisseur créditeur 6000 ; compte 4457 créditeur 750 ; résultat−10000 ; bilan 96750.

Écritures attendues : Capital : D5141/C1111=100000. Achat : D6111=10000,D34552=2000,C4411=12000. Cash : D4411/C5141=5250. Capture : D4411/C4457=750.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## RRP683-02 — Saisir la pièce de versement à rapprocher

Module : Rapprochements RAS

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Référence VERSEMENT-RR683, date 19/10/2026, débit 4457=750, crédit 5141=750.

Actions dans l’interface : Dans Journal, créer la pièce BQ VERSEMENT-RR683 avec les deux lignes indiquées, puis la valider. Consulter ses montants avant toute création de rapprochement.

Résultat attendu : 5 pièces validées/11 lignes ; débit=crédit 118750 ; banque 94000 ;4457 soldé ; fournisseur 6000 ; CPC −10000 ; bilan 96000.

Écritures attendues : Une nouvelle pièce de750 au débit et au crédit. Aucune date de paiement fiscal n’est déduite de sa date comptable.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## RRP683-03 — Rapprocher une première part300

Module : Rapprochements RAS

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Capture750 ; pièce validéeVERSEMENT-RR683 ; montant 300.

Actions dans l’interface : Déclaration TVA → Registre des retenues TVA 2026 → capture sur achat → Rapprochement comptable d’un versement. Chercher VERSEMENT-RR683, sélectionner la pièce, saisir300, confirmer le rapprochement documentaire puis enregistrer.

Résultat attendu : Lien actif 300, capacité documentaire450 ; acteur et empreinte visibles. Journal inchangé à 5 pièces/11 lignes et118750 MAD.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## RRP683-04 — Compléter par450

Module : Rapprochements RAS

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Même capture et même pièce ; montant 450.

Actions dans l’interface : Sélectionner à nouveau la pièce disponible, saisir450, confirmer et enregistrer. Actualiser les rapprochements.

Résultat attendu : Deux liens actifs300+450=750 ; capacité documentaire0. Aucun double paiement ni écriture supplémentaire.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## RRP683-05 — Retirer le lien450

Module : Rapprochements RAS

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Motif : ERREUR DOCUMENTAIRE FICTIVE RR683.

Actions dans l’interface : Sur le lien 450, cliquer Retirer le rapprochement, saisir exactement le motif, puis Confirmer le retrait documentaire. Relire la trace après actualisation.

Résultat attendu : Lien 300 actif et lien 450 retiré conservés. Montant rapproché300, capacité documentaire450. Le versement comptabilisé reste750 :450n’est pas un reste fiscal à payer.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## RRP683-06 — Refuser un dépassement

Module : Rapprochements RAS

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Après retrait, capacité 450 ; tentative500 sur la même pièce.

Actions dans l’interface : Choisir la pièceVERSEMENT-RR683, saisir500, confirmer puis enregistrer. Lire l’alerte et actualiser les rapprochements.

Résultat attendu : Rejet explicite ; montant rapproché toujours300, capacité 450 et deux traces. Aucun changement de pièce, lien ou retrait.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## RRP683-07 — Vérifier le lecteur et le PDF

Module : Rapprochements RAS

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Compte Lecture lecture683@example.com, mot de passe fictif RecetteHisab683!2026 ; LOGO_FICTIF_683.png.

Actions dans l’interface : Dans la société RAS, importer le logo de test dans les paramètres puis créer le compte Lecture indiqué depuis Administration → Utilisateurs. Se déconnecter et se reconnecter avec ce compte. Ouvrir la capture et les rapprochements. Vérifier l’absence de commandes de création/retrait. Télécharger PDF des rapprochements documentaires et l’ouvrir.

Résultat attendu : Lecture et PDF autorisés ; liens actif 300/retiré450 et motif conservés, empreintes et références exactes. Logo actuel si configuré. Le PDF interne ne vaut pas reçu fiscal.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## RRP683-08 — Vérifier le cloisonnement et le sens des soldes

Module : Rapprochements RAS

Prérequis : Cas précédent terminé sur base fictive isolée.

Données exactes : Société BAL du cas 01, ne contenant aucune capture RAS de la société RAS.

Actions dans l’interface : Revenir au compte administrateur, sélectionner RECETTE BALANCES 683 SARL et ouvrir son registre TVA 2026. Vérifier l’absence de captureRR683. Revenir ensuite à la société RAS et retrouver les deux traces.

Résultat attendu : Aucune capture ni pièce de l’autre société visible. Retour : mêmes liens et écritures. Déclaration/imputation/versement DGI toujours distincts de cette preuve documentaire.

Écritures attendues : Aucune nouvelle écriture.

Impacts fiscaux : Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.

Contrôles : Comparer aux montants de l’oracle et conserver la preuve.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture de l’écran et export lorsqu’il est indiqué.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : À renseigner par la personne chargée de la recette.

## Limites et prochaine reprise

Qualifications RAS supposées du laboratoire, aucun dossier réel qualifié.

Compte 4457 explicitement choisi dans le jeu, pas imposé réglementairement.

Liasse seule complète, ETIC/fiscalité/annexes et formats officiels toujours partiels ou bloqués.

Le rapprochement n’est ni preuve de versement DGI ni crédit imputable ; aucune déclaration automatique déverrouillée.

Installation103 réelle, recette humaine et production non validées. RH/paie différées.

Les guides généraux antérieurs et leurs statuts humains restent conservés. Modes d’emploi : docs/LIASSE_BALANCES_DETAIL_677.md, docs/LIASSE_BALANCES_CONSULTATION_679.md et docs/RAS_RAPPROCHEMENT_681.md. Les rapports techniques détaillent les commandes réellement exécutées.
