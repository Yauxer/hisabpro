# Alerte stock indicative des devis — 8 octobre 2026

L'alerte existante en création reposait sur le stock mémorisé dans chaque ligne, sans cumul des lignes d'un même article. L'édition initialisait ce stock à null et ne proposait aucune alerte. Les deux formulaires utilisent désormais la même lecture API du stock physique de la société. Aucun stock n'est réservé, aucun règlement ou mouvement comptable n'est créé et l'enregistrement reste autorisé en rupture.

Le composant affiche le cumul demandé, le stock physique et le manque selon la réponse réelle. Les services non stockables et les stocks inconnus sont distingués. Les valeurs Decimal reçues en texte sont conservées en texte ; elles ne sont jamais transformées en Infinity. Une actualisation relit le serveur. Les requêtes sont annulées et leurs réponses ignorées lorsqu'elles ne correspondent plus aux lignes/année courantes. Une erreur de lecture reste visible sans empêcher l'enregistrement.

Recette prévue : Edge 1365 et 390 px sur API et PostgreSQL nonce. Deux lignes de trois unités d'un article avec stock cinq donnent demandé six et manque un ; service sans contrôle ; ancien stock null explicitement inconnu ; cumul 2 × 1e308 sans Infinity. Création malgré rupture, édition après relecture, réponse HTTP réelle retenue avant changement des quantités, stock fictif changé par API puis actualisé, sauvegarde encore autorisée. Snapshots contrôlent l'absence de mouvements de stock et d'écritures.

Premiers tests exécutés : échec Edge en 32,75 s lors de la sélection de l'article ; analyse API ciblée ensuite en 15,79 s démontre `GET /api/articles` HTTP 500 avec un stock historique null. La sortie ArticleOut héritait du champ float non nullable de la création. Le diagnostic de stock savait déjà conserver ce cas en « inconnu », mais l'autocomplétion ne pouvait pas charger la liste. La recette est suspendue jusqu'à la correction minimale de cette sortie par l'agent principal (lot distinct 248). Aucun stock inconnu n'est remplacé par zéro.

L'actualisation est préparée avec le workflow existant `PATCH /api/articles/{id}/stock`, référence et note fictives explicites, qui crée un seul mouvement traçable de correction de cinq à zéro. L'oracle attend ce seul mouvement supplémentaire ; les devis et leur diagnostic ne doivent en ajouter aucun. Le PATCH de la fiche article demeure interdit pour modifier le stock.

Après correction du lot distinct 248, la recette initiale inchangée passe : **2 passed en 26,62 s**, Edge 1365 et 390 px. Le GET des articles à stock null est contrôlé HTTP 200. Création et édition malgré manque de stock, réponse tardive ignorée, actualisation réelle et quantités Decimal en texte sont exécutées. Le bouton Enregistrer reste disponible pendant la lecture retenue. Le seul mouvement supplémentaire est la correction de stock explicitement déclenchée par la recette ; les lectures et les devis ne créent aucun mouvement ni écriture.

Connexes exécutés : **34 passed et 1 failed en 84,74 s**. Les parcours existants devis/notes, cycle commercial, documents BR et le diagnostic API passent. L'unique échec concerne une assertion statique du test historique 069, qui imposait littéralement l'ancien appel `lignes.some(stockInsuffisantPourDevis)`. Après autorisation explicite de l'agent principal, seule cette assertion obsolète est retirée avec un commentaire renvoyant aux vrais oracles API 241/Edge 242 ; les oracles Node, services et nature des articles sont conservés. Relance finale de tout le module 069 et des deux nouvelles recettes Edge : **10 passed en 28,26 s**, zéro échec et zéro test ignoré. Aucune source applicative n'a changé entre les connexes et cette relance.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_devis_stock_alerte_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_devis_notes_isole.py Test/test_e2e_cycle_commercial_isole.py Test/test_e2e_reception_client_documents_isole.py Test/test_devis_stock_diagnostic.py Test/test_patch069_stock_services.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_patch069_stock_services.py Test/test_e2e_devis_stock_alerte_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_patch069_stock_services.py Test/test_e2e_devis_stock_alerte_isole.py
npm run build
```

Build Vite final après ajustement de précision des petites quantités : **138 modules, exit 0 en 4,84 s** (avertissements XLSX et taille des chunks existants). Les nombres finis sont affichés avec jusqu'à 17 chiffres significatifs ; une petite quantité ne devient pas visuellement zéro par un arrondi à huit décimales. Compilation Python des deux tests : exit 0.

Aucune donnée ou fichier utilisateur réel n'est concerné. La lecture est celle du stock actuel et ne prétend pas reconstituer le stock historique à la date d'un ancien devis. Une indisponibilité de lecture est affichée explicitement sans désactiver l'enregistrement ; une panne réseau n'a pas été fabriquée pour obtenir une preuve fonctionnelle supplémentaire. Les contrôles propres à la commande/livraison sont conservés. La recette utilisateur sur ses références d'articles reste à effectuer.
