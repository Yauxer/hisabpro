# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

## Achats en deux réceptions

Annexe autonome : achats reçus en deux parties, facturation, règlements et lettrage. Deux cas utilisateur Non testé, même si des tests développeur existent. Exécuter exclusivement dans une installation de recette isolée et une société fictive neuve, sans ajouter ces mouvements au scénario annuel. Aucun dépôt, droit fiscal, certification ou conformité réglementaire ne sont validés automatiquement.

## Jeu de données

- **Installation** : Administrateur dans une installation de recette isolée contenant les lots 275, 280 et 283. Si un champ ou une action requis manque, noter Bloqué et la version. Ne pas utiliser la société réelle ni son compte bancaire réel.
- **Société et exercice** : Créer ANNEXE ACHATS PARTIELS FICTIVE suivant Administration → Sociétés du cahier principal. Exercice 2026 ouvert, 01/01/2026–31/12/2026. Aucun ICE/IF ou justificatif réel à inventer. Activer Facturation et Comptabilité si nécessaire. Sélectionner cette société et cet exercice.
- **Stock** : Paramètres → Fiche société → Gestion du stock : Achats — entrée de stock = À la réception — BR passé en « livré ». Enregistrer. Ne pas conserver le réglage À la facturation pour ce scénario.
- **Fournisseur** : Clients / Fournisseurs → Nouveau tiers : nom FOURNISSEUR PARTIEL 284, type Fournisseur, délai de paiement 30 jours ; paramétrage comptable compte fournisseur 4411. Laisser identifiants et taux RAS non renseignés ; pas de retenue dans ce laboratoire. Enregistrer.
- **Article** : Articles → Nouvel article : code REC284-STOCK, désignation Marchandise partielle fictive, unité unité, article stockable, stock initial 0, prix achat HT 500, prix vente HT 700, TVA proposée 20 %, compte achat 6111. Emballage, transport, remises et autres frais zéro. Enregistrer.
- **Dates et références** : BC 15/03/2026 ; BR1 16/03/2026, BR2 18/03/2026 ; factures fournisseur FR284-001 du 16/03/2026 et FR284-002 du 18/03/2026 ; règlements par virement 20/03/2026 et 21/03/2026, références VIR284-001/VIR284-002. Noter les numéros internes réellement attribués, sans les deviner.
- **Qualification choisie** : TVA 20 %, qualification de ligne Taxable ; qualification TVA de l’achat Charge / achat courant, déductible 100 %. Ce sont des données explicites de laboratoire, sans nouvelle affirmation légale du droit à déduction. Pas de RAS, avoir, remise, escompte ou acompte dans ce scénario.
- **Banque** : Le parcours Payer le fournisseur propose Mode et Banque, sans champ de compte comptable ni option de comptabilisation. Dans cette société vierge, laisser Banque vide et utiliser le virement proposé ; vérifier ensuite que l’écriture automatique utilise 5141. Si un autre compte apparaît, noter Bloqué et son paramétrage au lieu de modifier l’oracle. Aucun apport initial prévu : solde comptable final crédit 2 400, soit −2 400. Ce solde fictif ne représente pas une banque réelle ni une trésorerie financée.
- **Traçabilité** : Consigner numéros BC, BR1, BR2, factures et quatre écritures dans les observations. Conserver captures et exports avant/après. Ne pas modifier une écriture validée. Les photos techniques DB des tests développeur ne sont pas exigées d’un utilisateur non développeur.

## Oracle indépendant

- `quantite_br1` : 1
- `quantite_br2` : 3
- `ht_facture1` : 500
- `ht_facture2` : 1500
- `tva_facture1` : 100.0
- `tva_facture2` : 300.0
- `ttc_facture1` : 600.0
- `ttc_facture2` : 1800.0
- `stock_final` : 4
- `solde_6111` : 2000
- `solde_34552` : 400.0
- `solde_4411` : 0.0
- `solde_5141` : -2400.0
- `total_debit` : 4800.0
- `total_credit` : 4800.0

## ACH-284-01 — Recevoir en deux parties, payer et lettrer le même fournisseur

**Module** :
Achats

**Impacts fiscaux** :
TVA documentaire totale 400, choisie déductible 100 % pour ce laboratoire. Aucun dépôt TVA ni validation réglementaire.

**Statut** :
Non testé

**Résultat réel** :
À renseigner pendant la recette.

**Anomalies** :
À renseigner pendant la recette.

**Observations** :
À renseigner pendant la recette.

**Prérequis** :
Installation isolée ; réaliser toutes les préparations du Jeu de données ci-dessus. Société neuve sans autre facture, règlement ou écriture. Exercice 2026 ouvert.

**Données à saisir** :
Une commande de 4 unités à 500 HT, TVA 20 %. BR1 : 1 unité ; BR2 : 3 unités. FR284-001 : 600 TTC ; FR284-002 : 1 800 TTC. VIR284-001 : 600 ; VIR284-002 : 1 800. Dates et comptes : voir Jeu de données.

**Actions détaillées** :

1. Cycle commercial → Achat → Bons de commande → Nouveau BC. Type Achat ; date 15/03/2026 ; sélectionner FOURNISSEUR PARTIEL 284 depuis les propositions, pas seulement son texte. Ajouter REC284-STOCK depuis les articles proposés, quantité 4, prix HT 500, TVA 20 %, Taxable. Créer la commande. Noter son numéro ; HT 2 000 / TVA 400 / TTC 2 400 ; stock 0.
2. Sur le BC, Réceptionner (infobulle Créer un bon de réception sur le reliquat). Nouveau bon de réception : date 16/03/2026 ; quantité proposée 4, remplacer par 1 ; Créer le bon de réception. Noter BR1. Bons de réception : ligne BR1, Marquer en cours puis Marquer réceptionné. Vérifier article stock 1, une seule entrée 1 et BC reste 3. Un BR seulement préparé ne doit pas déjà augmenter le stock.
3. Sur BR1 réceptionné, Facturer. Quantité 1 ; Créer la facture en brouillon. Dans Factures → Achats, ouvrir Modifier le brouillon correspondant. N° facture fournisseur FR284-001, date 16/03/2026. Qualification TVA de l’achat Charge / achat courant ; TVA déductible (%) 100 ; enregistrer puis rouvrir pour vérifier. Valider définitivement, puis Générer l’écriture comptable de cette facture. Journal : contrôler et Valider son écriture. Noter numéros facture/écriture ; stock reste 1.
4. Revenir au même BC et Réceptionner. Quantité proposée 3 ; date 18/03/2026 ; recevoir 3. Sur BR2, Marquer en cours puis Marquer réceptionné. Stock 4 ; exactement deux entrées 1 et 3 ; BC reste 0. Facturer BR2, quantité 3. Modifier ce nouveau brouillon : FR284-002, date 18/03/2026, Charge / achat courant et déductible 100. Enregistrer, vérifier, Valider définitivement, Générer son écriture et la Valider dans Journal. Stock reste 4 ; première facture/écriture inchangée.
5. Factures → Achats : FR284-001, Payer le fournisseur. Date 20/03/2026, montant 600, mode Virement, référence VIR284-001 ; laisser Banque vide dans ce laboratoire. Enregistrer : le règlement génère son écriture automatiquement. Répéter sur FR284-002 : date 21/03/2026, montant 1 800, Virement, référence VIR284-002, Banque vide. Vérifier chacune Payée et reste 0. Journal : contrôler les deux nouvelles écritures, notamment contrepartie 5141, puis Valider les brouillons de règlement uniquement (deux si aucun autre brouillon).
6. Comptabilité → Lettrage. Exercice 2026, Compte Fournisseurs (4411), Tiers FOURNISSEUR PARTIEL 284. Cocher les quatre lignes : crédits 600 et 1 800 des factures, débits 600 et 1 800 des virements. Total sélection débit = crédit 2 400 ; Lettrer 4 lignes. Noter le code commun de trois lettres attribué (AAA attendu si aucun lettrage antérieur dans la société neuve). Vérifier le compteur 4 lettrée(s), solde 0. Recharger puis sélectionner à nouveau compte/tiers : code et lignes conservés.
7. Comparer Journal, Grand livre comptes 6111/34552/4411/5141 et Stocks. Cycle commercial → Achat → Factures contient les deux factures ; BR1 etBR2 gardent leur lien à chacune. Exporter Journal CSV ou balances Excel/PDF et conserver les preuves. Aucun troisième mouvement stock ni nouvelle facture après rechargement.

**Résultat attendu** :
Un BC, deux BR de 1/3, deux factures payées 600/1 800, deux virements 600/1 800 ; quatre écritures définitives, dix lignes. Exactement deux entrées de stock, stock final 4. Fournisseur soldé et quatre lignes 4411 lettrées sous un code commun. Chaque document conserve son lien source ; pas de double entrée à la validation facture.

**Écritures attendues** :
Facture 1 : D6111=500, D34552=100, C4411=600. Facture 2 : D6111=1 500, D34552=300, C4411=1 800. Règlement 1 : D4411=600, C5141=600. Règlement 2 : D4411=1 800, C5141=1 800. Chaque écriture équilibrée ; cumul D = C 4 800. Soldes D − C : 6111 = 2 000, 34552 = 400, 4411 = 0, 5141 = −2 400. Quatre lignes fournisseur rattachées au vrai tiers/auxiliaire.

**Contrôles** :
Comparer les montants à l’oracle indépendant, les numéros, quantités et sources. Vérifier toutes les écritures validées, quatre lignes lettrées et aucune troisième entrée. Aucun apport initial fictif à ajouter pour changer le solde banque attendu.

**Preuves/captures** :
Captures réglage stock, BC/reliquats 3 puis 0, BR1/BR2, stock 0/1/4, qualification 100 %, deux factures Payées, deux virements, quatre écritures, lettrage quatre lignes et exports ouverts.

**Sources de mise en œuvre** : [src/pages/Commercial.jsx](../../src/pages/Commercial.jsx), [src/pages/Factures.jsx](../../src/pages/Factures.jsx), [src/pages/Lettrage.jsx](../../src/pages/Lettrage.jsx), [src/pages/Parametres.jsx](../../src/pages/Parametres.jsx), [Test/test_e2e_cycle_achat_reception_partielle_isole.py](../../Test/test_e2e_cycle_achat_reception_partielle_isole.py)

## ACH-284-02 — Empêcher la reconversion et préserver les pièces définitives

**Module** :
Achats

**Impacts fiscaux** :
TVA documentaire totale 400, choisie déductible 100 % pour ce laboratoire. Aucun dépôt TVA ni validation réglementaire.

**Statut** :
Non testé

**Résultat réel** :
À renseigner pendant la recette.

**Anomalies** :
À renseigner pendant la recette.

**Observations** :
À renseigner pendant la recette.

**Prérequis** :
ACH-284-01 effectué dans la même société ; conserver ses captures/exports avant essai. Ne pas créer un autre dossier pour ce cas négatif.

**Données à saisir** :
Même BC épuisé, BR1 etBR2 déjà facturés ; FR284-001/002 déjà validées, comptabilisées et payées ; mêmes dix lignes et deux mouvements stock.

**Actions détaillées** :

1. Cycle commercial → Achat → Bons de commande : sur le même BC tenter Réceptionner si disponible. Constater reliquat 0 et impossibilité de créer un nouveau BR ; si action indisponible, conserver la capture. Ne pas saisir une autre commande.
2. Bons de réception : sur chacun des BR déjà facturés, tenter Facturer si disponible. Une quantité restante 0 ou un refus clair empêche une nouvelle facture. Si l’action est masquée/désactivée, noter ce comportement et capturer ; ne pas utiliser API/SQL ou outils développeur pour forcer une conversion.
3. Factures → Achats : ouvrir les deux pièces. Vérifier absence de Modifier le brouillon et de Générer l’écriture déjà produite, ou refus explicite si une action reste proposée. Ne pas annuler, contrepasser, délettrer ou faire appel à une intervention admin sur une pièce définitive.
4. Recharger Cycle commercial, Factures, Stocks et Lettrage ; rouvrir les exports. Comparer au cas 01 : un BC/deux BR/deux factures/deux règlements/quatre écritures/dix lignes, stock 4, deux entrées et code commun des quatre lignes inchangés. Une action empêchée est un résultat attendu ; une pièce créée/modifiée est une anomalie à consigner.

**Résultat attendu** :
Aucune reconversion ni édition de brouillon définitif. Bouton indisponible ou refus compréhensible selon l’état de l’interface. Tous les totaux, documents, dates, montants, liens et code de lettrage du cas 01 sont conservés.

**Écritures attendues** :
Aucune écriture supplémentaire ou réécriture. Les quatre écritures/dix lignes du cas 01 restent identiques : cumul D = C 4 800, fournisseur 0, banque −2 400.

**Contrôles** :
Avant/après : nombres de pièces et mouvements, stock 4, auxiliaire fournisseur, montants et code. Les refus HTTP409/400 sont contrôlés par les tests développeur, sans les exiger du lecteur utilisateur.

**Preuves/captures** :
Captures boutons absents/désactivés ou message de refus, liste des pièces et stock ; exports et lettrage avant/après.

**Sources de mise en œuvre** : [src/pages/Commercial.jsx](../../src/pages/Commercial.jsx), [src/pages/Factures.jsx](../../src/pages/Factures.jsx), [src/pages/Lettrage.jsx](../../src/pages/Lettrage.jsx), [src/pages/Parametres.jsx](../../src/pages/Parametres.jsx), [Test/test_e2e_cycle_achat_reception_partielle_isole.py](../../Test/test_e2e_cycle_achat_reception_partielle_isole.py)
