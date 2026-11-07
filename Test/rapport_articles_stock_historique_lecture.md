# Lecture des articles au stock historique inconnu — 8 octobre 2026

La recette Edge des devis 242 a réellement rencontré une réponse 500 de
`GET /api/articles` : `ArticleOut` héritait du stock obligatoire de la création,
incompatible avec un historique SQL NULL. Les deux diagnostics navigateur
échoués (32,75 s et 15,79 s) restent consignés dans le rapport 242.

Correction minimale du contrat de sortie, sans migration ni réparation :
stock NULL, NaN, ±Infinity ou négatif exposé comme NULL avec
`stock_diagnostic` explicite. Une valeur finie non négative reste exacte.
Le contrat `ArticleCreate` reste distinct : le stock NULL n'est pas autorisé
à la création. La projection de lecture n'écrit jamais dans l'objet SQL.
Le diagnostic de devis 241 relit la source et continue à signaler « inconnu ».

Commande réellement exécutée par le principal, dotenv désactivé :

```text
python -X utf8 Test/run_unit_tests.py Test/test_articles_stock_historique_lecture.py Test/test_devis_stock_diagnostic.py Test/test_articles_archivage_stock.py Test/test_stock_integrite_mouvements.py --tb=short
```

**76 réussis, 25 avertissements, 31,35 s, code 0**, aucun ignoré.
Neuf nouveaux contrôles, dont huit sur vraie API et PostgreSQL nonce,
comparent les instantanés SQL complets d'articles, mouvements et écritures.
La première fixture attendait à tort HTTP201 à l'inscription, dont le contrat
existant est HTTP200 : un succès et huit erreurs de préparation en 15,93 s.
Seule cette attente de fixture a été corrigée, sans changement d'oracle métier.
Compilation Python du schéma et du test : code 0.

Limites : autres données historiques de prix/TVA/CMUP non finis hors périmètre.
Cette correction de sortie ne valide pas les mouvements sur un stock invalide,
les tableaux de stock historiques ou le PostgreSQL utilisateur. La recette
Edge 242 doit reprendre sur ce schéma de lecture, sans remplacer l'inconnu par 0.
