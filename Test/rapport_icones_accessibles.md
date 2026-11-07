# Icônes locales : affichage préservé et noms accessibles — lot326

## Problème et correction

Après localisation des polices Tabler, les pseudo-éléments CSS des icônes décoratives étaient inclus dans les noms accessibles des contrôles. Le texte visible « Achat » restait correct, mais le nom accessible contenait U+EA13 suivi d'Achat. Un lecteur d'écran et le sélecteur exact du navigateur recevaient donc un nom pollué.

La capture réelle de l'arbre accessible et du DOM a confirmé cette cause (voir `rapport_retests_globale315.md`). La correction applicative effectuée par l'agent principal conserve les4962 glyphes et ajoute à leurs déclarations CSS l'alternative textuelle vide : `content: "glyph" / ""`. Le CSS local, sa provenance et ses empreintes sont actualisés dans :

- `public/vendor/tabler/tabler-icons.css` ;
- `public/vendor/MANIFEST.json` ;
- `public/vendor/README.md`.

Les fontes WOFF2 restent identiques. Les contrôles uniquement composés d'une icône doivent garder un libellé explicite (`aria-label` ou titre) ; le masquage décoratif ne crée pas un nom métier manquant. La vérification indépendante du manifeste a contrôlé les tailles et SHA256 des **12 fichiers** déclarés, sans divergence. Le CSS contient **4962 alternatives vides**.

## Tests réellement exécutés

L'essai préalable en mémoire du navigateur, avant correction applicative : **2 passed, 25 warnings, 22.27 s** (Edge1365/390), session66294. Glyphe, police chargée, visibilité et dimensions13×13px préservés ; noms accessibles exacts et clics réels rétablis. Ce résultat préalable n'est pas une validation du fichier livré ; il justifie le choix de correction.

Nouveau test persistant `Test/test_e2e_icones_accessibles_isole.py`, **sans injection CSS ou modification du DOM** : Edge1365/390, vraie application et API sur PostgreSQL nonce. Il vérifie les noms exacts Achat/Vente/Bons de commande/Nouveau devis/Nouvelle facture, les clics réels Vente/Achat, les glyphes U+EA13/U+EA24 réellement rendus avec leur alternative vide, leur fonte chargée et dimensions visibles. L'arbre accessible des boutons ne contient plus de caractères privés des icônes. Photographie des articles, écritures, mouvements et inventaires inchangée (tous vides dans ce dossier fictif), aucune erreur JavaScript/API ni ressource vendor404.

- Nouveau test seul : **2 passed, 25 warnings, 23.00 s**, session59148, code0, XML `.codex-tests/icones326_persistant_initial.xml`.
- Ancien test de chargement local et nouveau test ensemble, avant adaptation de l'oracle de contenu CSS : **2 failed, 2 passed, 25 warnings, 42.31 s**, session24308, code1, XML `.codex-tests/icones326_chargement_initial.xml`. Les deux échecs viennent uniquement de l'ancien retrait des guillemets supposant un contenu sans alternative (`glyph" /` au lieu du glyphe seul).
- Correction minimale autorisée de `Test/test_e2e_chargement_sans_cdn_isole.py` : assertion désormais stricte du glyphe de déconnexion U+EBA8 **et** de son alternative vide. Les sélecteurs, les contrôles métier, la simulation d'un CDN ne répondant pas et la navigation `wait_until='load', timeout=5000` restent inchangés.
- Rejeu des deux modules après cette adaptation : **4 passed, 25 warnings, 48.62 s**, session26678, code0, XML `.codex-tests/icones326_chargement_final.xml`. Les fontes sont servies localement avec HTTP200 et aucune requête CDN ; navigation cinq secondes maintenue.
- `python -X utf8 -m py_compile Test/test_e2e_chargement_sans_cdn_isole.py Test/test_e2e_icones_accessibles_isole.py` : code0, 0.40s.

Commande finale avec `PYTHON_DOTENV_DISABLED=1` :

```text
python -X utf8 Test/run_unit_tests.py Test/test_e2e_chargement_sans_cdn_isole.py Test/test_e2e_icones_accessibles_isole.py -vv --tb=short --junitxml=.codex-tests/icones326_chargement_final.xml
```

## Périmètre et limites

Aucun PostgreSQL réel, donnée comptable utilisateur ou migration modifié. Les résultats concernent Edge/Chromium disponible sur ce poste ; validation humaine et autres moteurs de navigateur restent à effectuer. Ce correctif ne démontre pas à lui seul la cause profonde des incidents Node/driver ni de tous les délais historiques de la globale315. Le retest ciblé des54 anciens cas est consigné séparément dans `rapport_retests_globale315.md` ; aucune globale en échec n'est reclassée rétroactivement comme réussie.
