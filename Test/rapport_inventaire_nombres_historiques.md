# Inventaire, clôture et livre — nombres historiques — lot313

## Résultat et périmètre

Un stock ou coût absent, non fini ou invalide reste inconnu : les lectures
retournent `null` et des diagnostics, jamais un zéro de substitution. Les
totaux incomplets sont signalés dans l'inventaire, la clôture, le livre,
le CSV et le PDF. Les données historiques ne sont pas réparées.

La simulation et la validation précontrôlent les sources avant photographie,
mouvement ou écriture, même si la quantité comptée égale la quantité théorique.
La précision des colonnes PostgreSQL et les agrégats sont contrôlés avant
écriture. Une source inconnue refuse aussi génération, clôture et archivage ;
un brouillon existant n'est pas supprimé avant ce contrôle.

Le calcul de lecture partagé utilise Decimal et les arrondis du moteur stock.
Les quantités finies signées historiques restent lisibles. Un CMUP zéro connu
reste zéro ; le recours métier existant au prix d'achat lors du comptage est
préservé, y compris lorsque ce prix vaut réellement zéro. Une photographie
historique conserve ses valeurs stockées. Les règles d'arrondi de l'aperçu
courant ne permettent pas de revendiquer l'identité avec des anciens calculs
sur quantités dépassant quatre décimales.

## Tests réellement exécutés

Principal, sur la source finale : **148 réussites, 25 avertissements,
60,73 s, code0**. Treize modules : nouveau livre/PDF, nouveau backend
historique, calcul frontend, comptage et dix ensembles connexes stock/clôture.
Preuve locale : `.codex-tests/inventaire_313_integre.xml`.

Agent navigateur : **4 réussites, 25 avertissements, 46,66 s, code0**.
Edge bureau1365 et mobile390 connecté à FastAPI et PostgreSQL nonce.
Preuve : `.codex-tests/inventaire_313_e2e_livre_retest.xml`.

Le scénario positif calcule indépendamment 10×20=200, comptage8 →160,
perte40, une correction stock, deux lignes de photographie dont un article
zéro connu. Génération3111 débit160 /6114 crédit160, validation réelle du
journal puis rapprochement à160 et écart0.

Le scénario négatif conserve un capital fictif validé1000 ; stock NULL,
NaN/Inf, coût négatif et dépassement sont visibles, comptabilisation/clôture
refusées, lecteur403 et autre société404. PDF200 ouvert avec pypdf et texte
« À vérifier », archivage409, empreintes/contenus des archives inchangés.

Principal : compilation des trois fichiers livre/PDF/test, code0 ;
build139modules, 4,93 s, code0. Avertissements Vite xlsx/chunk préexistants.
Agent : compilation des cinq fichiers backend, code0. Résultats backend109
et frontend22 ciblés recouvrent la suite148 : ils ne sont pas additionnés.

## Échecs intermédiaires conservés

- Baseline principal avant correction :32 réussites,1,57 s.
- Backend : erreur de nom de table,1échec22,04 s ; reproduction réelle
  stockNULL exposé comme zéro,1échec21,17 s ; après correction,40réussites
  et1échec23,31 s pour oracle supposant mouvement signé. Le mouvement est
  positif et la perte40 est distincte ; oracle rectifié. Extension :17réussites
  et1échec22,79 s car ORM remplaçait NULL par défaut0 ; fixture SQL explicite.
  Dernier run backend :109réussites28,67 s.
- Livre/PDF principal :1échec/6réussites/7erreurs3,18 s, fixture SQLite
  incompatible INTERVAL/EXTRACT et regex « nan » correspondant à « financier ».
  Passage au vrai PostgreSQL nonce et contrôle de jetons numériques.
  Puis13réussites/1échec27,60 s : CMUP photographie NOT NULL, fixture remplacée
  par NaN réellement stockable sans changer le schéma.23réussites30,46 s,
  puis suite finale148 après extension aux grands montants finis.
- Frontend :21réussites/1échec3,06 s, tableau vide assimilé à une case vide ;
  type contrôlé,22réussites1,75 s après correction.
- Edge :4échecs71,87 s, clôture2026 future et clic avant chargement ; prérequis
  exercice2025 et attente du vrai bouton.2réussites/2échecs31,80 s, exercice2025
  absent avant capital ; création explicite.4réussites44,49 s. ExtensionPDF :
  2réussites/2échecs34,45 s, regex prenait les références fixtures NAN-/INF-
  pour des nombres ; contrôle des cellules. Final4réussites46,66 s.

## Limites et suite

Tous les accès SQL utilisent des clusters éphémères nonce vérifiés. Dotenv
désactivé ; aucune base PostgreSQL utilisateur, migration ou donnée réelle
modifiée. Aucun archivage historique réécrit. SQLite n'est pas une preuve
PostgreSQL. Les sources booléennes de quantité API sont refusées422 avant
mutation ; inconnues métier : simulation400, validation409.

Le 500 observé dans une fixture qui tentait le capital2025 sans exercice
explicite reste un résultat de prérequis manquant, sans diagnostic de cause
ni revendication de correction applicative. L'E2E final crée l'exercice.

Recette utilisateur annuelle complète et déploiement réel restent à effectuer.
La non-régression globale311 échouée demeure une preuve historique distincte ;
une nouvelle globale sur sources figées doit tester ce lot. Familles et autres
consommateurs de données article restent à contrôler indépendamment.
