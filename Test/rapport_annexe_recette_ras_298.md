# Annexe de recette — RAS estimée et paiements réels

Lot 298 — 9 octobre 2026. Deux cas utilisateur **Non testé**, dans deux sociétés fictives neuves et indépendantes : vente et achat. Les parcours ne réutilisent aucune donnée annuelle ni réelle. Ils complètent le cahier principal et les annexes existantes sans les réécrire.

## Livrables et périmètre

- `Test/generer_annexe_recette_ras_298.py` : générateur autonome, aucune connexion à une base, aucun import de moteur métier.
- `Test/test_annexe_recette_ras_298.py` : oracles et documents ouverts réellement.
- `docs/recette/ANNEXE_RECETTE_RAS_ESTIMATION_20261009.md` : parcours lisible et liens vers les sources présentes.
- PDF du même nom : **6 pages**, en-têtes et rubriques en français.
- Classeur du même nom : **Synthèse**, **Recouvrement**, **Jeu de données** ; deux statuts Non testé, résultats réels, anomalies, preuves réelles et observations laissés vierges. Les preuves attendues disposent d’une colonne distincte.
- Présent rapport.

Les taux TVA 20 % et RAS 10 % sont explicitement choisis pour le laboratoire. Leur applicabilité fiscale n’est pas affirmée. La capture d’une retenue opérée, les attestations et les futurs parcours de saisie correspondants ne sont pas présentés comme disponibles dans cette annexe. Une donnée historique inconnue conduit à un diagnostic et une vérification contrôlée ; aucune manipulation SQL ou NaN n’est demandée au lecteur utilisateur.

## Oracle indépendant

Les montants sont calculés avec `Decimal`, sans importer les services de l’application : HT 1 000 + TVA 200 = TTC 1 200 ; RAS estimée 100 et net estimé 1 100. L’estimation ne diminue pas le solde : avant paiement 1 200, après virement de 1 100 reste 100, après second virement de 100 reste zéro. RAS imputée attendue : zéro.

Pour chaque société : une facture et deux virements, trois écritures, sept lignes ; total débit = crédit **2 400**. Client 3421 ou fournisseur 4411 soldé, banque 5141 respectivement **+1 200 / −1 200**, sans apport initial. Aucune ligne 3453/4457 ni OD de RAS. Les trois lignes du tiers sont à lettrer sous un code commun ; AAA est attendu exclusivement dans une société vierge sans lettrage antérieur. Les actions précisent les boutons, références, dates, validations et preuves à conserver.

## Exécutions réelles

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/generer_annexe_recette_ras_298.py
```

Sortie 0, PDF/XLSX/MD générés. Après amélioration des libellés d’oracle du PDF et des espaces des instructions, régénération également réussie.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_annexe_recette_ras_298.py Test/test_annexe_recette_achats_partiels_284.py Test/test_annexe_recette_corrections_277.py --tb=short
```

Premier passage : **9 réussis en 1,61 s**. Après les changements de présentation : **9 réussis en 1,59 s**. Dernier passage après ajout des références de preuve du lot 304 : **9 réussis en 1,56 s**, sortie 0, aucun échec ou test ignoré. Trois tests nouveaux, six tests connexes des annexes 284/277. Vérifications : arithmétique indépendante, sociétés distinctes, absence de résultat prévalidé, colonnes/formules de suivi, suivi vierge, sources existantes et ouverture réelle des documents générés.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/generer_annexe_recette_ras_298.py Test/test_annexe_recette_ras_298.py
```

Compilation sortie 0. Les livrables du dépôt ont été ouverts séparément avec PyMuPDF et openpyxl : 6 pages PDF, les trois onglets attendus, K2/K3 = Non testé et N2/N3 vides. Les pages PDF **1 et 3** ont été rendues puis inspectées visuellement : texte lisible, rubriques et étapes non tronquées. Images temporaires dans `.codex-tests/recette298-visuel/`, exclues du livrable. Première ouverture : avertissement de dépréciation de l’alias `fitz`. Dernière ouverture et rendu, avec l’import `pymupdf`, réussis sans cet avertissement après ajout des sources 304 ; PDF final 6 pages et référence 304 présente, onglets et suivi vierge conservés.

## Limites

Cette étape valide les documents et les oracles, **pas l’exécution utilisateur des deux parcours**. Aucun E2E de l’application, build ou PostgreSQL réel n’a été lancé par cet agent pour ce lot documentaire. L’agent principal a transmis une preuve complémentaire distincte, lot 304 : `Test/test_e2e_ras_solde_lettrage_isole.py`, quatre cas Edge vente/achat 1 365/390 réussis en 49,81 s, avec deux virements UI, validation des écritures et lettrage trois lignes AAA. Son rapport est `Test/rapport_e2e_ras_solde_lettrage.md` ; ces deux sources sont référencées dans l’annexe. Il s’agit d’un résultat exécuté par l’agent principal, pas par cet agent ni par un utilisateur. Les cas de ce classeur restent Non testé jusqu’à une recette humaine. Aucun fichier applicatif, migration ou historique comptable modifié. Journal et ZIP différentiel : agent principal.
