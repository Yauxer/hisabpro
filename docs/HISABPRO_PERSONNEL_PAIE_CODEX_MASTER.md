# HISABPRO — MASTER SPEC CODEX — MODULE PERSONNEL & PAIE (MAROC)

> **Type :** cahier des charges fonctionnel, comptable et technique + feuille de route exécutable par Codex  
> **Version :** 1.0 — 27/10/2026  
> **Statut :** spécification de référence, **pas une preuve d'implémentation**  
> **Emplacement conseillé dans le dépôt :** `docs/HISABPRO_PERSONNEL_PAIE_CODEX_MASTER.md`  
> **Périmètre :** Maroc — gestion du personnel **strictement nécessaire à la paie, aux obligations sociales/fiscales et à la comptabilité**  
> **Devise de base :** MAD ; exercice annuel ; multi-société

---

## 0. MODE D'EMPLOI POUR CODEX — À LIRE AVANT TOUTE MODIFICATION

**Ce fichier est la référence de périmètre et de séquencement pour l'ensemble du projet Personnel & Paie.** Il ne remplace ni l'audit du code existant, ni la réglementation officielle, ni une validation métier par un professionnel de la paie marocaine.

1. Inspecter **le dépôt réel** avant de proposer du code : backend, frontend, PostgreSQL, migrations, conventions, services de comptabilité/fiscalité/trésorerie, auth, tests. Ne pas inventer l'arborescence ni présumer qu'une API ou une table existe.
2. Identifier les composants réutilisables et éviter un deuxième moteur de journaux, de paiements, d'exercices, de verrouillage ou de RBAC.
3. **Ne travailler que sur le lot et la sous-étape explicitement demandés.** Ne pas implémenter tous les lots en une session. Commencer par le **Lot 0** si aucun lot n'a été désigné.
4. Avant d'écrire le code : présenter le périmètre de la sous-étape, les fichiers potentiellement impactés, dépendances, migrations, risques, critères de recette. Si une décision fonctionnelle est indispensable, consigner l'hypothèse dans la restitution au lieu de coder une règle arbitraire.
5. Après chaque sous-étape : tests ciblés + tests de non-régression pertinents, échec/limites explicités, **ZIP différentiel contenant exclusivement les fichiers ajoutés/modifiés** avec l'arborescence exacte du dépôt, récapitulatif court et prochaine étape. Ne jamais remplacer le ZIP différentiel par un ZIP complet du projet.
6. Distinguer obligatoirement **tests automatisés**, **tests API**, **build frontend**, **tests navigateur** et **validation sur PostgreSQL réel**. Ne jamais annoncer une vérification non réalisée.
7. Aucune modification de données métier de production pour des essais sans consentement exprès. Les migrations doivent être sûres, reproductibles, idempotentes si pertinent, et sans destruction des données historiques. Sauvegarde et procédure de retour arrière à étudier.
8. Ne jamais figer dans le code un taux, un plafond ou une exonération sociale/fiscale non vérifié(e). La conformité réglementaire peut bloquer la validation du lot 3/5.
9. Le projet HisabPro a déjà des écritures comptables et exercices réels : **préserver l'existant**. Les règles déjà retenues par l'utilisateur (p. ex. écritures manuelles sans référence de pièce obligatoire, exercice annuel, périodes verrouillées) ne doivent pas être cassées par le module de paie.
10. Ne pas traiter ce document comme une autorisation d'effectuer des paiements bancaires ou dépôts de déclarations réels. Le système devra préparer, faire approuver, puis tracer des actions opérées par un utilisateur autorisé.

### Commande de départ conseillée pour Codex

> « Lis intégralement `docs/HISABPRO_PERSONNEL_PAIE_CODEX_MASTER.md`. Commence **uniquement par le LOT 0** : audit du code et des dépendances, cartographie des tables/services existants, modèle de données proposé, matrice RBAC et plans de migrations/tests. Ne développe pas encore le moteur de paie ni les formulaires tant que l'architecture n'a pas été examinée. Présente les points de décision, puis la proposition de sous-étape LOT 1A. Respecte les ZIPs différentiels, sans créer de doubles services comptables. »

---

## 1. OBJECTIF ET LIMITES

**Produit visé :** un module intégré « **Personnel & Paie** », et **non un SIRH complet**. Il doit permettre de : créer un salarié ; configurer ses conditions de rémunération ; saisir les variables ; calculer et valider la paie ; établir bulletins/livre de paie ; calculer IR et cotisations ; gérer avances/prêts/notes de frais ayant un impact financier ; préparer les déclarations ; payer et rapprocher ; comptabiliser ; arrêter les comptes ; produire les états.

**Explicitement hors périmètre :** recrutement/ATS, gestion de carrières, évaluations, formation, organigramme avancé, portail salarié/manager, pointage matériel quotidien, planning d'équipes, workflow complet de demandes de congé. **Exception limitée :** enregistrer heures/absences/congés/départs/contrats si nécessaires aux calculs ou charges à payer.

**Deux modes cibles :** (A) paie calculée dans HisabPro ; (B) paie externe importée avec contrôles et comptabilisation — ce second mode relève normalement du Lot 7, avec un parcours accéléré possible si priorisé explicitement.

### Rubriques visibles dans le menu

| N° | Rubrique | Rôle métier |
|---|---|---|
| 01 | Personnel | Création et suivi financier des salariés |
| 02 | Éléments de paie | Rémunérations et variables ; catalogue des primes et indemnités |
| 03 | Traitement de la paie | Campagnes, calcul, bulletins et livre |
| 04 | Charges sociales | CNSS, AMO, retraite/mutuelle si applicables, déclaration |
| 05 | Fiscalité salariale | IR retenu et déclarations fiscales |
| 06 | Avances & prêts | Avances, acomptes, prêts et retenues |
| 07 | Paiements | Salaires, organismes et État, banques, rapprochement |
| 08 | Comptabilisation | Journal de paie, OD, imputations, ajustements |
| 09 | États & reporting | Masse salariale, dettes, rapprochements, justificatifs |

**Clôture & régularisations** = sous-ensemble transversal rattaché aux rubriques 08 et 09, sans obligation d'en faire une 10e rubrique de navigation.

---

## 2. RÉPARTITION OFFICIELLE DES LOTS PAR RUBRIQUE — NE PAS CHANGER SANS DÉCISION

| Lot | Rubriques couvertes | Objectif livrable |
|---|---|---|
| **LOT 0** | Transversal 01–09 | Audit, architecture, modèle de données, sécurité, workflows, stratégie de tests |
| **LOT 1** | **01 Personnel** | Salariés, dossier, contrat utile, rémunération contractuelle, approbation, historique |
| **LOT 2** | **02 Éléments de paie** | Catalogue des rubriques, primes/indemnités, variables, assiettes, justificatifs, exonérations paramétrées |
| **LOT 3** | **03 Traitement**, **04 Charges sociales (calcul)**, **05 Fiscalité salariale (calcul)** | Campagnes, brut/net, cotisations, IR, bulletins et livre de paie |
| **LOT 4** | **06 Avances & prêts**, **08 Comptabilisation** | Avances, prêts, retenues, journal PAI, écritures automatiques, correctifs ; notes de frais financières si retenues |
| **LOT 5** | **07 Paiements**, **04 Charges sociales (déclarations)**, **05 Fiscalité salariale (déclarations)** | Dettes à régler, virements, rapprochements, exports et suivi des déclarations |
| **LOT 6** | **09 États & reporting**, **08 Comptabilisation (clôture)** | Reporting, congés à payer, primes à payer, autres charges, provisions, extournes, rapprochements |
| **LOT 7** | Transversal | Import de paie externe, recette E2E, sécurité avancée, performance, UX, documentation |

**Attention :** 04 et 05 sont volontairement séparées en **calcul au lot 3** et **déclaration au lot 5** ; 08 est traitée au **lot 4** (paie courante) puis au **lot 6** (OD de clôture). C'est le même périmètre initial, simplement rendu explicite.

### Ordre recommandé

`LOT 0 -> LOT 1 -> LOT 2 -> LOT 3 -> LOT 4 -> LOT 5 -> LOT 6 -> LOT 7`

Chaque lot se développe en petites livraisons : **A = modèles/API/règles**, **B = interfaces/workflows**, **C = intégration/tests/recette**, avec subdivision supplémentaire pour les moteurs de calcul. Pas de développement simultané de trois lots entiers.

---

## 3. SÉCURITÉ, ACTEURS ET VALIDATIONS (CONTRÔLES TRANSVERSAUX)

### 3.1 Rôles cibles (à adapter au système RBAC existant)

- **Administrateur société :** paramètres généraux, habilitations, activation du module ; pas de droit automatique à approuver sa propre paie.
- **Gestionnaire personnel :** création/modification des salariés ; proposition de changement contractuel.
- **Gestionnaire paie :** saisie variables, simulations, préparation bulletins, cotisations, déclarations.
- **Responsable validation :** approbation des données sensibles, primes/avances/campagnes ; indépendant du préparateur pour opérations à risque.
- **Comptable :** paramétrage imputations, prévisualisation/validation des écritures, rapprochements et clôture.
- **Trésorier :** préparation/exécution de paiements selon délégations ; interdiction de changer une paie validée.
- **Auditeur / expert-comptable :** lecture restreinte et consultation des justificatifs/historiques, sans modification.

Rôles combinables dans petites entreprises **avec alertes de séparation des tâches** et, si possible, approbation par une deuxième personne pour création de bénéficiaires, changements de RIB, salaires, paies et paiements.

### 3.2 Matrice qui fait quoi

| Action | Prépare | Approuve / valide | Comptabilise / paye |
|---|---|---|---|
| Créer salarié | Gestionnaire personnel | Responsable validation | Aucune écriture |
| Modifier salaire/date d'effet/RIB | Gestionnaire personnel | Responsable validation | Aucune écriture tant qu'aucune dette n'est née |
| Paramétrer rubrique de paie | Gestionnaire paie | Responsable habilité | Compte de charge validé par comptable |
| Variables/primes exceptionnelles | Gestionnaire paie | Responsable validation | Lors de la paie seulement |
| Campagne mensuelle | Gestionnaire paie | Responsable validation | Comptable après approbation |
| Cotisations / IR | Gestionnaire paie | Responsable habilité | Comptable / trésorier selon opération |
| Avance ou prêt | Gestionnaire personnel/paie | Responsable validation | Trésorier pour versement, comptable pour écriture |
| Règlement salaire/CNSS/IR | Trésorier | Signataire autorisé | Trésorerie + comptabilité |
| OD de clôture | Comptable | Responsable comptable | Comptable habilité |

**Règles de sécurité minimales :** autorisation côté backend sur toute API ; `company_id` vérifié sur **chaque** lecture/écriture ; salariés d'une société invisibles dans une autre ; fichiers sécurisés ; RIB/CIN/numéros CNSS masqués dans listes/logs ; journal d'audit ; timestamps + auteur + motif ; protection des exports ; attention aux fichiers PDF en cache ; interdiction de supprimer une fiche reliée à une écriture ou un bulletin validé.

### 3.3 États métier

- Salarié : `BROUILLON -> A_VALIDER -> ACTIF -> SUSPENDU/SORTI` (avec rejet/retour brouillon contrôlé).
- Élément variable : `BROUILLON -> SOUMIS -> VALIDE/REJETE -> INTEGRE_A_PAIE`.
- Campagne : `BROUILLON -> CALCULEE -> A_CONTROLER -> APPROUVEE -> COMPTABILISEE -> PARTIELLEMENT_PAYEE/PAYEE` ; les statuts doivent refléter l'état réel, non simplement une action UI.
- Déclaration : `PREPAREE -> VALIDEE -> DEPOSEE_CONFIRME -> PAYEE/ECART`, avec justificatif de dépôt et paiement.
- Paiement : `PREPARE -> APPROUVE -> TRANSMIS -> EXECUTE_CONFIRME -> RAPPROCHE` ; **transmis ≠ exécuté**.
- OD clôture : `PROPOSEE -> CONTROLEE -> VALIDEE/REJETEE -> EXTORNEE_SI_APPLICABLE`.

Les états exacts et transitions doivent être formalisés en code et testés ; les écritures/comptabilisations confirmées ne sont jamais supprimées silencieusement.

---

## 4. LOT 0 — AUDIT & ARCHITECTURE (AVANT CODE MÉTIER)

### Sous-étapes

- **0A Audit :** arborescence réelle, modèles existants, conventions Python/JS, outils et tests, services journaux/écritures, exercice annuel, verrouillage, tiers/auxiliaires, banque/import relevés, PDFs, déclaration, RBAC, multi-société ; identifier points de réutilisation et risques.
- **0B Conception :** schéma de données, relations, clés uniques, dates d'effet, composants, contrats API, règles de sécurité et autorisations, mapping CGNC, workflows.
- **0C Plan d'intégration :** migrations, stratégies de reprise, plan de tests, cas de recette, critères de « terminé » par lot ; vérifier contraintes de l'UX existante.

### Entités conceptuelles (NOMS INDICATIFS, vérifier conventions du dépôt)

- `employee` : société, matricule, identité minimale, statut, date entrée/sortie, CNSS, coordonnées de paiement sécurisées.
- `employee_contract`, `employee_compensation_version` : salaire contractuel, périodicité, date d'effet, montant, nature, validateur ; **pas d'écrasement de l'ancien salaire**.
- `payroll_item_type`, `payroll_item_version` : rubriques, formule, affectations IR/CNSS, plafonds, justification, compte comptable, bornes de validité.
- `payroll_input` : éléments variables mensuels, source, justificatif, statut d'approbation.
- `payroll_campaign`, `payroll_statement`, `payroll_statement_line` : campagne, bulletins, lignes, versions de règles utilisées, snapshots immuables après validation.
- `social_rule_version`, `income_tax_rule_version`, `legal_rule_source` : fiscal/social distincts, taux/plafonds/date/texte/source, statut de validation juridique.
- `employee_advance`, `employee_loan`, `loan_installment` : avances/prêts, mouvements, imputations, échéanciers.
- `payroll_accounting_link` : lien unique et traçable entre campagne, paiement/OD et écriture de journal existante.
- `payroll_payment_link`, `payroll_declaration`, `payroll_declaration_line` : paiements réels, déclarations/états, soldes, confirmations.
- `leave_financial_balance`, `payroll_accrual`, `payroll_audit_event`, `employee_attachment` : droits financiers de congés, charges à payer, audit, justificatifs.

**Contraintes de conception :** `company_id` obligatoire sur les entités multi-sociétés ; unicité `(company_id, matricule)` ; unicité campagne ordinaire `(company_id, période, type)` avec autorisation explicite de campagnes complémentaires ; garantie d'idempotence de comptabilisation via une clé métier stable ; pièces stockées de manière sûre ; schéma extensible sans sur-collecte de données personnelles ; décimaux exacts (pas de `float` pour MAD) ; erreurs transactionnelles propres ; migrations non destructrices.

**Livrables de fin Lot 0 :** audit, schéma, matrice RBAC, règles de versionnement, mapping comptable initial, stratégie de migrations, parcours E2E, liste des points nécessitant arbitrage réglementaire/métier. **Aucune fonctionnalité n'est réputée livrée au seul terme de ce lot.**

---

## 5. LOT 1 — RUBRIQUE 01 : PERSONNEL

### Écrans

1. **Liste salariés** : matricule, nom, statut, date d'entrée, type de contrat, filtre société/statut, recherche/tri/pagination ou scroll ; rémunération masquée selon rôle.
2. **Créer un salarié** : matricule unique, nom/prénom, identifiants justifiés, date d'entrée, type/date contrat si applicable, numéro CNSS, régime AMO, régime retraite/mutuelle si applicable, salaire/périodicité, banque/RIB sécurisé, paramètres fiscaux pertinents, justificatifs.
3. **Fiche salarié** : identité utile, rémunérations successives, statut, paies, avances/prêts, paiements, pièces, journal des modifications.
4. **Validation / sortie** : demandes d'approbation, historique des changements et dates d'effet, désactivation ou sortie (les droits financiers sont calculés dans les lots suivants).

### Sous-étapes / droits / tests

- **1A :** tables + migrations + services/API, validation des champs et doublons, tests isolés.
- **1B :** liste, formulaire responsive sans défilement horizontal inutilisable, fiche, gestion des erreurs et états de chargement.
- **1C :** circuit approbation, historique, masquage, tests RBAC et multi-société.
- Gestionnaire du personnel crée ; responsable approuve ; comptable lit seulement ce qui lui est autorisé.
- Pas de salarié « actif pour paie » sans activation validée ; ne jamais supprimer un salarié déjà référencé ; modification du salaire conservée avec date d'effet ; changement de RIB soumis à contrôle renforcé.

**Écriture comptable : AUCUNE lors de la création ou modification administrative d'un salarié.**

**Recette :** créer trois salariés, refuser un doublon de matricule, modifier un salaire à effet futur, refuser une auto-approbation sensible, sortir un salarié, confirmer isolation multi-société et absence d'écriture comptable.

---

## 6. LOT 2 — RUBRIQUE 02 : ÉLÉMENTS DE PAIE ET EXONÉRATIONS

### Écrans

1. **Catalogue des rubriques** : salaire de base, ancienneté, primes, gratifications, transport, déplacements, panier, titres-repas, représentation, caisse, salissure, outillage, lait, téléphone, indemnités/avantages, heures supplémentaires, absences, rappels, régularisations, retenues autorisées.
2. **Paramétrage réglementaire** : pour chaque rubrique, nom/code, type (gain/retenue/remboursement), périodicité, formule, assiette IR, assiette(s) sociales, partie exonérable, plafond, unité (mensuel, journalier, pourcentage, SMIG horaire), dates d'effet, conditions, incompatibilités/non-cumul, justificatifs, référence juridique, statut de validation et compte de charge.
3. **Saisie variables** : salarié + période + quantité/montant + source + justificatif + statut + approbateur ; récurrence contrôlée pour éléments contractuels.
4. **Contrôles** : alertes de plafond, cumul interdit, doublon, période verrouillée, absence de preuve, formule invalide, montant négatif inapproprié.

### Sous-étapes

- **2A :** schéma catalogue + versionnement ; séparer **règles DGI** de **règles CNSS** ; gérer indemnité partiellement exonérée et partiellement soumise ; dictionnaire des pièces.
- **2B :** formulaires, listes, validation d'éléments variables ; récupération du salaire contractuel applicable au mois.
- **2C :** tests de calcul intermédiaire, contrôle des preuves, droits, changements de règles et dates d'effet.

**Qui valide ?** Gestionnaire paie saisit, responsable approuve les variables sensibles, expert métier valide les règles réglementaires, comptable valide comptes d'imputation.

**Écriture :** aucune à la simple saisie d'une variable. Son impact sur une charge peut provenir d'une paie approuvée ou d'une OD de clôture justifiée.

**Recette :** montant sous/au-dessus plafond ; IR et CNSS divergents ; prime seule ; non-cumul ; justificatif manquant ; modification du barème applicable seulement aux périodes futures ; montant dépassant plafond automatiquement ventilé (selon règles validées).

**Annexe réglementaire à implémenter en lot 2/3 : voir §14.**

---

## 7. LOT 3 — RUBRIQUES 03 + 04 (CALCUL) + 05 (CALCUL)

### Écrans

- **Campagnes** : période, société, type (normale/complémentaire/régularisation), état et actions.
- **Simulation par salarié** : salaire de base, rémunérations variables, brut, bases IR, bases CNSS/AMO/autres cotisations, parts salariales/patronales, net après obligations, retenues sur avances/prêts (structure prévue, intégration effective au lot 4), net à virer, coût employeur.
- **Anomalies** : salarié sans paramètres, fiche non approuvée, numéro requis absent, règle non validée, assiette négative inattendue, incohérence des totaux.
- **Bulletin PDF** et **livre de paie** conformes aux indications requises, exports contrôlés.
- **Comparaison période précédente**, historique de recalcul et approbation.

### Sous-étapes

- **3A :** structure de campagne, snapshots des données/règles, simulation du brut.
- **3B :** moteur des cotisations par branche, assiette et plafond ; taux versionnés ; cotisations salariales distinctes des cotisations patronales.
- **3C :** calcul IR, revenu net imposable, déductions/abattements/réductions légaux, arrondis, rappels.
- **3D :** cas complexes (entrée/sortie dans le mois, absence, temps partiel, régularisation, primes avec plafonds/conditions) ; calcul du net.
- **3E :** bulletins/livre PDF, workflow, verrouillage, tests réglementaires, comparatifs et non-régression.

### Règles essentielles

- Formules et règles **versionnées par date d'application**, référencées par campagne. **Ne pas réécrire les bulletins passés** lors du changement de barème.
- Montants monétaires en décimaux, politique d'arrondi explicite, distinction des arrondis par rubrique, des assiettes et du total.
- Sous-totaux contrôlés : rémunération brute, retenues salariales, IR, dette nette salariés, charges patronales, organisme/État.
- Deux « moteurs » distincts IR / social ; statut **NON_VALIDE_JURIDIQUEMENT** bloque une paie présentée comme conforme (mode simulation explicitement signalé possible).
- Aucun versement bancaire automatique ni déclaration automatique à ce stade.
- Sur campagne approuvée : snapshot gelé ; rectification par nouveau document/régularisation traçable.

**Qui fait quoi ?** Gestionnaire paie prépare/simule ; responsable approuve ; comptabilisation dans Lot 4.

**Écriture :** l'approbation peut préparer les montants à comptabiliser mais **ne doit pas contourner le workflow comptable**.

**Recette :** dossiers de référence Maroc validés (smig, plafond CNSS, IR, exonérations, cas frontières, retenues, embauche/sortie), égalités arithmétiques, bulletins cohérents, ancienne campagne stable après changement des taux. Tout barème utilisé en réel doit avoir sa preuve réglementaire.

---

## 8. LOT 4 — RUBRIQUES 06 + 08 : AVANCES, PRÊTS, NOTES DE FRAIS ET COMPTABILISATION

### Rubrique 06 — Avances & prêts

- Liste, création, approbation, décaissement, calendrier de remboursement, solde, remboursement partiel/anticipé, rattachement salarié, justificatifs.
- Distinguer **acompte sur rémunération acquise**, **avance sur salaire futur** et **prêt au personnel** ; gérer juridiquement les retenues, sans supposer qu'une retenue sur paie est toujours autorisée.
- En cas de sortie : solde et traitement documenté, sans prélèvement automatique non autorisé.
- **Notes de frais (si besoin)** : demande financière, pièces, approbation, remboursement, mapping nature/compte ; séparer frais professionnels remboursés et salaire/avantage imposable. Ne pas dériver vers un logiciel de déplacements.

### Rubrique 08 — Comptabilisation

- Paramétrer **journal PAI** (ou journal existant choisi par société) ; mapping 617/443/444/445/343/241/514 ; autorisations.
- Prévisualiser, contrôler et valider les écritures issues d'une campagne approuvée et des opérations d'avances/remboursements.
- Réutiliser API de journal/écriture/numérotation/validation/verrouillage déjà présentes. La référence de la campagne est une **traçabilité interne** ; ne pas imposer soudain une référence de pièce aux écritures manuelles du reste de HisabPro.
- Clé métier d'idempotence : campagne/version/type d'opération → écriture unique ; transaction atomique.
- Contrepassation/régularisation autorisée si correction nécessaire, jamais effacement d'une écriture validée.
- Définir centralisation comptable ou détail salarié avec état auxiliaire réconciliable et confidentialité.

### Sous-étapes

- **4A :** mapping des comptes + service d'écritures + tests équilibrage/idempotence/écritures en période bloquée.
- **4B :** écrans avances/acompte/prêt/échéancier, règlements et mouvements ; intégrer les retenues au **net à virer** et distinguer le net après retenues légales.
- **4C :** UI journal de paie, pièces, double-validation, rapprochement interne, tests E2E.

**Qui fait quoi ?** Gestionnaire paie prépare ; responsable approuve les avances ; trésorier décaisse ; comptable valide imputation/écriture.

**Recette :** campagne approuvée = écriture équilibrée unique ; double clic/idempotence ; avances comptabilisées puis déduites sans double charge ; prêt >12 mois affecté à une créance immobilisée appropriée ; correction par régularisation ; période close interdite.

---

## 9. LOT 5 — RUBRIQUES 07 + 04 (DÉCLARATIONS) + 05 (DÉCLARATIONS)

### Écrans et flux

1. **Dettes à payer** : net dû salariés, CNSS/AMO, retraite/mutuelle si applicables, IR ; états préparé/autorisé/transmis/exécuté/rapproché ; montants restants.
2. **Lots de virements** : préparation de fichiers bancaires si format disponible, sans présumer d'une API banque ; suivi des rejets et paiements partiels.
3. **Déclarations sociales** : états et exports selon formats applicables, notamment CNSS/Damancom ; population déclarée, assiettes, cotisations, périodes, dépôt confirmé, preuve.
4. **Déclarations IR salarial** : états de retenues et déclaration(s) annuelle(s) applicables ; export conforme à un format officiel **vérifié**, justificatif et date dépôt.
5. **Rapprochement** : lier chaque règlement réel aux écritures existantes et relevés importés ; proposer anomalies / écarts.

### Sous-étapes

- **5A :** suivi des dettes et paiements, API service trésorerie réutilisé.
- **5B :** exports sociaux, états IR et leur validation réglementaire.
- **5C :** liens bancaires, preuves dépôt/paiement, écarts et tests.

**Qui fait quoi ?** Gestionnaire paie prépare déclaration ; responsable habilité approuve ; trésorier prépare/exécute paiements ; comptable contrôle rapprochement.

**Écriture :** paiement débit des dettes correspondantes, crédit banque ; **ne pas créer de nouvelle charge** au paiement d'une paie déjà constatée.

**Recette :** paiement total/partiel/refusé ; pas de faux statut payé ; déclarations vs paie et comptes 444/445 cohérents ; aucun doublon de dette ; dépôt externe manuel traité comme tel, et non comme un appel API imaginaire.

---

## 10. LOT 6 — RUBRIQUES 09 + 08 (CLÔTURE)

### États & reporting (rubrique 09)

- Journal/livre de paie, détail masse salariale, coût employeur mensuel/annuel, par centre analytique si HisabPro le permet.
- Dettes salariales, IR, cotisations par période/organisme.
- Avances, acomptes, prêts par salarié, échéanciers et soldes.
- Variations mois N/N-1, bulletin → campagne → OD → règlement → banque.
- Rapprochements des comptes comptables (617, 343, 443, 444, 445), exports PDF/Excel accessibles selon droits.

### Clôture comptable

1. **Congés acquis non pris** : compteurs *strictement financiers* (droits, consommés, reliquats), valorisation selon droits applicables, charges patronales estimées le cas échéant.
2. **Primes/bonus acquis non encore traités** : charge à payer, vérifier absence dans paie courante.
3. **Salaires/heures de N enregistrés en N+1** : rattachement approprié à N.
4. **Dettes CNSS/IR** : vérifier les soldes, ne pas refaire une charge déjà passée.
5. **Indemnités de départ et risques sociaux** : distinguer dette certaine, charge à payer, provision pour risques (conditions et compte à valider selon le cas), information justificative.
6. **OD de régularisation** : prévisualisation, validation, lien à pièce, extourne N+1 lorsque approprié, sans double comptabilisation.
7. **Intégration états de synthèse/liasse** : réutiliser les soldes comptables existants ; les états RH alimentent les justificatifs, pas une seconde comptabilité.

### Sous-étapes

- **6A :** états et tableaux de contrôle.
- **6B :** moteur des propositions d'OD, provisions/charges à payer et extournes.
- **6C :** recette d'arrêté N et d'ouverture N+1 sur jeu isolé, rapprochements et accès.

**Qui fait quoi ?** Gestionnaire paie prépare base documentaire ; comptable propose OD ; responsable comptable valide. **Pas d'OD automatique définitive sans validation**.

**Recette :** décembre N ↔ janvier N+1 ; congés/primes non payés, détection des doublons, extournes, blocage exercice clôturé, soldes auxiliaires justifiés, intégration aux états financiers.

---

## 11. LOT 7 — IMPORTS, RECETTE ET FINALISATION

- Importer un état de paie externe (CSV/Excel ou format défini après analyse), mapper salariés, rubriques, exercices, période, comptes, organismes et IR.
- Détecter lignes manquantes, doublons, salariés inconnus, écarts de brut/net/cotisations ; validation humaine avant génération d'OD ; archiver état original et preuve d'import.
- Réaliser tests E2E sur parcours réel : salarié → rémunérations → paie → dettes → OD → règlement → banque → clôture.
- Audit de sécurité (fuites inter-sociétés, exports, permissions backend, accès aux pièces), performances, UX (scroll, colonnes stables, formulaires entièrement accessibles), aide utilisateur, monitoring.
- Ajouter un parcours d'**import comptable simplifié** plus tôt uniquement si l'utilisateur change explicitement les priorités.

**Recette :** import reproductible, sans écriture double ; cohérence des montants ; tests sur PostgreSQL réel dans environnement de validation ; rapport des limitations restantes ; non-régression de la comptabilité/facturation/fiscalité existantes.

---

## 12. PLAN COMPTABLE — RÈGLES DE GÉNÉRATION ET EXEMPLES

> Comptes ci-dessous issus du **CGNC / plan général marocain** et fournis comme **mapping initial à contrôler dans le plan de chaque société**. Le moteur doit valider compte actif et imputable avant toute OD. Les traitements sectoriels particuliers exigent validation dédiée.

| Compte CGNC | Usage ciblé |
|---|---|
| 61711 | Appointements et salaires |
| 61712 | Primes et gratifications |
| 61713 | Indemnités et avantages divers |
| 61714 | Commissions au personnel |
| 61741 | Cotisations de sécurité sociale (part employeur) |
| 61742 | Cotisations aux caisses de retraite (part employeur) |
| 61743 | Cotisations aux mutuelles (part employeur) |
| 61765 | Indemnités de préavis et de licenciement |
| 3431 | Avances et acomptes au personnel |
| 3438 | Autres créances courantes du personnel, selon nature |
| 2411 | Prêts au personnel **immobilisés** (>12 mois à l'origine selon critères CGNC) |
| 4432 | Rémunérations dues au personnel |
| 4437 | Charges du personnel à payer |
| 4441 | CNSS |
| 4443 | Caisses de retraite |
| 4445 | Mutuelles |
| 4447 | Charges sociales à payer |
| 4448 | Autres organismes sociaux |
| 44525 | État, IGR (dans le CGNC historique ; IR salarial) |
| 5141 | Banque |

### 12.1 Exemple pédagogique — Paie normale, sans avance

**Hypothèse purement illustrative, aucun taux légal implicite :** brut 100 000 ; cotisations salariales 6 000 ; IR 5 000 ; patronales 15 000 ; net dû 89 000 (MAD).

| Compte | Débit | Crédit |
|---|---:|---:|
| 6171 (subdiviser selon rubriques) | 100 000 | — |
| 6174 (subdiviser selon organismes) | 15 000 | — |
| 4432 | — | 89 000 |
| 444x (salariales + patronales) | — | 21 000 |
| 44525 | — | 5 000 |
| **TOTAL** | **115 000** | **115 000** |

**Contrôles :** total débit = crédit ; 6174 = charges patronales seules ; les cotisations salariales/IR ne sont **pas** une seconde charge ; la dette salariale est le net après retenues légales, avant récupération d'avance si journalisé séparément ; organismes à ventiler par type.

### 12.2 Avance sur salaire : 2 000 MAD

- Décaissement : **D 3431 / C 5141 : 2 000**.
- Récupération : **D 4432 / C 3431 : 2 000**.
- Paiement du reliquat : **D 4432 / C 5141 : montant restant**.
- **Ne pas débiter deux fois le 617** et ne pas déduire deux fois l'avance dans le net à virer.

### 12.3 Prêt au personnel

- Si prêt relevant des immobilisations financières : **D 2411 / C Banque**, remboursement **D Banque / C 2411** ; pour créances courantes, compte correspondant selon classification validée, éventuellement 3438.
- Échéancier, intérêts éventuels, retenues légales/autorisations et distinction capital/intérêts à paramétrer et valider.

### 12.4 Paiement après comptabilisation

- Salaires : **D 4432 / C 5141**.
- CNSS/organisme : **D 444x / C 5141**.
- IR salarial : **D 44525 / C 5141**.

### 12.5 Clôture — exemple congés/primes acquis et non encore comptabilisés

- Congés acquis non pris valorisés : **D 61713 (ou compte de charge approprié validé) / C 4437**.
- Charges patronales estimables liées : **D 6174 / C 4447** si les critères sont remplis.
- Prime annuelle due : **D 61712 / C 4437** (si non déjà traitée dans paie).
- Extourne N+1 selon schéma retenu et nécessité de neutraliser le doublon à la paie effective ; **une OD déjà passée ne doit pas être repostée**.
- Risque social incertain : analyser conditions de provision, **pas de provision automatique**.

### 12.6 Invariants de génération d'écritures

1. Écritures équilibrées au centime selon politique d'arrondi documentée.
2. Imputation sur **comptes actifs du plan de la société** ; journal/exercice/période ouverts et autorisés.
3. Lien réversible en consultation depuis campagne, bulletin, règlement, pièce et journal.
4. Comptabilisation **exactement une fois** par opération et version ; concurrence/retry contrôlés.
5. Aucun compte erroné utilisé comme « défaut silencieux ». Erreur lisible avec proposition de correction.
6. Mouvements validés immuables ; ajustements via écriture identifiable, pas de modification silencieuse.
7. Rapprochement entre dette due, montants payés et solde justifiable ; aucune charge réenregistrée au paiement.

---

## 13. SCHÉMA DE CALCUL DE PAIE — INVARIANTS

```
Fiche salarié validée + rémunération contractuelle en vigueur
  + variables approuvées (Lot 2)
  -> rémunération brute et éléments spécifiques
  -> calcul fiscal IR et calcul social CNSS/AMO/autres (moteurs distincts)
  -> parts salariales + retenue IR + parts patronales
  -> net après retenues légales / coût employeur
  -> récupération avances & prêts autorisés (Lot 4)
  -> NET À VIRER
  -> validation campagne (Lot 3)
  -> écritures de paie (Lot 4)
  -> déclarations et règlements (Lot 5)
  -> contrôle / régularisation / clôture (Lot 6)
```

**Attention aux doubles déductions :** net à payer en paie, acomptes déjà versés, retenues sur prêt, net bancaire ; définir explicitement le sens de chaque champ. Les bases IR et CNSS **ne se déduisent pas mécaniquement du salaire brut avec le même plafond** ; chaque règle s'applique individuellement. Contrôler les avantages en nature, remboursements sur pièces et rémunérations indirectes.

---

## 14. ANNEXE PRIORITAIRE — PRIMES/INDEMNITÉS ET EXONÉRATIONS 2026

**Contexte :** une infographie transmise le 27/10/2026 illustre des catégories de primes/indemnités et des « plafonds DGI/CNSS ». Elle constitue une **liste de besoins métier**, **pas une source réglementaire autonome**. Ne pas recopier ses chiffres automatiquement.

### 14.1 Catégories à prévoir dans le catalogue (Lot 2) et calculer (Lot 3)

| Famille | Rubrique(s) métier | Champs / contrôles nécessaires |
|---|---|---|
| Transport | Transport domicile-travail urbain / hors urbain | Zone, distance, transport employeur/voiture, plafond mensuel DGI/CNSS distinct, justificatifs, non-cumul |
| Déplacement professionnel | Forfait / frais au réel | Mission, trajet, dates, preuve, formule, plafond conditionnel, traitement fiscal et social |
| Repas | Prime panier en espèces | Jours éligibles, SMIG horaire à date d'effet, plafond en fonction des jours, non-cumul |
| Repas | Bons / titres-repas | Nombre de jours, montant/jour, % du brut imposable applicable, exclusions et non-cumul |
| Représentation | Indemnité de représentation | Fonction éligible, salaire de base, taux plafond distinct IR/CNSS, justificatifs |
| Fonction | Prime de caisse | Poste, barème plafonné, période, preuve et assiettes propres |
| Fonction | Indemnité de salissure | Conditions de poste, nombre de jours, formule/plafonds validés |
| Fonction | Prime d'outillage | Conditions de fonction et dépenses, plafond et preuve |
| Fonction | Indemnité de lait | Exposition/conditions réglementaires, plafond et preuve |
| Social | Gratifications à caractère social | Événement, plafonds annuel / période, cumul et preuve |
| Social | Aide médicale | Nature, justification et règles spécifiques |
| Frais pro | Frais de téléphone | Justificatifs professionnels, usage personnel/pro, plafond si applicable |
| Frais pro | Remboursements de frais divers | Nature, factures, ordre de mission, traitement remboursement vs avantage |
| Rupture | Indemnités de départ/licenciement | Qualification juridique, motifs, mode de calcul, plafond DGI et CNSS spécifiques |

**Doivent être extensibles au-delà de cette image** : autres catégories réglementaires de l'arrêté CNSS n° 1314-25 et éléments du CGI, sans ajouter de règles juridiques supposées.

### 14.2 Champs techniques des règles d'exonération (indispensables)

Pour chaque version de règle :

- `code_rubrique`, `juridiction=MA`, `regime=IR|CNSS|AMO|AUTRE` ; **ne pas mutualiser naïvement le plafond IR/CNSS**.
- `date_debut`, `date_fin`, `texte_reference`, `article`, `url_source`, `date_validation`, `valide_par`.
- `plafond_type` : montant fixe, quantité × montant horaire, % salaire, % assiette, annuel, mensuel, journalier, forfait sous conditions.
- `plafond_valeur` ou formule/version de SMIG applicable ; nombre de jours effectivement éligibles ; conditions de cumul et incompatibilités.
- `conditions_eligibilite` et `types_justificatifs_requis`, date/validité des pièces ; affichage des raisons de rejet d'une exonération.
- `montant_total`, `part_exoneree_IR`, `part_soumise_IR`, `part_exclue_CNSS`, `part_soumise_CNSS`, éventuellement assiettes autres régimes.
- `statut_reglementaire` (`A_VERIFIER`, `VALIDE`, `OBSOLETE`) + journal de version et comparaison.

**Comportement :** calculer séparément les fractions par régime, justifier la formule utilisée, afficher l'assiette soumise/exclue, bloquer l'approbation si justification ou règle requise non validée. Permettre une simulation pédagogique explicitement non conforme en attendant vérification.

### 14.3 Sources réglementaires de départ — à revalider à la date du développement

1. **DGI — CGI 2026** (fiscalité des salaires : articles 56–59 notamment) :  
   https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf
2. **CNSS — arrêté n° 1314-25 du 19 mai 2025**, publié au BO 7443 du 29/09/2025 : éléments exclus de l'assiette des cotisations, plafonds et justificatifs ; **rechercher aussi les rectificatifs / versions consolidées ultérieures (notamment signalés en décembre 2025)** :  
   https://documentationjuridiquemarocaine.gov.ma/bo-en-ligne/page/3  
   https://juritheque.com/loi/arrete-1314-25-elements-salaire-indemnites-non-soumis-cotisations-sociales
3. **Code du travail marocain**, notamment articles 370–374 sur bulletin et livre de paie :  
   https://adala.justice.gov.ma/api/uploads/2024/04/30/code%20du%20travail-1714463246806.pdf
4. **CGNC / Plan comptable marocain** :  
   https://befec.ma/documentation/comptabilite/Plan_comptable/CGNC/cgnc.pdf

**Remarque sur la validation :** le CGI 2026 officiel et le Code du travail ont été identifiés ; l'arrêté CNSS 1314-25, sa date d'application et l'existence de rectificatifs sont documentés, mais **chaque plafond détaillé de l'infographie doit être vérifié dans le texte consolidé applicable et dans ses conditions d'exonération**. Même lorsqu'un chiffre « semble correct », pas de règle codée sans vérification et tests de référence. Les taux peuvent évoluer après le présent document.

---

## 15. CAS DE RECETTE OBLIGATOIRES, DE BOUT EN BOUT

### 15.1 Cas simple : 3 salariés

- Créer trois salariés dans société A ; société B ne les voit jamais.
- Refuser doublon matricule ; fiche non validée exclue de la campagne.
- Enregistrer salaire fixe et une variation datée ; règle de salaire historique conservée.
- Préparer mois M : salarié 1 sans prime ; salarié 2 avec prime de transport ; salarié 3 avec heures supplémentaires et absence.
- Appliquer plafonds IR et CNSS indépendamment, y compris part au-dessus du plafond ; afficher le détail du calcul.
- Simuler, contrôler puis approuver ; produire PDF et livre ; pas de changement historique après approbation.
- Générer et valider **une seule** OD équilibrée (ou OD autorisées selon modèle). Un deuxième clic ne la duplique pas.
- Payer deux salariés entièrement et le troisième partiellement ; rapprochements + soldes corrects.
- Générer les états de cotisations et d'IR, puis enregistrer dépôt et paiement vérifiés.
- Contrôler 4432 / 444x / 44525 et détail par salarié/organisme.

### 15.2 Avance de 2 000 MAD

- Approuver l'avance et enregistrer son décaissement (3431/banque).
- Vérifier que le remboursement par retenue sur paie diminue 4432 et 3431 (sans doubler le 617).
- Vérifier net après retenues légales, avance déjà payée et **net à virer**.

### 15.3 Congés à payer à la clôture

- Au 31/12/N, valoriser reliquats financiers et charges patronales estimables ; vérifier qu'ils ne sont pas déjà dans la paie.
- Proposer OD 4437 et 4447, validation comptable, pièces et justification.
- À l'ouverture N+1, contrepasser quand applicable ; confirmer absence de charge doublée lors du paiement.

### 15.4 Scénarios négatifs

- Salarié non validé ; changement RIB sans approbation ; permissions insuffisantes ; données d'autre société.
- Période verrouillée, exercice clos, compte absent/inactif, compte non imputable, erreur de précision/arrondi.
- Déclaration « préparée » non confondue avec « déposée », paiement « transmis » non confondu avec « exécuté ».
- Plafond dépassé, absence de preuve, assiette réglementaire non validée, barème ancien modifié en cours de route.
- Idempotence après timeout/retry, deux utilisateurs simultanés, PDF re-généré qui ne change pas un bulletin approuvé.

---

## 16. CRITÈRES DE TERMINAISON D'UNE SOUS-ÉTAPE / D'UN LOT

Une étape n'est **terminée** que si :

1. Code conforme aux conventions du dépôt, aucune duplication inutile des services existants.
2. Migrations sûres et documentées ; tests de schéma/contraintes.
3. Backend ET frontend cohérents, permissions backend réellement testées.
4. Parcours fonctionnels heureux + erreurs courantes testés et validés.
5. Les règles de calcul et les comptes ont des références juridiques/comptables vérifiées et versionnées si concernés.
6. Résultats annoncés par famille : unitaires, intégration, PostgreSQL réel, navigateur, build ; expliquer ce qui n'a pas été exécuté.
7. Pas de régression prouvée sur les modules de comptabilité/facturation/fiscalité/trésorerie impactés.
8. Remettre **ZIP différentiel** (fichiers ajoutés/modifiés seulement, **arborescence exacte**) + court résumé + prochaine sous-étape.
9. La recette utilisateur et les points restant à valider sont listés sans prétendre que la production est prête.

**Ne pas compter une simple maquette comme une fonctionnalité livrée.**

---

## 17. INSTRUCTIONS PRATIQUES POUR LES ITÉRATIONS CODEX

### Prompt pour démarrer le LOT 0

```
Lis docs/HISABPRO_PERSONNEL_PAIE_CODEX_MASTER.md en entier et respecte-le comme cahier des charges.
Commence le LOT 0, sans implémenter la paie : fais l'audit du dépôt réel et des services
comptables, le schéma cible, le workflow d'approbation, les droits et le plan de migrations.
Liste précisément le réutilisable, les incompatibilités et les décisions à prendre.
Propose ensuite un plan exécutable de LOT 1A avec ses tests.
Ne suppose ni endpoints, ni tables, ni taux réglementaires non constatés.
```

### Prompt pour lancer une sous-étape ensuite

```
Lis docs/HISABPRO_PERSONNEL_PAIE_CODEX_MASTER.md et l'état actuel du projet.
Implémente UNIQUEMENT [LOT X / sous-étape Y] conformément aux critères d'acceptation.
Avant code : vérifie dépendances et composants existants.
Après code : exécute les tests pertinents, distingue automatisés et PostgreSQL réel,
indique les limites, livre un ZIP différentiel aux chemins exacts,
un résumé court et la prochaine étape. Ne touche pas aux autres lots.
```

### Prompt pour valider un lot

```
Audite et teste le LOT X selon la checklist de
HISABPRO_PERSONNEL_PAIE_CODEX_MASTER.md.
Contrôle droits, comptabilité, périodes fermées, doublons, sécurité et non-régression.
N'annonce pas « validé » sans preuves. Fournis anomalies et ZIP correctif différentiel
si des corrections sont effectuées, puis indique si le LOT X+1 peut commencer.
```

---

## 18. DÉCISIONS ET QUESTIONS À CONSERVER DANS LE BACKLOG

**Décisions actées dans ce document :** module « Personnel & Paie », 9 rubriques ; 8 lots (0–7) ; salarié créé en rubrique 01 ; pas de comptabilisation sur création salarié ; paie et comptabilité séparément approuvées ; exonérations DGI/CNSS paramétrées distinctement ; clôture comprise ; mode import externe prévu ; développement par sous-étapes testées et ZIPs différentiels.

**À trancher après audit, sans présumer :** système de rôles existant ; journal PAI créé ou réutilisé ; centralisation vs détail par salarié ; fournisseurs/organismes comme tiers ou classes dédiées ; nomenclature/numérotation des bulletins ; règles de paie spécifiques à chaque convention/secteur ; règles de retenue légales ; politique de durée de conservation/archivage et chiffrement ; déclaration sociale/fiscale par formats réellement disponibles ; choix éventuel du **mode import externe en avance** pour livrer rapidement une comptabilisation de paie.

**Important :** aucune information de ce document ne certifie que les lots sont déjà codés. Toujours comparer au dépôt présent au moment de l'exécution.
