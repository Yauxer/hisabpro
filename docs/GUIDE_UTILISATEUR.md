# HisabPro — Mode d'emploi

*Version du 11 novembre 2026. Ce guide décrit les écrans tels qu'ils existent aujourd'hui dans l'application.*

HisabPro regroupe trois modules, accessibles depuis le menu de gauche :

| Module | À quoi il sert |
|---|---|
| **Facturation** | Devis, commandes, livraisons, factures, avoirs, acomptes, règlements, chèques et effets, clients, fournisseurs, articles et stock. |
| **Comptabilité** | Journal et écritures, plan comptable, grand livre, balances, lettrage, rapprochement bancaire, immobilisations, TVA, IS, liasse fiscale, clôture. |
| **Personnel & Paie** | Salariés, cotisations, calcul de la paie du mois, bulletins, avances, paiement et comptabilisation des salaires. |

Les trois modules sont reliés : une facture validée produit son écriture comptable, un règlement produit son écriture de banque ou de caisse, la paie produit l'écriture des salaires.

> HisabPro aide à tenir une comptabilité conforme au plan comptable marocain (CGNC) et à préparer les déclarations. Il n'est ni certifié ni homologué par l'administration, et les déclarations (TVA, IS, CNSS, IR) se déposent toujours sur les portails officiels (DGI, Damancom).

---

## Sommaire

1. [Premiers pas](#1-premiers-pas)
2. [Tableau de bord](#2-tableau-de-bord)
3. [Facturation](#3-facturation)
4. [Comptabilité](#4-comptabilité)
5. [Personnel & Paie](#5-personnel--paie)
6. [Parcours pas à pas](#6-parcours-pas-à-pas)
7. [Questions fréquentes et messages](#7-questions-fréquentes-et-messages)
8. [Ce que HisabPro ne fait pas encore](#8-ce-que-hisabpro-ne-fait-pas-encore)

---

## 1. Premiers pas

### 1.1 Se connecter, choisir la société et l'exercice

- Connectez-vous avec votre e-mail et votre mot de passe.
- En haut de l'écran :
  - le **sélecteur de société** permet de passer d'une société à l'autre si vous en gérez plusieurs ;
  - le **sélecteur d'exercice** (« 2026 — Ouvert ») choisit l'année affichée. Un exercice clôturé reste consultable mais n'accepte plus d'écriture.

### 1.2 Les rôles des utilisateurs

| Rôle | Ce qu'il peut faire |
|---|---|
| **Administrateur** | Tout, y compris les paramètres, les utilisateurs et les habilitations Personnel. |
| **Comptable** | Saisir, valider, comptabiliser, déclarer. |
| **Consultation seule** | Lire sans rien modifier. |
| **Personnel seul** | Accès limité au module Personnel & Paie (salariés, paie). |

Les utilisateurs se gèrent dans **Paramètres → Utilisateurs**.

### 1.3 Les réglages à faire une fois (menu Paramètres)

| Onglet | À renseigner |
|---|---|
| **Fiche société** | Raison sociale, forme juridique, IF, ICE, RC, patente, n° CNSS, adresse, logo (repris sur les PDF). |
| **Modules** | Activer Facturation, Comptabilité, Paie / GRH selon vos besoins. |
| **Fiscalité** | Régime de TVA (encaissement ou débit) et périodicité (mensuelle ou trimestrielle). |
| **Comptes bancaires** | Chaque banque utilisée, pour que les règlements arrivent sur le bon compte. |
| **Facturation** | Préfixes et présentation des factures, avoirs et règlements. |
| **Utilisateurs** | Inviter vos collaborateurs et leur donner un rôle. |
| **Sociétés liées** | Relier plusieurs sociétés que vous gérez. |
| **Sécurité & contrôle**, **Mon compte** | Mot de passe et sessions. |

### 1.4 Préparer les données de base

1. **Plan de comptes** (Comptabilité → Plan de comptes) : le plan CGNC est fourni ; ajoutez seulement vos sous-comptes si besoin.
2. **Clients / Fournisseurs** (Facturation) : identité, coordonnées, **conditions de règlement** (délai), paramétrage comptable.
3. **Articles** (Facturation) : désignation, prix, taux de TVA, nature (bien stocké ou service), comptes comptables.
4. **Soldes d'ouverture** : si l'entreprise existait avant HisabPro, saisissez les soldes de départ (banque, caisse, clients, fournisseurs, capital…) par une écriture au journal **AN — À nouveau**. **Sans solde d'ouverture, la caisse est vide** et HisabPro refusera les paiements en espèces.

---

## 2. Tableau de bord

La page d'accueil résume l'activité de l'exercice : chiffre d'affaires, ventes par article, dernières écritures.

Le bloc **« À faire »** liste ce qui attend une action, avec un lien direct :

- écritures en brouillon à valider ;
- factures échues non soldées ;
- chèques et effets à remettre ou à encaisser, effets fournisseurs à payer ;
- FEC bloqué par des anomalies ;
- déclaration de TVA de la période à enregistrer.

Si le bloc indique « Rien d'urgent », aucune action n'est en attente.

---

## 3. Facturation

### 3.1 Cycle commercial

C'est le cœur de la facturation. Les onglets suivent le parcours d'une vente ou d'un achat :

| Onglet | Rôle |
|---|---|
| **Devis** | Proposition au client. Actions : *Marquer envoyé*, *Marquer accepté*, *Acter le statut Expiré*, *Transformer le devis* (en bon de commande ou directement en facture), *Télécharger PDF*. |
| **Bons de commande** | Commande client ou fournisseur. Le détail montre *Commandé*, *Livré / réceptionné*, *Facturé*, *Reste à livrer*, *Reste à facturer*. Actions : créer un bon de livraison ou de réception sur le reliquat, *Facturer directement la commande*. |
| **Bons de livraison** | Ce qui part chez le client. Actions : confirmer l'expédition, *Confirmer la remise au client*, *Facturer tout ou partie du reliquat*. |
| **Réception client** | Documents reçus du client et retours client. |
| **Bons de réception** | Ce que vous recevez d'un fournisseur. Actions : *Marquer réceptionné*, *Retour fournisseur*, *Créer la facture fournisseur depuis ce bon de réception*. |
| **Factures** | Raccourci vers les factures du cycle. |
| **Règlements** | Tous les paiements reçus et émis (voir 3.3). |

**Vente classique** : Devis → accepté → Bon de commande → Bon de livraison → Facture → Règlement.
**Achat classique** : Bon de commande fournisseur → Bon de réception → Facture fournisseur → Règlement.
Chaque étape est facultative : on peut créer une facture directement.

### 3.2 Factures

**Créer une facture** (bouton *Créer une facture*) :

- **Type** : vente ou achat.
- **Tiers**, **date**, **délai de paiement** : l'échéance se calcule automatiquement (*Auto*), ou se saisit à la main. Un **échéancier** est possible (boutons *50 / 50*, *30 / 40 / 30*, *4 × 25 %*).
- **Lignes** : article ou désignation libre, quantité, prix HT, taux de TVA, remise éventuelle.
- **Retenue à la source** (RAS) si elle s'applique.
- Pour un achat, le **N° de facture du fournisseur** est obligatoire avant validation.

**Le cycle de vie d'une facture** :

1. **Brouillon** : modifiable librement.
2. **Valider** : la facture devient définitive et reçoit son numéro.
3. **Comptabiliser** : HisabPro crée l'écriture comptable (clients ou fournisseurs, ventes ou achats, TVA). Cette écriture arrive **en brouillon dans le Journal**.
4. Dans le **Journal**, *Valider les brouillons* rend l'écriture définitive.

Une facture validée ne se modifie plus : pour la corriger, on émet un **avoir**. Autres actions : *Dupliquer*, télécharger le PDF, joindre des pièces.

Statuts : *En attente*, *Part. payée*, *Payée*, *En retard*, *Annulée*.

### 3.3 Règlements

Un règlement s'enregistre depuis la facture ou depuis **Cycle commercial → Règlements** :

- **Montant**, **date**, **mode** : virement, chèque, effet, espèces.
- **Référence** (n° de chèque, de virement…) et **banque** concernée.
- Option **comptabiliser** : crée l'écriture de banque (BQ), de caisse (CA) ou d'effet, en brouillon dans le Journal.

Ce qu'il faut savoir :

- **Chèque client** : il va d'abord « en portefeuille », puis se suit dans **Effets & Chèques** (remise à l'encaissement, puis encaissé ou rejeté).
- **Effet fournisseur** : il reste « à payer » jusqu'à son échéance, puis se règle depuis **Effets & Chèques**.
- **Espèces** : la caisse doit contenir assez d'argent à la date du paiement. Sinon, HisabPro refuse et indique le solde disponible (voir la [question 7.1](#71-pourquoi-hisabpro-refuse-mon-paiement-en-espèces-)).
- **Erreur de règlement** : utilisez *Annuler par contrepassation* ; HisabPro passe l'écriture inverse, rien n'est effacé.
- Un règlement peut couvrir plusieurs factures d'un même tiers (*Ventiler par tiers*).

### 3.4 Avoirs

Un avoir corrige une facture validée : retour de marchandise, remise après facture, correction de prix, autre avoir financier. On choisit la **facture d'origine**, la **nature** et le montant (en pourcentage ou en montant fixe). Ensuite l'avoir peut être **utilisé** sur une autre facture ou **remboursé**. Statuts : *Émis*, *Utilisé*, *Remboursé*, *Annulé*.

### 3.5 Acomptes

Un acompte est une avance reçue d'un client ou versée à un fournisseur avant la facture. On le saisit (date, montant, mode, traitement de la TVA), puis on l'**impute** sur la facture le moment venu. Statuts : *Disponible*, *Partiellement imputé*, *Imputé*, *Annulé*.

### 3.6 Effets & Chèques

Suivi de tous les chèques et effets, filtrables par statut : en portefeuille, à l'encaissement, encaissés, rejetés ou impayés, effets à payer, payés. Chaque action (remettre, encaisser, payer) enregistre la date réelle de l'opération et produit l'écriture correspondante.

### 3.7 Situation financière

Vue d'ensemble du recouvrement : créances clients, clients en retard, dettes fournisseurs, taux de règlement, chèques et effets en portefeuille, à l'encaissement, à payer.

### 3.8 Délais de paiement

Suivi des délais de paiement par facture et par tiers, avec les retards. Le bouton *Compléter* permet de renseigner les informations manquantes.

### 3.9 Clients / Fournisseurs

Fiche de chaque tiers : identité (ICE, IF), coordonnées, **conditions de règlement**, **paramétrage comptable** (compte client 3421 ou fournisseur 4411 et compte auxiliaire), délai de paiement.

### 3.10 Articles

Fiche article : informations générales, prix et fiscalité (TVA), emballage et transport, nature (stocké ou non) et comptes comptables de vente et d'achat.

### 3.11 Inventaire & stock

- **Comptage physique** à une date donnée.
- **Valeur du stock** et **mouvements**, valorisés au coût moyen pondéré (CMUP).
- **Rapprochement comptable** entre le stock physique et la comptabilité.

---

## 4. Comptabilité

### 4.1 Journal

C'est la liste de toutes les écritures, quelle que soit leur origine (factures, règlements, paie, saisie manuelle).

**Brouillon ou définitive** :

- une écriture **brouillon** se modifie et se supprime, et n'a pas de numéro ;
- une écriture **définitive** (validée) reçoit un numéro (par exemple `CA-2026-0001`) et ne se modifie plus. Pour la corriger, on la **contrepasse** : HisabPro crée l'écriture inverse, et les deux restent visibles (piste d'audit).

**Les journaux** : AC Achats, VT Ventes, BQ Banque, CA Caisse, OD Opérations diverses, AV Avoirs, AN À nouveau, EN Encours, AE À encaisser, AM Amortissements, TV TVA, PR Provisions, CL Clôture, SA Salaires.

**Saisir une écriture** (*Nouvelle écriture*) : date, journal, référence du justificatif, libellé, puis les lignes (compte, débit ou crédit). L'écriture doit être **équilibrée** (total débit = total crédit). La case *Valider immédiatement* la rend définitive tout de suite.

**Valider les brouillons** : valide en une fois les brouillons affichés, dans l'ordre chronologique. Les écritures refusées sont listées avec la raison (écriture déséquilibrée, tiers manquant, caisse insuffisante…).

Autres fonctions : filtres par journal, par date, regroupement par jour, mois ou trimestre ; justificatifs joints ; *Imprimer* ; *Exporter CSV* ; **export FEC** (écritures définitives uniquement).

### 4.2 Plan de comptes

Le plan comptable CGNC de la société. Vous pouvez y ajouter des sous-comptes. Quand un compte est choisi dans une écriture, son libellé s'affiche automatiquement.

### 4.3 Grand livre

Tous les mouvements, compte par compte, avec les soldes d'ouverture et cumulés, sur une période. Export CSV.

### 4.4 Balances

| Onglet | Contenu |
|---|---|
| **Balance générale** | Total des débits, crédits et soldes de chaque compte. |
| **Balance âgée** | Créances et dettes par ancienneté. |
| **Balance auxiliaire** | Détail par client et par fournisseur. |
| **Balance résultat** | Comptes de charges et de produits. |
| **Balance comparative** | Comparaison avec l'exercice précédent. |

Exports Excel et PDF.

### 4.5 Lettrage

Le lettrage relie une facture à son règlement sur un compte client ou fournisseur : les montants exactement opposés sont associés par un code. Un **règlement partiel** laisse le code ouvert jusqu'au solde complet. On peut *délettrer* en cas d'erreur.

### 4.6 Rapprochement bancaire

Comparez votre relevé bancaire avec la comptabilité. Le relevé se saisit à la main (*Saisie manuelle*) ou s'importe (*Import Excel / CSV*). On pointe ensuite chaque ligne avec l'écriture correspondante ; les écarts restants indiquent une opération oubliée ou une erreur.

### 4.7 Immobilisations

Registre des immobilisations : acquisition (catégorie, comptes, date, valeur), puis **dotations aux amortissements**, calculées et générées depuis l'écran (journal AM). En fin de vie : **Cession / mise au rebut**, avec un aperçu du résultat de sortie, puis *Encaisser la cession*.

### 4.8 Déclaration TVA

La page reprend la TVA de la période selon votre régime (encaissement ou débit) et votre périodicité. Une barre de navigation mène à chaque section :

- **Déclaration** : *Synthèse* (TVA collectée, récupérable, crédit antérieur, TVA due ou crédit), *Détail par taux*, *Préparation DGI* (les montants à reporter).
- **Dépôt** : HisabPro **prépare** la déclaration ; **le dépôt se fait sur le portail de la DGI**. Une fois déposée, enregistrez la **date** et la **référence du dépôt** : la période est alors figée. Une erreur se corrige par une **rectificative**, avec un motif.
- **RAS TVA** : retenues à la source sur la TVA.
- **Paramètres** : régime et périodicité.

### 4.9 Résultat fiscal / IS

Le passage du résultat comptable au résultat fiscal, puis le calcul de l'impôt :

1. résultat comptable avant IS ;
2. **réintégrations** et **déductions** fiscales ;
3. **déficit antérieur** imputé ;
4. bénéfice fiscal imposable et **IS théorique** ;
5. **cotisation minimale** (CM) ;
6. acomptes versés, retenues et crédits ;
7. reste à payer ou crédit.

Une fois les chiffres vérifiés, la **liquidation** est confirmée et figée.

### 4.10 Liasse fiscale

Le dossier fiscal annuel : bilan (actif et passif), CPC, état des soldes de gestion, tableau de financement, état des informations complémentaires (ETIC, tableaux T3 à T25), passage fiscal, IS et CM.

La section **Contrôles de finalisation** liste ce qui empêche de finaliser : balance déséquilibrée, brouillons restants, exercice non clôturé, liquidation IS non confirmée, **caisse créditrice**, etc. Chaque contrôle indique quoi faire. Une fois tous les contrôles au vert, la liasse se finalise et s'archive. L'envoi électronique (EDI / SIMPL-IS) n'est pas encore activé : la liasse se dépose sur le portail de la DGI.

### 4.11 Clôture d'exercice

En fin d'année :

1. vérifier les contrôles d'inventaire (stock physique et immobilisations rapprochés de la comptabilité) ;
2. passer les **ajustements** de fin d'exercice (charges et produits à rattacher, provisions…) ;
3. calculer le **résultat** comptable puis net après impôt ;
4. enregistrer l'**affectation du résultat** : décision ou PV, réserve légale, autres réserves, report à nouveau, dividendes ;
5. clôturer : HisabPro génère les écritures de clôture et les **à-nouveaux** de l'exercice suivant.

### 4.12 Livre d'inventaire

Document annuel regroupant le bilan (actif et passif), la synthèse du CPC, l'inventaire des stocks et des immobilisations, les écritures d'inventaire et la balance des comptes de bilan.

---

## 5. Personnel & Paie

### 5.1 Mettre la paie en service (une seule fois)

À la première ouverture d'une page Paie, un encadré **« Mise en service de la paie »** indique ce qui manque : module activé, protection des données du personnel, habilitations. Un administrateur clique sur **« Tout activer maintenant »**.

La case **« Je gère seul la paie »**, cochée par défaut, active la **validation par une seule personne** : dans une petite entreprise, l'administrateur peut préparer **et** valider lui-même (chaque décision reste enregistrée à son nom). Ce réglage se change ensuite dans **Personnel → Habilitations → Mode de validation**. Dans tous les cas, un salarié ne peut jamais valider ses propres données.

### 5.2 Paie du mois : la page de départ

Choisissez le mois. La page affiche les étapes dans l'ordre, chacune avec son état (*Fait*, *En cours*, *À faire*, *Après l'étape précédente*) et un bouton vers le bon écran :

1. Salariés
2. Paramètres de paie (cotisations)
3. Primes et variables du mois
4. Calcul du brut
5. Cotisations sociales
6. Bases fiscales
7. Impôt sur le revenu (IR)
8. Bulletins de paie
9. Comptabilisation
10. Paiement des salaires

**« Calculer la paie du mois »** fait les étapes 4 à 8 en une fois pour tous les salariés actifs. Les hypothèses sont affichées avant le calcul :

- salaire de base soumis à 100 % à la CNSS et à l'AMO, et imposable à 100 % (les primes suivent la règle de leur rubrique) ;
- frais professionnels selon le CGI (article 59-I-A : 35 % ou 25 % selon le revenu annuel, plafond 35 000 DH par an, soit 2 916,66 DH par mois) ;
- personnes à charge reprises de la fiche du salarié.

Le résultat s'affiche salarié par salarié. Un salarié incomplet est écarté avec la raison exacte (par exemple « Personnes à charge non renseignées »), sans bloquer les autres. Relancer le calcul ne refait pas un bulletin déjà établi.

### 5.3 Personnel

- **Salariés** : fiche, contrat, rémunération, date d'entrée, n° CNSS, situation familiale et **personnes à charge** (indispensable pour l'IR). Chaque modification est une **demande** qui doit être validée (par une autre personne, ou par vous-même en validation unique).
- **Reprendre un salarié déjà enregistré** : reprend une fiche existante sans tout ressaisir.
- **Demandes à traiter** : les modifications en attente de validation.
- **Habilitations** (administrateur) : qui peut voir l'identité, voir les salaires, préparer, valider ; mode de validation.

### 5.4 Éléments de paie

- **Catalogue** : les **rubriques** (primes, indemnités, heures supplémentaires…), avec leur traitement CNSS, AMO et IR.
- **Variables mensuelles** : les montants du mois pour chaque salarié (une prime de novembre, par exemple), à soumettre puis approuver. Sans variable, le brut se calcule sur le seul salaire de base.

### 5.5 Charges sociales

- **Taux et plafonds** : les cotisations. Le bouton **« Charger le modèle CNSS (à vérifier) »** propose les 5 cotisations du secteur privé, avec les taux relevés sur cnss.ma et leur déductibilité IR (CGI article 59) :

  | Cotisation | Salarié | Employeur | Base |
  |---|---|---|---|
  | Prestations sociales court terme | 0,52 % | 1,05 % | plafonnée à 6 000 DH |
  | Prestations sociales long terme | 3,96 % | 7,93 % | plafonnée à 6 000 DH |
  | Prestations familiales | — | 6,40 % | salaire total |
  | AMO | 2,26 % | 2,26 % | salaire total |
  | Solidarité AMO | — | 1,85 % | salaire total |

  **Relisez-les, puis approuvez-les une par une** : ce sont des propositions, à vérifier par rapport aux taux en vigueur. La taxe de formation professionnelle n'est pas incluse.
- **Calcul des cotisations** : l'historique des calculs mensuels.

### 5.6 Traitement, Fiscalité salariale

Ces écrans montrent le détail des étapes, et servent à contrôler un cas précis ou à faire le calcul étape par étape :

- **Traitement de la paie** : calcul du brut du mois.
- **Fiscalité salariale** : *Bases fiscales* (salaire imposable), *IR du mois* (salarié par salarié), *Cumuls et frais annuels*, *Contrôle annuel IR*.

### 5.7 Bulletins de paie

Un bulletin par salarié et par mois : brut, cotisations, revenu net imposable, IR, retenues sur avances, **net à payer**, coût employeur. On peut l'**imprimer**. Un bulletin validé est figé : pour le corriger, on l'annule puis on l'établit de nouveau (tant qu'il n'est ni comptabilisé ni payé).

### 5.8 Avances & prêts

Registre des avances sur salaire et des prêts, avec la retenue mensuelle prévue. Le remboursement se fait par des retenues sur les bulletins. Le versement se comptabilise (débit 3431).

### 5.9 Comptabilisation, Paiements, États

- **Comptabilisation** : une écriture par mois au journal des salaires (SA), en brouillon. Au débit : 6171 rémunérations, 6174 charges patronales. Au crédit : 4441 CNSS/AMO, 44525 IR, 3431 avances, 4432 nets à payer.
- **Paiements** : sélectionnez les salariés à payer (virement, chèque ou espèces). HisabPro prépare l'écriture de paiement (débit 4432). La CNSS et l'IR se règlent depuis le Journal, après les déclarations sur Damancom et SIMPL.
- **États & reporting** : récapitulatif mensuel (brut, CNSS/AMO et IR à verser, nets, coût employeur) et **livre de paie** exportable en CSV.

---

## 6. Parcours pas à pas

### 6.1 Ma première vente, jusqu'au paiement

1. **Clients / Fournisseurs** : créez le client.
2. **Factures** → *Créer une facture* : type **vente**, le client, les lignes. Enregistrez.
3. **Valider**, puis **Comptabiliser**.
4. Le client paie par virement : **Règlements**, montant, mode *virement*, votre banque, *comptabiliser*.
5. **Journal** → *Valider les brouillons*.
6. La facture passe en *Payée*. Facultatif : **Lettrage** pour relier facture et règlement.

### 6.2 Un achat payé en espèces

1. **Avant tout** : la caisse doit contenir l'argent. Si ce n'est pas déjà fait, saisissez son alimentation au **Journal** (journal CA), par exemple :
   - débit 5161 Caisses ;
   - crédit 5141 Banques (retrait d'argent à la banque), **ou** 4463 Comptes courants des associés (apport d'un associé), **ou** 1111 Capital social (libération du capital).
2. **Factures** → type **achat**, le fournisseur, son **n° de facture**, les lignes. **Valider**, **Comptabiliser**.
3. **Règlement** en **espèces** à la date du paiement.
4. **Journal** → *Valider les brouillons*.

### 6.3 Déclarer la TVA du mois

1. Vérifiez que les factures du mois sont validées et comptabilisées, et que leurs écritures sont validées.
2. **Déclaration TVA**, choisissez la période : contrôlez la *Synthèse* et le *Détail par taux*.
3. *Préparation DGI* : reportez les montants sur le portail de la DGI et déposez.
4. Revenez dans HisabPro : **Dépôt**, saisissez la date et la référence du dépôt.

### 6.4 Faire la paie de novembre

1. **Personnel & Paie → Paie du mois**, mois de novembre.
2. Si l'encadré de mise en service apparaît : *Tout activer maintenant*.
3. Étape 2 : **Charges sociales** → *Charger le modèle CNSS (à vérifier)*, relisez, approuvez.
4. Étape 1 : vos salariés, avec contrat, salaire et **personnes à charge**.
5. Étape 3 (facultatif) : les primes du mois dans **Éléments de paie → Variables**.
6. **Calculer la paie du mois**. Corrigez les salariés signalés « À compléter », puis relancez.
7. **Comptabilisation** du mois, puis **Paiements**, puis **Journal** → *Valider les brouillons*.

### 6.5 Clôturer l'exercice

1. **Journal** : plus aucun brouillon.
2. **Inventaire & stock** et **Immobilisations** : comptage et rapprochements.
3. **Résultat fiscal / IS** : vérifiez puis confirmez la liquidation.
4. **Clôture d'exercice** : ajustements, résultat, affectation, clôture.
5. **Liasse fiscale** : contrôles au vert, finalisation, puis dépôt sur le portail de la DGI.

---

## 7. Questions fréquentes et messages

### 7.1 Pourquoi HisabPro refuse mon paiement en espèces ?

Message : *« Caisse insuffisante (5161) au … : solde disponible … DH »*.

Une caisse contient de l'argent physique : elle ne peut **jamais** être créditrice. Enregistrez d'abord l'argent qui y entre (solde d'ouverture, apport, retrait de la banque), avec une date antérieure ou égale au paiement (voir le [parcours 6.2](#62-un-achat-payé-en-espèces)). Une **banque**, elle, peut être créditrice (découvert) : elle apparaît alors au passif du bilan.

### 7.2 Ma caisse est déjà créditrice, que faire ?

Rien n'est à supprimer : ajoutez l'entrée d'argent manquante avec une date antérieure ou égale à la sortie, ou annulez le paiement erroné par contrepassation. Le contrôle « Aucune caisse créditrice » de la liasse repasse alors au vert.

### 7.3 Mon écriture ne se valide pas

- **Déséquilibrée** : le total des débits doit égaler le total des crédits.
- **Tiers manquant** : une ligne sur un compte client (3421) ou fournisseur (4411) doit être rattachée à un tiers.
- **Brouillons plus anciens** : les écritures se valident dans l'ordre chronologique ; validez d'abord les plus anciennes (*Valider les brouillons* les traite dans l'ordre).
- **Exercice ou période clôturé** : on ne peut plus y écrire ; passez la correction sur une période ouverte.

### 7.4 Je me suis trompé sur une écriture validée

On ne modifie pas une écriture définitive : **contrepassez-la** (bouton *Contrepasser* dans le Journal), puis saisissez la bonne écriture. Les deux restent visibles, c'est la piste d'audit.

### 7.5 Quelle différence entre « valider » une facture et « valider » une écriture ?

- **Valider une facture** la rend définitive et lui donne son numéro.
- **Comptabiliser** crée son écriture, en brouillon.
- **Valider l'écriture** au Journal la rend définitive et lui donne son numéro comptable.

### 7.6 Pourquoi un salarié est « À compléter » dans la paie ?

La raison est affichée : personnes à charge non renseignées, entrée ou sortie en cours de mois, contrat ou salaire non validé, prime non approuvée, cotisation non approuvée… Complétez la fiche ou la donnée indiquée, puis relancez le calcul.

### 7.7 Pourquoi une page Paie affiche « Mise en service de la paie » ?

La paie n'est pas encore activée pour cette société, ou vos habilitations ne suffisent pas. Un administrateur clique sur *Tout activer maintenant*, ou vous accorde les droits dans **Personnel → Habilitations**.

---

## 8. Ce que HisabPro ne fait pas encore

- **Dépôts officiels** : TVA, IS, liasse, CNSS et IR se déposent sur les portails (DGI, Damancom, SIMPL). HisabPro prépare les montants. L'EDI / SIMPL-IS n'est pas activé.
- **Paie** :
  - pas de prorata pour une entrée ou une sortie en cours de mois ;
  - pas de taux de frais professionnels spéciaux (journalistes, VRP, navigants…) ;
  - pas de régularisation IR annuelle ;
  - pas de taxe de formation professionnelle ;
  - 50 salariés au maximum par calcul.
- **Certification** : HisabPro n'est ni certifié ni homologué. Les taux et règles proposés (CNSS, IR, TVA) restent à vérifier par l'utilisateur au regard des textes en vigueur.
