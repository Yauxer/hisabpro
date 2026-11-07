# Chargement des polices et icônes locales — lot320

## Problème reproduit, sans extrapolation

index.html chargeait Inter et Tabler depuis Google Fonts et jsDelivr. Un
nouveau testEdge suspend ces trois domaines dans le navigateur, sans envoyer
de requête Internet, puis conserve page.goto(wait_until='load',timeout=5000).
Avant correction, les deux viewports1365/390 expirent exactement sur cette
navigation. Cette reproduction démontre la dépendance au CDN pour ce test ;
elle ne prouve pas rétroactivement la cause des délais mobiles311/315.

## Correction livrée

- Inter400/500/600, sept sous-ensembles WOFF2 : servis sous public/vendor/inter.
- Tabler Icons2.47.0 : version effectivement servie par l’ancien lien à cette
  préparation, conservée avec ses règles de glyphes identiques hors font-face.
  Seul le chemin de source est adapté au WOFF2 local ; aucune montée de
  version d’icônes ni changement de package.json/package-lock.
- index.html pointe vers les deux CSS locaux et retire le preconnectGoogle.
- Licences InterOFL et TablerMIT, README de provenance et MANIFEST des
  douze fichiers avecURL, taille etSHA256 inclus. Quatorze fichiersvendor au
  total ; aucun secret ni donnée comptable.
- Le helper E2E copie public vers son répertoire web, comme Vite le fait
  pour la distribution. Les fontes ne passent pas par son bundle esbuild.
  Aucune réponse simulée ne remplace les polices dans la recette.

Les téléchargements ont été préparés uniquement en cache pendant le gel315.
Une première tentative ciblait le nouveau packageTabler3.49 au chemin ancien
et obtenait404 ; le cache final a été refait en2.47.0 pour conserver la version
utilisée par l’application. L’ancien lien @latest répondait200 : il n’est pas
présenté comme un lien cassé. Voir public/vendor/README.md et MANIFEST.json.

## Commandes et résultats réellement exécutés

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_chargement_sans_cdn_isole.py -vv --tb=short --junitxml=.codex-tests/cdn320_local_harness_1434.xml
npm run build
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile Test/test_e2e_chargement_sans_cdn_isole.py Test/e2e_isole_support.py
```

Agentfrontend, étapes réellement exécutées dans cette reprise :

1. Baseline :2failed,25warnings,34,38s, code1, preuvescdn320_baseline_1434.
   Timeouts5000ms sur load avec les CDN suspendus. Exceptions asyncio de
   fermeture des routes restent dans le log, sans masquer la navigation.
2. Après assets, avant copiepublic dans le helper :2failed,24,41s, code1.
   Navigation et login réussissent mais document.fonts est vide : les URL
   vendor404 sont révélées par l’assertion de fontes réellement chargées.
   document.fonts.check seul pouvait répondre vrai via le fallback ; il
   n’est pas utilisé seul pour rendre ce test vert.
3. Après helper corrigé par le principal :2passed,25warnings,42,17s, code0 ;
   XML/log/exitcdn320_local_harness_1434. Même test, sans relâcher load5000ms,
   sans assouplir l’assertion des glyphes ni intercepter les polices locales.
4. Compilation du test/helper par agent : code0 ; compilationhelper du
   principal : code0.

Principal : buildVite139modules en6,93s, code0 ; avertissements existants
XLSX statique/dynamique et taille de chunk conservés. Contrôle indépendant :
les14fichiersvendor de dist sont byte-identiques à public, les12SHA256 sont
conformes au manifeste et index/CSS ne comportent plus de sourcefontHTTP.

## Ce que prouvent les deux parcours connectés

Edge1365/390, vraie connexionAPI et PostgreSQLnonce vérifié. Login puis pages
Articles, Inventaire et Journal avec wait_until=load5000ms. FontesInter400,
500,600 et Tabler effectivementloaded, WOFF2locaux200 et glyphelogoutU+EBA8
avec sa familleTabler vérifiés. Aucune requêteHTTPexterne, aucune erreurJS
ouAPI500, photographiearticles/mouvements/écritures inchangée.

Le chargement local des fontes ne supprime pas le besoin du backend pour
les données métier. Aucun PostgreSQL réel ni aucune migration. Après
déploiement des fichiers, vérifier visuellement les icônes et la typographie
dans le navigateur utilisateur. La globale315 échouée reste conservée et
les retests réalisés après320 constituent des preuves distinctes.
