# Lot332 — alertes de stock historiques en lecture seule

## Problème reproduit

La route réelle est `GET /api/articles/stock/alertes`. Avant correction :

- stockNULL : classé en rupture par le repli `or0`, alors que la quantité
  physique n'est pas connue ;
- stockNaN ou+Inf : absent des deux listes, sans diagnostic ;
- stock-Inf : classé en rupture puis réponse500 lors de la sérialisation JSON.

Le journal de la vraie API du cluster nonce conserve l'erreur :
`ValueError: Out of range float values are not JSON compliant`.

## Correction minimale

Seule la fonction `alertes_stock` dans `routers/articles.py` change. Elle
réutilise la projection `nombre` du service existant, sans arrondir les quantités
et en conservant les nombres finis signés.

Le contrat garde `rupture` et `faible`, et ajoute `inconnus` et `diagnostics`.
Les lignes inconnues exposent `stock_actuel:null`, `stock_diagnostic` et
`nombres_diagnostics`. Les lignes connues conservent les anciens champs et
leurs valeurs, avec diagnosticNone/dictionnairevide.

Les règles existantes restent identiques :stock<=0 en rupture, 0<stock<5 en
faible, stock>=5 hors de ces listes. Le seuil fixe5 n'est pas remplacé par
`stock_min`. Les articles inactifs, services non stockables et autres sociétés
restent exclus. Aucune valeur source n'est corrigée ou remplacée dans l'ORM.

## Tests réellement exécutés

Toutes les commandes utilisent `PYTHON_DOTENV_DISABLED=1` et le runner isolé.

Avant correction :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_articles_alertes_stock_historique_postgres.py -vv --tb=short --junitxml=.codex-tests/alertes_332_avant.xml
```

**5échecs, 6réussites, 25avertissements, 36,25 s, code1**.
Les quatre quantités inconnues reproduisent les anomalies décrites. Le cinquième
échec est la lecture du-Inf appartenant à la deuxième société, alors que la
première société exclut bien cet article. Les six valeurs connues0/-1/0,1/
4,99999/5/1e308 conservent déjà leur classement attendu.

XML et vrai journal API restent conservés dans le cache de preuve, notamment
`alertes_332_api_echec_2a4c3bc564.log`.

Après correction, tests ciblés et connexes :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_articles_alertes_stock_historique_postgres.py Test/test_patch069_stock_services.py --tb=short --junitxml=.codex-tests/alertes_332_apres.xml
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile hisabpro-backend/routers/articles.py Test/test_articles_alertes_stock_historique_postgres.py
```

**19réussites, 25avertissements, 36,29 s, code0** :11nouveaux cas API et8connexes.
Compilation des deux fichiers Python :**code0**, 0,47 s.

Les lectures passent par HTTP vers une application complète et un PostgreSQL
éphémère dont URL/dossier/nonce sont vérifiés. Chaque quantité inconnue est
visible dans `inconnus` avec diagnostic, sans fausse rupture ni disparition.
Les nombres finis signés, zéro, fractions, seuil5 et grand nombre fini sont
préservés. Les services/inactifs sont exclus, la société active ne voit que
ses articles. La photographie globale des articles, familles, mouvements,
écritures, lignes et inventaires reste identique après les lectures.

## Limites et prochaine étape

Aucune base PostgreSQL utilisateur, migration ou donnée comptable réelle
appelée ou modifiée. Aucun frontend modifié ; aucun consommateur de cette route
n'a été trouvé dans `src` lors de l'analyse. La recette visuelle utilisateur
ne découle pas de ces tests API.

Le schéma brut `MouvementStockOut`, les moteurs de mutation de stock et
`/api/inventaire/controle-mouvements` restent des lots distincts. La réussite
de ce lot ne constitue pas une validation de leurs historiques numériques.
