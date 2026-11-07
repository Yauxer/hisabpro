# MODE D’EMPLOI ET RECETTE — RATTACHEMENTS DES CLÔTURES AUX COMPTES

Version 1 du 21 octobre 2026. Complément interne B2/B2bis/B5 de la préparation depuis balances.

## Fonction et prérequis

Dans Comptabilité → Liasse fiscale → Préparer depuis des balances externes,
ouvrir une préparation contenant les mouvements documentaires713 puis
Raccorder les clôtures de mouvements aux comptes sources. Le formulaire ne
crée aucune écriture et ne modifie pas les mouvements déclarés.

Utiliser une société fictive séparée en MAD, exercice2026 ouvert, avec les
comptes et deux CSV décrits dans le guide713. Les migrations du module de
préparations doivent être installées ; aucune migration nouvelle n’est ajoutée.
Redémarrer le backend et reconstruire le frontend. Prévoir administrateur ou
comptable pour conserver et lecteur pour contrôler les droits. Ajouter un logo
fictif aux paramètres et noter le nombre d’écritures au Journal.

Les tableaux de mouvements713 doivent être conservés avant tout rattachement.
L’ouverture du nouveau formulaire avant cette étape affiche un message explicite.
Les codes sont ceux du catalogue interne HisabPro, sans certification officielle.

## Données exactes et oracles indépendants

Réutiliser BALANCE_FICTIVE_MOUVEMENTS713_N.csv et BALANCE_FICTIVE_MOUVEMENTS713_N1.csv,
ainsi que les trois déclarations de DONNEES_MOUVEMENTS713.json. Les fichiers sont
fournis au lot713 et présents dans le cumulatif. DONNEES_RACCORDS715.json décrit
les choix et résultats du présent complément.

Balance N :2340 débit11000 ;2834 crédit4500 ;1511 crédit700 ;5141 débit4200 ;1111 crédit10000.
Débit=crédit15200MAD, actif net/passif10700MAD. N-1 :2340 débit10000 ;2834 crédit4000 ;
1511 crédit500 ;5141 débit4500 ;1111 crédit10000. Débit=crédit14500, net10500MAD.
Les mouvements restent explicitement déclarés sur des pièces fictives distinctes.

Dans les mouvements713 : B2 clôture11000 ; B2bis clôture4500 ; B5 clôture700,
une ligne par tableau. Choisir leurs comptes dans le nouveau formulaire :

- B2 ligne1 Matériel de transport fictif : compte2340.
- B2bis ligne1 Amortissements transport fictifs : compte2834.
- B5 ligne1 Litige fictif : compte1511.

Oracle B2 : solde source débit−crédit11000 ; somme des clôtures rattachées11000 ;
écart11000−11000=0. B2bis : source crédit−débit4500, somme4500, écart0.
B5 : source crédit−débit700, somme700, écart0. Aucun écart n’est corrigé automatiquement.

Périmètres techniques repris des tableaux HisabPro existants : B2 comptes21/22/23,
B2bis281/282/283 et B5 comptes15/29/39/45/59. Seuls les comptes effectivement
présents dans la source N détaillée sont proposés. Les libellés historiques de
comptes ne sont pas conservés dans cette source ; aucun nom n’est reconstruit
depuis le plan courant. La nature affichée reste celle déclarée dans les mouvements.
Les périmètres ne prétendent pas définir une nouvelle obligation réglementaire.

## Parcours utilisateur

1. Importer les CSV713, contrôler puis conserver la préparation et les trois tableaux713 avec leurs pièces fictives de référence. Noter version/empreinte et le Journal.
2. Ouvrir Raccorder les clôtures de mouvements aux comptes sources. Aucun choix n’est prérempli automatiquement pour un nouveau contrôle.
3. Choisir B2 dans Tableau de rattachement puis2340 pour Compte source B2 ligne1 ; passer à B2bis et choisir2834 ; passer à B5 et choisir1511. Revenir à B2 pour vérifier que le choix2340 est conservé dans le brouillon.
4. Cocher Je confirme les rattachements explicites, sans valider une liasse complète. Cliquer Conserver les rattachements dans une nouvelle version.
5. La nouvelle version est immédiatement sélectionnée. Rouvrir le formulaire et vérifier les trois comptes/soldes/sommes/écarts ci-dessus. Les mouvements déclarés restent inchangés.
6. Télécharger PDF, Excel et dossier ZIP ; vérifier le logo, les sources, l’auteur et les contrôles.

Plusieurs lignes peuvent être rattachées au même compte. Le contrôle additionne
leurs clôtures connues, puis les compare au solde du même compte. Il ne répartit
pas un compte automatiquement entre les lignes. Chaque ligne doit apparaître
exactement une fois, y compris les lignes laissées Non rattachée.

## Brouillons, inconnus et contrôles anciens

Un choix vide signifie Non rattachée. Le compte source sans ligne correspondante
garde une somme et un écart indisponibles, jamais0. Une clôture inconnue dans une
ligne rattachée rend aussi la somme et l’écart indisponibles. Les lignes non
rattachées restent listées. Un compte explicitement présent à solde0 et des
clôtures explicitement0 peuvent donner un vrai écart0. Les signes inverses sont
préservés. Sans source N détaillée complète, les comptes restent indisponibles.

Modifier les choix du brouillon ne change pas les contrôles conservés. Une
nouvelle conservation est nécessaire pour figer un autre rattachement.

Après les étapes précédentes, ouvrir les mouvements713 de la même préparation,
modifier seulement la clôture B2 de11000 en10999,99, confirmer et conserver.
Dans le formulaire de rattachement de cette nouvelle version, l’ancien contrôle
est signalé À refaire : il conserve son ancienne clôture11000 et son écart0.
Les choix pour les mouvements actuels repartent Non rattachée ; aucune ancienne
affectation de ligne n’est réutilisée silencieusement.

Choisir à nouveau2340/2834/1511 puis confirmer et conserver. Le nouveau B2 donne
10999,99−11000=−0,01MAD. La clôture de source reste11000. La version antérieure
garde son ancien contrôle et ses références. La révision du bloc de mouvements
ou des sources N est détectée par leurs empreintes conservées, sans recalculer
les contrôles historiques. Une autre note indépendante ne change pas ces bases.

Ce raccord porte uniquement sur les clôtures par compte du périmètre. Il ne
prouve pas l’origine de chaque ouverture/flux, l’exhaustivité du registre, les
cessions B3 ou la conformité fiscale d’un dossier. Aucun résultat fiscal ni
liquidation n’est créé. Une clôture inconnue doit être documentée à sa source,
sans saisir0 artificiellement pour obtenir un écart nul.

## Vérifier les exports

PDF : contrôles conservés, lignes/natures/clôtures/comptes/références, auteur/date,
version source et empreintes des mouvements et de N. Excel : Origine raccords,
Raccord B2/B2bis/B5, Contrôle raccord B2/B2bis/B5 et Diagnostic raccords.
La mention Raccord actuel vaut Oui ou À refaire. Elle indique seulement que les bases correspondent, pas que tous les rattachements sont complets. Les lignes du contrôle conservé
gardent leurs anciennes clôtures et références, même si les mouvements actuels
ont changé. La feuille Mouvements B2 peut alors afficher10999,99 tandis que
Raccord B2 conserve11000 : la mention À refaire explique cette différence.

ZIP : raccords_mouvements.json et les fichiers du dossier avec MANIFESTE_SHA256.json.
Le JSON distingue snapshot conservé et contexte courant. Les montants inconnus
ne deviennent pas0, les grands montants restent exacts et les textes restent
des textes, même préfixés par un signe égal. Le logo actuel apparaît dans les
exports, hors empreinte historique. Les pièces restent attachées à leur version
d’origine, sans copie implicite. Les autres compléments sont préservés.

## Recette humaine à effectuer

Prérequis communs ci-dessus ; aucun impact comptable/fiscal du formulaire.
Renseigner résultat réel, anomalies et preuves dans l’Excel. Les tests automatisés
ne remplissent pas cette recette à la place de l’utilisateur.

|ID|Actions / données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|R715-01|Ouvrir les mouvements713 conservés avec les CSV et déclarations ci-dessus puis le nouveau formulaire ; examiner les choix de chaque tableau.|Aucune attribution initiale ; B2 propose2340, B2bis2834, B5 1511 ;1111/5141 hors périmètre. Message explicite si mouvements non encore conservés. Captures des choix.|Non testé|
|R715-02|Choisir2340/2834/1511, confirmer, conserver puis rouvrir chaque tableau.|Nouvelle version sélectionnée immédiatement ; soldes/sommes11000/4500/700 et écarts0 ; auteur/source/empreintes présents. Journal et mouvements inchangés. Captures des contrôles.|Non testé|
|R715-03|Sur un brouillon du cas02, laisser B2 ligne1 Non rattachée ; observer le contrôle puis conserver.|Avant conservation, ancien écart0 ; après, ligne1 non rattachée et somme/écart indisponibles, jamais0 fabriqué. Captures avant/après.|Non testé|
|R715-04|Depuis la version du cas02, changer la clôture des mouvements B2 en10999,99 et conserver ; ouvrir les rattachements ; choisir à nouveau2340/2834/1511 et conserver.|Ancien contrôle À refaire gardant11000/écart0, choix actuels vides ; nouveau raccord donne−0,01. Version précédente inchangée. Captures du contrôle ancien et refait.|Non testé|
|R715-05|Avec logo fictif, télécharger PDF, Excel et ZIP de la version signalée À refaire puis de celle refaite au cas04.|Anciennes clôtures/références conservées avec avertissement ; nouveau raccord10999,99/source11000/écart−0,01 ; logos et manifeste corrects. Conserver les exports.|Non testé|
|R715-06|Se connecter comme lecteur ; consulter les trois tableaux du cas02 et télécharger le ZIP.|Choix désactivés et aucun bouton de conservation ; consultation/export autorisés ; aucune nouvelle version/écriture. Capture droits et ZIP.|Non testé|

## État et suite

Les tests et limites sont consignés au rapport715. Recette humaine, ouverture
Office et installation cible restent à vérifier ; production nonvalidée. Les
sources fiscales autonomes et les spécifications officielles restent distinctes.
RH/paie et point6 humain différés. Aucune certification officielle affirmée.
