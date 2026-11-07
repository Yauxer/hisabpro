# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

## Capture déclarative et annulation traçable

Annexe autonome : capture explicite, validation, lettrage et annulation d’une retenue déclarée. Deux cas utilisateur Non testé, dans deux sociétés fictives neuves et indépendantes. Installation de recette isolée exclusivement. TVA 20 %, RAS estimée 10 %, montants 30/70 et comptes 3453/4457 sont des choix de laboratoire : aucune obligation ni qualification fiscale automatique, attestation ou crédit IS certifié.

## Jeu de données

- **Activation préalable** : Administrateur d’une copie isolée : suivre le guide MISE_A_JOUR_RAS_20261009.md. Migration 083 manuelle avec le rôle de migration, jamais sur une base réelle dans cette recette. Le lecteur utilisateur n’a pas à exécuter SQL : demander une installation de recette prête. Sans 083, message d’indisponibilité attendu, noter Bloqué sans contourner ni forcer une capture.
- **Date exacte du parcours** : D = date réelle du jour d’exécution de la recette, à noter dans les observations avant de commencer ; exemple 10/10/2026. E = année de D, exemple 2026. Saisir D pour la facture, chacun des deux virements et chacune des deux captures. L’annulation par bouton utilise également le jour courant. Réaliser tout le cas le même jour ; sinon noter Bloqué et préparer des dates cohérentes avant de reprendre, sans réécrire de pièce définitive.
- **Société vente** : Créer ANNEXE CAPTURE VENTE FICTIVE 306 suivant Administration → Sociétés du cahier principal. Exercice E ouvert, du 01/01/E au 31/12/E, aucun autre mouvement ni lettrage. Créer CLIENT CAPTURE 306, compte client 3421. Aucun identifiant fiscal officiel à inventer.
- **Société achat** : Créer séparément ANNEXE CAPTURE ACHAT FICTIVE 306, même exercice E ouvert et vierge. Créer FOURNISSEUR CAPTURE 306, compte fournisseur 4411. Ne pas réutiliser la société vente.
- **Facture** : Date D ; une ligne Service laboratoire capture 306, quantité 1, prix unitaire HT 1 000, TVA 20 %, Taxable. Vente : compte produit 7111. Achat : N° facture fournisseur ACH-CAP306-001, compte 6111, qualification Charge / achat courant, TVA déductible (%) 100. RAS (sur HT) 10 % explicite : estimation 100, net estimé 1 100. Remises, emballage, transport et acomptes zéro.
- **Premier virement et capture** : Virement 400, date D, référence VIR-CAP306-400, Banque vide. Capture : Montant RAS * 30, Date de l’opération RAS * D, Référence RAS * PIECE-CAP306-30, Compte destination RAS * 3453 en vente / 4457 en achat. Aucune valeur de montant, référence ou compte préremplie ne doit être inventée.
- **Second virement et capture** : Virement 700, date D, référence VIR-CAP306-700, Banque vide. Capture 70, date D, référence PIECE-CAP306-70, même compte destination. Les montants déclarés sont saisis indépendamment : ni taux ni prorata automatique.
- **Comptes et trésorerie** : Virement comptabilisé automatiquement en 5141 dans ces sociétés neuves. Vérifier ce compte ; sinon Bloqué et noter la configuration plutôt que changer l’oracle. Aucun apport initial : après annulation, banque +400 en vente ou −400 en achat. Comptes 3453/4457 actifs choisis uniquement pour le laboratoire, pas imposés fiscalement.
- **Limites et sécurité** : Flux actuel limité aux virements et espèces immédiats déjà comptabilisés, sur facture validée non proforma et non annulée. Pas de mélange avec un historique déjà marqué RAS comptabilisée. Aucune attestation fiscale ni transfert automatique vers crédits IS. Si À vérifier apparaît, conserver le diagnostic et noter Bloqué ; aucun SQL, NaN, réparation de données ou modification d’écriture définitive n’est demandé au lecteur.
- **Preuves et comparaison** : Noter numéros des factures, règlements, OD et contrepassations réellement attribués, et D/E. Exporter le Journal avant/après. Le délettrage change volontairement le code de lettrage ; il ne change pas les montants, comptes, dates, références ou numéros des écritures originales. Ne pas comparer le maintien de AAA après avoir demandé son délettrage.

## Oracle indépendant

- `ht` : 1000
- `tva` : 200
- `ttc` : 1200
- `ras_estimee` : 100
- `cash1` : 400
- `reste_apres_cash1` : 800
- `ras1` : 30
- `reste_apres_capture1` : 770
- `cash2` : 700
- `reste_apres_cash2` : 70
- `ras2` : 70
- `reste_solde` : 0
- `total_debit_solde` : 2400
- `total_credit_solde` : 2400
- `reste_apres_annulation` : 770
- `ras_active` : 30
- `total_debit_final` : 3170
- `total_credit_final` : 3170
- `banque_vente` : 400
- `banque_achat` : -400
- `retenue_vente` : 30
- `retenue_achat` : -30
- `collectif_vente` : 770
- `collectif_achat` : -770

## CAP-306-01 — Capture déclarative et annulation traçable — vente

**Module** :
Recouvrement

**Prérequis** :
Installation isolée activée 083 ; société vente vierge du Jeu, exercice E ouvert, tiers CLIENT CAPTURE 306 créé, comptes actifs. Même jour D pendant tout le cas.

**Données à saisir** :
Facture 1 000 HT +200 TVA =1 200 TTC ; virements 400/700 ; captures déclarées 30/70, références et comptes explicites du Jeu. Compte destination 3453.

**Actions détaillées** :

1. Sélectionner ANNEXE CAPTURE VENTE FICTIVE 306 et E. Factures → Ventes → Nouvelle facture. Sélectionner CLIENT CAPTURE 306 dans les propositions ; saisir D et la ligne du Jeu. Choisir RAS (sur HT) 10 %. Enregistrer en brouillon, vérifier HT 1 000/TVA 200/TTC 1 200, puis Valider définitivement et Générer l’écriture comptable. Journal : contrôler et Valider cette première écriture uniquement. Noter son numéro ; reste dû 1 200, estimation seule non imputée.
2. Facture : Encaisser le client. Date D, Montant * 400, Mode Virement, référence VIR-CAP306-400, Banque vide. Enregistrer : une écriture de trésorerie en brouillon est produite. Avant capture, reste dû 800. Ne pas valider d’autres écritures à ce stade.
3. Cycle commercial → Vente → Règlements. Sur la ligne du virement 400, bouton avec infobulle Consulter ou déclarer la RAS. Vérifier montant/référence/compte vides ; saisir Montant RAS * 30, confirmer Date de l’opération RAS * D, Référence RAS * PIECE-CAP306-30, sélectionner Compte destination RAS * 3453. Cliquer Préparer la RAS déclarée. Vérifier reste dû 770. Rouvrir ce bouton : capture visible, À contrôler et à valider, aucun nouveau bouton de préparation pour ce même règlement ; Fermer. La référence de laboratoire n’est pas une attestation fiscale.
4. Revenir à la même facture : Encaisser le client. Date D, Montant * 700, Virement, référence VIR-CAP306-700, Banque vide ; Enregistrer. Reste avant capture 70. Cycle commercial → Règlements : sur la ligne 700, Consulter ou déclarer la RAS ; saisir montant 70, date D, référence PIECE-CAP306-70, compte 3453 ; Préparer la RAS déclarée. Vérifier facture soldée, reste 0, RAS déclarée totale 100. Ce total vient des deux saisies, pas d’une certification du taux estimé.
5. Journal : quatre brouillons nouveaux attendus, deux virements et deux OD déclaratives. Contrôler chacun, notamment les comptes, références, auxiliaires et montants 400/30/700/70. Cliquer Valider les brouillons et confirmer les quatre seulement dans cette société vierge. Cinq écritures définitives, onze lignes, total débit = crédit 2 400. Exporter CSV et conserver comme comparaison avant annulation.
6. Comptabilité → Lettrage : Compte Clients (3421), Tiers CLIENT CAPTURE 306, exercice E. Cocher cinq lignes : débit facture 1 200, crédits 400/30/700/70. Débit = crédit 1 200 ; Lettrer 5 lignes. Vérifier 5 lettrée(s) et AAA dans cette société neuve. Noter le code réellement attribué ; si l’action manque ou les lignes ne concordent pas, Bloqué et capture sans forcer.
7. Avant l’annulation, utiliser le bouton infobulle Délettrer le code AAA (ou le code réellement attribué), puis accepter la confirmation native du navigateur. Vérifier les cinq lignes délettrées. Cette action est volontaire et tracée ; conserver les preuves. Ne pas essayer de supprimer ou réécrire les écritures originales pour annuler un règlement.
8. Cycle commercial → Vente → Règlements : sur le virement 700 uniquement, cliquer Annuler par contrepassation et accepter la confirmation native. Vérifier règlement annulé. Consulter ou déclarer la RAS de cette ligne : Annulée par contrepassation et capture originale conservée. Fermer. Le virement 400 et sa capture 30 restent actifs. Facture : reste dû 770, RAS déclarée active 30 ; aucune nouvelle capture automatique.
9. Journal : deux contrepassations nouvelles en brouillon, trésorerie 700 et RAS 70. Contrôler puis Valider ces deux écritures. Comparer exports et Grand livre : sept écritures, quinze lignes, total débit = crédit 3 170. Banque +400, compte 3453 +30, collectif 3421 +770. Vérifier les cinq écritures originales identiques en montants/comptes/dates/références/numéros ; seul le lettrage a été volontairement retiré. Aucun nouveau lettrage à inventer après l’annulation.

**Résultat attendu** :
400+30 → reste 770 ; 700+70 → reste 0 ; cinq écritures/onze lignes D=C 2 400 ; cinq lignes lettrées AAA puis délettrées volontairement. Annulation du second règlement et de sa capture → reste 770, capture active 30 ; sept écritures/quinze lignes D=C 3 170. Originaux conservés.

**Écritures attendues** :
Facture : D3421=1 200, C7111=1 000, C4455=200. Virements : D5141/C3421 pour 400 puis 700. OD déclaratives : D3453/C3421 pour 30 puis 70. Annulation : D3421/C5141=700 et D3421/C3453=70. Après annulation : banque +400, retenue +30, collectif +770. Avant/après : D=C 2 400 puis 3 170.

**Impacts fiscaux** :
Saisies explicites de laboratoire, comptes et TVA sans qualification obligatoire. RAS estimée distincte des captures. Aucune attestation fiscale authentifiée, déclaration, prorata légal automatique ni crédit IS généré.

**Contrôles** :
Mode immédiat comptabilisé, date D explicite et période ouverte ; vrais liens règlement/facture/OD, compte choisi, cinq puis sept écritures équilibrées, auxiliaire tiers, validation, AAA et délettrage. Capture annulée conservée avec son inverse ; aucun montant inconnu remplacé par zéro.

**Statut** :
Non testé

**Résultat réel** :
À renseigner pendant la recette.

**Anomalies** :
À renseigner pendant la recette.

**Preuves/captures** :
À renseigner pendant la recette.

**Observations** :
À renseigner pendant la recette.

**Preuves attendues** :
Installation isolée/activation, données D/E, facture, deux virements, captures avec montant/date/référence/compte, solde 770/0/770, OD brouillon puis définitive, cinq lignes AAA puis délettrées, confirmation annulation, deux inverses, CSV avant/après et Grand livre. Inscrire les preuves réellement produites dans Preuves/captures.

**Sources de mise en œuvre** : [docs/MISE_A_JOUR_RAS_20261009.md](../../docs/MISE_A_JOUR_RAS_20261009.md), [hisabpro-backend/083_ras_reglements.sql](../../hisabpro-backend/083_ras_reglements.sql), [src/pages/Commercial.jsx](../../src/pages/Commercial.jsx), [src/pages/Factures.jsx](../../src/pages/Factures.jsx), [src/pages/Lettrage.jsx](../../src/pages/Lettrage.jsx), [Test/test_e2e_ras_capture_isole.py](../../Test/test_e2e_ras_capture_isole.py), [Test/test_ras_capture_reglement_postgres.py](../../Test/test_ras_capture_reglement_postgres.py), [Test/test_sauvegarde_ras_reglements_isole.py](../../Test/test_sauvegarde_ras_reglements_isole.py), [Test/rapport_sources_ras_20261009.md](../../Test/rapport_sources_ras_20261009.md)

## CAP-306-02 — Capture déclarative et annulation traçable — achat

**Module** :
Recouvrement

**Prérequis** :
Installation isolée activée 083 ; société achat vierge du Jeu, exercice E ouvert, tiers FOURNISSEUR CAPTURE 306 créé, comptes actifs. Même jour D pendant tout le cas.

**Données à saisir** :
Facture 1 000 HT +200 TVA =1 200 TTC ; virements 400/700 ; captures déclarées 30/70, références et comptes explicites du Jeu. Compte destination 4457.

**Actions détaillées** :

1. Sélectionner ANNEXE CAPTURE ACHAT FICTIVE 306 et E. Factures → Achats → Nouvelle facture. Sélectionner FOURNISSEUR CAPTURE 306 dans les propositions ; saisir D et la ligne du Jeu. N° facture fournisseur ACH-CAP306-001, compte 6111, Charge / achat courant et déductible 100 %. Choisir RAS (sur HT) 10 %. Enregistrer en brouillon, vérifier HT 1 000/TVA 200/TTC 1 200, puis Valider définitivement et Générer l’écriture comptable. Journal : contrôler et Valider cette première écriture uniquement. Noter son numéro ; reste dû 1 200, estimation seule non imputée.
2. Facture : Payer le fournisseur. Date D, Montant * 400, Mode Virement, référence VIR-CAP306-400, Banque vide. Enregistrer : une écriture de trésorerie en brouillon est produite. Avant capture, reste dû 800. Ne pas valider d’autres écritures à ce stade.
3. Cycle commercial → Achat → Règlements. Sur la ligne du virement 400, bouton avec infobulle Consulter ou déclarer la RAS. Vérifier montant/référence/compte vides ; saisir Montant RAS * 30, confirmer Date de l’opération RAS * D, Référence RAS * PIECE-CAP306-30, sélectionner Compte destination RAS * 4457. Cliquer Préparer la RAS déclarée. Vérifier reste dû 770. Rouvrir ce bouton : capture visible, À contrôler et à valider, aucun nouveau bouton de préparation pour ce même règlement ; Fermer. La référence de laboratoire n’est pas une attestation fiscale.
4. Revenir à la même facture : Payer le fournisseur. Date D, Montant * 700, Virement, référence VIR-CAP306-700, Banque vide ; Enregistrer. Reste avant capture 70. Cycle commercial → Règlements : sur la ligne 700, Consulter ou déclarer la RAS ; saisir montant 70, date D, référence PIECE-CAP306-70, compte 4457 ; Préparer la RAS déclarée. Vérifier facture soldée, reste 0, RAS déclarée totale 100. Ce total vient des deux saisies, pas d’une certification du taux estimé.
5. Journal : quatre brouillons nouveaux attendus, deux virements et deux OD déclaratives. Contrôler chacun, notamment les comptes, références, auxiliaires et montants 400/30/700/70. Cliquer Valider les brouillons et confirmer les quatre seulement dans cette société vierge. Cinq écritures définitives, onze lignes, total débit = crédit 2 400. Exporter CSV et conserver comme comparaison avant annulation.
6. Comptabilité → Lettrage : Compte Fournisseurs (4411), Tiers FOURNISSEUR CAPTURE 306, exercice E. Cocher cinq lignes : crédit facture 1 200, débits 400/30/700/70. Débit = crédit 1 200 ; Lettrer 5 lignes. Vérifier 5 lettrée(s) et AAA dans cette société neuve. Noter le code réellement attribué ; si l’action manque ou les lignes ne concordent pas, Bloqué et capture sans forcer.
7. Avant l’annulation, utiliser le bouton infobulle Délettrer le code AAA (ou le code réellement attribué), puis accepter la confirmation native du navigateur. Vérifier les cinq lignes délettrées. Cette action est volontaire et tracée ; conserver les preuves. Ne pas essayer de supprimer ou réécrire les écritures originales pour annuler un règlement.
8. Cycle commercial → Achat → Règlements : sur le virement 700 uniquement, cliquer Annuler par contrepassation et accepter la confirmation native. Vérifier règlement annulé. Consulter ou déclarer la RAS de cette ligne : Annulée par contrepassation et capture originale conservée. Fermer. Le virement 400 et sa capture 30 restent actifs. Facture : reste dû 770, RAS déclarée active 30 ; aucune nouvelle capture automatique.
9. Journal : deux contrepassations nouvelles en brouillon, trésorerie 700 et RAS 70. Contrôler puis Valider ces deux écritures. Comparer exports et Grand livre : sept écritures, quinze lignes, total débit = crédit 3 170. Banque −400, compte 4457 −30, collectif 4411 −770. Vérifier les cinq écritures originales identiques en montants/comptes/dates/références/numéros ; seul le lettrage a été volontairement retiré. Aucun nouveau lettrage à inventer après l’annulation.

**Résultat attendu** :
400+30 → reste 770 ; 700+70 → reste 0 ; cinq écritures/onze lignes D=C 2 400 ; cinq lignes lettrées AAA puis délettrées volontairement. Annulation du second règlement et de sa capture → reste 770, capture active 30 ; sept écritures/quinze lignes D=C 3 170. Originaux conservés.

**Écritures attendues** :
Facture : D6111=1 000, D34552=200, C4411=1 200. Virements : D4411/C5141 pour 400 puis 700. OD déclaratives : D4411/C4457 pour 30 puis 70. Annulation : D5141/C4411=700 et D4457/C4411=70. Après annulation : banque −400, retenue −30, collectif −770. Avant/après : D=C 2 400 puis 3 170.

**Impacts fiscaux** :
Saisies explicites de laboratoire, comptes et TVA sans qualification obligatoire. RAS estimée distincte des captures. Aucune attestation fiscale authentifiée, déclaration, prorata légal automatique ni crédit IS généré.

**Contrôles** :
Mode immédiat comptabilisé, date D explicite et période ouverte ; vrais liens règlement/facture/OD, compte choisi, cinq puis sept écritures équilibrées, auxiliaire tiers, validation, AAA et délettrage. Capture annulée conservée avec son inverse ; aucun montant inconnu remplacé par zéro.

**Statut** :
Non testé

**Résultat réel** :
À renseigner pendant la recette.

**Anomalies** :
À renseigner pendant la recette.

**Preuves/captures** :
À renseigner pendant la recette.

**Observations** :
À renseigner pendant la recette.

**Preuves attendues** :
Installation isolée/activation, données D/E, facture, deux virements, captures avec montant/date/référence/compte, solde 770/0/770, OD brouillon puis définitive, cinq lignes AAA puis délettrées, confirmation annulation, deux inverses, CSV avant/après et Grand livre. Inscrire les preuves réellement produites dans Preuves/captures.

**Sources de mise en œuvre** : [docs/MISE_A_JOUR_RAS_20261009.md](../../docs/MISE_A_JOUR_RAS_20261009.md), [hisabpro-backend/083_ras_reglements.sql](../../hisabpro-backend/083_ras_reglements.sql), [src/pages/Commercial.jsx](../../src/pages/Commercial.jsx), [src/pages/Factures.jsx](../../src/pages/Factures.jsx), [src/pages/Lettrage.jsx](../../src/pages/Lettrage.jsx), [Test/test_e2e_ras_capture_isole.py](../../Test/test_e2e_ras_capture_isole.py), [Test/test_ras_capture_reglement_postgres.py](../../Test/test_ras_capture_reglement_postgres.py), [Test/test_sauvegarde_ras_reglements_isole.py](../../Test/test_sauvegarde_ras_reglements_isole.py), [Test/rapport_sources_ras_20261009.md](../../Test/rapport_sources_ras_20261009.md)
