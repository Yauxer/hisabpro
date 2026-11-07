# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Version 1 du 19 octobre 2026

Annexe — Sociétés liées et factures correspondantes 633/635

Recette utilisateur à effectuer. Tous les cas sont Non testé. Ce complément ne remplace pas le cahier annuel général.

Sociétés, opérations et identifiants de recette fictifs. Aucun dépôt, conformité officielle ou mise en production validé.

## Préparer le jeu de données

| Objet | Société A | Société B | Valeur / consigne |

|---|---|---|---|

| Société | ATLAS SERVICES RECETTE639 SARL | RIF CONSEIL RECETTE639 SARL | Dossiers vierges, créés pour la recette uniquement |

| Administrateur | groupe639@example.com | Même utilisateur, administrateur secondaire | Mot de passe fictif : RecetteGroupe639! |

| Exercice | 2026 | 2026 | 01/01/2026 au31/12/2026, périodes ouvertes |

| Société / comptabilité | SARL, MAD | SARL, MAD | Capital social 10000 MAD chacune ; régime fiscal IS |

| Préfixe Factures | ATLAS | RIF | À paramétrer avant la première facture ; numéros attribués à validation |

| Tiers | Client : RIF CONSEIL RECETTE639 SARL | Fournisseur : ATLAS SERVICES RECETTE639 SARL | Comptes collectifs3421 et4411 ; codes auxiliaires générés |

| Article | REC639-V : Prestation étude recette639 | REC639-A : Étude achetée recette639 | Services non stockables ; prix 100 ; vente71243 / achat6111 |

| TVA de laboratoire | Encaissement, taux20% | Encaissement, achat Charge, déduction 100% | Prorata annuel100% ; hypothèses du scénario, pas qualification fiscale |

| Logo | LOGO_RECETTE_FICTIF.png | LOGO_RECETTE_FICTIF.png | Fichier fourni dans docs/recette/images |

Liaison A → B : Relation commerciale fictive de recette639 vérifiée dans les deux sociétés.

Facture datée du19/10/2026, délai 60 jours et échéance18/12/2026. Deux lignes : Lot A recette639 (2×100 MAD) et Lot B recette639 (3×100 MAD), taux20%, aucune remise, frais ou RAS.

Capitaux le02/01/2026 : CAP-A-639 etCAP-B-639. Deux virements séparés le19/10/2026 : VIR-A-639 etVIR-B-639, chacun600 MAD. Lecteur : lecteur639@example.com / RecetteLecture639!.

ICE/IF/RC laissés vides : conserver les avertissements de mentions incomplètes. Ne jamais inventer des mentions pour obtenir un document utilisable en production.

## Calculs indépendants attendus

Calcul en centimes entiers, sans appel aux services comptables de l’application.

Deux lots :2×100+3×100=500HT ; TVA 20%=100 ; TTC 600. Capital 10000 par société. Aucun stock, remise, frais, RAS ou impôt dans le parcours principal.

| Société | Banque finale MAD | Résultat avant impôt MAD | Actif = passif MAD |

|---|---|---|---|

| A | 10600.00 | 500.00 | 10600.00 |

| B | 9400.00 | -500.00 | 9500.00 |

Dans chacune :3 pièces,7 lignes, débit=crédit 11200.00 MAD. A : TVA facturée100, client 0. B : TVA récupérable100, fournisseur 0.

Les paiements sont saisis et justifiés séparément dans les deux sociétés ; aucune compensation ou consolidation fiscale présumée. Les variantes utilisent d’autres dossiers.

## GRP-001 — Créer les deux sociétés depuis une installation isolée vierge

Module : Préparation

Objectif : Créer les deux sociétés depuis une installation isolée vierge

Prérequis : Technicien : installation102 préparée et sauvegarde de référence ; aucune base réelle.

Données exactes : Admin groupe639@example.com / RecetteGroupe639! ; sociétés A et B : noms exacts dans le jeu de données.

Actions dans l’interface : Sur l’inscription, créer A avec cet administrateur. Se connecter. Dans le sélecteur de société, Nouvelle société : créer B. Revenir à A puis vérifier que le sélecteur donne accès aux deux.

Résultat attendu : Deux sociétés distinctes, administrateur dans chacune, aucune facture ni écriture. Ne pas réutiliser un dossier existant.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-002 — Configurer calendriers, préfixes et hypothèses du laboratoire

Module : Préparation

Objectif : Configurer calendriers, préfixes et hypothèses du laboratoire

Prérequis : GRP-001 réussi.

Données exactes : 2026 : 01/01→31/12 ; MAD ; SARL ; capital social 10000,00 chacune ; IS ; TVA encaissement ; prorata 100% ; préfixes ATLAS et RIF ; logo de recette fourni.

Actions dans l’interface : Dans chaque société : Paramètres → Fiche société, renseigner les valeurs et Préfixe Factures. Charger le logo fourni et enregistrer. Vérifier Exercices 2026 et ses périodes ouvertes. Déclaration TVA : sélectionner 2026, conserver Prorata annuel de déduction 100% et enregistrer.

Résultat attendu : Réglages séparés. Le capital social déclaré ne crée pas à lui seul une écriture. Numéros définitifs attribués à la validation.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : 20% et100% sont des hypothèses de laboratoire ; ne pas les assimiler à un droit fiscal réel.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : ICE/IF/RC restent volontairement vides ; conserver les avertissements, ne pas inventer de mentions légales ni déposer ces documents.

## GRP-003 — Créer les tiers qui représentent chaque société

Module : Préparation

Objectif : Créer les tiers qui représentent chaque société

Prérequis : GRP-002 réussi.

Données exactes : Chez A : client RIF CONSEIL RECETTE639 SARL, compte 3421. Chez B : fournisseur ATLAS SERVICES RECETTE639 SARL, compte 4411. Délai 60 jours, tiers actifs.

Actions dans l’interface : Dans A, Clients/Fournisseurs : créer le client. Basculer B : créer le fournisseur. Conserver les comptes collectifs et les codes auxiliaires générés. Revenir A.

Résultat attendu : Deux tiers propres à leurs sociétés ; aucun identifiant technique réutilisé de l’autre côté.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-004 — Créer les articles non stockables

Module : Préparation

Objectif : Créer les articles non stockables

Prérequis : GRP-003 réussi.

Données exactes : A : REC639-V, Prestation étude recette639, vente71243. B : REC639-A, Étude achetée recette639, achat6111. Prix 100, TVA 20%, non stockables.

Actions dans l’interface : Articles → Nouvel article dans chaque société : saisir code et désignation, désactiver le caractère stockable ; dans les comptes comptables, sélectionner le compte indiqué. Enregistrer puis relire les fiches.

Résultat attendu : Les services sont disponibles sans stock initial ; aucune écriture de stock ou acquisition.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-005 — Enregistrer les deux apports bancaires

Module : Préparation

Objectif : Enregistrer les deux apports bancaires

Prérequis : GRP-004 réussi.

Données exactes : A : CAP-A-639 ; B : CAP-B-639 ; date 02/01/2026 ; montant10000,00 MAD chacune.

Actions dans l’interface : Dans chaque société, Journal → Nouvelle écriture : journalBQ, date 02/01/2026, référence et libellé Apport fictif de recette639. Saisir débit 5141=10000 et crédit 1111=10000, enregistrer puis valider.

Résultat attendu : Une pièce définitive par société, deux lignes, débit=crédit 10000 ; banque 10000.

Écritures attendues : Dans chacune : D5141 Banque 10000 / C1111 Capital social 10000.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Pièces BQ et balances initiales des deux sociétés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-006 — Enregistrer la liaison commerciale explicite

Module : Facturation liée

Objectif : Enregistrer la liaison commerciale explicite

Prérequis : GRP-005 réussi, société activeA.

Données exactes : AcheteurB ; client chez A=RIF CONSEIL RECETTE639 SARL ; fournisseur chez B=ATLAS SERVICES RECETTE639 SARL ; justification du JSON.

Actions dans l’interface : Paramètres → Sociétés liées : choisir B, puis les deux tiers. Saisir la justification exacte, cocher la vérification et Enregistrer la liaison. Relire la ligne active.

Résultat attendu : Liaison active A → B et historique de création ; aucune facture, mouvement ou écriture créée.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-007 — Créer le brouillon de vente

Module : Facturation liée

Objectif : Créer le brouillon de vente

Prérequis : GRP-006 réussi.

Données exactes : A ; date 19/10/2026 ; client B ; deux lignes articleREC639-V : Lot A recette639, qté2×100 ; Lot B recette639, qté3×100 ; TVA 20 ; remises/frais/RAS0 ; délai 60 jours.

Actions dans l’interface : Facturation → Factures → Nouvelle facture de vente. Renseigner le client et les deux lignes ; choisir Enregistrer le brouillon. Vérifier les totaux et l’échéance18/12/2026.

Résultat attendu : Brouillon sans numéro définitif : HT 500,00, TVA 100,00, TTC 600,00 ; aucun Journal nouveau.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-008 — Valider et comptabiliser la vente chez A

Module : Facturation liée

Objectif : Valider et comptabiliser la vente chez A

Prérequis : GRP-007 réussi.

Données exactes : Facture de600,00 MAD ; numéro attendu ATLAS-2026-001.

Actions dans l’interface : Dans la liste Factures, Valider définitivement le brouillon. Conserver les avertissements de mentions du laboratoire. Générer son écriture comptable, puis au Journal valider ce brouillon. Ouvrir le détail de la vente.

Résultat attendu : Vente définitive et comptabilisée ; A possède deux pièces, banque 10000 et client débiteur600. B ne possède encore que son capital.

Écritures attendues : A : D3421=600 / C71243=500 / C4455=100 ; auxiliaire du client réel.

Impacts fiscaux : TVA facturée100 dans le Journal ; le régime encaissement ne constitue pas à lui seul une déclaration déposée.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-009 — Préparer l’achat et vérifier l’aperçu

Module : Facturation liée

Objectif : Préparer l’achat et vérifier l’aperçu

Prérequis : GRP-008 réussi, détail de la vente dans A.

Données exactes : Liaison A → B ; chaque ligne source vers REC639-A ; nature Charge ; pourcentage propre facture 100%.

Actions dans l’interface : Déplier Correspondance entre sociétés. Choisir B. Associer les deux lignes à REC639-A. Choisir Charge et saisir 100. Cliquer Vérifier le brouillon d’achat sans confirmer la création.

Résultat attendu : Aperçu HT 500, TVA 100, TTC 600, date 19/10/2026 et exercice acheteur 2026 ; fournisseur A. B reste sans nouvelle pièce ni facture.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-010 — Créer le brouillon correspondant chez B

Module : Facturation liée

Objectif : Créer le brouillon correspondant chez B

Prérequis : GRP-009 réussi, aperçu relu.

Données exactes : Mêmes paramètres ; référence fournisseur ATLAS-2026-001.

Actions dans l’interface : Cocher la vérification de la société, articles, montants et TVA ; Créer le brouillon chez l’acheteur. Noter son identifiant et actualiser la correspondance.

Résultat attendu : Un seul achat lié, non validé et non comptabilisé, aucun numéro interne ; référence ATLAS-2026-001. Aucune écriture créée chez B et aucune modification de la venteA.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-011 — Valider et comptabiliser l’achat chez B

Module : Facturation liée

Objectif : Valider et comptabiliser l’achat chez B

Prérequis : GRP-010 réussi.

Données exactes : Achat B 600,00 MAD, numéro interne attendu RIF-2026-001 ; référence fournisseur ATLAS-2026-001.

Actions dans l’interface : Fermer le détail, basculer B. Facturation → Factures → filtre Achats : ouvrir et vérifier le brouillon. Valider définitivement, générer son écriture puis la valider au Journal. Relire le panneau de correspondance.

Résultat attendu : Deux pièces dans B ; achat et écriture propres à B, fournisseur créditeur600, banque 10000. Suivi : deux factures comptabilisées, aucun écart documentaire.

Écritures attendues : B : D6111=500 / D34552=100 / C4411=600 ; auxiliaire du fournisseur réel.

Impacts fiscaux : TVA récupérable100 selon les hypothèses100% du laboratoire ; aucune qualification fiscale réelle ou déclaration validée.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-012 — Payer le fournisseur chez B sans régler silencieusementA

Module : Règlements et lettrage

Objectif : Payer le fournisseur chez B sans régler silencieusementA

Prérequis : GRP-011 réussi.

Données exactes : B ; factureRIF-2026-001 ;19/10/2026 ;600,00 ; Virement ; référence VIR-B-639 ; banque 5141.

Actions dans l’interface : Sur l’achat, Payer le fournisseur : saisir ces valeurs, choisir la comptabilisation et enregistrer. Valider l’écriture de règlement au Journal. Basculer A et consulter la vente sans y saisir de règlement.

Résultat attendu : B : facture payée, dette0, banque 9400. A : vente encore impayée600 tant que son encaissement n’a pas été saisi.

Écritures attendues : B : D4411=600 / C5141=600. A : aucune nouvelle écriture.

Impacts fiscaux : Consulter les impacts du règlement dans chaque dossier, sans transférer automatiquement une déclaration TVA.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-013 — Enregistrer l’encaissement réel dans le dossierA

Module : Règlements et lettrage

Objectif : Enregistrer l’encaissement réel dans le dossierA

Prérequis : GRP-012 réussi.

Données exactes : A ; venteATLAS-2026-001 ;19/10/2026 ;600,00 ; Virement ; référence VIR-A-639 ; banque 5141.

Actions dans l’interface : Sur la vente, Encaisser le client : saisir ces valeurs, choisir la comptabilisation et enregistrer. Au Journal, valider l’écriture de règlement. Revenir dans chaque liste de factures et vérifier Payée.

Résultat attendu : A : banque 10600, client 0. B : banque 9400, fournisseur 0. Trois pièces définitives par société.

Écritures attendues : A : D5141=600 / C3421=600. Le règlement B n’est pas créé une seconde fois.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-014 — Lettrer les deux auxiliaires séparément

Module : Règlements et lettrage

Objectif : Lettrer les deux auxiliaires séparément

Prérequis : GRP-013 réussi, toutes les écritures validées.

Données exactes : A : compte 3421 et client B ; B : compte 4411 et fournisseur A ; deux lignes équilibrées dans chaque sélection.

Actions dans l’interface : Lettrage dans A : choisir3421, client B, cocher la ligne facture 600 au débit et celle du règlement600 au crédit, Lettrer2 lignes. Noter le code généré d’au moins trois lettres. Répéter dans B sur4411 avec les sens opposés.

Résultat attendu : Deux lettrages propres à leurs sociétés, solde0 chacun. Les lignes définitives gardent les mêmes comptes/montants/références.

Écritures attendues : Aucune écriture supplémentaire ; lettrage enregistré hors réécriture des lignes définitives.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-015 — Comparer balances, FEC, CPC, bilans et PDF

Module : Contrôles

Objectif : Comparer balances, FEC, CPC, bilans et PDF

Prérequis : GRP-014 réussi.

Données exactes : Résultats attendus de la feuille Oracle : A banque 10600/résultat+500/bilan 10600 ; B banque 9400/TVA 100/résultat−500/bilan 9500 ; D=C11200 dans chaque Journal.

Actions dans l’interface : Dans chaque société : exporter le FEC2026, la balance et la facture PDF ; ouvrir Liasse fiscale pour bilan/CPC. Comparer compte par compte à l’oracle et aux14 lignes attendues. Relire les références et le logo de chaque PDF. Paramètres → Sociétés liées : déplier Factures de la liaison puis Actualiser les factures liées ; vérifier TTC 600, reste0 et encaissé/payé600 dans chacun des deux dossiers.

Résultat attendu : Trois pièces et sept lignes par société, six pièces/quatorze lignes au total de contrôle. Aucun écart documentaire. PDFA=ATLAS, PDFB=RIF avec référenceATLAS ; aucun logo d’une société tierce.

Écritures attendues : Voir Journal attendu et soldes indépendants ; ne pas transformer le total de contrôle en consolidation fiscale.

Impacts fiscaux : Résultats avant impôt seulement ; pas d’IS/CM/CSS calculé, pas de déclaration ou archivage définitif.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : FEC/PDF/balances et captures CPC/bilan des deux sociétés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-016 — Vérifier un compte de consultation seule

Module : Négatifs

Objectif : Vérifier un compte de consultation seule

Prérequis : GRP-015 réussi ; administrateur prépare un lecteur dans A puis l’invite dans B en lecture.

Données exactes : lecteur639@example.com / RecetteLecture639! ; rôleLecture dans les deux sociétés.

Actions dans l’interface : Paramètres → Utilisateurs : créer le lecteur dans A ; dans B, inviter son email avec rôleLecture. Se déconnecter et se connecter comme lecteur. Ouvrir Sociétés liées et les deux détails de facture.

Résultat attendu : Suivi consultable, aucun formulaire d’association ou de création, aucune commande de retrait ou comptabilisation. Les pièces et soldes du scénario restent identiques.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-017 — Vérifier qu’une vente ne crée pas un second achat

Module : Négatifs

Objectif : Vérifier qu’une vente ne crée pas un second achat

Prérequis : GRP-015 réussi ; se reconnecter administrateur.

Données exactes : VenteATLAS-2026-001 déjà liée à RIF-2026-001.

Actions dans l’interface : Dans A, rouvrir le détail de la vente puis Correspondance entre sociétés. Actualiser, fermer et rouvrir le panneau. Vérifier qu’il affiche l’achat existant sans proposer une nouvelle création. DansB, compter les achats correspondants.

Résultat attendu : Un seul achat ; aucun nouveau numéro, stock ou Journal. Les répétitions réseau avec même clé sont couvertes par les tests techniques635.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-018 — Afficher un écart de brouillon sans modifier une vente définitive

Module : Négatifs

Objectif : Afficher un écart de brouillon sans modifier une vente définitive

Prérequis : Utiliser deux AUTRES sociétés VAR-A 639 et VAR-B 639 ; répéterGRP-001→010 avec préfixesVARA/VARB et tiers aux noms correspondants. Ne pas toucher au scénario principal.

Données exactes : Dans le brouillonVAR-B, prix du Lot A=101 au lieu100 ; quantité2 inchangée ; Lot B 3×100 ; TVA 20%.

Actions dans l’interface : Dans VAR-B, modifier le brouillon d’achat et enregistrer. Rouvrir le détail puis Actualiser la correspondance. Basculer VAR-A et relire la vente d’origine.

Résultat attendu : Achat modifié HT 502, TVA 100,40, TTC 602,40 ; alerte Écarts à vérifier sur les lignes. Vente d’origineHT500/TTC 600 intacte ; aucune écriture d’achat générée.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Variante isolée seulement ; aucune facture définitive n’est réécrite pour faire disparaître le contrôle.

## GRP-019 — Retirer la liaison en conservant les pièces

Module : Contrôles

Objectif : Retirer la liaison en conservant les pièces

Prérequis : Scénario principal GRP-015 terminé, administrateur connectéA.

Données exactes : Liaison A → B ; motif Fin de recette639 — liaison retirée.

Actions dans l’interface : Paramètres → Sociétés liées : Retirer la liaison, saisir ce motif, confirmer. Rouvrir les détails des factures et comparer FEC/Journal/balances aux exportsGRP-015.

Résultat attendu : Liaison retirée avec historique, correspondance conservée, mêmes pièces et montants. Ce retrait ne supprime pas les factures ni les écritures et n’autorise pas une nouvelle copie de la même vente.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Capture de l’écran et référence des documents concernés.

Preuves réelles : À renseigner par le testeur.

Observations : Sociétés fictives uniquement ; résultat humain à renseigner.

## GRP-020 — Vérifier le paquet et le banc d’installation isolé

Module : Technique

Objectif : Vérifier le paquet et le banc d’installation isolé

Prérequis : Technicien, copie de travail isolée ; aucun paramètre de base réelle.

Données exactes : Test/verifier_zip_session.py avec le ZIP cumulatif fourni ; Test/recette_installation_vierge_102.py --rapport .codex-tests/recette639-installation.md.

Actions dans l’interface : Vérifier le manifeste embarqué du ZIP sans extraction. Lancer le CLI102 depuis la racine avec le Python du projet ; lire le rapport et vérifier que son cluster temporaire est supprimé. Ne jamais passer une URL de base ni lancer ces SQL sur le dossier réel pour cette recette.

Résultat attendu : ZIP CRC/SHA/liste valides ;93SQL distincts et29rejeux,80tables, droits limités, cluster supprimé. Ce CLI ne migre pas l’installation active.

Écritures attendues : Aucune écriture créée par cette action.

Impacts fiscaux : Aucune liquidation ou déclaration fiscale dans ce cas.

Contrôles : Vérifier la société active, les montants et l’absence de doublon.

Statut humain : Non testé

Résultat réel : À renseigner par le testeur.

Anomalies constatées : À renseigner par le testeur.

Preuve attendue : Sortie du vérificateur, rapport d’installation et résultat des tests techniques635/637.

Preuves réelles : À renseigner par le testeur.

Observations : Cas technique distinct des actions métier ; aucune validation humaine globale ou production déduite.

## Limites non exécutables et décisions

Les deux limites ci-dessous sont séparées des20cas humains ; ne pas les compter comme des tests réussis.

LIM-639-01 — Bloqué — Consolidation fiscale ou qualification réglementaire du groupe : Hors de ce scénario ; nécessite dossier et textes applicables, aucun résultat déduit.

LIM-639-02 — Bloqué — Synchronisation automatique des règlements/avoirs/livraisons : Non développée ; traiter séparément dans chaque société et conserver les alertes.
