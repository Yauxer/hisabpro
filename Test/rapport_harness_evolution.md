# Actualisation des tests après les évolutions livrées

Lot `TESTS-HARNESS-EVOLUTION-20261008`, 8 octobre 2026 UTC. **Fichiers de tests uniquement**, aucune modification de l’application, de migration ou de donnée réelle.

## Analyse des sept échecs

Le journal `.codex-tests/global_20261008_0458.log` et son XML recensent sept échecs concernés : un ancien libellé d’échéance, une ancienne lecture du plan sans comptes inactifs, trois extractions de sauvegarde sans leurs nouvelles dépendances RAS, un ancien lien ETIC dans la barre latérale et un export Excel extrait sans ses imports de présentation. La commande globale initiale terminait à 2 019 réussites, 7 échecs et 31 erreurs ; cette analyse ne déclare pas les autres erreurs résolues.

## Corrections minimales du harness

- `test_fact4_facturation_robuste.py` : vérifie le libellé livré « Échéance » et l’absence du libellé obsolète « Échéance contractuelle ».
- `test_patch055_plan_societe_exercices_decales.py` : vérifie la lecture du plan incluant les comptes inactifs afin de conserver leurs libellés historiques. Vérifie aussi que le cache et le plan des sélecteurs continuent à filtrer les comptes actifs.
- `test_patch073_actualisation_edition_facture.py` : fournit aux fonctions JavaScript réellement extraites `rasTaux=10`, `rasInitialInvalide=false`, `rasChoisi=false`. Le scénario reste celui d’une pièce verrouillée ; il vérifie l’absence de RAS dans le payload. Les contrôles PATCH → attente du rechargement → fermeture, attente réellement suspendue et erreur sans fermeture restent exécutés.
- `test_patch09_2_etic.py` : conserve les routes API et la route directe historique `/etic`, vérifie la navigation principale vers le cockpit Liasse fiscale, la présence des sections ETIC et le bouton ouvrant `/etic` depuis ce cockpit.
- `exports09a.py` : charge le véritable module `src/utils/liassePresentation.js` et son JSON canonique. Seule la résolution de son import JSON Vite est adaptée dans un module Node en mémoire ; les fonctions et la note ne sont pas remplacées par des doublures. L’export Excel réel est sérialisé puis relu avec XLSX ; ses feuilles T1/T2, sa note, les références internes conservant B6/B7, chaque colonne de ventilation et chaque erreur de contrôle sont vérifiées. Les frontières de sections utilisent les références effectives, y compris les codes particuliers. La source JSON reste identique après export ; le contrôle canonique Python et le PDF réel restent vérifiés.

## Tests réellement exécutés

Première commande ciblée : les quatre fichiers corrigés et `Test/test_patch128_exports09a.py` : **34 réussis en 1,11 s**.

Après ajout des assertions d’immutabilité RAS et de repérage Excel, commande finale :

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_fact4_facturation_robuste.py Test/test_patch055_plan_societe_exercices_decales.py Test/test_patch073_actualisation_edition_facture.py Test/test_patch09_2_etic.py Test/test_patch128_exports09a.py Test/test_liasse_numerotation_interne.py
```

Résultat : **37 réussis en 1,37 s**, dont les sept cas précédemment échoués, exports PDF/Excel en mémoire et tests connexes de numérotation/archives. Aucun échec de test intermédiaire de ce lot. Les simulations de callbacks JavaScript sont des tests de harness, pas une nouvelle recette navigateur connectée. Les accès fichiers ont été vérifiés avant le lancement ; un chemin de composant supposé a été remplacé par les fichiers de cache/plan réellement présents.

Compilation Python des cinq fichiers modifiés : **OK**. Aucun build frontend nécessaire : aucune source frontend modifiée. Aucun PostgreSQL réel utilisé ; cette exécution ciblée ne prouve pas une validation PostgreSQL ni une relance complète de la suite globale. La suite globale est à reprendre par l’agent principal après ses corrections indépendantes.

## Différentiel

- `Test/test_fact4_facturation_robuste.py`
- `Test/test_patch055_plan_societe_exercices_decales.py`
- `Test/test_patch073_actualisation_edition_facture.py`
- `Test/test_patch09_2_etic.py`
- `Test/exports09a.py`
- `Test/rapport_harness_evolution.md`

Journal et ZIP différentiel vérifié assurés par l’agent principal.
