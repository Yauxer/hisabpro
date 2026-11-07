# Articles : lecture des nombres historiques — lot 310

10 octobre2026. Complément ciblé de LIM18, sans migration, réparation d'historique ou changement des règles fiscales.

## Cause et preuve avant correction

Le contrat `ArticleOut` héritait du modèle de saisie. Seul le stock physique possédait une projection nullable. Les prix/frais/seuil/TVA historiques NULL pouvaient échouer lors de la validation de réponse ; des prix ou CMUP NaN/Inf pouvaient atteindre le JSON et provoquer500. Les valeurs négatives et les TVA hors intervalle de saisie avaient aussi une validation de sortie incompatible avec leur consultation.

Le test réel session47033 injecte un prix de vente NULL dans un article fictif, exclusivement sur PostgreSQL nonce possédé. Le GET `/api/articles` renvoie500 au lieu200 :1 échec,91 désélectionnés,19,91s, sortie1.

## Projection de lecture

`ArticleOut` projette désormais sept champs en valeurs flottantes facultatives : `prix_vente_ht`, `prix_achat_ht`, `frais_emballage`, `frais_transport`, `stock_min`, `tva`, `cmup`. Un NULL, booléen, non-fini ou nombre négatif est rendu NULL avec une entrée `nombres_diagnostics[champ]`. Une TVA supérieure à100 suit la même projection. Une donnée finie dans l'intervalle historique0..100 n'est pas requalifiée fiscalement par cette lecture.

La projection agit uniquement sur l'objet Pydantic retourné. Aucun attribut ORM, prix, taux, coût ou stock persisté n'est changé. Zéro, fractions et grands prix finis restent exacts dans le contrat flottant existant, sans plafond commercial arbitraire. Le contrat `stock_actuel`/`stock_diagnostic` du lot248 est conservé.

Les validateurs de création et PATCH du lot268 restent stricts : aucun NULL, booléen ou non-fini n'est autorisé dans une nouvelle saisie numérique. Un PATCH textuel omet les nombres inconnus et conserve leurs valeurs historiques. Une correction numérique explicite ne change que le champ demandé.

## Couverture réelle

- 49 cas purs : chacun des sept champs avec NULL, NaN, Inf, -Inf, négatif et deux booléens ; sortie JSON NULL et diagnostic.
- 3 cas purs : zéro, fraction0,125 et1e308, avec TVA20 et diagnostic vide.
- 2 cas purs : TVA101 et1e308 rendues inconnues.
- 35 cas API/PG : chaque champ avec NULL, NaN, Inf, -Inf et-1 ; GET200, diagnostic, stock0 conservé, photographies `articles`, `mouvements_stock`, `ecritures` identiques avant/après lecture.
- 1 cas API : TVA101 inconnue, aucune mutation.
- 1 parcours API : tous les sept champs NULL ; PATCH description seul, puis correction explicite du prix de vente à0,125 ; les six autres NULL restent stockés. Autre société : liste vide et tentative PATCH404, aucune mutation.
- 1 parcours API : prix/frais/seuil connus0,0,125 et1e308, restitutions sans diagnostic.

Total92 nouveaux tests, dont38 cas API ou parcours sur PostgreSQL isolé. Il n'existe pas de GET `/api/articles/{id}` dans ce routeur : la liste et les réponses POST/PATCH sont les contrats réellement exercés.

## Commandes et résultats

Environnement `PYTHON_DOTENV_DISABLED=1`, sans lecture du `.env` utilisateur :

```powershell
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_articles_historique_nombres_lecture.py -k 'api_nombres and None and prix_vente_ht' --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_articles_historique_nombres_lecture.py --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_articles_nombres_finis.py Test/test_articles_stock_historique_lecture.py Test/test_articles_archivage_stock.py --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -m py_compile hisabpro-backend/schemas.py Test/test_articles_nombres_finis.py Test/test_articles_historique_nombres_lecture.py
```

- Avant correction47033 :1 échec,91 désélectionnés,19,91s, sortie1.
- Première collection après modification :1 erreur de collection,0,60s ; import Pydantic `Field` manquant, corrigé avant toute déclaration de test réussi.
- Ciblés finaux46878 :92 réussis,25 avertissements,23,44s, sortie0.
- Connexes17399 :230 réussis,25 avertissements,40,80s, sortie0. Saisies strictes268, stock historique248 et protections d'archivage.
- Compilation des trois fichiers Python après modification finale : sortie0.

L'assertion historique du test268 qui attendait NaN/Inf en sortie est mise à jour explicitement pour le nouveau contrat NULL/diagnostic. Les assertions de refus de saisie et de non-mutation restent conservées.

## Limites explicites

Cette étape ne traite pas `FamilleOut` et sa TVA par défaut historique, les calculs d'inventaire, les alertes stock brutes ou les moteurs de valorisation. Ces consommateurs lisent encore l'ORM directement ; rendre une fiche article consultable ne répare ni ne valide leurs coûts historiques. Aucune valeur inconnue ne devient un coût nul fiable. Les preuves frontend finales sont consignées ci-dessous après leur exécution réelle. LIM18 n'est donc pas déclaré intégralement résolu pour tous les consommateurs.

## Interface et preuves finales du principal — reprise09:36UTC

La même livraison inclut `Articles.jsx`, `Commercial.jsx`, `Factures.jsx` et
le helper `articlesNombres.js`. Un montant historique inconnu est affiché
« À vérifier » ; les champs restent vides. Une édition simple envoie seulement
les champs modifiés. Un champ inconnu touché puis vidé doit être renseigné
explicitement ou sa modification annulée. Un zéro explicitement saisi est
accepté ; aucun prix, frais, seuil ou taux historique n'est remplacé par défaut.

Les sélections d'articles sur devis, commandes et nouvelles factures conservent
les prix/TVA inconnus vides, avec totaux indicatifs « À vérifier ». Création
et édition devis/commande sont refusées tant que ces nombres sont inconnus.
Le choix de TVA dans la ligne commerciale met désormais à jour taux et
qualification en une seule opération : les deux mises à jour sur les mêmes
props perdaient précédemment le choix du taux. Aucune formule fiscale nouvelle.

Le nouveau module navigateur contient un cas Node et deux Edge1365/390.
Les articles NaN/Inf/NULL/négatifs sont créés exclusivement dans le cluster
nonce, puis les montants sont photographiés. Le PATCH description contient
uniquement `description` ; la correction explicite d'un frais contient
uniquement `frais_emballage:0`. Les autres nombres sont conservés. Un devis
vente, une commande achat et les deux factures brouillon sont créés avec
prix100 et TVA20 explicitement choisis :100HT/20TVA/120TTC chacun.
Les sélections inconnues en édition devis/commande refusent le PATCH.
Un produit de stock non fini est diagnostiqué ; aucune écriture ni mouvement
de stock n'est créé par ces documents brouillon.

Résultats intermédiaires rapportés par l'agent :

- Premier Edge :1échec44,77s, helper de test limité aux inputs alors que TVA
  et description sont select/textarea. Correction du helper seulement.
- Deuxième Edge :1échec44,05s, vrai défaut des deux mises à jour TVA démontré.
- Après correction atomique :1échec et1réussi32,90s ; le résumé HT lignes
  et la cellule HT affichaient encore un zéro indicatif. Les deux
  affichages sont maintenant diagnostiqués. Aucun calcul métier modifié.
- La dernière session92900 n'a pas pu être récupérée après le quota ;
  **son résultat n'est pas déclaré réussi**. Le principal a relancé les tests.

Commandes réelles du principal, `PYTHON_DOTENV_DISABLED=1` et Python du venv :

```text
python -X utf8 Test/run_unit_tests.py Test/test_e2e_articles_historique_nombres_isole.py -vv --tb=short --junitxml=.codex-tests/ui_articles_310_0936.xml
python -X utf8 Test/run_unit_tests.py Test/test_e2e_articles_frais_isole.py Test/test_e2e_devis_stock_alerte_isole.py Test/test_e2e_articles_stock_inconnu_isole.py --tb=short --junitxml=.codex-tests/connexes_articles_310_0936.xml
python -X utf8 -m py_compile hisabpro-backend/schemas.py Test/test_articles_nombres_finis.py Test/test_articles_historique_nombres_lecture.py Test/test_e2e_articles_historique_nombres_isole.py
npm run build
```

- Ciblés15220 :**3réussis,25avertissements,47,20s, sortie0**, dont les deux Edge.
- Connexes45274 :**5réussis,25avertissements,88,95s, sortie0** ; frais
  articles, avertissements stock devis et lecture du stock historique inconnu.
- Compilation des quatre Python : sortie0.
- Build14381 :**139modules,12,72s, sortie0**. Avertissements existants sur
  taille des chunks et import mixte XLSX, aucun échec du build.

Les nombres des suites qui se recouvrent ne sont pas additionnés en un total
global. La nouvelle consolidation fera l'objet d'un rapport distinct.
Tests humains et installation sur PostgreSQL réel restent à effectuer.
