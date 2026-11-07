# MODE D’EMPLOI ET RECETTE — MOUVEMENTS D’IMMOBILISATIONS ET PROVISIONS

Version 1 du 21 octobre 2026. Saisie documentaire interne B2/B2bis/B5, exercice N.

## Fonction et accès

Dans Comptabilité → Liasse fiscale → Préparer depuis des balances externes,
ouvrir une préparation conservée puis Documenter les mouvements d’immobilisations
et provisions. Choisir B2, B2bis ou B5 dans Tableau ETIC à documenter.
Ces identifiants reprennent le catalogue HisabPro existant ; les colonnes de ce
formulaire sont internes, sans prétendre former un modèle officiel DGI.

Chaque ligne décrit une nature documentée, son ouverture, ses augmentations ou
dotations, ses diminutions/sorties/reprises et sa clôture déclarée. Les montants
proviennent de sources explicites, jamais d’une déduction des seules balances
N/N-1. Aucun registre réel ou Journal courant n’est lu pour inventer ces flux.

Contrôle : ouverture + augmentations − diminutions = clôture reconstituée.
Écart = clôture déclarée − clôture reconstituée. Chaque tableau conserve ses
contrôles séparément, sans sommer immobilisations, amortissements et provisions
entre eux. Le formulaire ne prouve pas un raccord par compte au bilan ou au
registre et ne calcule aucun résultat fiscal. Les cessions B3 sont un complément
distinct, sans rapprochement automatique avec ces mouvements.

## Prérequis et données fictives exactes

Utiliser une société fictive séparée en MAD, exercice2026 ouvert, comptes1111,
2340 Matériel de transport,2834 Amortissements du matériel de transport,
1511 Provisions pour litiges et5141 Banque présents au plan. Migration071 du
module de préparations existante ; aucune nouvelle migration requise.
Redémarrer le backend et reconstruire le frontend après application des fichiers.
Prévoir administrateur/comptable et lecteur ; ajouter un logo fictif aux paramètres.
Noter le nombre d’écritures au Journal : cette préparation ne doit pas le modifier.

Importer BALANCE_FICTIVE_MOUVEMENTS713_N.csv et BALANCE_FICTIVE_MOUVEMENTS713_N1.csv
fournis dans docs/recette. DONNEES_MOUVEMENTS713.json contient déclarations et oracles.

N :1111 crédit10000 ;2340 débit11000 ;2834 crédit4500 ;1511 crédit700 ;5141 débit4200.
Débit=crédit=15200MAD. Actif net11000−4500+4200=10700 ; capital10000+provision700=10700.
N-1 :1111 crédit10000 ;2340 débit10000 ;2834 crédit4000 ;1511 crédit500 ;5141 débit4500.
Débit=crédit=14500MAD. Actif net10000−4000+4500=10500 ; capital10000+provision500=10500.
Toutes les autres cellules valent explicitement0.

Ces balances de contexte sont équilibrées. Les mouvements suivants sont des
données distinctes de registre/pièces fictifs. Leur ouverture n’est pas calculée
automatiquement à partir de N-1. Le jeu ne reconstitue pas les écritures et
impacts fiscaux de toutes les opérations d’un exercice réel.

B2 : statut Saisie documentée — à revoir ; justification Registre fictif713 B2.
Ajouter une ligne Nature déclarée Matériel de transport fictif ; ouverture10000 ;
acquisitions et augmentations2000 ; sorties et diminutions1000 ; clôture11000 ;
référence Pièce fictive713 B2. Oracle10000+2000−1000=11000 ; écart0.

B2bis : même statut ; justification Registre fictif713 B2bis. Nature Amortissements
transport fictifs ; ouverture4000 ; dotations1000 ; amortissements sortis500 ;
clôture4500 ; référence Pièce fictive713 B2bis. Oracle4000+1000−500=4500 ; écart0.

B5 : même statut ; justification Registre fictif713 B5. Nature Litige fictif ;
ouverture500 ; dotations300 ; reprises et utilisations100 ; clôture700 ;
référence Pièce fictive713 B5. Oracle500+300−100=700 ; écart0.

## Parcours utilisateur

1. Importer les deux CSV, contrôler puis conserver la préparation fictive ; noter version/empreinte.
2. Ouvrir Documenter les mouvements d’immobilisations et provisions. Saisir statut, justification et ligne B2 ci-dessus.
3. Passer à B2bis puis B5 et saisir leurs données ; revenir à B2 pour vérifier le brouillon.
4. Cocher Je confirme les données et déclarations saisies, sans valider une liasse complète. Cliquer Conserver les tableaux ETIC dans une nouvelle version. Les trois tableaux sont conservés ensemble.
5. Rouvrir le formulaire de la nouvelle version immédiatement sélectionnée ; vérifier les clôtures reconstituées11000,4500,700 et les écarts0.
6. Dans B2, changer seulement la clôture déclarée11000 en10999,99 sans conserver. Les contrôles affichent encore ceux de la version conservée, soit écart0.
7. Confirmer puis conserver : clôture reconstituée11000, déclarée10999,99 et écart−0,01MAD. La version précédente garde son écart0.
8. Télécharger PDF, Excel et dossier ZIP de la nouvelle version ; vérifier logo, références et contrôles.

Ouverture et clôture peuvent être signées. Augmentations et diminutions sont des
montants non négatifs, deux décimales maximum en MAD. Une case vide reste inconnue,
un zéro est explicite. Si une donnée de l’équation manque, sa clôture reconstituée
ou son écart reste indisponible. Chaque total exige des valeurs connues pour
toutes ses lignes ; une absence de ligne ne fabrique pas0. NaN, infinis,
booléens et décimales excessives sont refusés.

Nature et référence sont requises pour identifier une ligne déclarée documentée.
Les montants inconnus ne deviennent pas obligatoires. Néant exige une justification
et des lignes vides ; il ne prouve pas l’exhaustivité du registre. Une note non
applicable et un tableau renseigné gardent une alerte. Aucun chiffre n’est ajusté.

## Exports et traçabilité

PDF : données par tableau/ligne, références, auteur/date/source, contrôles et
logo actuel. Excel : Origine mouvements, Déclaration mouvements, Mouvements
B2/B2bis/B5 et Contrôle MV B2/B2bis/B5. Les montants inconnus restent indisponibles.
Les textes restent des textes, même préfixés par un signe égal ; les grands
nombres deviennent des textes si nécessaire pour conserver leurs décimales.

ZIP : mouvements_documentaires.json, sources CSV, PDF, Excel, pièces propres à
la version et MANIFESTE_SHA256.json. Aucun recalcul des anciens contrôles à la
lecture/export. Les autres compléments et anciennes versions sont préservés.
Les pièces ne sont pas copiées implicitement entre versions. Le logo actuel
reste extérieur à l’empreinte historique du contenu.

## Recette humaine à effectuer

Prérequis communs ci-dessus. Aucune écriture ou liquidation fiscale créée par
ce formulaire. Renseigner résultat réel, anomalies et preuves dans le classeur ;
les tests automatisés ne remplissent pas la recette humaine.

|ID|Actions / données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|M713-01|Importer N/N1 fournis dans une société fictive2026/MAD ; conserver puis saisir B2/B2bis/B5 ci-dessus.|Balances équilibrées15200/14500MAD, données explicites et brouillons préservés en changeant de tableau. Captures des lignes.|Non testé|
|M713-02|Confirmer puis conserver et rouvrir chaque tableau.|Nouvelle version immédiatement sélectionnée ; clôtures reconstituées11000/4500/700, écarts0. Références/auteur/source présents. Captures des contrôles.|Non testé|
|M713-03|Changer la clôture B2 de11000 en10999,99 sans conserver, puis confirmer et conserver ; revenir à la version précédente.|Avant conservation écart0 ; après écart−0,01 et clôture reconstituée11000 ; ancienne version écart0. Journal inchangé. Captures des versions.|Non testé|
|M713-04|Dans un autre brouillon B2, saisir acquisitions−1 et conserver ; corriger en2000 et reconfirmer ; essayer ensuite acquisitions vides.|Montant négatif refusé et brouillon préservé ; correction réinitialise confirmation puis réussit. Avec donnée inconnue, contrôle indisponible, jamais0. Captures erreur/inconnus.|Non testé|
|M713-05|Avec logo fictif, télécharger PDF, Excel et ZIP de la version du cas03 ; ouvrir les fichiers.|Logo/données/source/références présents, tableaux séparés et écart−0,01 exact ; JSON contrôles et manifeste vérifiables. Conserver trois exports.|Non testé|
|M713-06|Se connecter comme lecteur ; consulter les trois tableaux du cas02 et télécharger le ZIP.|Champs désactivés et aucun bouton de conservation ; lecture/export autorisés ; aucune version/écriture créée. Capture droits et ZIP.|Non testé|

## État et limites restantes

Tests et limites au rapport713. Le complément ne prouve pas le rapprochement
au bilan/registre ou aux cessions B3, ni l’exhaustivité des mouvements. Les
sources fiscales autonomes restent distinctes et partielles. Recette humaine,
ouverture Office et production restent à valider. RH/paie et point6 humain
différés. Aucune certification officielle affirmée.
