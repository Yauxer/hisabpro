# MODE D’EMPLOI ET RECETTE — TITRES DE PARTICIPATION DEPUIS LES BALANCES

Version 1 du 21 octobre 2026. Complément B4 de la préparation indépendante.

## Fonction et périmètre du contrôle

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

## Prérequis et données fictives

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

## Parcours utilisateur

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

## Vérifier les exports

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

## Recette humaine à effectuer

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

## État et suite

Développement de ce complément et résultats automatisés sont consignés dans
le rapport707. La recette humaine, l’ouverture dans Word/Excel et l’installation
cible restent à vérifier. Les autres compléments ETIC et fiscaux restent partiels.
Prochaine étape : documenter les émetteurs depuis des sources explicites, puis
traiter les mouvements d’immobilisations/provisions sans les inventer depuis
les seules balances. RH/paie et point6 humain restent différés.
