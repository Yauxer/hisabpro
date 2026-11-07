# Lot335 — mutations de stock et sources historiques inconnues

## Analyse et reproductions réelles

Tests exécutés avec l'application FastAPI réelle et un cluster PostgreSQL
éphémère identifié par nonce, créé puis arrêté et supprimé par les fixtures.
`PYTHON_DOTENV_DISABLED=1` ; aucun fichier `.env` ni PostgreSQL utilisateur.
Les données historiques anormales sont introduites uniquement par SQL dans ce
cluster isolé, après création d'articles fictifs par inscription/API.

Avant correction, `D(None)` transformait une source absente en zéro : DELETE
renvoyait204 et PATCH archivage/conversion200 sur un stockNULL. Pour NaN/Inf,
ces routes produisaient500 par `ValueError` non interceptée. Les journaux
authentiques de l'API sont conservés dans
`.codex-tests/mutations_335_api_*.log` ; ils identifient les appels à
`D(article.stock_actuel)` dans `routers/articles.py`.

Le moteur acceptait également le CMUPNULL/négatif, et une correction de cible
identique passait avant validation du CMUP. Les coûts par défaut utilisaient
`or`, confondant une valeur absente avec un zéro connu.

Une seconde reproduction concernait les compensations : coûtunitaireNULL,
CMUPaprèsNULL ou quantitéNaN de l'original étaient acceptés ; stockavant/après
Inf ou CMUPavantNaN provoquaient un refus après l'insertion d'une compensation
saine dans la même transaction. Le test relève le nombre de mouvements dans
la session avant rollback, afin de détecter cette mutation partielle.

## Correction minimale

- `nombre_source_stock` qualifie les sources nécessaires : absence, booléen ou
  non-fini refusés ; coût négatif refusé ; quantités finies signées conservées.
  `D` reste inchangé, notamment pour les remises facultatives.
- Entrée/sortie/correction qualifient stock et CMUP après relecture verrouillée,
  avant calculs et avant le retour sur delta nul. Les reprises idempotentes
  déjà enregistrées conservent leur comportement.
- Les coûts par défaut conservent leur priorité : prix d'achat pour entrée,
  CMUP pour sortie, puis repli uniquement sur zéro connu. Une source inutilisée
  n'est pas exigée. Un coût explicite garde sa priorité ; il ne répare pas un
  stock ou un CMUP historique inconnu.
- Archivage, DELETE et conversion en service refusent409 si le stock courant
  est inconnu, avant modification. La cible omise d'une correction conserve
  la source brute au lieu de lui inventer zéro. Un PATCH de description seule
  reste autorisé avec conservation des sources inconnues.
- Les compensations qualifient toutes les fiches courantes et les sources des
  originaux avant la première mutation. La restitution du CMUP est précalculée
  avec la formule existante. Le CMUPavantNULL legacy reste dérivable lorsque
  ses sources sont connues ; aucun original n'est réparé.

Aucune migration, modification d'UI, règle fiscale ou réparation historique.

## Commandes et résultats

Préfixe PowerShell utilisé pour chaque commande pytest :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py ...
```

1. Première tentative de baseline :39échecs,57.04s, code1. **Invalide comme
   preuve métier** : la fixture lisait `societe_id` dans ArticleOut, qui ne
   l'expose pas. Correction de la fixture par lecture SQL nonce.
2. Baseline métier, avant modification du backend :
   `Test/test_mutations_stock_historique_postgres.py --tb=short --junitxml=.codex-tests/mutations_335_avant.xml`
   → **30échoués /9réussis**,25warnings,55.12s, code1.
3. Premier ciblé après correction : nouveau module +
   `test_stock_integrite_mouvements.py`, `test_patch069_stock_services.py`,
   `test_patch06c_stock_engine.py`, XML `mutations_335_apres.xml`
   → **82réussis**,25warnings,57.30s, code0.
4. Vérification étendue intermédiaire : **96réussis /1échoué**,25warnings,
   90.23s, code1. L'échec provenait du SQL de test : la société d'une période
   passe par `exercice_id`. Fixture corrigée, sans changement métier.
5. Vérification intermédiaire corrigée : **99réussis**,25warnings,93.40s,
   code0. Le véritable XML99 a été copié avant le dernier run vers
   `.codex-tests/mutations_335_intermediaire_99.xml`.
6. Baseline complémentaire avant garde des originaux :
   `Test/test_mutations_stock_historique_postgres.py -k 'origine_compensation or legacy_absent' --tb=short --junitxml=.codex-tests/mutations_335_origine_avant.xml`
   → **6échoués /1réussi /45désélectionnés**,25warnings,28.56s, code1.
7. Finale après garde complète :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_mutations_stock_historique_postgres.py Test/test_stock_integrite_mouvements.py Test/test_patch069_stock_services.py Test/test_patch06c_stock_engine.py Test/test_articles_alertes_stock_historique_postgres.py --tb=short --junitxml=.codex-tests/mutations_335_final.xml
```

   → **106réussis**,25warnings,98.28s, code0 :52nouveaux tests,31intégrité
   mouvements existants,8patch069,4patch06C,11alertes332. L'XML final a été
   déplacé après achèvement vers
   `.codex-tests/mutations_335_final_origines.xml` :106tests,0échec,0erreur.

Les XML intermédiaires97/99 ont réutilisé `mutations_335_final.xml` ; l'XML97
n'est pas conservé. Ses résultats ci-dessus proviennent de la sortie réelle
de commande, sans reconstruction d'un XML manquant.

Compilation réelle des trois fichiers Python modifiés :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile hisabpro-backend/services/stock_movement_service.py hisabpro-backend/routers/articles.py Test/test_mutations_stock_historique_postgres.py
```

→ code0,0.41s. Warnings pytest préexistants de dépréciation multipart/Pydantic.

## Couverture et limites

Les refus photographient articles, familles, mouvements, écritures et lignes
comptables, inventaires et lignes d'inventaire. Les compensations multiarticles
vérifient aussi la session avant rollback. Le contrôle réel couvre les refus
409/404, la correction stock10→8 avec CMUP20/coût20 et mouvement2 unités,
zéro connu, coût explicite32 donnant stock12/CMUP22, périodes fermées,
idempotence, défauts historiques et restitution legacy connue20.

Les nouveaux tests API/moteur utilisent PostgreSQL nonce. Les31tests connexes
d'intégrité historiques utilisent SQLite et ne prouvent pas une concurrence
PostgreSQL entre transactions. Aucun test visuel navigateur ni accès aux
données réelles n'a été exécuté dans ce lot. Les valeurs historiques inconnues
restent inchangées et nécessitent des justificatifs pour toute réparation.
