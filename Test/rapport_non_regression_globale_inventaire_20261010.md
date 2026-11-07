# Non-régression complète après inventaire313 — 10 octobre2026 — lot315

## Commande et gel

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test -vv --tb=short --junitxml=.codex-tests/global_Inventaire_20261010_1103.xml
```

Nouvelle commande du principal, session51725. Log, XML, code de sortie et
empreintes portent un nouveau préfixe1103 ; les preuves300/311 ne sont pas
écrasées. 2796cas collectés et653sources figées (application, tests, SQL,
configurations). Aucun de ces fichiers modifié pendant la commande.

Les documents et livraisons313/314/317 ont avancé indépendamment. L'annexe317
est générée sans connexion DB dans docs/recette ; elle ne modifie pas le
périmètre applicatif/test figé. Les éventuels travaux futurs sur exercices ou
familles restent des analyses/cache jusqu'à achèvement et contrôle du gel.

## Résultat

**Échec :2742réussites,49échecs,5erreurs de préparation,0ignoré.**
2796cas au total. Journal pytest :3410,26s (56min50s),32avertissements.
XML final :3409,679s. Les fichierslog/XML complets ont été récupérés et lus
par le principal à14:34UTC, après les échanges bilan et guide utilisateur323.
La session51725 du wrapper est désormais introuvable et son fichier.exit
est absent : son code retour n’est pas inventé à partir du résumé pytest.
La commande pytest a bien écrit sa synthèse et son XML final ; elle n’est
pas déclarée réussie. Les653empreintes sont toujours identiques lors de la
vérification finale14:34UTC, avant ajout des tests318/320.

## Répartition des54cas non réussis

| Module | Résultat | Trace constatée |
|---|---|---|
| Achat/réception partielle connecté | 1échec mobile390 | Ligne93 :navigation /factures attend load, timeout20000ms ; cause non établie |
| Clôture auxiliaires, support navigateur | 1échec mobile390 | Clic summary visible/stable, timeout5000ms au moment de l’action ; cause non établie |
| Import relevés, moteurJS | 40échecs | Sous-processus Node se termine3221225794 (0xC0000142), stdout/stderr vides ; assertions métier suivantes non atteintes |
| Import relevés, API/PGnonce | 1échec | Même arrêtNode lors de la préparation des lignes CSV, avant l’appel métier concerné |
| Import relevés, support navigateur | 5erreurs de préparation | Compilation esbuild par Node se termine avec le même code3221225794 ; composant de test non préparé |
| Tri commercial,6types de documents | 6échecs | Playwright Connection.init :Connection closed while reading from the driver, avant manipulation du navigateur |

La trace prouve un échec de lancement/driver pour les52cas concernés ; elle
ne prouve pas une régression du parseur bancaire ni du tri. La cause du code
Windows reste à qualifier et une relance réussie ne la démontrera pas à elle
seule. Node --version et npm --version répondent à la reprise14:34UTC
(v24.17.0 /11.13.0). Aucune modification de Node, système, assertions ou
données réelles n’est effectuée pour contourner les résultats.

Les4nouveaux parcours inventaire313 passent dans cette commande. Les49
échecs et5erreurs ne sont pas supprimés de la preuve, ni remplacés par
les résultats ciblés d’une relance ultérieure. Le dernier test PostgreSQL
non isolé reste exclu volontairement par le runner.

## Suite de reprise

Reproduire calendrier implicite318 et chargement CDN suspendu320 sur leurs
fixtures propres, puis retester les modules en échec. Une éventuelle
correction de chargement ne sera pas attribuée rétroactivement aux délais
315 sans preuve spécifique. Les tests futurs et leurs nouvelles empreintes
constituent une nouvelle version, distincte de ce gel653sources.

## Périmètre et limites

Dotenv désactivé. Les tests PostgreSQL utilisent exclusivement leurs clusters
éphémères nonce contrôlés ; le banc historique non isolé de séquences est
exclu par le runner. Aucun PostgreSQL réel consulté ou modifié. Les tests
unitaires purs, supports simulés et API/navigateurs réels sont distincts.
SQLite n'est pas présenté comme une validation PostgreSQL.

Les148tests ciblés313,4Edge et anciens runs qui se recouvrent ne sont pas
additionnés à cette commande. La globale311 échouée demeure une preuve
historique (2734réussites/4échecs). Les délais navigateur LIM20 restent sous
surveillance ; un run réussi ne démontre pas leur cause.

Ce rapport ne valide pas automatiquement une recette humaine, un déploiement,
une base réelle ou la conformité réglementaire.
