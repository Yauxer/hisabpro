# Lot341 — refus contrôlé des coûts historiques inconnus au bon de réception

## Problème reproduit

Après le durcissement du moteur de stock335, le calcul du coût achat dans
`_mouvement_stock_bon_livre` restait avant le `try` interceptant les
`ValueError`. Pour un BR avec déclencheur de stock à la réception, quantité
positive et prix de ligne zéro, une source historique nécessaire absente ou
non finie produisait une réponse HTTP500.

La baseline réellement exécutée reproduit neuf réponses HTTP500 : quatre prix
d'achat NULL/NaN/+Inf/-Inf, quatre CMUP NULL/NaN/+Inf/-Inf avec prix d'achat
zéro, et un BR comportant une première ligne saine puis une seconde inconnue.
Les quatre témoins passent déjà : coût normal de20, coût connu de0, prix BR
explicite de32 avec prix d'achat historique NULL, autre société HTTP404.

Les journaux authentiques de l'API nonce sont conservés dans
`.codex-tests/br_cout_341_api_*.log`, notamment
`br_cout_341_api_94f56fd2.log`. Ils montrent l'appel
`commercial.py:1464` → `cout_entree_par_defaut` → `nombre_source_stock`, avec
`ValueError: La valeur historique prix_achat_ht est absente ...`.

## Correction minimale

Seules trois lignes de calcul sont déplacées dans le `try` déjà présent dans
`hisabpro-backend/routers/commercial.py` : `cout=None` et la sélection du coût
achat. Le `except ValueError` existant assure désormais aussi le rollback et
la réponse HTTP409 de ce calcul.

L'expression `prix_bc.get(...) or l.prix_unitaire or cout_entree_par_defaut(...)`
est strictement conservée. Aucune modification des priorités BC/BR/défaut,
des prix zéro, des formules CMUP, des dates ou des règles comptables. Aucune
migration ni réparation de données historiques.

## Tests réellement exécutés

Chaque API utilise les fixtures existantes d'application et d'inscription,
avec PostgreSQL éphémère identifié par nonce. La cible est vérifiée avant
toute manipulation SQL. `PYTHON_DOTENV_DISABLED=1` ; aucun fichier `.env`
ni PostgreSQL utilisateur utilisé. Les anomalies ne sont introduites que
dans des articles fictifs du cluster isolé, après création valide par API.

Les transitions réellement suivies sont `en_preparation` → `expedie` →
`livre`. Les refus HTTP409 photographient sociétés, articles/familles, BR/lignes
(statuts et snapshots inclus), mouvements, écritures/lignes comptables,
inventaires et lignes d'inventaire. Le cas à deux lignes prouve le rollback
de la réception entière, y compris l'entrée saine commencée avant le refus.

Baseline, avant modification du backend :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_br_cout_historique_postgres.py --tb=short --junitxml=.codex-tests/br_cout_341_avant.xml
```

**9 échoués /4 réussis**, 25 warnings, 41.21s, code de sortie1. XML distinct conservé
et vérifié :13 tests, 9 échecs, 0 erreur, 0 ignoré, 41.190s.

Après correction, ciblés et connexes :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_br_cout_historique_postgres.py Test/test_mutations_stock_historique_postgres.py Test/test_stock_integrite_mouvements.py Test/test_patch069_stock_services.py Test/test_patch06c_stock_engine.py Test/test_articles_alertes_stock_historique_postgres.py Test/test_e2e_cycle_achat_reception_partielle_isole.py Test/test_e2e_cycle_commercial_isole.py --tb=short --junitxml=.codex-tests/br_cout_341_final.xml
```

**122 réussis**, 25 warnings, 227.75s, code de sortie0 ; aucun échec, erreur ou test ignoré.

| Domaine exécuté | Cas réussis |
|---|---:|
| Nouveaux refus409 et témoins BR341 | 13 |
| Mutations historiques et compensations335 | 52 |
| Intégrité des mouvements existante | 31 |
| Services non stockables069 | 8 |
| Moteur06C | 4 |
| Alertes historiques332 | 11 |
| Edge achat : réception partielle, bureau et mobile | 2 |
| Edge vente : cycle commercial et traçabilité | 1 |
| **Total** | **122** |

Les trois scénarios Edge ont réellement été exécutés. Les31 tests connexes
d'intégrité utilisent SQLite ; ils ne remplacent pas les nouveaux tests API
PostgreSQL nonce et ne prouvent pas une concurrence entre transactions PG.

Compilation réelle :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile hisabpro-backend/routers/commercial.py Test/test_br_cout_historique_postgres.py
```

Code de sortie0, 0.43s. Warnings préexistants de dépréciation multipart/Pydantic.

## Résultat et portée

Une source de coût nécessaire inconnue renvoie désormais HTTP409 avec son message
métier, en conservant toutes les données photographiées et le statut expédié.
Les témoins conservent stock10→12 : CMUP20 pour coût20, CMUP0 pour coût0,
CMUP22 pour prix BR explicite32. L'accès d'une autre société reste HTTP404.

La globale336 a été terminée par l'agent principal **avant** cette correction341,
sur les sources alors figées. Son résultat antérieur ne valide pas ce nouveau
déplacement de code ni les13 nouveaux cas. La preuve de la version341 est la
commande ciblée et connexe ci-dessus, avec son XML final distinct ; aucune
nouvelle globale de l'ensemble du backend n'est revendiquée dans ce lot.

Pas de manipulation des données réelles. Le refus de coût inconnu a été testé
par API ; une revue utilisateur du message dans l'interface BR reste distincte
des scénarios Edge positifs exécutés. Aucune recette utilisateur ou conformité
réglementaire n'est déclarée validée automatiquement.
