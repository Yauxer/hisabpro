# Mise à jour HisabPro — reprise du 10 octobre2026

Cette livraison est un différentiel à appliquer à une installation déjà au
niveau342 ou du cumulatif `HisabPro_Session_20261010_1939_Cumulatif_Verifie.zip`.
Le dépôt courant contient ces changements ; ne pas réappliquer les anciens patches.
Pour une installation au niveau312, appliquer d’abord ce cumulatif1939 selon
sa procédure, puis celui de cette reprise2129. Ce dernier contient uniquement
les fichiers livrés depuis343, avec leurs versions les plus récentes.
Il ne remplace pas un projet complet ni le socle des migrations antérieures.

## Installation sur une copie de recette

1. Préparer une installation et une base isolées avec leurs propres
   identifiants. Conserver la configuration de l’installation et ses pièces.
   Une société fictive créée dans une base réelle ne rend pas cette base
   isolée. Ne pas réinitialiser la base, rejouer des réparations historiques
   ou effacer les écritures pour simplifier un contrôle.
2. Comparer les fichiers locaux avant remplacement. Faire arrêter puis
   relancer uniquement les services de cette copie, selon la procédure
   d’exploitation habituelle. Le développement de cette session n’a arrêté
   aucun backend ou Vite lancé par l’utilisateur.
3. Extraire le cumulatif final de cette reprise,
   `HisabPro_Session_20261010_2129_Cumulatif_Verifie.zip`, à la racine
   du projet : les répertoires `hisabpro-backend`, `src`, `public`, `Test`
   et `docs` gardent leur arborescence. Préserver les fichiers locaux sans
   correspondance et les configurations. Aucun `.env`, environnement
   virtuel, cache, dump ou dossier `node_modules` n’est livré.
4. Vérifier que `public/vendor/inter` et `public/vendor/tabler` sont présents,
   notamment les fontes WOFF2, CSS, licences et le manifeste d’empreintes.
   Ces fichiers doivent être servis avec le frontend. Vite les copie dans
   son répertoire de build ; ne pas déployer uniquement le bundle JavaScript
   en oubliant `vendor`. L’application ne télécharge plus ces fontes au
   démarrage.
5. Les corrections343/344 n’ajoutent aucune migration SQL. Les lots
   précédents313/318/324/326/330,332–335 et341 n’en ajoutaient pas non plus.
   Ne pas ajouter une contrainte improvisée ou modifier des données
   historiques pour les activer. Les prérequis de migrations du socle
   restent applicables. La capture RAS083 est une activation séparée,
   décrite dans [sa procédure](MISE_A_JOUR_RAS_20261009.md).
6. Construire le frontend de recette avec `npm run build`, puis le servir
   selon l’installation. Relancer son backend avec sa configuration de
   recette. Se reconnecter si les appels retournent401 ; un OPTIONS200
   seul ne valide pas l’authentification.
7. Suivre le [mode d’emploi Word](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx)
   ou son [PDF](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.pdf), puis les
   [cas annuels PDF](recette/CAHIER_RECETTE_HISABPRO.pdf) et le
   [suivi Excel](recette/CAHIER_RECETTE_HISABPRO.xlsx). Renseigner les
   résultats réels, anomalies et captures ; les statuts initiaux ne sont
   pas préremplis par les réussites automatisées.

## Contrôles utiles pour cette reprise

- Charger les écrans et ouvrir le cycle commercial en bureau/mobile :
  icônes visibles, boutons Achat/Vente accessibles avec leurs noms lisibles.
  Les fontes sont locales ; le backend reste nécessaire.
- Article : choisir une famille historique à TVA inconnue si la fixture
  en possède une. La TVA proposée devient vide ; enregistrer sans choix
  est refusé. Choisir explicitement20% pour le laboratoire, puis vérifier
  que la famille est restée inconnue. La création rapide depuis une facture
  offre un choix explicite dans ce seul cas. Aucun taux fiscal réel n’est
  déduit de cet exemple.
- Réception fournisseur : convertir un BR en facture brouillon, retrouver
  la confirmation dans la page et son numéro de brouillon, puis ouvrir
  Factures. Renseigner le numéro fournisseur et contrôler la pièce avant
  validation. Une conversion ne crée pas une seconde réception de stock
  ni une écriture comptable définitive.
- Inventaire : suivre l’[annexe dédiée](recette/ANNEXE_RECETTE_INVENTAIRE_20261010.pdf)
  et son [Excel](recette/ANNEXE_RECETTE_INVENTAIRE_20261010.xlsx).
  Une valeur inconnue doit rester « À vérifier » ; un zéro connu demeure
  zéro. Comptabilisation/clôture/archivage refusés si les sources nécessaires
  restent indéterminées. Ne pas corriger les écritures validées pour lever
  ces contrôles.
- Calendrier : respecter les dates de l’exercice et les périodes fermées.
  Une date sans période dans un calendrier partiel est refusée. Le correctif
  des exercices implicites ne déverrouille pas les périodes existantes.
- Stock, onglet **Mouvements** de l’inventaire : vérifier le stock, le CMUP
  et la valeur de l’article, appliquer le filtre et utiliser **Recontrôler**.
  Une source inconnue affiche « À vérifier » avec son diagnostic ; elle ne
  devient pas un zéro. Le diagnostic d’un mouvement historique ne signifie
  pas nécessairement que la valorisation actuelle est inconnue : lire les
  deux contrôles. Suivre le chapitre12 du guide actualisé, version5.
- Archivage ou passage d’un article stockable en service : un stock inconnu
  est refusé, sans modifier la fiche. Un stock réellement nul reste distinct.
  Une correction physique ou une annulation qui nécessite un stock/CMUP/coût
  inconnu est refusée avant de changer les mouvements. Pour une annulation
  portant sur plusieurs articles, les origines sont qualifiées ensemble.
  Les demandes déjà exécutées gardent leur reprise idempotente ; les périodes
  fermées restent verrouillées. Ne pas renseigner un coût supposé pour forcer
  l’opération : réunir les justificatifs et traiter l’anomalie séparément.

Les scénarios historiques inconnus/non finis ont été préparés exclusivement
dans les bancs isolés des tests. Leur absence dans votre copie de recette
n’autorise pas leur injection dans une base réelle. Les projections de
l’API d’alertes et de l’historique brut contiennent des diagnostics ; elles
n’ajoutent pas un nouvel écran d’alertes dans la page Articles.

Pour la recette d’achat du chapitre08, enregistrer le déclencheur de stock
« À la réception » dans Paramètres → Fiche société → Gestion du stock et
saisir les dates2025 données dans le guide. Le correctif341 transforme le
défaut de coût nécessaire au BR en refus409 explicite, avec rollback de toutes
ses lignes ; les priorités de coût et les formules CMUP restent conservées.

La conversion BL/BR343 refuse un prix nécessaire absent/non fini ou un total
non représentable avant création durable du brouillon et de son lien au bon.
Les prix connus0, les priorités existantes et la sélection partielle sont
conservés. La validation normale/proforma344 refuse les sources monétaires
non finies avant numéro définitif, snapshots et mouvements ; elle conserve
les formules existantes. Ces contrôles ne réparent pas les pièces historiques.

## Ce qui reste séparé

Aucune commande de cette session n’a utilisé PostgreSQL réel ni modifié
des données comptables réelles. Les preuves automatiques reposent sur des
clusters éphémères vérifiés ; elles ne valident pas le schéma/migrations de
l’installation utilisateur. Une application ultérieure à cette installation
doit conserver sa sauvegarde et son contrôle de version habituels, décrits
dans [l’exploitation](EXPLOITATION_HISABPRO.md).

Les suites générales échouées restent consignées dans les rapports : les
retests sont des preuves distinctes. Le [rapport325](../Test/rapport_non_regression_reprise_20261010_1434.md)
indique le résultat de sa version avant332–335. Le [rapport336](../Test/rapport_non_regression_reprise_20261010_1939.md)
conserve séparément la consolidation suivante et son état effectif. Ses3009
réussites précèdent les correctifs341/343/344, qui possèdent leurs propres
tests ciblés et connexes. Les69tests343 et91tests344 ont réussi ; les suites
superposées ne sont pas additionnées. La consolidation346 est suivie
séparément dans le journal. Les recettes humaines, qualifications
fiscales, couverture sociale complète, schéma EDI applicable et production
restent à valider selon les limites de la
[matrice](audit/MATRICE_COUVERTURE_HISABPRO.md).
