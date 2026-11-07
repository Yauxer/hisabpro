# Recette — Documents commerciaux récents en tête

Lot `TRI-CREATION-COMMERCIAL-20261007`. Travail initial le 7 octobre 2026 ; reprise après interruption à 21:58 UTC le même jour.

## Modifications présentes dans le dépôt

Les listes API devis, bons de commande, bons de livraison, bons de réception, factures et règlements suivent la date technique de création décroissante, puis l'identifiant décroissant. Deux pièces créées au même instant restent dans un ordre stable. Une nouvelle pièce antidatée apparaît avant une pièce créée auparavant ; aucune date de document ou date comptable n'est modifiée.

Les horodatages historiques manquants restent nuls. Ces pièces sont placées après les pièces horodatées, avec leur identifiant décroissant comme départage. La lecture de ces données révélait aussi une incompatibilité réelle : cinq schémas de réponse imposaient un horodatage non nul alors que les modèles et la base autorisent NULL. Les seuls champs `created_at` de `DevisOut`, `BonCommandeOut`, `BonLivraisonOut`, `FactureOut` et `ReglementOut` acceptent désormais NULL, sans inventer une date.

Le cycle commercial conserve l'ordre API, au lieu de retrier localement les devis, commandes, factures ouvertes et règlements selon leur date de pièce. Le tri des articles par désignation est conservé. Les filtres, scopes de société/exercice, liens documentaires et règles de pagination restent inchangés.

Aucun modèle, migration ou enregistrement réel n'est modifié. Les changements initialement appliqués ont été retrouvés dans le dépôt à la reprise et n'ont pas été réappliqués.

## Résultats exécutés lors de la reprise

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_tri_creation_commercial_isole.py
```

**6 tests E2E réussis en 54,19 s**, aucun échec ni test ignoré. Vrais appels API et affichages Edge, exclusivement sur PostgreSQL éphémère protégé par le banc existant. Un scénario par liste vérifie : deux créations au même instant départagées par ID ; pièce antidatée en tête ; priorité de l'horodatage sur l'ID seul ; deux pièces historiques NULL après les autres ; stabilité entre deux lectures ; absence de réécriture des dates et horodatages. Le premier élément affiché dans chacun des six onglets est la pièce antidatée attendue.

Les filtres société, exercice, achat/vente, statut, recherche et facture liée sont vérifiés selon les paramètres propres à chaque route. La pagination des factures est vérifiée sur une tranche de deux éléments. Les réponses conservent réellement NULL pour les timestamps historiques. Les jeux de départ sont construits dans la base éphémère uniquement ; aucune donnée comptable réelle n'est utilisée.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_fact2_cycle_commercial.py Test/test_factC_cycle_documentaire.py Test/test_fact10_dashboard_commercial.py Test/test_fact9_documents_pdf.py
```

**29 tests connexes réussis en 2,27 s**, aucun échec ni test ignoré : cycle, traçabilité documentaire, dashboard commercial et documents PDF.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_cycle_commercial_isole.py Test/test_e2e_facturation_isole.py
```

**3 tests E2E connectés réussis en 69,31 s**, aucun échec ni test ignoré. Parcours vente devis → BC → BL → facture avec stock et traçabilité ; parcours vente et achat facture → validation → règlements partiels/complets → lettrage, via vraie UI/API et PostgreSQL éphémère. Les deux fixtures ont terminé leurs contrôles d'arrêt et de nettoyage. Avertissements existants Pydantic et python-multipart. Le résultat de l'ancien processus interrompu n'est pas considéré comme une preuve de réussite ; cette commande a été réellement relancée.

```text
npm run build
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile hisabpro-backend/routers/commercial.py hisabpro-backend/routers/factures.py hisabpro-backend/schemas.py Test/test_tri_creation_commercial_isole.py
```

**Build Vite réussi**, 135 modules, 7,97 s ; avertissements existants d'import XLSX et de taille du bundle. **Compilation Python réussie** sur les quatre fichiers concernés.

## Historique des essais avant interruption

- Premier passage : 6 échecs en 16,88 s ; véritables HTTP 500 sur les dates de création historiques NULL, incompatibilité de réponse corrigée sans réécriture des données.
- Deuxième passage : 5 réussites, 1 échec en 26,30 s ; la fixture règlement accédait à un ID SQLAlchemy après fermeture de sa session. ID capturé avant la fermeture, sans changement métier.
- Passages suivants observés : 6 réussites en 28,85 s, puis 6 réussites en 30,12 s après renforcement des assertions NULL/statut. À la reprise, les six tests ont été relancés sur l'état réel des fichiers.

`git status` reste inexécutable : ce dossier ne contient pas de dépôt `.git`. Aucun reset, commit, nettoyage global ou arrêt des processus de l'utilisateur n'a été effectué.

## Livraison

Fichiers exacts du lot, auxquels l'agent principal ajoute `CODEX_PROGRESS.md` dans le ZIP différentiel :

- `hisabpro-backend/routers/commercial.py`
- `hisabpro-backend/routers/factures.py`
- `hisabpro-backend/schemas.py`
- `src/pages/Commercial.jsx`
- `Test/test_tri_creation_commercial_isole.py`
- `Test/rapport_tri_creation_commercial.md`

Le nom `Test/test_tri_creation_commercial_postgres.py` cité dans une ancienne entrée du journal ne correspond pas au fichier réel ; le fichier testé et livré est `Test/test_tri_creation_commercial_isole.py`.

À effectuer par l'utilisateur : appréciation de l'ordre de présentation sur ses dossiers historiques. Aucun test sur PostgreSQL réel ni validation comptable/réglementaire officielle n'est revendiqué. Le banc isolé vérifie l'arrêt de ses processus et le nettoyage de ses dossiers à la fin des tests ; les services existants de l'utilisateur ne sont pas touchés.

Journal et vérification du ZIP assurés uniquement par l'agent principal. Prochaine tâche : consolidation de la couverture, audit RAS et non-régression globale.
