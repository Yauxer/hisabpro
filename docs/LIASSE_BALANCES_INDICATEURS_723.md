# MODE D’EMPLOI ET RECETTE — INDICATEURS COMPTABLES C3

Version 1 du 21 octobre 2026. Projection comptable interne, sans historique inventé.

## Accès et périmètre

Comptabilité → Liasse fiscale → Préparer depuis des balances externes →
sélectionner une préparation conservée → Consulter les indicateurs comptables
C3 depuis les balances. Confirmer puis Conserver les indicateurs C3 dans une
nouvelle version. Réouvrir le détail et choisir N, N-1 ou N-2.

La préparation réutilise le calcul ETIC existant avec une sortie décimale
exacte ; elle n’interroge ni le Journal courant ni le module RH. Le mode
historique normal du moteur conserve son contrat numérique. Les comptes
sources sont affichés sans libellé historique inventé. Les écarts aux états
figés restent visibles, sans reclassement ni modification des écritures.

Les montants certains sont la situation nette, le chiffre d’affaires711/712,
le résultat avant impôts, les impôts comptabilisés, le résultat net et le solde
de rémunérations6171. Ce dernier n’est pas un calcul de paie ni une validation
de bulletins. Le B13 documentaire et son impôt théorique déclaré restent
distincts : C3 présente l’impôt effectivement comptabilisé dans sa balance.

N-2 n’est pas une source du module d’import N/N-1. Il reste indisponible ;
aucun exercice du Journal courant n’est repris pour le compléter. Effectif
moyen, bénéfices distribués, affectations et données par titre restent aussi
à documenter. Leur saisie structurée n’est pas fournie par ce détail.
Les notes et pièces du dossier peuvent conserver les justificatifs ; elles
ne transforment pas automatiquement ces valeurs inconnues en indicateurs.

## Prérequis et données fictives

Utiliser une société fictive distincte en MAD, exercice2026, avec administrateur,
comptable et lecteur. Compléter le plan existant ; vérifier1111,2111,28111,
5141,7111,6132,7581,6701,6171 et1191. Ajouter un logo fictif. Module de
préparations/migrations existantes requis ; aucune migration nouvelle dans723.
Redémarrer le backend et reconstruire le frontend après application des fichiers.

Importer BALANCE_FICTIVE_INDICATEURS723_N.csv et
BALANCE_FICTIVE_INDICATEURS723_N1.csv fournis dans docs/recette.
Toutes les cellules non mouvementées de ces lignes valent explicitement0.

N :1111 crédit10000 ;2111 débit2000 ;28111 crédit500 ;5141 débit14500 ;
7111 crédit10000 ;6132 débit3000 ;7581 crédit1000 ;6701 débit1600 ;6171 débit400.
Débit=crédit=21500MAD. Courant10000−3000−400=6600 ; non courant1000 ;
résultat avant impôts7600 ; impôt comptabilisé1600 ; résultat net6000.
Non-valeurs nettes2000−500=1500 ; capitaux propres10000+6000=16000 ;
situation nette16000−1500=14500. Chiffre d’affaires10000 ; rémunérations6171=400.

N-1 :1111 crédit10000 ;2111 débit1000 ;28111 crédit200 ;5141 débit12200 ;
7111 crédit5000 ;6132 débit2000. Débit=crédit=15200MAD.
Résultat avant impôts=net=3000 ; impôt et rémunérations6171 explicitement0
dans la balance. Non-valeurs nettes800 ; situation nette10000+3000−800=12200.
Chiffre d’affaires5000. Aucun effectif moyen n’est déduit de ces soldes.

Ces données forment un jeu distinct du B13 fictif721. Ne pas mélanger les
résultats6000 et6400, ni les banques14500 et16400 entre ces deux sociétés.
DONNEES_INDICATEURS723.json contient les montants et les oracles indépendants.

## Parcours et contrôles

1. Importer les deux CSV puis contrôler et conserver. Noter version, empreinte et nombre d’écritures du Journal.
2. Ouvrir C3. Avant conservation, aucun ancien calcul n’est créé par la simple consultation. Cocher la confirmation et conserver une nouvelle version.
3. Vérifier la sélection de cette version sans F5. Réouvrir C3 et comparer les montants N ci-dessus ; écarts au bilan/CPC figés attendus0.
4. Choisir N-1 : situation12200, chiffre d’affaires5000, avant impôts/net3000, impôts et rémunérations0. Les données extra-comptables restent à documenter.
5. Choisir N-2 : source non fournie, montants indisponibles. Ne pas interpréter cet état comme une année d’activité nulle.
6. Télécharger le dossier ZIP : JSON des indicateurs, PDF, Excel et manifeste SHA256. Vérifier logo actuel, période, auteur, méthode et empreinte du parent.
7. Revenir à la version antérieure : elle conserve son contenu et ses pièces d’origine. Aucun calcul ni montant d’écriture n’a changé dans le Journal.

## Clôture technique et limites

Le CSV BALANCE_FICTIVE_INDICATEURS723_TECHNIQUE.csv est fourni pour un test
séparé après solde technique : importer1111 crédit10000,2111
débit2000,28111 crédit500,5141 débit14500 et1191 crédit6000 ; aucun compte6/7.
Débit=crédit=16500MAD. La situation nette reste14500 ; le résultat d’activité,
le chiffre d’affaires et les rémunérations sont indisponibles, jamais0 déduit.
Le résultat119 n’est pas ajouté une seconde fois. B11 demande aussi une
balance avant clôture technique ; les anciennes versions déjà conservées
ne sont pas recalculées ou réparées automatiquement.

Sans N-1, le comparatif est indisponible. Sans CPC exploitable, aucun résultat
d’activité fiable n’est affiché ; la situation nette reste calculable après119
lorsque ses sources comptables sont certaines. Un écart aux états figés ne
doit pas être masqué en modifiant une écriture validée. Les libellés des
comptes non conservés sont explicitement indisponibles.

Le lecteur consulte et télécharge sans conserver. Une autre société ne doit
pas accéder au dossier. Les réponses tardives après changement de version,
fermeture ou jeton ne doivent pas remplacer la sélection courante.

## Cas de recette humaine à effectuer

|ID|Actions et données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|I723-01|Dans une société fictive distincte, importer les deux CSV723, conserver puis ouvrir C3, confirmer et conserver.|Nouvelle version sélectionnée sans F5. N : situation14500, CA10000, avant impôts7600, impôts1600, net6000, rémunérations400. Écarts aux états figés0. Captures et empreintes.|Non testé|
|I723-02|Choisir successivement N-1 puis N-2 dans le détail conservé.|N-1 : situation12200, CA5000, avant/net3000, impôts et rémunérations0. N-2 et données extra-comptables indisponibles, aucune année du Journal reprise. Captures des périodes.|Non testé|
|I723-03|Dans une autre préparation fictive, importer seulement le CSV N723 puis conserver C3. Consulter et télécharger comme lecteur.|N inchangé ; N-1 absent et N-2 absent ne valent pas0. Lecteur sans bouton de conservation, exports accessibles. Captures et fichiers.|Non testé|
|I723-04|Dans une société fictive distincte, importer le CSV TECHNIQUE723 fourni (soldé119), conserver C3 puis un nouveau détail B11.|Situation14500 sans double ajout du119 ; activité C3 indisponible ; B11 demande la balance avant clôture. Aucun résultat nul fabriqué et aucun ancien snapshot réécrit. Captures et versions.|Non testé|
|I723-05|Ajouter un logo fictif et télécharger ZIP/PDF/Excel après C3. Comparer JSON, méthode, auteur, parent, sources et manifeste.|Même version et montants dans tous les formats ; logo actuel sur PDF/Excel ; grands montants exacts ; inconnus visibles. Fichiers et captures à conserver.|Non testé|
|I723-06|Comparer le Journal, les autres compléments, versions et pièces avant/après C3. Relire une ancienne version ; changer de sélection pendant un chargement.|Aucune écriture, liquidation, donnée RH ou autre complément modifié. Ancienne version intacte ; sélection courante respectée. Preuves avant/après et observations.|Non testé|

## Statuts

Projection comptable développée ; tests réellement exécutés dans le rapport723.
Le C3 réglementaire complet nécessite encore ses sources historiques et
extra-comptables. Recette utilisateur, Office Desktop, installation cible,
conformité réglementaire et production nonvalidées automatiquement.
Suite : données fiscales B12 et flux/déclarations B14 sur sources explicites.
RH/paie et point6 humain restent différés.
