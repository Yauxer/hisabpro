# Recette — Numérotation interne de la liasse HisabPro

Lot : `LIASSE-NUMEROTATION-INTERNE-20261007` — 7 octobre 2026.

Demande confirmée par l'utilisateur : repérer le bilan, le CPC et les 23 sections ETIC existantes par T1 à T25. Ce repérage est **interne HisabPro**, distinct de la codification DGI. Il n'ajoute aucun tableau fiscal officiel et n'active aucun export EDI/XML.

## Résultat

| Tableau interne | Document / code d'origine |
|---|---|
| T1 | Bilan, actif et passif |
| T2 | CPC |
| T3, T4, T5 | ETIC A1, A2, A3 |
| T6, T7, T8 | ETIC B1, B2, B2bis |
| T9, T10, T11 | ETIC B3, B4, B5 |
| T12, T13, T14 | ETIC B6, B7, B8 |
| T15, T16, T17 | ETIC B9, B10, B11 |
| T18, T19, T20 | ETIC B12, B13, B14 |
| T21, T22, T23, T24, T25 | ETIC C1, C2, C3, C4, C5 |

La correspondance est partagée par l'interface, l'export Excel et le PDF dans un fichier JSON unique. Les sections sont identifiées par leur code d'origine, indépendamment de l'ordre reçu et des sections absentes. Les anciens codes inconnus restent affichés sans numéro inventé. ESG, financement et fiscalité gardent leurs titres.

Dans le classeur : `T1 Bilan Actif`, `T1 Bilan Passif`, `T2 CPC` ; la feuille ETIC conserve tous ses contenus et présente chaque section sous la forme `T12 / B6`. Les onglets et titres du cockpit utilisent le même repérage. Les PDF conservent les codes ETIC d'origine.

Les API, migrations, montants, références comptables, snapshots et empreintes SHA-256 sont inchangés. Une ancienne archive se présente avec les nouveaux libellés sans réécrire son contenu.

## Tests exécutés ici

Commandes lancées avec le runner isolé, sans lecture des connexions réelles :

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_liasse_numerotation_interne.py Test/test_patch120_liasse_exports_ventilations.py Test/test_patch131_liasse_pdf_identite.py Test/test_patch09_3_liasse_fiscale.py Test/test_patch102_liasse_financement_n1.py
```

**24 tests réussis en 1,95 s**, aucun échec et aucun test ignoré. Correspondance complète T1–T25 avec le catalogue réel ; B2bis = T8 ; fallback ancien code ; sections reçues dans l'ordre inverse ; génération et relecture d'un vrai PDF ; génération et relecture d'un vrai XLSX ; conservation des montants, diagnostics B6/B7, contenu extra-comptable et empreinte d'archive.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_archive_liasse_isole.py
```

**1 test E2E réussi en 20,11 s**, aucun échec ni test ignoré. Edge → vraie API → PostgreSQL éphémère, protégé par le banc existant `verifier_cible_isolee` ; aucune connexion au PostgreSQL réel. Finalisation d'une société fictive, affichage des onglets T1/T2 et des sections T3/T8/T25 avec leurs codes d'origine, téléchargements PDF/Excel, archive verrouillée, SHA-256 vérifiée, codes originaux conservés dans le snapshot. Les processus et dossiers temporaires du banc sont arrêtés et nettoyés par la fixture ; son contrôle de fin est passé.

```text
npm run build
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile hisabpro-backend/services/liasse_presentation.py hisabpro-backend/services/liasse_pdf.py Test/test_liasse_numerotation_interne.py Test/test_patch120_liasse_exports_ventilations.py Test/test_e2e_archive_liasse_isole.py
```

**Build Vite réussi**, 134 modules ; avertissements existants de taille du bundle et d'import XLSX. **Compilation Python réussie** sur les cinq fichiers. Avertissements E2E : dépréciations Pydantic et python-multipart, aucun impact observé sur ce lot.

La première tentative `apply_patch` a été rejetée atomiquement sur une ligne JSX, puis corrigée. Une commande annexe `git diff --stat` a échoué parce que ce dossier n'est pas un dépôt Git ; la compilation a été exécutée seule ensuite avec code de sortie 0. Ces commandes ne sont pas des tests réussis.

## Livraison et limites

Fichiers de ce lot, à inclure avec `CODEX_PROGRESS.md` dans le ZIP différentiel préparé par l'agent principal :

- `hisabpro-backend/services/liasse_numerotation_interne.json`
- `hisabpro-backend/services/liasse_presentation.py`
- `hisabpro-backend/services/liasse_pdf.py`
- `src/utils/liassePresentation.js`
- `src/pages/LiasseFiscale.jsx`
- `Test/test_liasse_numerotation_interne.py`
- `Test/test_patch120_liasse_exports_ventilations.py`
- `Test/test_e2e_archive_liasse_isole.py`
- `Test/rapport_liasse_numerotation_interne.md`

Recette utilisateur à effectuer sur les dossiers réellement archivés et sur le choix des libellés. Aucune validation du PostgreSQL réel ni de conformité réglementaire n'est revendiquée. Le référentiel exhaustif DGI et la validation officielle du schéma EDI restent des sujets séparés, documentés dans l'audit de couverture.

Prochaine tâche indépendante : anomalies de factures partiellement payées en retard / lettrage sur trois lettres, puis approfondissement acomptes et RAS selon règles officiellement documentées. Le journal de session et le ZIP sont finalisés uniquement par l'agent principal.
