# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

## Annexe corrections ciblées

Complément ciblé du 9 octobre 2026 aux 218 cas du cahier annuel et aux annexes commerciale, GRH et bilan. Huit cas Non testé ; aucun résultat utilisateur prévalidé. Utiliser exclusivement un environnement de recette isolé et les quatre sociétés fictives ci-dessous, sans ajouter leurs mouvements au scénario annuel. TVA 20 % et déductibilité 80 % sont des données explicites de laboratoire : aucune règle légale nouvelle, certification, déclaration déposée ou conformité réglementaire automatiquement validée.

## Jeu de données

- **Installation** : Installer les lots 268, 269, 270, 273, 274 et 275 en recette isolée. Administrateur ; créer chaque société selon le parcours Administration du cahier annuel. Premier exercice 2026, ouvert du 01/01/2026 au 31/12/2026. Aucune donnée réelle ni identifiant légal inventé. Vérifier que les comptes des cas sont actifs. Si une version/champ requis manque, noter Bloqué et son motif.
- **Société Articles** : ANNEXE ARTICLES FICTIVE ; REC277-SERV, désignation Service frais fictifs, type Service / frais (non stockable), unité unité, prix achat HT 8,00, prix vente HT 10,00, TVA proposée 20 %, stock initial 0. Emballage HT par unité 2,50 ; transport HT par unité 7,25.
- **Société Libellés** : ANNEXE LIBELLES FICTIVE, sans facture initiale ; client CLIENT LIBELLE 277, type Client, délai 30 jours. Préfixe FA, modèle Facture de vente FA° {numero} {tiers}. Trois factures vente du 15/03/2026, références REF-INITIAL, REF-PREFIXE, REF-MODELE. Chaque ligne : Prestation fictive, quantité 1, PU HT 100, TVA 20 %, compte vente 7111. Remises/frais/escompte/RAS zéro.
- **Société Achats** : ANNEXE ACHATS FICTIVE ; fournisseur FOURNISSEUR TVA 277, type Fournisseur, délai 30 jours. Deux factures achat distinctes du 15/03/2026, références ACH80-277 et ACH0-277. Ligne Achat fictif, quantité 1, PU HT 1 000, TVA 20 %, compte achat 6111 ; remises/frais/escompte/RAS zéro. Ne comptabiliser qu’après édition du brouillon selon son cas.
- **Société Banque** : ANNEXE BANQUE FICTIVE, sans autre opération. Journal BQ : 05/01/2026, référence CAPITAL-277, libellé Capital fictif, débit 5141 = 1 000,00 et crédit 1111 = 1 000,00. Puis 15/03/2026, référence CHARGE-277, libellé Charge fictive mars, débit 6111 = 200,00 et crédit 5141 = 200,00. Enregistrer et Valider chacune. Ces mouvements fictifs sans facture/TVA servent uniquement au filtre et aux soldes ; ils ne qualifient pas une charge réelle.
- **Relevé Banque** : Même société Banque, compte 5141, période 01/03/2026–31/03/2026 ; solde initial déclaré 1 000,00, final déclaré 800,00. Une opération de relevé du 15/03/2026, libellé CHARGE RELEVE 277, sens débit, montant positif 200,00. La saisie manuelle du relevé n’expose pas de champ référence séparé. Le débit du relevé correspond au crédit du compte 5141. Aucun document bancaire authentique.
- **Limites** : Pas de report automatique des frais article dans la facture : leur saisie éventuelle sur un document et sa qualification restent explicites. Ne pas fabriquer de JSON, de SQL ou d’historique NaN. Le retard HTTP déterministe nécessite un opérateur de laboratoire ; il est couvert par les tests développeur liés, pas demandé au lecteur de ce cahier. Si ce contrôle technique est exigé sans opérateur, le déclarer Bloqué, sans prévalider la course réseau.

## COR-277-01 — Créer un service avec frais facultatifs

**module** : Articles

**prerequis** : Installation faite ; société Articles vierge.

**donnees** : ANNEXE ARTICLES FICTIVE ; REC277-SERV, désignation Service frais fictifs, type Service / frais (non stockable), unité unité, prix achat HT 8,00, prix vente HT 10,00, TVA proposée 20 %, stock initial 0. Emballage HT par unité 2,50 ; transport HT par unité 7,25.

**actions** : Facturation → Articles → Nouvel article. Saisir Code REC277-SERV, Désignation Service frais fictifs, Prix achat HT 8, Prix vente HT 10, TVA proposée 20 %, Unité unité. Choisir Service / frais. Dans Emballage & transport, saisir Emballage HT par unité 2,50 et Transport HT par unité 7,25. Cliquer Créer l’article ; rouvrir Modifier cet article.

**attendu** : Frais 2,50/7,25 conservés après réouverture ; service non stockable. Somme indicative par unité 9,75. Aucun report automatique dans une facture attendu.

**ecritures** : Aucune écriture ni mouvement de stock.

**fiscal** : Aucune nouvelle règle fiscale ni déclaration. Une proposition de TVA ne justifie pas le régime d’une opération réelle.

**controles** : Vérifier société/exercice ; comparer avant/après et conserver les références. Ne pas modifier une pièce définitive. Si un prérequis manque, statut Bloqué et motif.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Captures création/réouverture, code et frais ; journal avant/après.

**observations** : À renseigner pendant la recette.

**Sources de mise en œuvre** : [src/pages/Articles.jsx](../../src/pages/Articles.jsx), [Test/test_e2e_articles_frais_isole.py](../../Test/test_e2e_articles_frais_isole.py), [Test/test_articles_nombres_finis.py](../../Test/test_articles_nombres_finis.py)

## COR-277-02 — Modifier les frais puis les laisser vides

**module** : Articles

**prerequis** : COR-277-01 effectué ; même service.

**donnees** : Emballage 3,75 ; transport 8,50, puis les deux champs vides.

**actions** : Articles → Modifier REC277-SERV. Remplacer les frais par 3,75 et 8,50, Enregistrer les modifications. Rouvrir et vérifier. Effacer ensuite les deux champs facultatifs, enregistrer et rouvrir.

**attendu** : Première sauvegarde 3,75/8,50 (somme par unité 12,25). Deuxième sauvegarde zéro/zéro. Prix 8/10, code et type inchangés.

**ecritures** : Aucune écriture ni mouvement de stock.

**fiscal** : Aucune nouvelle règle fiscale ni déclaration. Une proposition de TVA ne justifie pas le régime d’une opération réelle.

**controles** : Vérifier société/exercice ; comparer avant/après et conserver les références. Ne pas modifier une pièce définitive. Si un prérequis manque, statut Bloqué et motif.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Captures de chaque sauvegarde et réouverture.

**observations** : À renseigner pendant la recette.

**Sources de mise en œuvre** : [src/pages/Articles.jsx](../../src/pages/Articles.jsx), [Test/test_e2e_articles_frais_isole.py](../../Test/test_e2e_articles_frais_isole.py), [Test/test_articles_nombres_finis.py](../../Test/test_articles_nombres_finis.py)

## COR-277-03 — Refuser un montant négatif ou non fini

**module** : Articles

**prerequis** : COR-277-02 effectué ; frais connus à zéro.

**donnees** : Emballage -1 ; ensuite transport 1e309.

**actions** : Modifier le service, saisir -1 dans Emballage HT par unité et tenter Enregistrer les modifications ; noter le refus. Remettre zéro. Taper 1e309 dans Transport HT par unité et tenter d’enregistrer. Si le navigateur refuse les caractères ou signale une saisie invalide, noter ce refus natif sans contourner le champ. Annuler puis rouvrir.

**attendu** : Aucune sauvegarde d’une valeur négative/non finie. Refus applicatif ou natif visible. Après réouverture frais zéro, prix8/10 et type inchangés. Ce parcours ne prouve pas l’injection JSON NaN, réservée aux tests API.

**ecritures** : Aucune écriture ni mouvement de stock.

**fiscal** : Aucune nouvelle règle fiscale ni déclaration. Une proposition de TVA ne justifie pas le régime d’une opération réelle.

**controles** : Vérifier société/exercice ; comparer avant/après et conserver les références. Ne pas modifier une pièce définitive. Si un prérequis manque, statut Bloqué et motif.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Message/champ invalide, navigateur utilisé et réouverture.

**observations** : À renseigner pendant la recette.

**Sources de mise en œuvre** : [src/pages/Articles.jsx](../../src/pages/Articles.jsx), [Test/test_e2e_articles_frais_isole.py](../../Test/test_e2e_articles_frais_isole.py), [Test/test_articles_nombres_finis.py](../../Test/test_articles_nombres_finis.py)

## COR-277-04 — Distinguer préfixe et modèle de libellé

**module** : Paramètres

**prerequis** : Installation faite ; société Libellés vierge ; client créé.

**donnees** : ANNEXE LIBELLES FICTIVE, sans facture initiale ; client CLIENT LIBELLE 277, type Client, délai 30 jours. Préfixe FA, modèle Facture de vente FA° {numero} {tiers}. Trois factures vente du 15/03/2026, références REF-INITIAL, REF-PREFIXE, REF-MODELE. Chaque ligne : Prestation fictive, quantité 1, PU HT 100, TVA 20 %, compte vente 7111. Remises/frais/escompte/RAS zéro.

**actions** : Fiche société : préfixe FA, Enregistrer. Fiscalité : modèle FA° {numero} {tiers}, Enregistrer directement. Créer REF-INITIAL avec sa ligne, Valider puis Comptabiliser et valider l’écriture. En Fiche société remplacer Préfixe Factures par VTE ; avant sauvegarde ouvrir Fiscalité et observer Aperçu (exemple), revenir Fiche société et enregistrer. Créer/valider/comptabiliser REF-PREFIXE. Fiscalité : saisir VENTE {numero} / {tiers} / {ref} / {date}, Enregistrer directement ; créer/valider/comptabiliser REF-MODELE. Valider chacune des écritures. Journal → Exporter CSV, ouvrir colonne Libellé écriture. En Fiscalité changer ensuite le modèle en NOUVEAU {numero}, enregistrer, relire les trois pièces et réexporter.

**attendu** : Numéros FA-2026-001, VTE-2026-002, VTE-2026-003. Exemple VTE-2026-014 sans réservation. REF-PREFIXE garde FA° littéral ; troisième titre VENTE VTE-2026-003 / CLIENT LIBELLE 277 / REF-MODELE / 15/03/2026. Anciens titres et CSV inchangés après le dernier réglage. Chaque facture HT100/TVA20/TTC120.

**ecritures** : Chaque facture : débit3421 client fictif120 ; crédit7111=100, 4455=20. Débit=crédit120. Réglages : aucune écriture supplémentaire.

**fiscal** : Aucune nouvelle règle fiscale ni déclaration. Une proposition de TVA ne justifie pas le régime d’une opération réelle.

**controles** : Vérifier société/exercice ; comparer avant/après et conserver les références. Ne pas modifier une pièce définitive. Si un prérequis manque, statut Bloqué et motif.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Aperçu, sauvegarde Fiscalité, numéros, écritures et deux CSV ouverts avant/après.

**observations** : À renseigner pendant la recette.

**Sources de mise en œuvre** : [src/pages/Parametres.jsx](../../src/pages/Parametres.jsx), [Test/test_e2e_facture_libelle_parametres_isole.py](../../Test/test_e2e_facture_libelle_parametres_isole.py)

## COR-277-05 — Éditer un achat courant à 80 %

**module** : Achats

**prerequis** : Installation faite ; société Achats, fournisseur créé ; facture ACH80-277 distincte en brouillon sans comptabilisation.

**donnees** : ANNEXE ACHATS FICTIVE ; fournisseur FOURNISSEUR TVA 277, type Fournisseur, délai 30 jours. Deux factures achat distinctes du 15/03/2026, références ACH80-277 et ACH0-277. Ligne Achat fictif, quantité 1, PU HT 1 000, TVA 20 %, compte achat 6111 ; remises/frais/escompte/RAS zéro. Ne comptabiliser qu’après édition du brouillon selon son cas. Utiliser ACH80-277 seulement.

**actions** : Factures → Achats : créer une facture, N° facture fournisseur ACH80-277, ligne 1 × 1 000 HT, TVA 20 %, compte 6111, date 15/03/2026. Enregistrer sans validation. Modifier le brouillon ; TVA de l’achat : Qualification TVA de l’achat = Charge / achat courant, TVA déductible (%) = 80. Enregistrer les modifications, rouvrir et vérifier. Valider définitivement puis utiliser Générer l’écriture comptable de cette facture ; ouvrir l’écriture dans Journal, contrôler et Valider.

**attendu** : Choix charge/80 conservé après réouverture ; HT 1 000 / TVA 200 / TTC 1 200. Charge 1 040 (= 1 000 + 40 non récupérables) ; TVA déductible 160.

**ecritures** : Débit 6111 = 1 040 ; débit 34552 = 160 ; crédit 4411 = 1 200, fournisseur fictif associé. Débit = crédit 1 200.

**fiscal** : TVA documentaire 200,00 ; part déductible selon le choix explicite du cas. Aucun droit légal à déduction ni dépôt validé.

**controles** : Vérifier société/exercice ; comparer avant/après et conserver les références. Ne pas modifier une pièce définitive. Si un prérequis manque, statut Bloqué et motif.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Captures choix80, réouverture et écriture avec auxiliaire fournisseur.

**observations** : À renseigner pendant la recette.

**Sources de mise en œuvre** : [src/pages/Factures.jsx](../../src/pages/Factures.jsx), [Test/test_e2e_facture_achat_tva_edition_isole.py](../../Test/test_e2e_facture_achat_tva_edition_isole.py)

## COR-277-06 — Éditer un autre achat non déductible

**module** : Achats

**prerequis** : Même société que COR-277-05 ; nouvelle facture distincte ACH0-277 en brouillon, sans comptabilisation.

**donnees** : ANNEXE ACHATS FICTIVE ; fournisseur FOURNISSEUR TVA 277, type Fournisseur, délai 30 jours. Deux factures achat distinctes du 15/03/2026, références ACH80-277 et ACH0-277. Ligne Achat fictif, quantité 1, PU HT 1 000, TVA 20 %, compte achat 6111 ; remises/frais/escompte/RAS zéro. Ne comptabiliser qu’après édition du brouillon selon son cas. Utiliser ACH0-277 seulement.

**actions** : Créer une autre facture avec N° facture fournisseur ACH0-277 et les mêmes montants sans validation. Modifier le brouillon ; Qualification TVA de l’achat = TVA non déductible. Vérifier TVA déductible (%) = 0 et champ désactivé. Enregistrer les modifications, rouvrir, vérifier puis Valider définitivement et Générer l’écriture comptable de cette facture. Contrôler et valider son écriture ; relire ACH80-277 sans la modifier.

**attendu** : Non déductible/0 conservé. HT 1 000 / TVA 200 / TTC 1 200 ; charge 1 200, TVA récupérable 0. ACH80-277 inchangée.

**ecritures** : Débit 6111 = 1 200 ; crédit 4411 = 1 200. Aucune ligne 34552 avec débit positif. Débit = crédit 1 200.

**fiscal** : TVA documentaire 200,00 ; part déductible selon le choix explicite du cas. Aucun droit légal à déduction ni dépôt validé.

**controles** : Vérifier société/exercice ; comparer avant/après et conserver les références. Ne pas modifier une pièce définitive. Si un prérequis manque, statut Bloqué et motif.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Captures zéro/champ désactivé, écriture et précédente facture inchangée.

**observations** : À renseigner pendant la recette.

**Sources de mise en œuvre** : [src/pages/Factures.jsx](../../src/pages/Factures.jsx), [Test/test_e2e_facture_achat_tva_edition_isole.py](../../Test/test_e2e_facture_achat_tva_edition_isole.py)

## COR-277-07 — Filtrer mars avec solde d’ouverture

**module** : Comptabilité

**prerequis** : Installation faite ; société Banque ; saisir et valider uniquement les deux écritures du Jeu.

**donnees** : ANNEXE BANQUE FICTIVE, sans autre opération. Journal BQ : 05/01/2026, référence CAPITAL-277, libellé Capital fictif, débit 5141 = 1 000,00 et crédit 1111 = 1 000,00. Puis 15/03/2026, référence CHARGE-277, libellé Charge fictive mars, débit 6111 = 200,00 et crédit 5141 = 200,00. Enregistrer et Valider chacune. Ces mouvements fictifs sans facture/TVA servent uniquement au filtre et aux soldes ; ils ne qualifient pas une charge réelle.

**actions** : Comptabilité → Grand livre, exercice 2026. Du = 01/03/2026, Au = 31/03/2026. Lire la ligne 5141 et ouvrir son détail. Exporter CSV, ouvrir et comparer lignes/soldes. Attendre la fin du chargement, vérifier les dates. Un rechargement complet n’est pas tenu de conserver un filtre local : ressaisir mars après rechargement.

**attendu** : 5141 : initial débiteur 1 000 ; mouvement débit 0, crédit 200 ; final débiteur 800. Seule ligne mars CHARGE-277 ; CAPITAL-277 pris dans l’ouverture, pas comme mouvement de mars. CSV cohérent. Réponse de chargement tardive ne remplace pas les dates déjà saisies.

**ecritures** : Seulement les deux écritures initiales ; consultation/export sans ajout ni réécriture.

**fiscal** : Aucune nouvelle règle fiscale ni déclaration. Une proposition de TVA ne justifie pas le régime d’une opération réelle.

**controles** : Vérifier société/exercice ; comparer avant/après et conserver les références. Ne pas modifier une pièce définitive. Si un prérequis manque, statut Bloqué et motif.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Écritures, dates, tableau/détail5141 et CSV. Retard HTTP déterministe réservé au laboratoire.

**observations** : À renseigner pendant la recette.

**Sources de mise en œuvre** : [src/pages/GrandLivre.jsx](../../src/pages/GrandLivre.jsx), [Test/test_e2e_grandlivre_dates_contexte_isole.py](../../Test/test_e2e_grandlivre_dates_contexte_isole.py)

## COR-277-08 — Conserver période et soldes du rapprochement

**module** : Banques

**prerequis** : COR-277-07 effectué ; même société Banque, aucun autre relevé.

**donnees** : Même société Banque, compte 5141, période 01/03/2026–31/03/2026 ; solde initial déclaré 1 000,00, final déclaré 800,00. Une opération de relevé du 15/03/2026, libellé CHARGE RELEVE 277, sens débit, montant positif 200,00. La saisie manuelle du relevé n’expose pas de champ référence séparé. Le débit du relevé correspond au crédit du compte 5141. Aucun document bancaire authentique.

**actions** : Comptabilité → Rapprochement bancaire. Compte 5141 ; Du = 01/03/2026, Au = 31/03/2026. Saisir solde initial 1 000, quitter ce champ et attendre le message « Soldes du relevé enregistrés. ». Ensuite saisir solde final 800, quitter ce champ et attendre à nouveau ce message avant d’ajouter une opération. Dans Relevé bancaire, saisir date 15/03/2026, Libellé… CHARGE RELEVE 277, Montant 200, sens Débit ; cliquer le bouton + Ajouter l’opération. Vérifier les KPI et mouvement du 15/03. Dans Écriture comptable associée de cette ligne, sélectionner le mouvement crédit 5141 = 200 du 15/03 proposé. Si absent, noter l’anomalie sans créer une autre écriture. Vérifier dates et soldes après chargements ; comparer Journal avant/après.

**attendu** : Solde comptable au 31/03 = 800 ; bancaire déclaré 800 ; final calculé 1 000 − 200 = 800 ; écart 0. Seul mouvement mars crédit 200. Une réponse antérieure concernant une autre période, société ou compte ne remplace pas le contexte mars ni ses soldes sauvegardés. Ce cas ne garantit pas la préservation d’une saisie non sauvegardée contre une réponse de lecture de la même portée. Le rapprochement relie les lignes sans créer une charge.

**ecritures** : Aucune nouvelle écriture ; rapprochement technique. Capital et charge définitifs intacts.

**fiscal** : Aucune nouvelle règle fiscale ni déclaration. Une proposition de TVA ne justifie pas le régime d’une opération réelle.

**controles** : Vérifier société/exercice ; comparer avant/après et conserver les références. Ne pas modifier une pièce définitive. Si un prérequis manque, statut Bloqué et motif.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Paramètres, KPI et lien rapproché ; journal avant/après. Sans opérateur, ne pas prétendre avoir reproduit une course HTTP déterministe.

**observations** : À renseigner pendant la recette.

**Sources de mise en œuvre** : [src/pages/RapprochementBancaire.jsx](../../src/pages/RapprochementBancaire.jsx), [Test/test_e2e_rapprochement_dates_contexte_isole.py](../../Test/test_e2e_rapprochement_dates_contexte_isole.py)
