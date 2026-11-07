# Annexe utilisateur — achats partiels, règlements et lettrage

Lot `ANNEXE-RECETTE-ACHATS-PARTIELS-20261009-284` ; six nouveaux fichiers, aucun module applicatif modifié.

## Contenu et limites

Annexe autonome du cahier de recette : deux cas **Non testé** (cycle complet et protections contre reconversion/édition définitive). Les colonnes résultat réel, anomalies et observations restent vides. Les preuves à conserver sont décrites sans être préremplies. Les tests développeur ne constituent pas une recette utilisateur validée.

La société fictive neuve, le fournisseur, l’article, les comptes, dates, références, réglage du stock et choix TVA sont précisés. Le scénario utilisateur suit les interfaces existantes : paramètre stock au BR, commande de quatre unités, deux BR de une et trois unités, factures fournisseurs de 600/1 800, paiements par virement de 600/1 800 puis lettrage commun des quatre lignes 4411. La qualification charge/TVA déductible 100 % est une donnée de laboratoire, sans nouvelle règle réglementaire.

Le formulaire « Payer le fournisseur » n’expose ni compte comptable ni case de comptabilisation : cette annexe indique le virement avec Banque vide dans cette société vierge, puis le contrôle de la contrepartie 5141 générée automatiquement. Les deux écritures de règlement sont ensuite explicitement validées dans le Journal. Une contrepartie différente exige le statut Bloqué et la documentation du paramétrage, sans ajuster l’oracle.

Oracle Decimal indépendant du moteur : HT 2 000, TVA 400, TTC 2 400 ; quatre écritures et dix lignes, débit = crédit = 4 800 ; soldes débit moins crédit 6111 = 2 000, 34552 = 400, 4411 = 0, 5141 = −2 400 ; stock final quatre, exactement deux entrées de une et trois unités. Le solde banque créditeur vient de l’absence d’ouverture dans le laboratoire ; aucun apport inventé n’est ajouté pour le masquer. Le cas négatif décrit un bouton indisponible ou un refus compréhensible, sans demander API/SQL à un non-développeur.

Le rapport du lot 283, lu dans le dépôt, mentionne **2 Edge réussis en 33,67 s** puis **8 ciblés/connexes réussis en 118,89 s**. Ces résultats sont exécutés par l’autre agent et distingués des vérifications documentaires ci-dessous. La cause de l’échec mobile de la précédente suite globale n’est pas présentée comme prouvée par cette annexe.

## Commandes exécutées ici

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_annexe_recette_achats_partiels_284.py --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_annexe_recette_achats_partiels_284.py Test/test_annexe_recette_corrections_277.py --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/generer_annexe_recette_achats_partiels_284.py
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/generer_annexe_recette_achats_partiels_284.py Test/test_annexe_recette_achats_partiels_284.py
```

Premier ciblé : **3 passed en 0,70 s**. Après relecture du formulaire et des espaces de prose, ciblés/connexes finaux : **6 passed en 1,02 s, exit 0**, aucun échec, erreur ou test ignoré. Deux reprises intermédiaires du même périmètre ont passé en 1,04 et 1,03 s ; les dernières sources sont celles du run 1,02 s. Compilation Python et génération effective MD/PDF/XLSX : **exit 0**. Aucun test métier connecté ni build applicatif supplémentaire n’est annoncé pour ce lot strictement documentaire.

Les tests ouvrent réellement le PDF avec pypdf et le classeur avec openpyxl : identifiants, chiffres, sources existantes, statuts, résultats réels vides, validation des statuts, filtres/volets et formules de synthèse sont contrôlés. Les valeurs des oracles Excel sont numériques. Le classeur propose les feuilles Synthèse, Achats et Jeu de données ; les deux cas restent Non testé.

Rendu PDF avec PyMuPDF : six pages A4, aucun bloc de contenu en dehors des marges contrôlées. La page des actions principales et écritures a été examinée visuellement ; texte lisible, pas de tableau ni ligne comptable tronqués. Les PNG de contrôle restent temporaires dans `.codex-tests`, exclus du ZIP. Les artefacts finaux sont regénérés après amélioration des espaces et libellés exacts.

## Livraison

- `Test/generer_annexe_recette_achats_partiels_284.py`
- `Test/test_annexe_recette_achats_partiels_284.py`
- Ce rapport.
- `docs/recette/ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.md`
- `docs/recette/ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.pdf`
- `docs/recette/ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.xlsx`

Aucune base, donnée réelle, migration ou application n’est modifiée. Le journal et le ZIP différentiel vérifié sont assurés par l’agent principal. Recette utilisateur et contrôle du paramétrage réel restent à effectuer dans l’environnement autorisé.
