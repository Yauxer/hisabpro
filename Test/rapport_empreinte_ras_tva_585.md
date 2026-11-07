# Empreinte des données dans les exports RAS TVA — lot585

CSV, Excel et PDF conservent désormais l'empreinte SHA-256 du registre JSON
déjà contrôlée par l'API avant téléchargement. Il s'agit de l'empreinte des
données, pas du binaire PDF/Excel ni d'une signature officielle. Aucun montant,
statut ou compte n'est modifié ; aucune nouvelle migration ou règle fiscale.
Le guide Markdown/PDF a été mis à jour et régénéré depuis sa source unique.

## Vérifications réellement terminées le18octobre2026

- Ciblé :10tests réussis,29avertissements,70,65s, code0 : nouvelle correspondance
  JSON/CSV/Excel/PDF, sept API du registre et deux contrôles de formats précis.
- Consolidation sur les sources finales :**137tests réussis**,29avertissements,
  **320,10s**, code0. Le banc commun585 inclut les parcours581, le cockpit583
  et l'empreinte, avec les cinq fichiers purs utilisés dans581.
- Nouvelle restauration native :**1test réussi**,29avertissements,**84,49s**,
  code0. JSON/empreinte, CSV, textePDF, valeursExcel et logos identiques après
  reprise ;75tables, schéma/données/ACL/séquences conservés, source préservée,
  cibles supprimées. Preuve585 distincte ; ancienne preuve581 conservée.
- GuidePDF :2pages, mention SHA-256, texte et image présents, bornes de page
  vérifiées. Le générateur583 ne se connecte à aucune base.
- Le dernier build frontend583 (6,37s) reste applicable : aucun frontend modifié
  dans585. Les2Edge sans099 restent une exécution distincte réussie de579.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_ras_tva585_isole.py Test/test_ras_tva_simulation.py Test/test_patch02_tva_service.py Test/test_patch02b_tva_service.py Test/test_montant_decimal_exact_frontend.py Test/test_ras_tva_registre_precision.py -ra
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_restauration_registre_ras_tva_isole.py -ra
```

Les avertissements existants portent sur Pydantic/anyio. PostgreSQL réel non
contacté. L'installation cible099 et la recette utilisateur restent à effectuer.
RAS TVA demeure partielle : crédit imputable, reversement et déclaration
complète ne sont pas déduits de l'empreinte ou du registre.
