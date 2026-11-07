# MODE D’EMPLOI ET RECETTE — DÉTAIL DU CPC DEPUIS LES BALANCES

Version 1 du 21 octobre 2026. Complément B11 de la préparation indépendante.

## À quoi sert cette avancée ?

Dans Comptabilité → Liasse fiscale → Préparer depuis des balances externes,
vous pouvez désormais conserver le détail des comptes de charges et produits
d’une balance externe. Il reste distinct de la comptabilité tenue dans HisabPro.
Ce document couvre cette avancée seulement, pas la recette intégrale du produit.
Les cas humains restent Non testé, même lorsque les tests automatisés réussissent.

Le numéro B11 et son titre reprennent le catalogue interne existant. Aucune
exhaustivité officielle du modèle DGI ou validation de dépôt n’est présumée.
RH/paie et le point6 humain précédemment différé restent hors de ce lot.

## Prérequis et données fictives exactes

Utiliser une société de recette fictive séparée en MAD, avec un exercice2026
ouvert et les comptes1111,1191,3421,5141,6132,6193,7111,7119 présents dans son
plan comptable. Ne pas effectuer cette recette sur une société comptable réelle.
Un administrateur ou comptable conserve les versions ; un lecteur les consulte.
Seul le rôle autorisé aux paramètres de société ajoute le logo ; prévoir un
administrateur pour le cas06. Avant le cas01, noter le nombre d’écritures du
Journal de cet exercice pour pouvoir vérifier qu’il ne change pas.
Si l’exercice2026 existe déjà dans la société choisie, ne pas le recréer.

Les fichiers fournis dans docs/recette sont directement importables :
BALANCE_FICTIVE_CPC703_N.csv, BALANCE_FICTIVE_CPC703_N1.csv et
BALANCE_FICTIVE_CPC703_TECHNIQUE.csv. DONNEES_CPC703.json donne les valeurs
exactes et les résultats calculés indépendamment du moteur applicatif.
Ces fichiers sont entièrement fictifs et ne sont pas des écritures à injecter
dans votre comptabilité. L’import de préparation ne crée aucune écriture.

Balance N : capital1111 crédit1000 ; produit7111 crédit2000,30 ; reprise6193
crédit200,01 ; charge6132 débit1200,10 ; réduction7119 débit100,02 ; banque5141
débit1900,19. Toutes les autres cellules de débit/crédit de ces six lignes
valent explicitement0. Débit = crédit =3200,31 MAD.

Balance N-1 : capital1111 crédit6000 ; clients3421 débit2000 ; banque5141
débit4000 ; autres cellules0. Débit = crédit =6000 MAD. Aucune classe6/7 non
nulle : résultat N-1 égal0, distinct d’une absence de balance comparative.

Oracle indépendant N : charges1200,10 −200,01 =1000,09 ; produits2000,30 −100,02
=1900,28 ; résultat1900,28 −1000,09 =900,19 MAD. Banque et total bilan1900,19
= capital1000 + résultat900,19. Les trois écarts au CPC figé valent0 dans ce jeu.

## Parcours dans l’interface

1. Sélectionner la société fictive et l’exercice2026. Ouvrir Comptabilité → Liasse fiscale.
2. Dans Préparer depuis des balances externes, cliquer Importer N / N-1.
3. Choisir BALANCE_FICTIVE_CPC703_N.csv dans Balance N et le fichier N1 dans Balance N-1 facultative.
4. Cliquer Contrôler et préparer. Vérifier débit/crédit3200,31 et résultat900,19 avant de continuer.
5. Cliquer Conserver une nouvelle version. Noter son numéro et son empreinte ; dans une société vierge, c’est la version1.
6. Ouvrir Détailler le CPC depuis les balances conservées. L’ancienne version sans détail indique Aucun détail CPC conservé.
7. Cocher la confirmation de conservation depuis les seules balances de cette version, puis Conserver le détail CPC dans une nouvelle version.
8. La nouvelle version est sélectionnée automatiquement. Rouvrir le détail et examiner les charges, produits, résultat, écarts et comptes.
9. Choisir N-1 dans Période du détail CPC. Les totaux du jeu comparatif valent0 ; choisir N pour revenir.
10. Exporter la préparation PDF, Excel, puis Télécharger le dossier de préparation ZIP.

## Comment lire le détail ?

Les charges sont calculées débit moins crédit et les produits crédit moins
débit. La ligne6193 reste donc une charge de sens inverse à−200,01 ;7119
reste un produit de sens inverse à−100,02. Aucun reclassement n’est effectué.
Les comptes soldés sont omis. Les libellés individuels ne figurent pas dans
la source normalisée actuelle : Libellé non conservé est affiché explicitement.
Le plan actuel n’est pas utilisé pour inventer un libellé historique.

Chaque indicateur distingue total du détail, agrégat du CPC déjà figé et
écart détail moins CPC. Un écart non nul reste un diagnostic ; aucune correction
automatique ni écriture n’est créée pour le supprimer. Les anciens agrégats
numériques restent présentés tels que conservés ; le détail utilise Decimal.
Les montants dépassant la précision exacte d’Excel sont exportés comme texte.

Une source détaillée absente ou incomplète reste indisponible. Une balance
après solde technique119 ne reçoit pas un faux détail nul de charges/produits.
N-1 absent n’est jamais remplacé par zéro. La date, l’auteur, la méthode et la
référence de la version source sont conservés avec le détail dans la nouvelle
version. Une simple consultation ou un téléchargement ne recalcule pas B11.

## Versions, exports et logo

La nouvelle version conserve les autres compléments documentaires. Les pièces
jointes restent rattachées à leur version d’origine ; elles ne sont pas copiées
automatiquement vers la nouvelle. Revenir à une version antérieure ne la modifie pas.

Le PDF contient B11 et ses rapprochements. L’Excel contient Origine détail CPC,
Détail CPC N/N-1 et Rapprochement CPC N/N-1. Le ZIP contient également
detail_cpc_documentaire.json et le manifeste SHA-256 de ses fichiers.
Le logo et l’identité actuels sont ajoutés aux PDF/Excel, hors de l’empreinte
historique du contenu. Ajouter auparavant un logo fictif dans les paramètres
de société pour tester ce point. Ces exports ne constituent pas une archive
fiscale définitive, un XML officiel, un dépôt ou une preuve de conformité.

## Cas de recette humaine à suivre dans l’ordre

Prérequis communs : société fictive en MAD, exercice et comptes indiqués plus
haut, administrateur/comptable. Le cas07 utilise un lecteur de cette société.
Pour chaque cas, renseigner résultat réel, anomalies et preuve dans le classeur.
Les opérations ci-dessous n’ont aucune écriture ou incidence fiscale attendue.

|ID|Actions / données exactes|Résultat et justificatif attendus|Statut|
|---|---|---|---|
|C703-01|Importer N et N1 fournis, contrôler puis conserver la première version. Ouvrir le détail CPC avant sa conservation.|Débit/crédit3200,31 ; résultat N900,19. Aucun détail CPC conservé. Noter numéro/empreinte et garder capture.|Non testé|
|C703-02|Cocher la confirmation, conserver le détail, rouvrir. Examiner N puis N-1.|N charges1000,09 ; produits1900,28 ; résultat900,19 ; trois écarts0. Lignes6193−200,01 et7119−100,02, libellés non conservés. N-1 totaux0. Capture et empreinte de la nouvelle version.|Non testé|
|C703-03|Sélectionner la version source notée au cas01, puis celle du cas02 dans Préparations conservées.|Ancienne version toujours sans détail ; nouvelle version inchangée. Aucun Journal modifié. Captures des deux sélections et numéros.|Non testé|
|C703-04|Dans une nouvelle préparation, importer N seulement, sans N1 ; conserver la préparation puis son détail.|N résultat900,19 ; N-1 source absente et valeurs indisponibles, jamais0. Capture du comparatif manquant.|Non testé|
|C703-05|Importer le fichier TECHNIQUE seul ; contrôler puis conserver la préparation et son détail.|Débit/crédit1900,19 ; classe119 avec résultat900,19 conservé au bilan. CPC/détail N indisponible avec motif du solde technique. Aucune ligne de charges/produits inventée. Capture du motif.|Non testé|
|C703-06|Avec un administrateur, revenir à la version du cas02. Ajouter un logo fictif dans les paramètres société, puis télécharger PDF, Excel et ZIP.|Logo visible dans PDF/Excel ; soldes signés et totaux identiques. JSON du ZIP identique au détail, manifeste vérifiable. Conserver les trois fichiers et capture des montants.|Non testé|
|C703-07|Se connecter avec un lecteur de la même société ; ouvrir la version du cas02 et télécharger son ZIP.|Consultation/export possibles ; aucun bouton de conservation ou édition du détail. Conserver capture des droits et le ZIP téléchargé.|Non testé|

## Limites et prochaine étape

Ces sept cas constituent une recette utilisateur à effectuer. Les tests
automatisés et la restauration isolée sont consignés séparément dans le rapport703.
L’installation PostgreSQL cible et l’ouverture des guides dans Word/Excel restent
à vérifier par l’utilisateur. Aucune migration nouvelle n’est nécessaire pour B11.
Le module optionnel des pièces de préparation utilise la migration104 déjà
documentée ; elle n’est pas exécutée sur une base réelle par cette session.

La suite est le détail B1 des non-valeurs sur sources certaines. Les mouvements
bruts d’immobilisations et les informations extra-comptables ne peuvent pas être
reconstruits depuis deux seules balances de clôture. La liasse indépendante
reste partielle et n’est pas automatiquement prête à déposer.
