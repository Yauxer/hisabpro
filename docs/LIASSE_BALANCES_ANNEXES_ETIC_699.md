# Autres annexes documentaires ETIC dans Liasse seule

Version 699 du 21 octobre 2026 — recette fictive, sans données réelles.

Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
choisir une préparation conservée puis **Documenter les autres annexes ETIC**.
Le menu reprend six tableaux déjà définis dans le catalogue HisabPro :
A2 dérogations, A3 changements de méthodes, B10 crédit-bail, C1 capital,
C2 affectation des résultats et C4 opérations en devises. Les colonnes sont
reprises telles qu’elles existaient ; cette saisie ne certifie pas un modèle
administratif applicable ni une liasse complète.

## Fonctionnement du formulaire

Choisir **Tableau ETIC à documenter**, la **Déclaration du tableau**, puis la
**Justification du tableau**. Ajouter autant de lignes nécessaires, au maximum
100 par tableau. Changer de tableau conserve les brouillons du formulaire.
Chaque ligne documentée nécessite une désignation et une référence de source.
Les autres champs restent facultatifs et peuvent être inconnus.

**À compléter** conserve un brouillon partiel. **Saisie documentée — à revoir**
signifie seulement que la déclaration et ses lignes sont identifiées et sourcées.
**Néant — déclaré et justifié** exige une justification et aucune ligne ;
retirer explicitement les lignes du brouillon avant cette déclaration. Une
liste vide laissée À compléter ne signifie pas qu’il n’existe aucune opération.

Confirmer puis **Conserver les tableaux ETIC dans une nouvelle version**. Les
six tableaux du formulaire sont conservés ensemble, la nouvelle version est
sélectionnée et l’ancienne reste intacte. Auteur, date UTC, catalogue, unités,
valeurs et empreinte de source sont figés. Les autres compléments, dont B8/B9,
notes, financement et échéances, sont préservés. Les pièces jointes restent
propres à leur version, sans copie automatique.

Une note déclarée non applicable contredisant des lignes de la même rubrique
produit une alerte. Revoir les deux compléments ; aucun texte ou montant n’est
modifié automatiquement. Le statut documenté ne valide pas une rubrique complète.

## Unités, dates et précision

Les montants financiers sont des valeurs comptabilisées en MAD, positives ou
nulles, finies, avec deux décimales maximum et une borne technique de
9 999 999 999 999,99 MAD. Dans C4, saisir les contre-valeurs MAD documentées,
pas des montants bruts en euros ou autres devises. Le code devise décrit les
opérations ; aucun taux ni conversion n’est calculé ou présumé.

Dans C1, **Nombre de titres / parts** est un entier positif ou nul, limité
techniquement à 18 chiffres. **% capital** accepte une valeur entre 0 et 100,
avec au plus 12 décimales. Il ne s’agit pas d’un montant MAD. Le nominal et
le capital détenu restent des montants MAD. Ces limites de saisie sont
techniques, pas des règles fiscales nouvelles. Aucun pourcentage, capital
ou nombre de titres n’est déduit du seul solde comptable.

Les dates de contrat B10 sont saisies avec le sélecteur de date et conservées
en AAAA-MM-JJ. Elles peuvent être antérieures à l’exercice. Le backend refuse
les dates impossibles ou mal formées, sans les remplacer par une date de pièce,
d’acquisition ou d’échéance. Une date vide reste inconnue. Les durées sont des
textes documentaires ; aucun échéancier de crédit-bail n’est fabriqué.

## Jeu de recette humain et calculs indépendants

Prérequis : société fictive en MAD, exercice 2026, comptes des fichiers695,
utilisateur administrateur/comptable et un lecteur. Importer
**BALANCE_FICTIVE_FINANCEMENT695_N.csv** et **BALANCE_FICTIVE_FINANCEMENT695_N1.csv**
du dossier docs/recette puis conserver. N : débit = crédit 17 000 MAD,
capital1111 10 000 MAD et produits7111 2 000 MAD. N-1 : débit = crédit 6 000 MAD.
Les sources et déclarations suivantes sont exclusivement des hypothèses de recette.
Ne créer aucune écriture supplémentaire dans le Journal pour ce jeu documentaire.

A2 : Néant, justification **Revue fictive699 : aucune dérogation déclarée**.
A3 : Néant, justification **Revue fictive699 : aucun changement de méthode déclaré**.
C2 : Néant, justification **PV fictif699 : aucune affectation durant cet exercice**.
Ces déclarations sont explicites ; elles ne sont pas calculées depuis les balances.

B10 : Saisie documentée, justification **Contrat fictif699, sans qualification
réglementaire présumée**. Bien **Machine en crédit-bail fictif699** ; date
**2025-12-15** ; durée **48 mois** ; valeur estimée **10000** ; redevances
exercice **1200** ; redevances restantes **6400** ; référence **Contrat A fictif699**.
Ces trois montants sont donnés par le contrat fictif, sans formule automatique
supposant leur rapport ou leur traitement comptable.

C1 : Saisie documentée, justification **Registre fictif699 des associés**.
Associé **Associé unique fictif699** ; identifiant **Identifiant de recette uniquement** ;
titres **100** ; nominal **100** ; capital détenu **10000** ; pourcentage **100** ;
référence **Registre A fictif699**. Contrôle humain : 100 × 100 MAD = 10 000 MAD,
soit le capital1111 de la balance N ; associé unique à 100 %. Cette vérification
manuelle ne prouve pas la validité d’un registre réel.

C4 : Saisie documentée, justification **État fictif699 des contre-valeurs
comptabilisées en MAD**. Devise **EUR** ; achats **0** ; ventes **2000** ; laisser
créances et dettes vides ; observation **Contre-valeurs en MAD sourcées ; aucun
cours de change présumé** ; référence **État A fictif699**. Contrôle humain :
ventes documentées 2 000 MAD = produits7111 N. L’affectation en devise est une
hypothèse explicite de ce jeu, jamais une déduction de HisabPro. Créances et
dettes en devises restent inconnues malgré les soldes de la balance.

Les données exactes et l’oracle en centimes figurent dans
**DONNEES_ANNEXES_ETIC699.json**. Les tests de précision de pourcentages à
12 décimales sont des stress-tests distincts, pas les données de ce capital.

## Exports et droits

PDF et Excel présentent les mêmes champs et sources avec le logo et l’identité
actuels, hors empreinte historique. Titres et pourcentages sont conservés en
texte exact dans Excel pour éviter l’arrondi d’affichage ou la perte de chiffres.
Les valeurs financières sont numériques lorsqu’elles sont représentables exactement.
Les textes commençant par = restent des textes. Le ZIP ajoute
annexes_etic_documentaires.json et son SHA-256 au manifeste. Aucun téléchargement
ne crée une écriture, un impôt ou une archive fiscale définitive.

Un lecteur consulte et exporte, sans conservation ni modification. Un compte
extérieur non invité ne peut pas accéder à la préparation. Après un refus,
le brouillon reste disponible ; corriger puis confirmer de nouveau. Relire
les tableaux conservés réinitialise le brouillon : conserver d’abord toute
saisie que l’on souhaite garder.

## Cahier de recette humaine

Tous les résultats restent Non testé jusqu’à votre propre recette. Capturer
la version et l’empreinte visibles. Prérequis communs : environnement isolé
et données fictives ci-dessus. Aucune écriture ni aucun impact fiscal attendu.

| ID | Actions et données exactes | Résultat, contrôle et preuve attendus | Statut humain |
|---|---|---|---|
|AX699-01|Ouvrir une préparation conservée puis les autres annexes. Parcourir A2/A3/B10/C1/C2/C4 avant toute saisie.|Six tableaux À compléter sans ligne. Aucun néant présumé, aucune écriture créée. Captures de la version et des déclarations.|Non testé|
|AX699-02|Saisir A2/A3/C2 Néant et leurs trois justifications exactes du guide. Changer de tableau puis revenir et conserver avec confirmation.|Déclarations et brouillons préservés, nouvelle version sélectionnée, ancienne intacte. Captures comparées et sources visibles.|Non testé|
|AX699-03|Saisir B10 avec date2025-12-15, durée48mois, valeur10000, redevances1200/6400 et source Contrat A fictif699. Conserver.|Date historique exacte, trois valeurs distinctes en MAD, aucune acquisition ou charge créée dans le Journal. Captures et JSON exporté.|Non testé|
|AX699-04|Saisir C1 :100titres, nominal100, capital10000,100%; C4 :EUR,achats0,ventes2000,créances/dettes vides, avec identités/sources exactes du guide. Conserver.|100×100=10000, capital1111 N ; ventes2000=produits7111 N. Titres et % sans unitéMAD, inconnus préservés, aucune conversion automatique. Captures et Excel.|Non testé|
|AX699-05|Remplacer %capital par101 et tenter de conserver ; corriger en100. Essayer titres1,5 puis100 ; redevancesNaN puis1200. Confirmer après chaque correction.|Chaque valeur invalide est refusée sans nouvelle version et sans perte du brouillon. Correction puis confirmation autorise une nouvelle version. Captures des refus et versions.|Non testé|
|AX699-06|Avec un lecteur, consulter la version documentée puis exporter PDF/Excel/ZIP avec logo fictif. Comparer version, champs, sources et manifeste ; vérifier qu’aucun bouton de conservation n’existe.|Lecture et exports autorisés ; saisie désactivée. Logo, date et unités cohérents ; titres/% exacts, inconnus et JSON conservés ; aucun journal ou impôt créé. Garder les trois exports et captures.|Non testé|

La présence de ces annexes n’achève pas les tableaux automatiques/assistés ni
les compléments fiscaux du mode indépendant. La revue des contrats, titres,
contre-valeurs et décisions réels reste humaine. RAS/EDI exigent leurs
spécifications officielles ; RH/paie et point6 restent différés.
