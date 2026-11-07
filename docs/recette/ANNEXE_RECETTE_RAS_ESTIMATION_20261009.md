# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

## RAS estimée et paiements réels

Annexe autonome : distinguer RAS estimée et règlement réellement enregistré. Deux cas Non testé, dans deux sociétés fictives neuves et indépendantes, exclusivement sur une installation de recette isolée. Les choix TVA 20 % et RAS 10 % sont des données de laboratoire, sans affirmation de leur applicabilité légale. Aucune attestation, déclaration fiscale, certification ou recette utilisateur n’est validée automatiquement.

## Jeu de données

- **Installation** : Administrateur, Facturation et Comptabilité disponibles, lots 291 et 292 intégrés. Si une action requise manque, noter Bloqué et la version ; ne pas utiliser une société ni une banque réelle.
- **Société vente** : Créer ANNEXE RAS VENTE FICTIVE 298, exercice 2026 ouvert du 01/01 au 31/12, suivant Administration → Sociétés du cahier principal. Créer client CLIENT RAS 298, compte client 3421 ; aucun autre mouvement. Ne pas inventer d’identifiants fiscaux officiels.
- **Société achat** : Créer séparément ANNEXE RAS ACHAT FICTIVE 298, même exercice ouvert. Créer fournisseur FOURNISSEUR RAS 298, compte fournisseur 4411 ; aucun autre mouvement. Ne pas réutiliser la société vente.
- **Factures** : Date 15/03/2026, une ligne Service laboratoire 298, quantité 1, prix unitaire HT 1 000, TVA 20 %, Taxable. Vente : compte produit 7111. Achat : compte achat 6111 ; référence fournisseur ACH-RAS298-001, qualification TVA Charge / achat courant, déductible 100 %. Remises, transport, emballage et acomptes zéro. Retenue à la source (sur HT) : 10 % explicitement choisie.
- **Règlements** : Premier virement réel de laboratoire : 20/03/2026, montant 1 100, référence VIR-RAS298-1100. Deuxième : 21/03/2026, montant 100, référence VIR-RAS298-100. Dans chaque société, laisser Banque vide : vérifier contrepartie automatique 5141, sinon Bloqué et noter le paramétrage. Aucun apport initial ; banque finale +1 200 en vente, −1 200 en achat.
- **Sens de la preuve** : La RAS estimée de 100 et le net estimé de 1 100 ne prouvent ni une retenue opérée ni un paiement. Ces scénarios règlent finalement les 1 200 en trésorerie et ne capturent aucune retenue. Ne pas comptabiliser une OD de RAS pour solder artificiellement les 100.
- **Historiques inconnus** : Si l’interface présente À vérifier ou un diagnostic historique, ne pas forcer un montant ni modifier une pièce définitive. Consigner Bloqué et conserver la capture pour une vérification contrôlée. La fabrication de NaN/SQL ou d’un ancien historique n’est pas demandée à l’utilisateur. Les autres écrans concernés par les lots 296/297 et la future capture explicite sont hors parcours de cette annexe.
- **Traçabilité** : Noter le numéro réellement attribué à chaque facture et ses trois écritures. Conserver captures et exports ouverts. Après validation, aucune réécriture des pièces : comparer avant/après par le Journal et le Grand livre.

## Oracle indépendant

- `ht` : 1000
- `tva` : 200
- `ttc` : 1200
- `ras_estimee` : 100
- `net_estime` : 1100
- `solde_avant` : 1200
- `cash1` : 1100
- `reste_apres_cash1` : 100
- `cash2` : 100
- `solde_final` : 0
- `ras_imputee` : 0
- `banque_vente` : 1200
- `banque_achat` : -1200
- `total_debit` : 2400
- `total_credit` : 2400

## RAS-298-01 — RAS estimée sans imputation — vente

**Module** :
Recouvrement

**Prérequis** :
Société vente neuve et isolée, exercice 2026 ouvert, tiers CLIENT RAS 298 préparé selon le Jeu. Aucun autre mouvement ni lettrage.

**Données à saisir** :
HT 1 000 / TVA 200 / TTC 1 200 ; taux RAS estimé 10 %, estimation 100, net estimé 1 100. Virements 1 100 puis 100, dates et références du Jeu.

**Actions détaillées** :

1. Sélectionner ANNEXE RAS VENTE FICTIVE 298 et exercice 2026. Factures → Ventes → Nouvelle facture. Sélectionner CLIENT RAS 298 dans les propositions, date 15/03/2026 ; saisir la ligne et le compte du Jeu. Choisir Retenue à la source (sur HT) 10 %. Enregistrer le brouillon, vérifier HT 1 000/TVA 200/TTC 1 200 et net estimé 1 100. Valider définitivement, puis Générer l’écriture comptable de cette facture. Dans Journal, contrôler et Valider cette écriture. Noter les numéros réellement attribués.
2. Sur cette facture, Encaisser le client. Le formulaire affiche RAS estimée 100,00 MAD et propose Montant * 1 200,00 : le solde reste le TTC, sans imputation de l’estimation. Annuler sans enregistrer. Situation financière & recouvrement → Échéances & impayés → Clients : retrouver cette pièce, reste dû 1 200 et imputé 0. Conserver les preuves avant paiement.
3. Revenir à la même facture, Encaisser le client. Date 20/03/2026, Montant * 1 100, Mode Virement, référence VIR-RAS298-1100 ; Banque vide. Enregistrer. Vérifier statut Part. payée, puis rouvrir ce formulaire : montant proposé 100,00, estimation toujours 100,00. Annuler. Journal : contrôler et Valider uniquement la nouvelle écriture de virement ; ne pas créer une retenue pour les 100 restants.
4. Même facture, Encaisser le client : date 21/03/2026, Montant * 100, Virement, référence VIR-RAS298-100, Banque vide. Enregistrer puis contrôler et Valider sa nouvelle écriture dans Journal. Vérifier facture Payée, reste 0. Aucune OD de RAS ni mouvement 3453/4457 ; seuls les deux virements réels ont soldé le tiers.
5. Comptabilité → Lettrage : exercice 2026, Compte Clients (3421), Tiers CLIENT RAS 298. Cocher les trois lignes : débit facture 1 200, crédits virements 1 100/100. Total débit = crédit 1 200 ; Lettrer 3 lignes. Noter le code commun de trois lettres, AAA attendu dans cette société neuve sans lettrage antérieur. Si le lettrage ou les lignes requis manquent, noter Bloqué et conserver la preuve, sans forcer de ligne.
6. Journal → Exporter CSV, ouvrir le fichier ; Grand livre : contrôler 3421 soldé et 5141 +1 200. Comparer trois écritures/sept lignes, total débit = crédit 2 400, aucune 3453/4457. Recharger et recontrôler facture Payée et code commun ; les écritures initiales restent inchangées.

**Résultat attendu** :
RAS estimée 100 et net estimé 1 100 distincts des paiements : solde initial 1 200 ; après trésorerie 1 100 reste 100 et Part. payée ; après trésorerie 100 reste 0 et Payée. Trois écritures, sept lignes ; trois lignes du tiers lettrées sous un code commun.

**Écritures attendues** :
Facture : D3421=1 200, C7111=1 000, C4455=200. Virements : D5141=1 100/C3421=1 100 puis D5141=100/C3421=100. Cumul D=C2 400 ; 3421=0 ; banque +1 200. Aucun compte 3453/4457 ni OD de RAS. Sept lignes, toutes définitives après validation.

**Impacts fiscaux** :
TVA documentaire 200 et RAS estimée 100 proviennent des choix explicites du laboratoire. Aucune retenue imputée, attestation, déclaration ni qualification réglementaire automatique. Ne pas transposer les taux à un dossier réel.

**Contrôles** :
Solde, statut, proposition de montant et estimation à chacune des trois étapes ; comptes, sens des virements, nombres de lignes, équilibre, vrai tiers, code AAA ou code attribué consigné ; pas de réparation historique.

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
Captures facture et trois étapes de solde, formulaire montant 1 200 puis 100, estimation 100 ; trois écritures validées, lettrage, Grand livre et CSV ouvert. Renseigner le chemin des preuves réellement obtenues dans la colonne Preuves/captures.

**Sources de mise en œuvre** : [src/pages/Factures.jsx](../../src/pages/Factures.jsx), [src/pages/Lettrage.jsx](../../src/pages/Lettrage.jsx), [src/pages/SituationFinanciere.jsx](../../src/pages/SituationFinanciere.jsx), [Test/test_e2e_ras_situation_isole.py](../../Test/test_e2e_ras_situation_isole.py), [Test/test_ras_estimation_solde_postgres.py](../../Test/test_ras_estimation_solde_postgres.py), [Test/test_e2e_ras_solde_lettrage_isole.py](../../Test/test_e2e_ras_solde_lettrage_isole.py), [Test/rapport_e2e_ras_solde_lettrage.md](../../Test/rapport_e2e_ras_solde_lettrage.md), [Test/rapport_sources_ras_20261009.md](../../Test/rapport_sources_ras_20261009.md)

## RAS-298-02 — RAS estimée sans imputation — achat

**Module** :
Recouvrement

**Prérequis** :
Société achat neuve et isolée, exercice 2026 ouvert, tiers FOURNISSEUR RAS 298 préparé selon le Jeu. Aucun autre mouvement ni lettrage.

**Données à saisir** :
HT 1 000 / TVA 200 / TTC 1 200 ; taux RAS estimé 10 %, estimation 100, net estimé 1 100. Virements 1 100 puis 100, dates et références du Jeu.

**Actions détaillées** :

1. Sélectionner ANNEXE RAS ACHAT FICTIVE 298 et exercice 2026. Factures → Achats → Nouvelle facture. Sélectionner FOURNISSEUR RAS 298 dans les propositions, date 15/03/2026 ; saisir la ligne et le compte du Jeu. N° facture fournisseur ACH-RAS298-001 ; Charge / achat courant, TVA déductible (%) 100. Choisir Retenue à la source (sur HT) 10 %. Enregistrer le brouillon, vérifier HT 1 000/TVA 200/TTC 1 200 et net estimé 1 100. Valider définitivement, puis Générer l’écriture comptable de cette facture. Dans Journal, contrôler et Valider cette écriture. Noter les numéros réellement attribués.
2. Sur cette facture, Payer le fournisseur. Le formulaire affiche RAS estimée 100,00 MAD et propose Montant * 1 200,00 : le solde reste le TTC, sans imputation de l’estimation. Annuler sans enregistrer. Situation financière & recouvrement → Échéances & impayés → Fournisseurs : retrouver cette pièce, reste dû 1 200 et imputé 0. Conserver les preuves avant paiement.
3. Revenir à la même facture, Payer le fournisseur. Date 20/03/2026, Montant * 1 100, Mode Virement, référence VIR-RAS298-1100 ; Banque vide. Enregistrer. Vérifier statut Part. payée, puis rouvrir ce formulaire : montant proposé 100,00, estimation toujours 100,00. Annuler. Journal : contrôler et Valider uniquement la nouvelle écriture de virement ; ne pas créer une retenue pour les 100 restants.
4. Même facture, Payer le fournisseur : date 21/03/2026, Montant * 100, Virement, référence VIR-RAS298-100, Banque vide. Enregistrer puis contrôler et Valider sa nouvelle écriture dans Journal. Vérifier facture Payée, reste 0. Aucune OD de RAS ni mouvement 3453/4457 ; seuls les deux virements réels ont soldé le tiers.
5. Comptabilité → Lettrage : exercice 2026, Compte Fournisseurs (4411), Tiers FOURNISSEUR RAS 298. Cocher les trois lignes : crédit facture 1 200, débits virements 1 100/100. Total débit = crédit 1 200 ; Lettrer 3 lignes. Noter le code commun de trois lettres, AAA attendu dans cette société neuve sans lettrage antérieur. Si le lettrage ou les lignes requis manquent, noter Bloqué et conserver la preuve, sans forcer de ligne.
6. Journal → Exporter CSV, ouvrir le fichier ; Grand livre : contrôler 4411 soldé et 5141 −1 200. Comparer trois écritures/sept lignes, total débit = crédit 2 400, aucune 3453/4457. Recharger et recontrôler facture Payée et code commun ; les écritures initiales restent inchangées.

**Résultat attendu** :
RAS estimée 100 et net estimé 1 100 distincts des paiements : solde initial 1 200 ; après trésorerie 1 100 reste 100 et Part. payée ; après trésorerie 100 reste 0 et Payée. Trois écritures, sept lignes ; trois lignes du tiers lettrées sous un code commun.

**Écritures attendues** :
Facture : D6111=1 000, D34552=200, C4411=1 200. Virements : D4411=1 100/C5141=1 100 puis D4411=100/C5141=100. Cumul D=C2 400 ; 4411=0 ; banque −1 200. Aucun compte 3453/4457 ni OD de RAS. Sept lignes, toutes définitives après validation.

**Impacts fiscaux** :
TVA documentaire 200 et RAS estimée 100 proviennent des choix explicites du laboratoire. Aucune retenue imputée, attestation, déclaration ni qualification réglementaire automatique. Ne pas transposer les taux à un dossier réel.

**Contrôles** :
Solde, statut, proposition de montant et estimation à chacune des trois étapes ; comptes, sens des virements, nombres de lignes, équilibre, vrai tiers, code AAA ou code attribué consigné ; pas de réparation historique.

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
Captures facture et trois étapes de solde, formulaire montant 1 200 puis 100, estimation 100 ; trois écritures validées, lettrage, Grand livre et CSV ouvert. Renseigner le chemin des preuves réellement obtenues dans la colonne Preuves/captures.

**Sources de mise en œuvre** : [src/pages/Factures.jsx](../../src/pages/Factures.jsx), [src/pages/Lettrage.jsx](../../src/pages/Lettrage.jsx), [src/pages/SituationFinanciere.jsx](../../src/pages/SituationFinanciere.jsx), [Test/test_e2e_ras_situation_isole.py](../../Test/test_e2e_ras_situation_isole.py), [Test/test_ras_estimation_solde_postgres.py](../../Test/test_ras_estimation_solde_postgres.py), [Test/test_e2e_ras_solde_lettrage_isole.py](../../Test/test_e2e_ras_solde_lettrage_isole.py), [Test/rapport_e2e_ras_solde_lettrage.md](../../Test/rapport_e2e_ras_solde_lettrage.md), [Test/rapport_sources_ras_20261009.md](../../Test/rapport_sources_ras_20261009.md)
