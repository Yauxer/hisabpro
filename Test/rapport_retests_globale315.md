# Non-régression 315 — lecture et retest ciblé du 10 octobre 2026

Agent `inventaire_e2e_313`, diagnostic puis tests du correctif326 autorisés : aucune source applicative, journal partagé, document commun ou ZIP modifié par cet agent. Le présent rapport est un livrable dans Test ; les lanceurs, traces et captures techniques restent en cache. Les tests ajoutés/adaptés pour326 sont consignés séparément.

## Globale historique conservée

Sources originales : `.codex-tests/global_Inventaire_20261010_1103.{log,xml}`. Le fichier exit du wrapper n’a pas été récupéré. XML : **2796 tests, 49 failures, 5 errors, 0 skipped**, donc **2742 réussites**. Durée XML : **3409.679 s**. Les 54 cas échoués/en erreur sont conservés comme tels ; le retest ci-dessous ne transforme pas rétroactivement cette globale en réussite.

Lecture des traces :

| Groupe | Nombre | Fait observé dans la globale |
|---|---:|---|
| Import relevé, tests Node `test_session133_releve_import.py` | 40 échecs | Sous-processus `node --input-type=module -e ...` termine avec 3221225794, stdout et stderr vides, assertion du retour avant contrôle des valeurs JSON |
| Relevé import/pointage PostgreSQL | 1 échec | Même retour Node dans le helper `lire`, lors de la préparation des lignes CSV |
| Import relevé navigateur | 5 erreurs | Fixture `bundle` arrêtée sur `node -e ... esbuild` retour 3221225794, stdout/stderr vides ; les scénarios navigateur ne sont pas entrés |
| Tri commercial | 6 échecs | `sync_playwright().__enter__` → `Connection.init: Connection closed while reading from the driver`, avant création/navigation d'une page |
| Réception partielle achat, 390 px | 1 échec | `Page.goto('/factures')`, délai 20 000 ms, attente `load` |
| Clôture auxiliaires, 390 px | 1 échec | `summary.click()`, délai 5 000 ms ; élément trouvé, visible/enabled/stable, scroll réalisé puis action click non terminée |

Le retour Node est exactement **0xC0000142**. L'échec de processus/driver est observé ; la DLL précise, une éventuelle saturation ou l'influence des CDN ne sont **pas démontrées** par ces traces. `node --version` relancé ici retourne `v24.17.0`, code 0, à l'instant du diagnostic. Aucun arrêt/réparation d'un processus ou composant système utilisateur effectué.

## Retest ciblé réel de tous les 54 cas

Lanceur `.codex-tests/lancer_nonreg315_retest_1434.py` : refuse l'écrasement des preuves, impose `PYTHON_DOTENV_DISABLED=1` et `PYTHONUTF8=1`, capture stdout/stderr et écrit le code de sortie séparé.

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 .codex-tests/lancer_nonreg315_retest_1434.py
```

Commande pytest réelle appelée :

```text
python -X utf8 Test/run_unit_tests.py
 Test/test_session133_releve_import.py
 Test/test_session133_releve_postgres.py::test_api_pg_csv_fr_import_soldes_et_pointage_sont_coherents
 Test/test_session133_releve_import_navigateur.py
 Test/test_tri_creation_commercial_isole.py
 Test/test_e2e_cycle_achat_reception_partielle_isole.py::test_cycle_reception_partielle_stock_br[390]
 Test/test_session133_cloture_auxiliaires_navigateur.py::test_auxiliaires_et_soldes_opposes_restent_visibles[390]
 -vv --tb=short --junitxml=.codex-tests/nonreg315_retest_1434.xml
```

Session **99746**, réellement terminée, code **0** : **54 passed, 25 warnings, 97.75 s** (lanceur 99.05 s). XML : **54 tests, 0 failures, 0 errors, 0 skipped**, temps XML 97.738 s, début **14:36:34.395980 UTC**. Les identifiants classname/name ont été comparés à la liste exacte des 49 failures et 5 errors de la globale : **54 correspondances, aucun cas manquant ni supplémentaire**.

Preuves nouvelles : `.codex-tests/nonreg315_retest_1434.{log,xml,exit}`. Aucun timeout, scénario ou assertion métier modifié ; import/date/centimes, pointage, tri et mobile ont été rejoués tels quels.

Sécurité du banc vérifiée dans les fixtures : import PostgreSQL utilise `engine/dossier/client` de `test_session132_operations_postgres`; tri commercial et réception partielle utilisent `application_isolee` avec PostgreSQL éphémère vérifié et arrêt/cleanup des seuls processus créés. L'import navigateur du module session133 utilise une **API synthétique interceptée**, comme l'indique son docstring ; ce groupe valide la page React et ses payloads, il ne constitue pas un test API PostgreSQL connecté. Ne pas assimiler ces cinq scénarios au banc connecté des autres groupes. Aucune base réelle ni fichier `.env` utilisateur lu.

## Limite de version — indispensable

L'agent n'a édité aucune source pendant la commande ; toutefois **l'agent principal a appliqué les lots 318/320 en parallèle**. `index.html` a une date de modification **14:37:23 UTC**, située dans le retest commencé à 14:36:34 UTC. Le bloc n'était donc pas figé sur les 653 empreintes de la globale 315. Les chargements successifs peuvent avoir utilisé des versions différentes des sources/assets modifiés ; les modules d'un serveur déjà démarré ne se rechargent pas nécessairement.

**Ce résultat est un retest ciblé réussi dans le dépôt courant pendant intégration, pas une preuve de réussite globale de la version 315 figée.** Le détail des fichiers du lot 318 et des empreintes finales est à croiser avec le journal de l'agent principal. Une répétition séparée des deux mobiles après stabilisation/build du lot 320 est prévue, sans modification des timeouts.

Précisions transmises par l'agent principal : lot318 `hisabpro-backend/services/exercices_service.py` (mtime relevé 14:36:34 UTC) et nouveau `Test/test_exercice_implicite_periodes_postgres.py`; lot320 `index.html` et ressources `public/vendor`. Build de l'agent principal : 139 modules, code 0, 6.93 s (résultat rapporté par l'agent principal, non exécuté par cet agent). Après le retest54, `Test/e2e_isole_support.py` a été modifié à **14:39:34 UTC** pour copier les vrais fichiers `public` vers le répertoire de service du banc E2E, afin que les nouvelles polices locales ne produisent pas HTTP404. Cette modification du banc n'est pas contenue dans le résultat54 de 14:36–14:38.

## Deux mobiles après intégration réelle des ressources locales — échec conservé

Après confirmation par l'agent principal des deux tests de chargement des polices et du build320, commande cache `python -X utf8 .codex-tests/lancer_nonreg315_mobile_stable_1434.py` : mêmes deux identifiants mobiles et délais inchangés, aucune modification de test/applicatif par cet agent.

Session **53590**, code **1** : **1 failed, 1 passed, 25 warnings, 42.25 s** (lanceur 43.59 s). Les **668 empreintes avant/après sont identiques** : les 653 chemins de la globale originale, le nouveau test318 et les ressources `public/vendor` supplémentaires. Preuves `.codex-tests/nonreg315_mobile_stable_1434.{log,xml,exit,hashes.json}`.

- Clôture auxiliaires mobile : réussi.
- Réception partielle mobile : échec **différent** de la globale315, au clic `get_by_role('button', name='Achat', exact=True)` ligne56, délai20s. Corps de page capturé contenant le texte Achat, erreurs JavaScript/API vides. Ne pas affirmer que la seule suppression des CDN a résolu l'instabilité historique de315.

## Rejeu unique du mobile en échec

Commande cache `python -X utf8 .codex-tests/lancer_nonreg315_reception_retest_1434.py`, cible réception partielle390 seulement, mêmes assertions et délais.

Session **23427**, code **1** : **1 failed, 25 warnings, 39.47 s** (XML39.463s, lanceur40.84s), début **14:44:10.027064 UTC**. **668 empreintes avant/après identiques**. Preuves nouvelles `.codex-tests/nonreg315_reception_retest_1434.{log,xml,exit,hashes.json}`. Même échec Achat exact20s, donc le problème de cette version est reproductible.

## Diagnostic du nouveau problème — cause démontrée

Un plugin de cache `.codex-tests/diagnostic_roles315.py` observe les erreurs de clic, enregistre DOM, noms accessibles, styles des pseudo-éléments, capture d'écran et trace Playwright. Il appelle l'action originale avec ses arguments et délais et **relève l'exception originale**, sans changer les assertions, cliquer un autre élément ou remplacer l'API.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
$env:PYTHONPATH='.codex-tests'
python -X utf8 Test/run_unit_tests.py Test/test_e2e_cycle_achat_reception_partielle_isole.py::test_cycle_reception_partielle_stock_br[390] -p diagnostic_roles315 -vv --tb=short --junitxml=.codex-tests/nonreg315_role_diagnostic_1434.xml
```

Session **49450**, code **1** : **1 failed, 25 warnings, 41.66 s**, même erreur et délais. Preuves cache `.codex-tests/nonreg315_role_diagnostic_1434.{log,xml,json,png,trace.zip}` (ces artefacts techniques sont exclus du ZIP différentiel, sauf choix explicite du principal).

Le JSON capturé démontre :

- DOM : bouton `innerText='Achat'`, sans `aria-label`, contenant `<i class="ti ti-arrow-down-left"></i>`.
- Style de cet élément décoratif : `::before` contient **U+EA13**, police `tabler-icons`, `document.fonts.status='loaded'`.
- Arbre accessible : nom du bouton **U+EA13 + espace + Achat**, et non Achat. Vente, les onglets commerciaux et plusieurs autres boutons incluent également des glyphes décoratifs dans leurs noms accessibles.

**Cause de ce nouvel échec après320 : les icônes CSS désormais chargées participent aux noms accessibles des boutons.** Le sélecteur exact Achat a raison de ne pas correspondre au nom pollué. Corriger le caractère décoratif des icônes dans l'application, puis rejouer les mêmes tests ; ne pas élargir les sélecteurs ou augmenter les délais pour dissimuler ce problème.

Cette preuve n'explique pas rétroactivement les 52 échecs de processus/driver ou les deux anciens délais de la globale315, puisque celle-ci utilisait des ressources et versions différentes. Ces incidents historiques restent conservés, avec cause profonde non établie.

## État au point de remise à l'agent principal

Les54cas sont passés dans le premier retest pendant intégration. Après la copie réelle des ressources locales dans le banc E2E, une régression d'accessibilité reproductible est identifiée et transmise au principal ; **aucune réussite de la version finale post320 n'est annoncée** tant que le correctif et le retest n'ont pas été réellement exécutés. Aucun correctif applicatif réalisé par cet agent, aucun PostgreSQL réel appelé. L'agent principal complète les preuves après correction et assure journal/ZIP.

## Essai de correction en mémoire — résultat réel, pas encore un patch applicatif

À la demande du principal, `.codex-tests/test_diagnostic_icones_alt315.py` ouvre la vraie application/API/PostgreSQL nonce en Edge1365 et390. L'essai modifie seulement les règles CSS en mémoire du navigateur : chaque contenu `.ti-*:before` conserve son glyphe et reçoit l'alternative textuelle vide `content: "glyph" / ""`.

Commande `python -X utf8 Test/run_unit_tests.py .codex-tests/test_diagnostic_icones_alt315.py -vv --tb=short --junitxml=.codex-tests/icones_alt315_initial.xml` avec dotenv désactivé, session **66294**, code **0** : **2 passed, 25 warnings, 22.27 s**.

Résultats desktop/mobile : **4962 règles** modifiées en mémoire ; noms accessibles exacts Achat, Vente, Bons de commande et Nouveau devis retrouvés ; clics réels Achat puis Vente réussis. Pour les deux icônes testées, code du glyphe conservé, police `tabler-icons` chargée, visibilité et dimensions identiques **13 ×13 px** avant/après. Les noms accessibles des boutons Exercice conservent leurs titres descriptifs au lieu d'un glyphe seul.

Preuves JSON avant/après et arbre accessible : `.codex-tests/icones_alternative_{1365,390}_315.json`, captures PNG correspondantes, XML/log `icones_alt315_initial.*`. Aucune source applicative n'est modifiée par cet essai ; **le correctif du fichier CSS livré et son test sans injection restent à réaliser par coordination avec le principal**. Solution minimale proposée : ajouter l'alternative textuelle vide aux4962 déclarations de contenu du CSS Tabler local, documenter la dérivation et actualiser les empreintes du manifeste, puis rejouer les sélecteurs exacts originaux.

## Correctif326 réellement intégré et contrôlé

Après la proposition ci-dessus, l'agent principal a modifié le CSS livré et ses métadonnées (voir `rapport_icones_accessibles.md`). Deux tests persistants Edge1365/390 sans injection CSS : **2 passed, 25 warnings, 23.00 s**. Test historique de chargement et ces deux nouveaux tests ensemble : **4 passed, 25 warnings, 48.62 s** après adaptation stricte de l'oracle du contenu de l'icône (glyphe inchangé et alternative textuelle vide), navigation `load` en5secondes et absence de requêtes CDN conservées. La régression du nom accessible Achat est donc corrigée dans les fichiers réellement servis.

## Les54 anciens cas après326 — résultat partiel exact

Commande cache `python -X utf8 .codex-tests/lancer_nonreg315_54_post326_1434.py`, mêmes54identifiants, mêmes assertions et délais, dotenv désactivé.

Session **71525**, code **1** : **53 passed, 1 failed, 25 warnings, 101.73 s** (lanceur103.00s). **670 empreintes avant/après identiques**, suivies sur les653chemins originaux, les tests318/320/326 et les ressources `public/vendor` supplémentaires. Preuves `.codex-tests/nonreg315_54_post326_1434.{log,xml,exit,hashes.json}`. Le suivi670 ne remplace pas le gel global674effectué séparément par le principal ; ne pas additionner ou confondre ces périmètres.

Les52anciens cas Node/driver et la clôture auxiliaire mobile réussissent. Le seul échec restant est la réception partielle mobile à la navigation `/factures` ligne93, attente `load` de20secondes : **le clic exact Achat passe désormais**. Le journal comporte également `Dialog.accept: Protocol error (Page.handleJavaScriptDialog): Not attached to an active page`, dans le gestionnaire de dialogue du scénario. Cette trace suggère un problème de synchronisation dialogue/navigation ; sa cause précise et le type du dialogue ne sont pas encore prouvés à ce point. Elle interdit d'attribuer automatiquement le délai aux anciens CDN.

Un diagnostic complémentaire est lancé par plugin de cache pour horodater les types/messages des dialogues, requêtes/réponses et événements de navigation sans modifier les actions ni leurs délais. Les sources applicatives et testsPY sont gelés par le principal à14:57; aucune éditionPY n'est faite par cet agent après ce gel. Le résultat et une éventuelle correction seront consignés séparément ; la commande54reste **échouée**, aucune globale complète n'est déclarée verte.

## Observation horodatée de l'alerte tardive de conversion

Le plugin de cache `.codex-tests/diagnostic_navigation315.py` appelle les actions originales avec leurs arguments, enregistre des événements et laisse le gestionnaire d'acceptation du scénario agir. Il ne remplace aucun clic, aucune navigation, aucune assertion et aucun délai. La journalisation et la trace peuvent néanmoins influencer le timing ; un succès instrumenté ne suffit pas à démontrer une correction.

Commande de la cible réception partielle390 avec `-p diagnostic_navigation315`, XML `.codex-tests/nonreg315_navigation_diagnostic_1434.xml` : session **76997**, code **0**, **1 passed, 25 warnings, 30.58 s**. Aucun correctif applicatif réalisé avant cette observation.

Le JSON des237événements démontre, lors de la seconde réception :

| Temps relatif (s) | Événement réel |
|---:|---|
|20.750|Début de `page.goto('/factures')`, depuis `/commercial`|
|20.766|Événement `beforeunload` du document commercial|
|20.782|Dialogue de type **alert**, sur l'ancien document commercial : « Brouillon de facture fournisseur #2 créé depuis BR-2026-002. Renseignez son numéro fournisseur dans Factures avant validation. »|
|20.954|Fin de navigation vers `/factures`|

Il existe donc réellement une alerte de succès de conversion **après que la navigation a commencé**. Le dialogue identifié est une alerte de succès, pas une confirmation `beforeunload`. L'incident antérieur `Dialog.accept ... Not attached to an active page` est cohérent avec ce chevauchement ; ce rejeu instrumenté n'a toutefois pas reproduit l'erreur et ne constitue pas, à lui seul, la preuve complète de toutes les causes des anciens délais.

Prochaine correction à coordonner avec le principal : rendre le feedback de cette conversion non bloquant et correctement synchronisé, ou attendre une fin explicite de flux dans la recette si c'est le contrat retenu. Conserver les messages d'aide, les contrôles métier et les assertions ; ne pas masquer la course par un sleep ou un délai augmenté. Les preuves53réussites/1échec restent historiques et inchangées. Les événements complets sont conservés dans `.codex-tests/nonreg315_navigation_diagnostic_1434.json`.
