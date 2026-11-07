# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Version 1 du 21 octobre 2026. Annexe : préparations depuis balances, compléments707–715.

## Objet et ordre de lecture

Ce document rassemble les modes d’emploi et trente cas de recette des titres de participation,
déclarations d’émetteurs, cessions/retraits, mouvements d’immobilisations/amortissements/provisions
et rattachements de leurs clôtures aux comptes sources. Il complète le cahier général HisabPro.
Il ne remplace pas la recette annuelle complète depuis une base vierge jusqu’à l’archivage.

Accès commun : Comptabilité → Liasse fiscale → Préparer depuis des balances externes.
Installer les fichiers différentiels autorisés, redémarrer le backend et reconstruire le frontend.
Les migrations existantes du module doivent être présentes ; aucune migration nouvelle dans ces lots.
Utiliser exclusivement une société fictive séparée, en MAD, exercice2026 et profils autorisés.
Aucun essai de ce cahier ne doit modifier la comptabilité réelle. Les préparations présentées ne
créent ni écriture ni liquidation fiscale ; noter le Journal avant et après chaque parcours.

## Trois jeux de recette distincts

Jeu A : participations707 et émetteurs709, dans une préparation partagée avec les CSV707.
N titres2510=4000MAD ; N-1=3000MAD ; brut financier entier6000/4000MAD.
Les déclarations de deux émetteurs N2500+1500 et d’un émetteur N-1 3000 sont sourcées séparément.
Le total24/25 ne doit pas être comparé au seul251. Les pourcentages ne sont pas inférés du capital.

Jeu B : cessions/retraits711, dans une préparation distincte avec le contexte CSV707.
Le registre fictif de sorties est un autre exemple : prix5000−VNA6000=−1000MAD, puis variante−0,01.
Ses sorties ne sont pas à additionner aux mouvements du jeu C. Aucun rapprochement de ces deux
registres fictifs distincts n’est revendiqué et aucun résultat fiscal n’est déduit de leur différence.

Jeu C : mouvements713 puis rattachements715, dans une préparation partagée avec les CSV713.
Clôtures11000/4500/700MAD ; rattachements explicites2340/2834/1511, écarts0.
Après clôture déclarée B2 à10999,99, l’ancien contrôle reste signalé À refaire ; le nouveau donne−0,01.
Les ouvertures et flux viennent de pièces fictives, jamais d’une déduction des seules balances.

Les trois préparations sont distinctes. Elles peuvent être conservées dans la même société fictive,
sans écriture créée. Noter pour chacune son numéro, sa version et son empreinte afin de choisir
la bonne préparation dans le sélecteur. Les numéros de version réels peuvent varier.

## Utiliser le classeur de suivi

Ouvrir CAHIER_PREPARATIONS_BALANCES_717.xlsx. La feuille Synthèse compte les statuts humains
et donne accès aux guides de chaque partie. Participations, Émetteurs, Cessions, Mouvements et
Rattachements contiennent six cas chacune : actions/données, résultats attendus, statut, résultat
réel, anomalies et preuves. Les trente statuts commencent à Non testé. Remplir le résultat réel
et ajouter les captures/exports après vos essais. Preuves et Anomalies sont les registres communs.
Conserver un modèle vierge et utiliser une copie pour les résultats de travail.
Les formules du tableau de bord se recalculent à l’ouverture dans Excel.

Distinguer quatre états : développement du complément terminé ; tests automatisés du lot validés ;
recette utilisateur à effectuer ; production nonvalidée. Les réussites automatisées consignées
aux rapports ne remplissent pas les résultats humains. Un contrôle actuel ou un écart0 ne prouve
pas la complétude d’un registre ou une conformité réglementaire. Les sources fiscales autonomes,
spécifications officielles et limites du cahier général restent des sujets distincts.
RH/paie et point6 humain restent différés. Aucun modèle DGI ou dépôt officiel n’est certifié.

## Partie Participations — complément707

Guide séparé : MODE_EMPLOI_PARTICIPATIONS_707.docx/.pdf/.xlsx. Données : DONNEES_PARTICIPATIONS707.json.


Version 1 du 21 octobre 2026. Complément B4 de la préparation indépendante.

### Fonction et périmètre du contrôle

Dans Comptabilité → Liasse fiscale → Préparer depuis des balances externes,
ouvrir Détailler les titres de participation depuis les balances conservées.
Le titre B4 reprend le catalogue interne existant, sans prétendre à une
exhaustivité officielle du modèle DGI ou à un dossier prêt à déposer.

Le solde signé des comptes251 est calculé débit moins crédit. Le brut financier
du bilan regroupe24/25, donc plusieurs postes : il ne doit jamais être comparé
directement au seul251. L’écran montre séparément titres251, autres soldes24/25
et brut financier entier. Seul le dernier est rapproché du même brut24/25 du
bilan déjà figé. Un écart reste un diagnostic sans correction automatique.

L’émetteur, son capital, la quote-part détenue et les produits reçus sont
inconnus depuis la seule balance. Ils restent à documenter séparément, par
exemple dans la note B4 avec des justificatifs. Aucun libellé historique n’est
reconstitué depuis le plan actuel. Les provisions ne sont pas réparties par
titre et aucun mouvement brut n’est déduit de N/N-1.

### Prérequis et données fictives

Utiliser une société fictive séparée en MAD, exercice2026 ouvert et comptes1111,
2411,2510,5141 présents au plan. Prévoir un administrateur/comptable pour conserver
et un lecteur pour consulter. Le module de préparations depuis balances, avec
la migration071 existante, doit déjà être installé. Aucune nouvelle migration
n’est requise. Après application des fichiers, redémarrer le backend et utiliser
le frontend reconstruit ou le serveur de développement.

Un administrateur ajoute un logo fictif aux paramètres société pour tester les
exports. Noter le nombre d’écritures du Journal avant la recette : il doit rester
inchangé. Ne pas utiliser une société comptable réelle pour ces essais.

Fichiers fournis dans docs/recette : BALANCE_FICTIVE_PARTICIPATIONS707_N.csv,
BALANCE_FICTIVE_PARTICIPATIONS707_N1.csv et DONNEES_PARTICIPATIONS707.json.
Ces balances sont fictives ; leur import en préparation ne crée pas d’écriture.

N : capital1111 crédit10000 ; titres2510 débit4000 ; prêts2411 débit2000 ;
banque5141 débit4000. Les autres cellules valent explicitement0.
N-1 : capital1111 crédit10000 ; titres2510 débit3000 ; prêts2411 débit1000 ;
banque5141 débit6000. Les autres cellules valent0.
Débit = crédit =10000MAD dans les deux périodes.

Oracle N : titres4000 + autres financiers2000 = brut financier6000 ; avec
banque4000, actif10000 = capital10000. N-1 :3000 +1000 =4000 ; avec banque6000,
actif10000. Les écarts sur le brut entier24/25 sont0. Aucun émetteur, pourcentage
ou revenu reçu ne peut être déterminé à partir de ces nombres.

### Parcours utilisateur

1. Choisir la société fictive et l’exercice2026, puis ouvrir Liasse fiscale.
2. Dans Préparer depuis des balances externes, ouvrir Importer N / N-1 et choisir les deux CSV fournis.
3. Cliquer Contrôler et préparer, vérifier débit/crédit10000 et résultat CPC0, puis Conserver une nouvelle version.
4. Noter numéro/empreinte et ouvrir Détailler les titres de participation depuis les balances conservées.
5. La version source indique qu’aucun détail des participations n’est conservé. Cocher la confirmation, puis Conserver les participations dans une nouvelle version.
6. La nouvelle version est sélectionnée immédiatement. Rouvrir le détail, vérifier N :4000,2000,6000 ; un seul écart de contrôle, sur le brut entier, égal0.
7. Choisir N-1 dans Période des participations :3000,1000,4000 et écart0. Revenir à N.
8. Télécharger la préparation PDF, Excel et le dossier de préparation ZIP.

Le calcul, titre, méthode, auteur, date et version source sont figés lors de
la conservation. Les anciennes versions ne sont pas modifiées ni recalculées
à la consultation ou à l’export. Les autres compléments restent conservés.
Les pièces jointes appartiennent à leur version ; aucune copie implicite.

### Vérifier les exports

PDF : B4, soldes251 signés et décomposition financière ; informations sur
l’émetteur explicitement à compléter. Excel : Origine participations,
Participations N/N-1, Contrôle financier N/N-1. Émetteur, capital, quote-part
et produits reçus y restent Indisponible, jamais des zéros fabriqués. Les lignes
Titres251 uniquement et Autres24/25 indiquent Non comparable au24/25. Le contrôle
du brut entier porte bien sur6000 en N et4000 en N-1.

ZIP : participations_documentaires.json, préparation conservée, sources CSV,
PDF, Excel, justificatifs propres à la version et MANIFESTE_SHA256.json.
Le logo et l’identité actuels apparaissent dans PDF/Excel, hors empreinte
historique du contenu. Sans N-1, le comparatif reste indisponible. Une source
complète sans solde251 donne explicitement0, sans présumer l’inventaire juridique.
Un solde technique119 n’empêche pas ce détail si ses sources sont présentes.

### Recette humaine à effectuer

Prérequis communs ci-dessus, administrateur/comptable sauf cas06 lecteur.
Aucune écriture ou incidence fiscale attendue pour ces préparations.
Remplir résultat réel, anomalies et preuves dans l’Excel fourni ; les tests
automatisés ne remplissent pas à votre place les statuts de cette recette.

|ID|Actions / données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|P707-01|Importer N et N1 fournis, contrôler et conserver la préparation ; ouvrir le détail des participations.|Débit/crédit10000 pour chaque période ; détail non encore conservé. Noter numéro/empreinte et capture.|Non testé|
|P707-02|Confirmer et conserver le détail B4 ; rouvrir et examiner N puis N-1.|N titres4000/autres2000/brut6000 ; N-1 3000/1000/4000. Un seul écart de contrôle par période, sur le brut entier, égal0. Émetteurs et autres informations inconnus. Captures des deux périodes.|Non testé|
|P707-03|Revenir à la version source du cas01 puis à celle du cas02 ; comparer le Journal au nombre initial.|Source toujours sans détail B4, nouvelle version inchangée, aucune écriture créée. Captures des versions et Journal.|Non testé|
|P707-04|Créer une autre préparation avec N seul ; conserver la préparation puis B4.|N titres4000 ; N-1 indisponible avec motif source absente, jamais un faux0. Capture du comparatif.|Non testé|
|P707-05|Depuis la version du cas02 avec logo fictif, télécharger PDF, Excel et ZIP.|Logo dans PDF/Excel, champs émetteur/quote-part/capital/produits indisponibles, valeurs et contrôle financier exacts. JSON et empreinte cohérents, manifeste vérifiable. Conserver les trois fichiers.|Non testé|
|P707-06|Se connecter avec un lecteur de la société fictive, ouvrir la version du cas02 puis télécharger son ZIP.|Consultation/export possibles, aucune conservation ou modification du détail. Capture des droits et ZIP réel.|Non testé|

### État et suite

Développement de ce complément et résultats automatisés sont consignés dans
le rapport707. La recette humaine, l’ouverture dans Word/Excel et l’installation
cible restent à vérifier. Les autres compléments ETIC et fiscaux restent partiels.
Prochaine étape : documenter les émetteurs depuis des sources explicites, puis
traiter les mouvements d’immobilisations/provisions sans les inventer depuis
les seules balances. RH/paie et point6 humain restent différés.
## Partie Émetteurs — complément709

Guide séparé : MODE_EMPLOI_EMETTEURS_709.docx/.pdf/.xlsx. Données : DONNEES_EMETTEURS709.json.


Version 1 du 21 octobre 2026. Complément documentaire709 de la préparation depuis balances.

### Accès et périmètre

Dans Comptabilité → Liasse fiscale → Préparer depuis des balances externes,
consulter une préparation conservée puis ouvrir Documenter les émetteurs des
participations. Les identifiants B4-N et B4-N1 sont des codes internes du
formulaire, sans prétendre à une numérotation officielle DGI.

Le détail automatique B4 du lot707 reste séparé et inchangé. Le nouveau
formulaire permet de documenter les émetteurs, leur capital, la quote-part
et les produits reçus depuis des sources explicites. Ces informations ne sont
jamais déduites des seuls soldes comptables.

Le rapprochement porte sur la valeur brute déclarée par compte251 et son solde
brut signé dans la balance source conservée. Il ne compare ni le capital de
l’émetteur au montant investi, ni le seul251 au total24/25 du bilan. Aucun
pourcentage n’est déduit ou additionné entre des sociétés différentes.

### Prérequis et données exactes

Utiliser exclusivement une société fictive séparée en MAD, exercice2026 ouvert,
comptes1111,2411,2510 et5141 déjà au plan ; utilisateur administrateur/comptable,
puis lecteur pour les droits. Le module existant de préparations et sa migration071
doivent être installés. Aucune nouvelle migration n’est ajoutée. Redémarrer le
backend et reconstruire le frontend après application des fichiers.

Réutiliser les deux CSV du lot707 dans docs/recette :
BALANCE_FICTIVE_PARTICIPATIONS707_N.csv et BALANCE_FICTIVE_PARTICIPATIONS707_N1.csv.
Chaque balance a débit=crédit=10000MAD. N contient2510 débit4000 ; N-1 contient2510
débit3000. Les autres postes sont explicités dans DONNEES_PARTICIPATIONS707.json.
Le JSON DONNEES_EMETTEURS709.json fournit les déclarations fictives et les oracles.
Aucun identifiant légal réel n’est nécessaire ni inventé comme exigence.

N : choisir B4-N, statut Saisie documentée — à revoir, justification Relevé fictif709 N.
Ajouter deux lignes au tableau, compte2510 pour chacune :

- Ligne1 : Émetteur Atlas Industrie fictive ; identifiant FICTIF-A ; valeur brute2500,00MAD ; capital500000,00MAD ; quote-part20 ; produits reçus vides ; référence Attestation fictive A.
- Ligne2 : Émetteur Rif Services fictive ; identifiant vide ; valeur brute1500,00MAD ; capital et quote-part vides ; produits reçus100,00MAD ; référence Attestation fictive B.

N-1 : choisir B4-N1, même statut, justification Relevé fictif709 N-1. Ajouter
une ligne2510 : Atlas Industrie fictive ; identifiant vide ; valeur brute3000,00 ;
capital500000,00 ; quote-part20 ; produits reçus0 explicitement ; référence Attestation fictive N-1.

Toutes les références et entités ci-dessus sont fictives. Le capital et le
pourcentage sont des données déclarées indépendantes :20% ne se calcule pas
à partir de2500/500000. Une donnée inconnue reste vide, un zéro est explicite.

### Parcours et contrôles indépendants

1. Noter le nombre d’écritures au Journal et ajouter un logo fictif aux paramètres société.
2. Importer les CSV dans une préparation, contrôler puis conserver une nouvelle version. Le Journal doit rester inchangé.
3. Ouvrir Documenter les émetteurs des participations. Saisir N puis N-1 ci-dessus ; revenir à N pour vérifier que le brouillon est préservé.
4. Cocher Je confirme les données et déclarations saisies, sans valider une liasse complète. Cliquer Conserver les tableaux ETIC dans une nouvelle version.
5. La nouvelle version est immédiatement sélectionnée. Rouvrir le formulaire. Contrôle N :2500+1500=4000 ; écart4000−4000=0. N-1 :3000−3000=0.
6. Dans la version conservée, modifier la valeur brute de la première ligne N en2499,99. Les contrôles affichés concernent toujours la version conservée, donc écart0 tant que ce brouillon n’est pas enregistré.
7. Confirmer et conserver à nouveau. Le nouveau contrôle N devient2499,99+1500−4000=−0,01MAD. Revenir à la version précédente : son écart reste0.
8. Télécharger PDF, Excel et dossier ZIP de la nouvelle version ; vérifier les données et le logo.

Si une valeur brute d’une ligne est inconnue, la somme de son compte et son
écart restent indisponibles. Le capital, la quote-part ou les produits reçus
peuvent rester inconnus sans empêcher un rapprochement brut dont toutes les
valeurs brutes sont connues. Une déclaration Néant avec un solde251 non nul
garde une alerte visible ; elle ne crée pas un zéro pour faire disparaître l’écart.

Les montants signés valeur brute et produits reçus ont deux décimales maximum.
Le capital est non négatif et a deux décimales. La quote-part va de0 à100 et
accepte au plus douze décimales. NaN, infinis et précisions monétaires excessives
sont refusés. Aucun taux fiscal ou règle de détention juridique n’est ajouté.
En l’absence de source N-1 détaillée, sa saisie est désactivée et le contrôle
reste indisponible. Les montants sont des contre-valeurs MAD documentées :
aucun cours de change ni conversion automatique n’est inventé.

### Exports et traçabilité

PDF : déclarations, références, auteur/date/version source, contrôles conservés
par compte et logo actuel. Excel : Origine émetteurs, Émetteurs N/N-1,
Déclaration émetteurs N/N-1 et Contrôle émetteurs N/N-1. Le pourcentage est un
texte décimal exact ; une cellule vide ne se transforme pas en0. Les textes
commençant par un signe égal restent des textes. Les montants trop grands pour
être représentés exactement comme nombres Excel sont exportés comme textes.

ZIP : declarations_emetteurs.json et les exports/source/pièces du dossier,
avec MANIFESTE_SHA256.json. Les anciennes versions et les autres compléments
restent inchangés ; les pièces restent rattachées à leur version d’origine.
Le logo actuel figure dans les exports et reste extérieur à l’empreinte
historique du contenu. Une note B4 déclarée non applicable alors que des
émetteurs sont saisis conserve une alerte ; aucune correction silencieuse.

### Recette humaine à effectuer

Prérequis communs ci-dessus ; conserver captures des versions, exports et
Journal. Aucun test automatisé ne remplit le résultat réel de votre recette.
Aucune écriture comptable ni liquidation fiscale n’est créée par ce formulaire.

|ID|Actions / données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|E709-01|Importer N et N1 du lot707, conserver ; saisir les deux lignes N et la ligne N-1 détaillées ci-dessus.|Comptes disponibles2510 uniquement ; brouillons préservés en changeant de période. Capture des trois lignes.|Non testé|
|E709-02|Confirmer puis conserver ; rouvrir N puis N-1.|Nouvelle version immédiatement sélectionnée ; N somme4000/écart0 ; N-1 somme3000/écart0. Capital et quote-part Rif inconnus, produits N-1 explicitement0. Capture des contrôles.|Non testé|
|E709-03|Modifier2500 en2499,99 dans N sans enregistrer, examiner les contrôles puis confirmer et conserver.|Avant enregistrement, contrôle conservé toujours0 ; après, nouvelle version écart−0,01. Version précédente toujours écart0, Journal inchangé. Captures des deux versions.|Non testé|
|E709-04|Dans un autre brouillon, saisir quote-part101 puis conserver ; corriger en20 et reconfirmer. Créer aussi une préparation N seul et ouvrir B4-N1.|101 refusé avec erreur lisible et brouillon conservé ; correction réinitialise confirmation puis réussit. N-1 absent : saisie désactivée et contrôle indisponible. Captures erreur et période absente.|Non testé|
|E709-05|Avec logo fictif, télécharger PDF, Excel et ZIP de la version du cas03 ; ouvrir les fichiers.|Montants signés, écart−0,01, données inconnues distinctes du0, références/auteur/source et logo présents. JSON contrôles identiques à l’écran, manifeste vérifiable. Conserver trois exports.|Non testé|
|E709-06|Se connecter comme lecteur à la société fictive ; ouvrir la version du cas02 et télécharger le ZIP.|Champs désactivés, aucun bouton de conservation, consultation et téléchargement autorisés ; aucune nouvelle version/écriture. Capture droits et ZIP.|Non testé|

### État et limites

Le développement et les tests automatisés du complément sont consignés dans
le rapport709. La recette humaine reste à effectuer ; l’ouverture Word/Excel
sur votre poste et la mise en production ne sont pas validées automatiquement.
La préparation indépendante ne devient pas une liasse complète ou prête à déposer.
Les mouvements ETIC, la fiscalité autonome et les validations réglementaires
restent des travaux distincts. RH/paie et point6 humain restent différés.
## Partie Cessions — complément711

Guide séparé : MODE_EMPLOI_CESSIONS_711.docx/.pdf/.xlsx. Données : DONNEES_CESSIONS711.json.


Version 1 du 21 octobre 2026. Complément B3 de la préparation depuis balances.

### Fonction et limites

Dans Comptabilité → Liasse fiscale → Préparer depuis des balances externes,
consulter une préparation puis ouvrir Documenter les cessions et retraits
d’immobilisations. Le formulaire B3 est un complément documentaire interne,
selon les données du tableau de cessions déjà présent dans HisabPro. Il ne
prétend pas constituer un modèle DGI exhaustif ou officiellement validé.

Désignation, date/type de sortie, valeur d’entrée, valeur nette d’amortissement
VNA et prix sont saisis depuis des sources explicites. Aucun de ces mouvements
n’est déduit des seules balances N/N-1 ou du registre comptable réel de la
société active. Le contrôle arithmétique donne prix déclaré moins VNA déclarée.
Il ne calcule pas un résultat fiscal et ne crée aucune écriture.

Le contrôle est figé avec la version, sa méthode, son auteur, sa date UTC et
l’empreinte de sa source. Les contrôles affichés concernent la version conservée,
pas le brouillon. Une information inconnue reste vide ; un zéro est explicite.
Un prix ou une VNA inconnus rendent la différence de la ligne indisponible.
Le total reste indisponible si une seule ligne est inconnue ou si aucune ligne
n’est déclarée. Une déclaration Néant est une déclaration justifiée, pas une
preuve de l’exhaustivité du registre ou du rapprochement B2/B2bis.

### Prérequis et jeu de données

Utiliser uniquement une société fictive séparée en MAD et l’exercice2026 ouvert.
La préparation depuis balances et la migration071 existantes doivent être
installées. Aucune nouvelle migration n’est ajoutée. Redémarrer le backend et
reconstruire le frontend après application des fichiers. Utilisateurs : un
administrateur/comptable pour saisir et un lecteur pour vérifier les droits.
Ajouter un logo fictif aux paramètres société et noter le nombre d’écritures
au Journal avant l’essai : il doit rester inchangé.

Réutiliser les CSV fictifs du lot707 : BALANCE_FICTIVE_PARTICIPATIONS707_N.csv
et BALANCE_FICTIVE_PARTICIPATIONS707_N1.csv, dans docs/recette. Chaque période
a débit=crédit=10000MAD. Ces soldes ne prouvent pas les sorties ci-dessous :
les déclarations proviennent du registre et des pièces fictives distinctes.
Les données exactes sont aussi fournies dans DONNEES_CESSIONS711.json.

Choisir B3, déclaration Saisie documentée — à revoir et justification
Registre fictif711 et pièces de sortie. Ajouter deux lignes :

- Ligne1 : Désignation Machine Atlas fictive ; date2026-06-30 ; type cession ; valeur d’entrée10000,00MAD ; VNA6000,00MAD ; prix5000,00MAD ; référence Acte fictif711 A.
- Ligne2 : Désignation Matériel Rif fictif ; date2026-09-15 ; type retrait ; valeur d’entrée3000,00MAD ; VNA0 explicitement ; prix0 explicitement ; référence PV fictif711 B.

Oracle indépendant : ligne1 =5000−6000=−1000MAD ; ligne2 =0−0=0MAD ; total−1000MAD.
Remplacer ensuite le prix de ligne1 par5999,99MAD : différence5999,99−6000=−0,01MAD,
total−0,01MAD. Ces chiffres servent uniquement à la recette documentaire,
sans affirmer une qualification juridique ou un calcul fiscal des opérations.

### Parcours d’utilisation

1. Importer et conserver la préparation fictive ; noter son numéro et son empreinte.
2. Ouvrir Documenter les cessions et retraits d’immobilisations. Choisir le statut et saisir la justification puis les deux lignes ci-dessus.
3. Les dates sont facultatives. Si renseignées, utiliser AAAA-MM-JJ ou le sélecteur de date. Le type peut rester vide ; sinon choisir cession, retrait ou autre.
4. Cocher Je confirme les données et déclarations saisies, sans valider une liasse complète. Cliquer Conserver les tableaux ETIC dans une nouvelle version.
5. La nouvelle version est immédiatement sélectionnée. Rouvrir le formulaire : ligne1−1000, ligne2 0, total−1000MAD.
6. Modifier le prix de la première ligne en5999,99 sans conserver. Les contrôles restent ceux de la version conservée, soit−1000MAD. Confirmer et conserver pour obtenir une nouvelle version à−0,01MAD.
7. Revenir à la version précédente : son prix5000 et son total−1000 doivent rester inchangés. Comparer le nombre d’écritures au Journal.
8. Télécharger PDF, Excel et dossier ZIP de la dernière version, puis vérifier le logo et les données.

Les montants saisis sont non négatifs en MAD, avec deux décimales maximum ;
leur différence peut être négative. NaN, infinis, booléens et précisions
excessives sont refusés. Aucun taux ou traitement fiscal n’est ajouté.
Une VNA supérieure à la valeur d’entrée déclarée garde une alerte visible ;
aucun chiffre n’est ajusté. Une date déclarée hors de la période conservée est
signalée. La désignation et la référence sont requises pour identifier chaque
ligne déclarée documentée, sans rendre date/type ou montants inconnus obligatoires.
Une note B3 Non applicable et un tableau renseigné conservent une contradiction visible.

### Vérifier les exports

PDF : déclarations, références, source/auteur/UTC, différences conservées et
logo actuel. Excel : Origine cessions, Cessions déclarées N, Déclaration cessions,
Contrôle cessions. Les montants inconnus restent indisponibles et ne deviennent
pas0. Les textes restent des textes, même s’ils commencent par un signe égal ;
les grands nombres deviennent des textes si nécessaire pour préserver la précision.

ZIP : cessions_documentaires.json, sources, PDF, Excel, pièces propres à la version
et MANIFESTE_SHA256.json. Les données et contrôles JSON correspondent à ceux
conservés ; vérifier les empreintes du manifeste. Le logo actuel est extérieur
à l’empreinte historique. Les autres compléments et anciennes versions sont
préservés. Les pièces jointes ne sont pas copiées implicitement entre versions.

### Recette humaine à effectuer

Prérequis communs ci-dessus ; administrateur/comptable sauf cas06 lecteur.
Résultat comptable et fiscal attendu du formulaire : aucune écriture, aucune
liquidation fiscale, aucun changement au bilan/CPC de la préparation.
Remplir résultat réel, anomalies et preuves dans le classeur fourni. Les tests
automatisés ne renseignent pas la recette utilisateur à votre place.

|ID|Actions / données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|C711-01|Importer et conserver les CSV707 dans une société fictive2026/MAD ; noter le Journal ; saisir B3 et les deux lignes ci-dessus.|Brouillon avec dates/types explicites et sources fictives. Aucun contrôle conservé avant enregistrement. Capture et nombre initial d’écritures.|Non testé|
|C711-02|Confirmer puis conserver et rouvrir B3.|Nouvelle version sélectionnée immédiatement ; ligne1−1000MAD, ligne2 0, total−1000. Auteur/source et données corrects. Capture des contrôles.|Non testé|
|C711-03|Modifier le prix ligne1 de5000 en5999,99 ; regarder les contrôles puis confirmer et conserver ; revenir à la version précédente.|Brouillon ne change pas le contrôle conservé−1000 ; après sauvegarde, nouvelle version−0,01 ; ancienne version toujours−1000 ; Journal inchangé. Captures des versions.|Non testé|
|C711-04|Sur un autre brouillon, saisir prix−1 et tenter de conserver ; corriger en5999,99. Essayer aussi VNA10001 avec entrée10000 et date2025-12-31.|Prix négatif refusé, brouillon préservé ; correction réinitialise confirmation puis réussit. VNA supérieure/date hors2026 conservent deux alertes sans ajustement. Captures erreur et alertes.|Non testé|
|C711-05|Télécharger PDF, Excel et ZIP du cas03 avec logo fictif ; ouvrir les trois fichiers ; sur un autre brouillon laisser le prix vide puis conserver.|Logo/source/références présents ; total−0,01 exact et manifeste vérifiable. Avec prix inconnu, différence et total indisponibles, jamais0. Conserver exports et capture des inconnus.|Non testé|
|C711-06|Se connecter comme lecteur ; consulter B3 du cas02 et télécharger son ZIP.|Champs désactivés et aucun bouton de conservation ; consultation et téléchargement autorisés ; aucune nouvelle écriture/version. Capture droits et ZIP.|Non testé|

### État et suite

Les tests exécutés et limites sont consignés au rapport711. La recette humaine,
l’ouverture Office sur votre poste et la mise en production restent à effectuer.
B3 documentaire ne prouve ni l’exhaustivité des sorties ni leur rapprochement
avec B2/B2bis. Les mouvements d’immobilisations, amortissements et provisions
restent à documenter depuis des sources explicites, puis la fiscalité autonome.
RH/paie et point6 humain restent différés. Aucune certification officielle affirmée.
## Partie Mouvements — complément713

Guide séparé : MODE_EMPLOI_MOUVEMENTS_713.docx/.pdf/.xlsx. Données : DONNEES_MOUVEMENTS713.json.


Version 1 du 21 octobre 2026. Saisie documentaire interne B2/B2bis/B5, exercice N.

### Fonction et accès

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

### Prérequis et données fictives exactes

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

### Parcours utilisateur

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

### Exports et traçabilité

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

### Recette humaine à effectuer

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

### État et limites restantes

Tests et limites au rapport713. Le complément ne prouve pas le rapprochement
au bilan/registre ou aux cessions B3, ni l’exhaustivité des mouvements. Les
sources fiscales autonomes restent distinctes et partielles. Recette humaine,
ouverture Office et production restent à valider. RH/paie et point6 humain
différés. Aucune certification officielle affirmée.
## Partie Rattachements — complément715

Guide séparé : MODE_EMPLOI_RACCORDS_715.docx/.pdf/.xlsx. Données : DONNEES_RACCORDS715.json.


Version 1 du 21 octobre 2026. Complément interne B2/B2bis/B5 de la préparation depuis balances.

### Fonction et prérequis

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

### Données exactes et oracles indépendants

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

### Parcours utilisateur

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

### Brouillons, inconnus et contrôles anciens

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

### Vérifier les exports

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

### Recette humaine à effectuer

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

### État et suite

Les tests et limites sont consignés au rapport715. Recette humaine, ouverture
Office et installation cible restent à vérifier ; production nonvalidée. Les
sources fiscales autonomes et les spécifications officielles restent distinctes.
RH/paie et point6 humain différés. Aucune certification officielle affirmée.
