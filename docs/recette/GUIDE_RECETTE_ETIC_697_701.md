# MODE D’EMPLOI ET RECETTE — AVANCÉES ETIC HISABPRO

Version 1 du 21 octobre 2026 — lots 697/699/701, hors RH et paie.

Ce guide réunit les trois modes d’emploi de cette session. Il couvre les huit
schémas de tableaux manuels déjà définis dans le catalogue HisabPro et les
contrôles arithmétiques du capital déclaré. Ce n’est pas le cahier de recette
complet de toute l’application ; les autres domaines conservent leurs cahiers.
La liasse indépendante complète et les formalités officielles restent partielles.

Les chiffres du parcours consolidé sont regroupés dans DONNEES_ETIC_SESSION701.json. La balance N comporte la charge de crédit-bail de 1 200 MAD, déjà prévue dans B10, et une banque de 6 800 MAD. Résultat et CAF N attendus : 800 MAD. Les guides unitaires conservent leurs jeux de saisie propres ; pour ce parcours suivre les deux CSV ETIC701.

## Parcours conseillé

Utiliser une société fictive en MAD et un exercice 2026 dans une base de test
autorisée. Ne pas effectuer ces essais dans un dossier comptable réel.
Importer BALANCE_FICTIVE_ETIC701_N.csv et BALANCE_FICTIVE_ETIC701_N1.csv,
puis conserver une préparation. Les fichiers existent dans ce même dossier.

Compléter d’abord B8/B9 et conserver. Compléter ensuite les six autres annexes
et conserver : les blocs précédents sont repris depuis la version sélectionnée.
La version courante calcule alors les contrôles C1 à sa conservation ; consulter
ces contrôles avant de télécharger le dossier. Conserver chaque formulaire
avant de passer à une modification dans un autre formulaire ou de relire une
ancienne version. Le nombre exact de versions dépend de vos conservations.

Les montants et sources ci-dessous sont exclusivement fictifs. Les inconnus
ne deviennent pas zéro ; un néant est une déclaration explicite et justifiée.
Une version conservée n’est jamais modifiée par ces formulaires. Une pièce
jointe reste propre à sa version et n’est pas copiée automatiquement.

Les PDF/Excel/ZIP utilisent l’identité et le logo actuels, hors empreinte
historique. Le ZIP contient les sources et un manifeste SHA-256. Aucun export
ne crée d’écriture, de liquidation, de preuve de dépôt ou de certification.

## Suivre la recette dans Excel

Le classeur associé comporte une synthèse, une feuille par domaine, les sources,
les preuves et les anomalies. Pour chaque cas, renseigner statut humain,
résultat réel, anomalie et preuve. Les seize cas sont initialement Non testé.
Les formules et barres de progression sont recalculées à l’ouverture dans Excel.
Les réussites des tests automatisés sont documentées séparément dans Test et
ne remplissent pas les résultats de votre propre recette.


## Sûretés et engagements



Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
sélectionner une préparation conservée puis **Documenter les tableaux ETIC B8 et B9**.
Ces tableaux reprennent les colonnes du catalogue HisabPro déjà présent. Ils ne
constituent pas une nouvelle définition du modèle réglementaire et ne donnent
aucun statut officiel à la préparation.

### Préparer le dossier de test

Utiliser une société fictive en MAD, un exercice 2026 et un compte administrateur
ou comptable. Importer les fichiers de recette existants
**BALANCE_FICTIVE_ETIC701_N.csv** et **BALANCE_FICTIVE_ETIC701_N1.csv**
du répertoire docs/recette, puis conserver une version. Débit = crédit N :
17 000 MAD ; N-1 : 6 000 MAD. Les engagements ci-dessous sont exclusivement des
hypothèses de recette documentaire : ne pas les enregistrer dans le Journal.
Les données exactes figurent aussi dans **DONNEES_TABLEAUX_ETIC697.json**.

### Comprendre les déclarations

**À compléter** permet de conserver un brouillon partiel sans présumer sa source.
**Saisie documentée — à revoir** exige une justification du tableau et, pour
chaque ligne, une nature et une référence de source permettant de l’identifier.
Les autres informations peuvent rester inconnues : ce statut ne signifie pas
que la rubrique est complète ou réglementairement validée.
**Néant — déclaré et justifié** exige une justification et aucune ligne.
Une liste vide avec À compléter ne signifie jamais qu’il n’existe aucun engagement.

Chaque montant est en MAD, positif ou nul, fini, avec deux décimales maximum et
une borne technique de 9 999 999 999 999,99 MAD. Les virgules décimales sont acceptées.
Le vide reste inconnu ; saisir 0 est une déclaration explicite. Aucune conversion
de devise ni totalisation de sûretés et engagements de sens différents n’est présumée.
Les bornes sont des contraintes de saisie, pas des seuils fiscaux.

### Saisir B8 puis B9

Choisir **B8**, sélectionner **Saisie documentée — à revoir**, saisir la justification
**Contrat fictif697 — sûreté déclarée** puis **Ajouter une ligne au tableau**.
Renseigner Nature : **Hypothèque fictive697** ; Objet : **Immeuble fictif** ;
Tiers : **Banque fictive697** ; Montant couvert : **12345,67** ; laisser Valeur nette
comptable vide ; Date / lieu d’inscription : **À confirmer** ; Référence de source :
**Annexe A fictive697**. La valeur nette ne doit pas être déduite arbitrairement
de la balance ou remplacée par zéro.

Choisir **B9**. Les saisies B8 restent dans le brouillon. Sélectionner
**Saisie documentée — à revoir**, justification **Relevé fictif697 des engagements**.
Ajouter une ligne : Reçu / donné **Donné** ; Nature **Caution fictive697** ;
Montant exercice **2000** ; Montant N-1 **0** ; Observation **Recette uniquement** ;
Référence de source **Annexe B fictive697**. Ce N-1 est déclaré d’après la source
fictive, pas calculé depuis la balance. B8 et B9 ne s’additionnent pas.

Confirmer les données puis **Conserver les tableaux ETIC dans une nouvelle version**.
Les deux tableaux sont conservés ensemble ; la nouvelle version est sélectionnée.
La précédente reste consultable sans modification. Auteur, date UTC, catalogue,
valeurs et empreinte de source sont conservés. Notes, échéances et financement
existants sont préservés. Les pièces jointes restent propres à leur version ;
elles ne sont pas copiées automatiquement dans la nouvelle version.

Si une note B8/B9 est déclarée non applicable alors que son tableau contient des
lignes, une alerte demande de revoir les deux compléments. Rien n’est effacé ou
reclassé automatiquement. Modifier les notes reste une opération distincte.

### Vérifier ou corriger

Le rôle lecture consulte les tableaux et exporte la préparation ; il ne peut
pas modifier les champs ou conserver une version. Un refus serveur conserve le
brouillon pour correction. Une modification de saisie retire la confirmation.
**Retirer la ligne du brouillon** ne touche pas une ancienne version : seul un
nouvel enregistrement conserve le retrait. **Relire les tableaux conservés**
réinitialise le brouillon à la version sélectionnée ; ne pas l’utiliser avant
d’avoir conservé une saisie que l’on souhaite garder.

PDF et Excel présentent les mêmes valeurs, les sources et les inconnus avec
l’identité et le logo actuels. Le dossier ZIP ajoute tables_etic_documentaires.json
et son SHA-256 au manifeste. Une formule saisie dans un texte reste du texte
Excel ; les montants sont numériques lorsqu’ils sont représentables exactement.
Les exports ne créent pas d’écriture, de liquidation ni d’archive fiscale définitive.

### Cahier de vérification humaine

Tous les cas ci-dessous restent **Non testé** pour la recette utilisateur.
Les résultats des bancs automatisés sont documentés séparément dans Test.
Capturer la version et l’empreinte visibles pour chaque preuve.

| ID | Actions et données exactes | Résultat, contrôle et preuve attendus | Statut humain |
|---|---|---|---|
|ET697-01|Dans une préparation fictive conservée, ouvrir B8/B9 avant saisie.|Deux tableaux À compléter sans ligne. Aucune absence d’engagement présumée. Capture de la version et des deux déclarations.|Non testé|
|ET697-02|Saisir les deux lignes chiffrées du mode d’emploi, changer B8/B9 puis conserver avec confirmation.|B8 12 345,67 MAD et valeur nette inconnue ; B9 2 000 MAD et N-1 explicitement nul. Brouillons préservés, nouvelle version sélectionnée, ancienne intacte. Captures et JSON ZIP.|Non testé|
|ET697-03|Dans une nouvelle saisie, remplacer montant couvert par NaN, confirmer et tenter de conserver ; corriger en 0 puis conserver.|Refus explicite, aucune version créée sur refus, brouillon conservé. Après correction et confirmation, zéro conservé exactement. Captures de l’erreur et du succès.|Non testé|
|ET697-04|Après le cas02, choisir Néant pour B9 en laissant la ligne ; tenter de conserver. Retirer la ligne explicitement et conserver avec justification Revue fictive697, aucun engagement.|Première demande refusée. Nouvelle version B9 Néant justifiée et sans ligne ; version précédente toujours avec caution. Captures comparées.|Non testé|
|ET697-05|Avec un lecteur de la société fictive, ouvrir une version documentée puis exporter le ZIP. Avec un compte d’une autre société sans invitation, demander cette préparation.|Lecteur : champs désactivés, aucun bouton de conservation, export autorisé. Autre société : données non accessibles. Captures des droits.|Non testé|
|ET697-06|Configurer un logo de test, télécharger PDF/Excel/ZIP de la même version. Si note B8 non applicable et ligne B8 présente, consulter l’alerte.|Logo et version cohérents ; références et inconnus conservés ; JSON et manifeste présents ; alerte visible sans effacement automatique. Conserver les exports et vérifier les empreintes.|Non testé|

Aucune écriture comptable ni aucun impact fiscal n’est attendu pour ces six cas.
La revue des contrats réels et de leur qualification appartient au responsable
du dossier. Les autres tableaux structurés, compléments fiscaux et spécifications
RAS/EDI officiels restent à traiter séparément. RH/paie et point6 restent différés.

## Autres annexes manuelles



Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
choisir une préparation conservée puis **Documenter les autres annexes ETIC**.
Le menu reprend six tableaux déjà définis dans le catalogue HisabPro :
A2 dérogations, A3 changements de méthodes, B10 crédit-bail, C1 capital,
C2 affectation des résultats et C4 opérations en devises. Les colonnes sont
reprises telles qu’elles existaient ; cette saisie ne certifie pas un modèle
administratif applicable ni une liasse complète.

### Fonctionnement du formulaire

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

### Unités, dates et précision

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

### Jeu de recette humain et calculs indépendants

Prérequis : société fictive en MAD, exercice 2026, comptes des fichiers695,
utilisateur administrateur/comptable et un lecteur. Importer
**BALANCE_FICTIVE_ETIC701_N.csv** et **BALANCE_FICTIVE_ETIC701_N1.csv**
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

### Exports et droits

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

### Cahier de recette humaine

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

## Contrôles arithmétiques du capital



Après les tableaux documentaires des lots 697/699, HisabPro conserve désormais
des contrôles arithmétiques C1 dans les nouvelles versions des annexes.
Ils comparent les nombres déclarés ; ils ne calculent pas une répartition
juridique présumée et ne corrigent pas les données ou la comptabilité.

### Où consulter les contrôles

Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
choisir une version puis **Documenter les autres annexes ETIC**, sélectionner
**C1** et ouvrir **Vérifier les données chiffrées du capital conservé**.

Le panneau présente les données de la version conservée. Modifier les champs
du brouillon ne change pas ce panneau. Pour obtenir des contrôles sur la nouvelle
saisie, confirmer puis conserver les annexes dans une nouvelle version.
Une ancienne version sans contrôle reste identifiée comme telle : aucun
résultat ne lui est attribué automatiquement à sa lecture.

Pour chaque ligne, le produit titres × nominal est calculé lorsque les deux
facteurs sont connus. L’écart est capital déclaré moins ce produit, seulement
si le capital est également connu. Les données saisies restent intactes,
même si l’écart est non nul.

La somme des capitaux déclarés est disponible seulement s’il existe au moins
une ligne et si tous les capitaux des lignes sont connus. Elle est rapprochée
à titre indicatif du solde crédit moins débit des comptes 111 de la balance N
conservée. Ce préfixe est celui de la rubrique Capital social ou personnel du
bilan HisabPro existant. Les informations détaillées absentes ne deviennent
pas un solde nul. Le contrôle ne lit pas le Journal courant et ne modifie pas
le capital renseigné dans les paramètres de la société.

La somme des pourcentages et son écart par rapport à 100 sont présentés lorsque
tous les pourcentages des lignes sont connus. Une somme de 100 n’établit ni
l’exhaustivité des associés ni la validité juridique des titres. Aucune règle
fiscale nouvelle, condition d’immatriculation ou obligation documentaire n’est
créée par ce contrôle arithmétique.

Un tableau vide, même déclaré néant, ne devient pas une somme nulle. Un zéro
explicitement saisi reste un vrai zéro. Si une composante manque, le calcul
concerné reste Indisponible. Les calculs sont exacts en décimal et conservés
dans le snapshot ; ils ne sont pas rejoués à la lecture ou à l’export.

### Jeu de recette et calcul indépendant

Utiliser la société fictive en MAD et les deux balances du présent guide consolidé.
Capital des comptes 111 N : 10 000 MAD. Préparer C1 avec l’associé fictif et la
source **Registre A fictif699** : 100 titres, nominal 100 MAD, capital 10 000 MAD,
pourcentage 100. Conserver les annexes dans une nouvelle version.

Attendu : 100×100=10 000 MAD ; écart de ligne 0 MAD ; somme des capitaux 10 000 MAD ;
écart avec la balance 111 : 0 MAD ; somme des pourcentages 100 % et écart 0 %.
Ces égalités décrivent les nombres fictifs déclarés, pas la conformité du dossier.

Modifier le capital en **9999,99** et le pourcentage en **99,99**. Avant
conservation, le panneau conserve les anciens résultats. Après confirmation et
conservation : produit inchangé 10 000 MAD, capital déclaré 9999,99 MAD,
écart de ligne −0,01 MAD et écart avec la balance −0,01 MAD ; pourcentages 99,99 %
et écart par rapport à 100 de −0,01 %. Les champs ne sont pas ajustés automatiquement.
La version précédente garde ses écarts nuls.

Dans une nouvelle version, laisser le nominal, le capital déclaré et le
pourcentage vides. Avec désignation et source toujours présentes, la saisie
documentaire est conservable. Le produit, l’écart de ligne et les sommes/écarts
concernés restent indisponibles. Le solde 111 connu de 10 000 MAD reste visible.

Les données exactes et les attendus indépendants se trouvent dans
**DONNEES_CONTROLES_CAPITAL701.json**. Les grands produits des tests automatisés
servent à éprouver la précision, sans correspondre à des données réelles.

### Exports et droits

PDF, feuille Excel **Contrôles capital** et JSON des annexes dans le ZIP reprennent
les résultats conservés. Les valeurs sont exportées en texte exact pour préserver
les centimes, grands produits et pourcentages. Les pièces et autres compléments
restent attachés ou conservés selon les règles des lots précédents.
Le lecteur consulte les contrôles et télécharge les exports sans pouvoir modifier
la saisie ou conserver une nouvelle version.

### Cahier de recette humaine

Prérequis communs : société et données fictives ci-dessus, administrateur ou
comptable ; un lecteur pour le dernier cas. Aucune écriture ou liquidation
fiscale attendue. Capturer systématiquement version et empreinte.

| ID | Actions et données exactes | Résultat, contrôle et preuve attendus | Statut humain |
|---|---|---|---|
|C701-01|Saisir C1 : 100 titres,nominal 100,capital 10000,pourcentage 100,associé/source fictifs. Conserver puis ouvrir le panneau de contrôle.|Produit 10000 MAD ; somme des capitaux 10000 MAD ; comparaison à la balance 111 : 10 000 MAD ; trois écarts nuls. Source, version et empreinte visibles. Capture et JSON.|Non testé|
|C701-02|Modifier capital 9999,99 et pourcentage 99,99. Observer avant conservation ; confirmer puis conserver et rouvrir les contrôles.|Avant :ancienne situation. Après :produit 10000 MAD et écarts de ligne/balance −0,01 MAD ; somme 99,99 % et écart −0,01 %. Ancienne version intacte, aucune correction automatique. Captures comparées.|Non testé|
|C701-03|Dans une nouvelle saisie, laisser nominal,capital,pourcentage vides ; garder 100 titres,associé/source puis conserver.|Calculs et sommes concernés Indisponible, jamais 0. Solde 111 fourni toujours 10000 MAD. Aucune écriture créée. Capture des inconnus et JSON.|Non testé|
|C701-04|Avec un lecteur, consulter la version du cas 02 et télécharger PDF/Excel/ZIP avec logo de test.|Modification interdite ; valeurs conservées exactes dans PDF, feuille Contrôles capital et JSON. Version/logo/source cohérents. Garder les exports, manifeste et capture des droits.|Non testé|

Ces quatre cas restent Non testé pour votre recette utilisateur. Les tests
automatisés sont consignés séparément dans Test. La revue juridique/comptable,
les autres états ETIC/fiscaux et la mise en production ne sont pas validés par
ces calculs. RH/paie et point 6 humain restent différés.
