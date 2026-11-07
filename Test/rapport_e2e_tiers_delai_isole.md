# Tiers — filtre du délai de paiement paramétré

Lot `TIERS-FILTRE-DELAI-20261009-279`.

## Analyse et périmètre

La page disposait de filtres de rôle, de recherche et d’activité commerciale, mais pas du filtre de délai demandé. Le nouveau sélecteur utilise uniquement `delai_paiement` du tiers : tous, comptant (0), 1–30 jours, 31–60 jours, plus de 60 jours, à vérifier. Il ne calcule aucune échéance de facture. Le prédicat exige un nombre fini, entier et positif ou nul ; NULL, booléens, chaînes, fractions et valeurs non finies ne deviennent jamais comptant. Le formulaire tiers et ses règles restent hors de ce lot.

Le sélecteur reprend le style des filtres existants et leur barre. Les autres filtres restent combinables. Il est indépendant de l’activité annuelle : un changement d’année conserve ce filtre de fiche, tandis que le changement natif de société recharge son propre périmètre.

## Tests réellement exécutés

Commandes :

```powershell
node --test Test/test_tiers_activite.mjs
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_tiers_delai_isole.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_tiers_delai_isole.py Test/test_e2e_tiers_activite_isole.py -x --tb=short
```

Node : **9 passed, 0 failed, 0 skipped**, 153,39 ms. Les nouveaux oracles purs couvrent exactement 0/1/30/31/60/61 et l’absence de conversion implicite des valeurs invalides.

Premier ciblé : **1 failed en 43,29 s**, timeout du sélecteur. L’écriture initiale par pipeline PowerShell avait remplacé les accents du nouvel `aria-label` par des points d’interrogation. Les chaînes ajoutées ont été réécrites en UTF-8 avec `apply_patch` ; aucune règle ni assertion métier n’est changée pour masquer cet échec.

Deuxième commande connectée : **1 failed en 26,76 s**, trois tiers obtenus au lieu de deux pour 31–60 jours. La création API du tiers fictif avec `delai_paiement: null` déclenchait le défaut ORM 60. Le prérequis historique NULL a été préparé explicitement dans la DB nonce avant les snapshots, sans changer l’application ni l’oracle des bornes.

Reprise finale : **4 passed en 46,08 s, exit 0**, aucun échec, erreur ou test ignoré : deux nouvelles recettes desktop/mobile et les deux recettes connectées d’activité existantes (homonymes, reliquats, pagination et historiques). Les 25 avertissements Pydantic/Starlette existants ne sont pas des tests ignorés.

Compilation Python réelle du nouveau test : **exit 0**. Relecture finale Node : **9 passed, 115,39 ms**, aucun échec ni test ignoré. Build final exécuté ici sur les sources stabilisées : `npm.cmd run build`, **exit 0, 138 modules, 4,84 s**. Les avertissements Vite existants de taille et d’import xlsx restent présents ; ils ne bloquent pas le build.

Les deux nouvelles recettes utilisent Edge aux largeurs 1365 et 390, FastAPI réel et PostgreSQL nonce gardé. Sept tiers fictifs portent les délais 0/1/30/31/60/61/NULL et les rôles client/fournisseur/les deux. 195 tiers supplémentaires portent 90 jours : les 202 lignes imposent une vraie seconde page API `skip=200`. Les tests vérifient frontières, rôles, recherche par ville, activité sans mouvements, impayés vides, remise à tous les délais, changement d’année et société B ne contenant que son fournisseur comptant. Les snapshots complets des tiers, écritures et lignes comptables doivent être identiques avant/après. Aucun POST/PATCH/DELETE tiers n’est émis par l’interface durant ces filtres.

## Limites

Aucune base réelle ni donnée utilisateur ne sont utilisées. Le délai NULL est un prérequis fictif du laboratoire, créé avant photographie. Les non-finis, booléens et chaînes sont vérifiés par Node car le contrat PostgreSQL entier ne les expose pas comme données ordinaires. La recette utilisateur reste à effectuer. Aucun impayé, date d’échéance ou régime fiscal n’est déduit du délai.

Fichiers : `src/pages/Tiers.jsx`, `src/utils/tiersActivite.js`, `Test/test_tiers_activite.mjs`, `Test/test_e2e_tiers_delai_isole.py`, ce rapport. Journal et ZIP vérifié assurés par l’agent principal.
