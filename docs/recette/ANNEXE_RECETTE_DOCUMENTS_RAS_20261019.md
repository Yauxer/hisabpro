# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Version 2 du 19 octobre 2026

Annexe 649 — Documents des OD RAS TVA · Révision653

Révision653 : le cas principal utilise une facture 12000 TTC et une quote-part 6000 TTC. Aucun cumul mensuel antérieur n’est supposé pour écarter une exclusion. Le cas initial649 reste une preuve arithmétique historique, à ne pas utiliser comme recette fiscale principale.

Recette utilisateur à effectuer. Tous les cas sont Non testé ; résultats réels, anomalies et preuves restent vierges.

Complément au cahier annuel et aux guides 573/593. Ni bordereau officiel, ni attestation fiscale, ni preuve de versement. RH/paie et recette humaine restent différées.

## Données du scénario

Utiliser exclusivement une base de test isolée. Ne pas lancer ce scénario dans une société réelle.

Les codes de situations ci-dessous correspondent aux choix de l’assistant déjà documenté573. Le taux75% est celui de ce seul jeu existant ; aucun cas réel n’est qualifié par cette annexe.

Société : SOCIETE FICTIVE DOC649 SARL. Devise MAD, forme SARL, capital 100000, régime IS, TVA sur encaissement. PréfixeDOC649. ICE/IF/RC non renseignés : conserver les avertissements.

Exercice 2026 ouvert, du 01/01/2026 au 31/12/2026. Opérations du 19/10/2026 ; capital au 02/01/2026. Crédit TVA d’ouverture 0 ; prorata annuel du laboratoire 100%.

Administrateur : docs649@example.com. Comptable : compta649@example.com. Lecture : lecture649@example.com. Mot de passe de ces comptes fictifs : DocumentsRecette649!.

Fournisseur : FOURNISSEUR FICTIF DOC649. Achat : référence fournisseur FOURN-DOC649 ; description SERVICE DOC649 ; quantité 1 ; prix HT 10000 ; TVA 20% ; charge, déduction 100%. Numéro attendu DOC649-2026-001.

Références à saisir : CAP-DOC649 pour le capital ; VIR-DOC649 pour le virement5250 ; RAS-DOC649 pour la capture ; COMP-DOC649 pour le complément documentaire.

Comptes du jeu : 1111 capital,5141 banque,6111 achat,34552 TVA sur achats,4411 fournisseur et 4457 compte destination explicitement choisi pour la capture.

Faits supposés du laboratoire : payeur personne morale privée assujettie ; prestataire personne physique assujettie ; prestation de liste B ; aucune exclusion après contrôle ; attestation présentée du 01/09/2026, référence ATT-FICTIVE-DOC649. Aucun de ces faits ne constitue une pièce réelle.

Quote-part : 6000 TTC dont1000 TVA. Justification à saisir : VENTILATION FICTIVE DOC649 : 5000 HT + 1000 TVA = 6000 TTC. Mois de versement prévu : 2026-11, sans versement présumé.

Document fourni : DOCUMENT_FICTIF_649.pdf, marqué essai uniquement. Motif d’annulation : ANNULATION FICTIVE DOC649 POUR RECETTE. Société témoin vide : TEMOIN DOC649 SARL.

Le fichier donnees_recette_documents_ras_20261019.json fournit également toutes les données structurées et les calculs indépendants.

## Calculs indépendants et Journal attendu

Calculs entiers en centimes, sans import d’un calcul métier. Achat 10000+2000=12000 ; quote-part 6000 dont TVA 1000 ; retenue du jeu 750 ; trésorerie 5250. Le compte 4457 est une convention de recette, pas une affectation imposée.

Avant annulation : banque 94750, fournisseur 6000, compte 4457 créditeur 750, résultat−10000, bilan 96750 ;4 pièces/9 lignes D = C = 118000.

Après annulation : banque 100000, fournisseur 12000, compte 4457 soldé, résultat−10000, bilan 102000 ;6 pièces/13 lignes D = C = 124000. Chaque ajout documentaire crée0 pièce/0 ligne/0 MAD.

| Phase | Journal | Compte | Débit / crédit MAD |

|---|---|---|---|

| Capital | BQ | 5141 | 100000.00 / 0.00 |

| Capital | BQ | 1111 | 0.00 / 100000.00 |

| Achat | AC | 6111 | 10000.00 / 0.00 |

| Achat | AC | 34552 | 2000.00 / 0.00 |

| Achat | AC | 4411 | 0.00 / 12000.00 |

| Règlement | BQ | 4411 | 5250.00 / 0.00 |

| Règlement | BQ | 5141 | 0.00 / 5250.00 |

| Capture RAS | OD | 4411 | 750.00 / 0.00 |

| Capture RAS | OD | 4457 | 0.00 / 750.00 |

| Annulation règlement | BQ | 5141 | 5250.00 / 0.00 |

| Annulation règlement | BQ | 4411 | 0.00 / 5250.00 |

| Annulation RAS | OD | 4457 | 750.00 / 0.00 |

| Annulation RAS | OD | 4411 | 0.00 / 750.00 |

## RDO-001 — Créer le dossier fictif

Module : Préparation

Prérequis : Environnement de test isolé, migrations existantes dont083/099 appliquées par administrateur ; aucune base réelle.

Données exactes : SOCIETE FICTIVE DOC649 SARL ; admin docs649@example.com / DocumentsRecette649! ; MAD ; SARL ; capital 100000 ; IS ; TVA encaissement ; exercice 2026 du 01/01 au 31/12 ; préfixeDOC649. ICE/IF/RC vides.

Actions dans l’interface : Créer le compte et la société. Dans Paramètres, renseigner les valeurs ci-dessus. Dans Exercices sélectionner2026 ouvert. Créer les utilisateurs compta649@example.com (Comptable) et lecture649@example.com (Consultation seule), même mot de passe. Créer FOURNISSEUR FICTIF DOC649 de type Fournisseur. Vérifier le plan et les comptes du jeu.

Résultat attendu : Société/exercice et rôles sélectionnables ; avertissements d’identifiants conservés ; aucun mouvement financier créé par ce paramétrage.

Écritures attendues : Aucune écriture.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Société de test et année 2026 visibles ; aucune identité légale inventée.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture Paramètres, exercice et rôles.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-002 — Comptabiliser capital et achat

Module : Préparation

Prérequis : RDO-001 ; comptes1111/5141/6111/34552/4411 disponibles.

Données exactes : Capital 02/01/2026 : CAP-DOC649,100000. Achat 19/10/2026 : FOURN-DOC649, SERVICE DOC649, quantité 1, prix HT 10000, TVA 20%, charge et déduction 100%. Prorata laboratoire 100%.

Actions dans l’interface : Dans Déclaration TVA, régler Prorata annuel de déduction (%) à1000 et crédit d’ouverture à0, puis Enregistrer. Dans Journal créer une écriture BQ : débit5141=100000, crédit1111=100000 ; référenceCAP-DOC649 et libellé Capital fictif DOC649. Valider. Dans Factures choisir Achat, le fournisseur du jeu et 19/10/2026. Saisir la référence fournisseur et la ligne ci-dessus. Valider puis comptabiliser. Dans Journal contrôler et valider l’écriture d’achat.

Résultat attendu : Achat 10000 HT+2000 TVA=12000 TTC ; numéro attribué DOC649-2026-001 à noter ; référence fournisseur FOURN-DOC649 conservée.

Écritures attendues : BQ : D 5141 = 100000 / C 1111 = 100000. AC : D 6111 = 10000 + D 34552 = 2000 / C 4411 = 12000.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Deux pièces/cinq lignes ; D = C = 11200. Ne pas inventer un paiement à cette étape.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Facture, deux pièces du Journal et leurs références.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-003 — Préparer la capture partielle et son OD

Module : Préparation

Prérequis : RDO-002 ; faits de laboratoire explicitement supposés, ne représentent pas des pièces fiscales réelles.

Données exactes : 19/10/2026, virement VIR-DOC649=5250. Quote-part TTC 6000, TVA 1000. Payeur personne morale privée assujettie ; prestataire personne physique assujettie ; liste B oui ; aucune exclusion après contrôle ; attestation présentée01/09/2026, ATT-FICTIVE-DOC649. RAS-DOC649, compte 4457.

Actions dans l’interface : Depuis Règlements enregistrer5250 sur la facture, en cochant la comptabilisation. Ouvrir Consulter ou déclarer la RAS → RAS TVA guidée. Dans Assistant renseigner les faits ci-dessus et simuler. Renseigner VENTILATION FICTIVE DOC649 : 5000 HT + 1000 TVA = 6000 TTC, référenceRAS-DOC649 et compte 4457. Vérifier l’aperçu, confirmer les pièces supposées du jeu puis préparer la capture. Valider les écritures correspondantes dans Journal.

Résultat attendu : Simulation du cas existant : 750 de retenue,5250 de trésorerie et mois prévu2026-11. Facture encore ouverte 6000. Quatre pièces/neuf lignes au total ; banque 94750.

Écritures attendues : BQ : D 4411 = 5250 / C 5141 = 5250. OD : D 4411 = 750 / C 4457 = 750. D = C = 118000 cumulés.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Retenue 750 distincte du virement5250. Dossier et OD conservés ; aucun versement fiscal enregistré.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Aperçu, dossier RAS, deux écritures et reste6000.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-004 — Joindre et relire le premier document

Module : Documents RAS

Prérequis : RDO-003. Utiliser DOCUMENT_FICTIF_649.pdf fourni, marqué essai uniquement.

Données exactes : Registre année 2026 ou préparation novembre 2026 ; capture RAS-DOC649 ; OD de capture créée en RDO-003.

Actions dans l’interface : Dans Déclaration TVA ouvrir le registre 2026 et la capture, puis Documents liés aux OD. Dans Capture · OD, cliquer Joindre un fichier et choisir le PDF fourni. Attendre son apparition sans F5. Cliquer Télécharger et ouvrir le document reçu.

Résultat attendu : Un fichier apparaît avec suffixe attribué. Sa référence documentaire et sa date sont visibles. Le PDF conserve la mention fictive. La référence d’attestation du dossier n’est pas remplacée par ce fichier.

Écritures attendues : Aucune écriture nouvelle ;4 pièces/9 lignes et D = C = 118000 inchangés.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Montants, OD et dossier099 d’origine inchangés. Fichier de la bonne société et bonne OD.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Capture avant/après et PDF téléchargé.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-005 — Conserver deux fichiers homonymes

Module : Documents RAS

Prérequis : RDO-004.

Données exactes : DOCUMENT_FICTIF_649.pdf envoyé une seconde fois sur la même OD.

Actions dans l’interface : Cliquer à nouveau Joindre un fichier dans la même section et sélectionner le même PDF. Attendre l’envoi ; relire les deux noms puis télécharger chacun.

Résultat attendu : Deux noms physiques distincts avec suffixes ; aucun écrasement. Deux compléments et deux fichiers sur l’OD de capture.

Écritures attendues : Aucune écriture ; invariants RDO-003 conservés.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Deux fichiers, contenus égaux à l’original fictif ; aucun bouton de suppression dans cet écran RAS.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Liste des deux fichiers et deux téléchargements.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-006 — Ajouter une référence sans fichier

Module : Documents RAS

Prérequis : RDO-005. Administrateur ou comptable.

Données exactes : RéférenceCOMP-DOC649 ; date19/10/2026 ; motif Complément documentaire fictif DOC649.

Actions dans l’interface : Ouvrir Journal → Justificatifs sur l’OD de capture. Ajouter la référence, sa date et le motif. Revenir au registre et cliquer Actualiser le registre, puis Documents liés aux OD.

Résultat attendu : Trois compléments sur l’OD : deux fichiers et une référence sans fichier. COMP-DOC649 n’est pas présenté comme un fichier ou un versement.

Écritures attendues : Aucune nouvelle écriture. La priorité de référence FEC suit le fonctionnement existant du Journal.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Référence sans fichier explicite, dates et référence d’origine conservées.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Historique Journal et section documentaire du registre.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-007 — Contrôler les trois exports actifs

Module : Documents RAS

Prérequis : RDO-006 ; logo de test facultatif dans Paramètres, jamais une marque réelle non autorisée.

Données exactes : Registre 2026 et préparation2026-11 ; deux fichiers et COMP-DOC649.

Actions dans l’interface : Exporter CSV, Excel et PDF du registre. Ouvrir la préparation mensuelle novembre et exporter les mêmes formats. Lire Documents liés. Vérifier la phase Capture, l’OD, les dates et les deux noms. Si une vue ancienne est refusée après un ajout, utiliser son bouton Actualiser puis retélécharger.

Résultat attendu : Trois lignes documentaires dans chaque export ; section/feuille distincte. Montants750 actifs,750 OD validée, aucun montant annulé. Logo présent dans PDF/Excel si configuré. Aucun fichier binaire embarqué.

Écritures attendues : Toujours4 pièces/9 lignes, D = C = 118000 ; aucun export ne crée de mouvement.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Le hash décrit les données/métadonnées, pas les octets des documents ; aucun bordereau officiel supposé.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Six exports et contrôle des trois lignes documentaires.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-008 — Annuler et documenter la contrepassation

Module : Documents RAS

Prérequis : RDO-007 ; même règlement 5250, aucun lettrage effectué.

Données exactes : Annulation 19/10/2026 ; motif ANNULATION FICTIVE DOC649 POUR RECETTE. PDF fictif fourni à joindre à l’OD de contrepassation.

Actions dans l’interface : Dans Règlements annuler VIR-DOC649 avec date/motif ci-dessus. Valider les nouvelles écritures dans Journal. Actualiser le registre et déplier Documents liés aux OD : noter la nouvelle OD de contrepassation. Joindre le PDF dans cette section distincte. Exporter à nouveau. Dans Comptabilité → Liasse fiscale, exercice 2026, contrôler Bilan et CPC ; exporter le FEC 2026 depuis Journal.

Résultat attendu : Capture annulée, données et documents d’origine conservés ; trois compléments côté Capture et un côté Contrepassation. Reste facture 12000 ; banque 100000 ; compte 4457 soldé. Registre : 750 saisis/750 annulés,0 actif. Six pièces/treize lignes ; bilan 102000 ; résultat avant impôt −10000.

Écritures attendues : BQ inverse : D 5141 = 5250 / C 4411 = 5250. OD inverse : D 4457 = 750 / C 4411 = 750. Cumul D = C = 124000.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Aucune suppression/remplacement des lignes initiales. FEC 13 lignes D = C = 124000 ; aucune déduction fiscale automatique due à l’annulation.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Deux contrepassations, documents par OD, soldes, FEC, bilan/CPC.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-009 — Consulter avec le rôle lecture

Module : Contrôles

Prérequis : RDO-008 et utilisateurlecture649 créé.

Données exactes : lecture649@example.com / DocumentsRecette649!.

Actions dans l’interface : Se déconnecter puis se connecter en consultation seule. Ouvrir registre 2026 et préparationnovembre. Ouvrir la capture et les deux OD. Télécharger une pièce de chaque OD puis un export.

Résultat attendu : Références et fichiers lisibles ; aucun bouton Joindre un fichier ni Supprimer ; montants et documents inchangés.

Écritures attendues : Aucune écriture.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Ne pas confondre consultation avec permission d’écriture ; exporter ne qualifie pas les pièces.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Captures lecture et deux documents reçus.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-010 — Vérifier la séparation des sociétés

Module : Contrôles

Prérequis : RDO-009 ; revenir à l’administrateur. Société secondaire de test vide à créer.

Données exactes : TEMOIN DOC649 SARL, aucun mouvement ni capture.

Actions dans l’interface : Depuis Paramètres créer la seconde société. La sélectionner dans l’en-tête. Ouvrir le registre 2026. Revenir à SOCIETE FICTIVE DOC649 SARL puis à son registre.

Résultat attendu : Aucune capture/document de la première société dans le témoin. Au retour, les pièces du scénario sont retrouvées sans duplication.

Écritures attendues : Aucune écriture créée par le changement de société.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Nom de société visible et aucune ancienne liste réaffichée dans le témoin.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Deux captures d’écran nom de société et registre.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-011 — Refuser un règlement au sous-centime

Module : Contrôles

Prérequis : RDO-010, première société active, administrateur.

Données exactes : Montant0,005 MAD sur la facture encore ouverte 12000 ; référenceREFUS-DOC649.

Actions dans l’interface : Tenter d’enregistrer un règlement de 0,005. Lire le message, fermer le formulaire et vérifier facture, règlements et Journal. Ne pas remplacer la valeur pour forcer le passage.

Résultat attendu : Montant refusé au centime. Aucun règlement, document ou mouvement créé ; soldes finaux RDO-008 conservés.

Écritures attendues : Aucune écriture ;6 pièces/13 lignes D = C = 124000.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Pas d’arrondi implicite à0,01 ni modification de la facture.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Message de refus et contrôle du Journal.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## RDO-012 — Afficher un refus de lecture sans faux vide

Module : Contrôles

Prérequis : RDO-011 ; deux sessions distinctes en environnement de test.

Données exactes : SessionA : compta649@example.com ; sessionB : administrateur docs649@example.com.

Actions dans l’interface : Dans A, ouvrir les fichiers de la capture et attendre leur chargement. Dans B, désactiver seulement le compte compta649 fictif. Dans A, cliquer Actualiser les pièces jointes ; constater le refus. Dans B, réactiver le compte. Reconnecter A et relire les documents.

Résultat attendu : Refus explicite, jamais Aucune pièce jointe à la place d’une erreur. Après reconnexion, tous les fichiers sont retrouvés ; aucun faux PDF téléchargé.

Écritures attendues : Aucune écriture ni suppression documentaire.

Impacts fiscaux : Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.

Contrôles : Ne pas désactiver un compte réel. Vérifier la conservation des trois fichiers et des quatre compléments.

Statut humain : Non testé

Résultat réel : À renseigner par la personne chargée de la recette.

Anomalies constatées : À renseigner par la personne chargée de la recette.

Preuve attendue : Message, réactivation et liste retrouvée.

Preuves réelles : À renseigner par la personne chargée de la recette.

Observations : Recette humaine à effectuer ; utiliser exclusivement la société fictive.

## Limites et reprise

Développement de ce complément disponible ; tests automatisés qualifiés séparément ; recette utilisateur et production non validées.

RDO-L01 — Bloqué — Déclaration/justificatifs officiels, imputation et reversement : Obtenir les spécifications applicables ; cet ajout documentaire ne les réalise pas.

RDO-L02 — Non testé — Recette humaine et mise en production : Attendre le retour utilisateur ; aucun résultat humain ou déploiement prévalidé.

Mode d’emploi : docs/RAS_DOCUMENTS_647.md. Rapports : Test/rapport_ras_documents647.md et Test/rapport_coherence_scenario653.md. Sources : docs/audit/SOURCES_SCENARIO_RAS_20261019_653.md. Ne pas réappliquer les lots645/647 ; utiliser cette révision des documents649.
