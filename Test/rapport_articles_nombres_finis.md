# Articles : refus des saisies numériques invalides avant mutation

Lot `ARTICLES-NOMBRES-FINIS-20261008-268`, terminé le 9 octobre 2026.

## Reproduction et correction minimale

Avant correction, deux appels sur un vrai serveur FastAPI et PostgreSQL nonce ont produit **HTTP 500 après modification de la table articles** : POST `prix_vente_ht="NaN"`, puis PATCH `frais_transport=null`. Les photographies exactes des tables mouvements_stock et écritures étaient inchangées. Commande :

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_articles_nombres_finis.py -k reproduction --tb=short
```

**2 échoués en 18,99 s**, 199 désélectionnés : reproduction attendue du défaut, pas un résultat réussi.

Les validateurs de saisie `ArticleCreate` et `ArticleUpdate` utilisent maintenant `_nombre_fini` avant conversion Pydantic pour prix de vente/achat, stock initial/actuel, seuil, emballage, transport et TVA. Les nombres non finis, booléens et null explicitement fournis sont refusés. Les contraintes non négatives et les taux autorisés existants restent en place. Un champ PATCH omis reste facultatif ; un PATCH portant un stock fini reste refusé 409 par le routeur, via le mécanisme traçable existant.

`ArticleOut` neutralise explicitement ce nouveau garde de requête hérité : le stock historique inconnu conserve null et son diagnostic. Les autres champs historiques ne sont ni corrigés ni remplacés par zéro. Aucune migration, mutation historique, route ou règle fiscale n'a été ajoutée. Les prix/frais finis de `1e308` restent acceptés, sans plafond arbitraire.

## Vérifications réellement exécutées

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_articles_nombres_finis.py --tb=short
```

Premier passage après correction : **201 réussis en 17,84 s**. Passage final avec six cas supplémentaires de littéraux NaN/Infinity hors JSON standard : **207 réussis en 19,83 s**, aucun échec ni test ignoré. Contrats purs et vrais appels API/JWT sur PostgreSQL nonce vérifient les refus 422 avant mutation, chaînes et littéraux non finis, null/booléens, conservation des champs omis, valeurs zéro/fractionnelles/grandes, réponse de validation JSON sûre, règle de stock 409 et lecture historique inchangée. Chaque refus connecté compare les tables articles, mouvements_stock et écritures avant/après.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_articles_stock_historique_lecture.py Test/test_e2e_articles_stock_inconnu_isole.py Test/test_fact1_facturation_fondations.py Test/test_patch06c_stock_engine.py Test/test_articles_archivage_stock.py --tb=short
```

**38 réussis en 40,47 s** : lectures historiques réelles, Edge sur stock inconnu, fondations facturation, moteur stock et archivage. Aucun test ignoré. Les avertissements Pydantic/python_multipart existants sont signalés dans pytest.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile hisabpro-backend/schemas.py Test/test_articles_nombres_finis.py
```

**OK**, code de sortie 0 après la dernière modification du test. Pas de build frontend : aucun fichier frontend n'a changé.

## Limites et reprise

Aucun PostgreSQL réel ni serveur utilisateur utilisé. Les effets observés avant correction concernent uniquement le laboratoire éphémère, fermé après chaque commande. Les prix, frais et seuils historiques déjà invalides peuvent encore rendre leur lecture impossible ; ce lot préserve leur contrat existant et empêche les nouvelles saisies défectueuses, sans réparation implicite. Une qualification de sortie et des gardes UI sur ces autres données doivent faire l'objet d'un lot distinct si nécessaire.

Prochaine étape indépendante : exposer les deux frais existants dans la fiche article, avec validation et libellé de référence explicites. Aucun transfert automatique ni traitement fiscal des frais article vers facture n'est introduit par ce correctif.

Différentiel : `hisabpro-backend/schemas.py` (classes articles uniquement), `Test/test_articles_nombres_finis.py`, ce rapport. Journal et ZIP vérifiés par l'agent principal.
