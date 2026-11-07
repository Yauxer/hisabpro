# Annexe des corrections récentes — lot 277

Complément documentaire aux 218 cas annuels et aux annexes commerciale, GRH et
bilan, lus avant rédaction. Aucun scénario annuel recalculé ou remplacé.
Huit cas **Non testé**, quatre sociétés fictives séparées, cinq domaines :
Articles (3), Paramètres (1), Achats (2), Comptabilité (1), Banques (1).

Les parcours décrivent les champs réellement exposés dans les sources des lots
268–275. La saisie bancaire ne réclame pas de référence séparée inexistante.
Le préfixe et le modèle sont distincts ; les paramètres ne réécrivent pas les
anciens titres. Les frais article ne sont pas supposés automatiquement reportés
dans une facture. Les achats à 80 % et à 0 % sont deux brouillons distincts.
Les courses HTTP déterministes restent des contrôles techniques de laboratoire,
pas une manipulation JSON/SQL demandée au lecteur non développeur.

Oracles `Decimal` indépendants, sans import des moteurs HisabPro ni accès DB :
HT 1 000, TVA 200, TTC 1 200 ; charge 1 040 et TVA déductible 160 à 80 % ;
charge 1 200 à 0 % ; ouverture bancaire 1 000, crédit mars 200, solde final 800.
Frais article par unité : 9,75 puis 12,25. Ces pourcentages sont des données
explicites de laboratoire, aucune règle légale nouvelle.

## Exécution réelle

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/generer_annexe_recette_corrections_277.py
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_annexe_recette_corrections_277.py Test/test_annexe_recette_bilan.py Test/test_annexe_recette_commerciale.py Test/test_annexe_recette_grh.py --tb=short
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/generer_annexe_recette_corrections_277.py Test/test_annexe_recette_corrections_277.py
```

- Génération PDF/XLSX/MD : code 0.
- Tests finaux : **9 passed, 1,72 s**, code 0 ; dont trois nouveaux tests 277.
- Compilation Python : code 0.
- PDF livré réellement ouvert par `PdfReader` : **18 pages**, huit identifiants,
  textes et montants lus ; aucune recette utilisateur présentée réussie.
  Rendu PyMuPDF des pages 1 (jeu), 11 (TVA achat) et 17 (rapprochement) dans
  `.codex-tests/recette277-visuel` ; pages réellement vues, lisibles sans texte
  tronqué. Les titres restent avec leur paragraphe après ajustement documentaire.
- Excel livré réellement ouvert par `load_workbook` : **7 feuilles**, huit cas
  Non testé, cellules d'oracle numériques 1 040/160/800, colonnes résultat réel,
  anomalies, preuves et observations, validation de statuts, filtres, synthèse
  avec formules de progression. Les formules seront recalculées à l'ouverture
  par le tableur ; aucune progression utilisateur calculée ici comme réussite.
- Markdown lu dans les tests : huit statuts Non testé et liens vers toutes les
  sources présentes. Aucun taux fiscal importé ou vérifié comme droit applicable
  à une société réelle pendant ce lot.

Échecs déclarés : la première tentative d'écriture du générateur le 8 octobre
a été interrompue avant exécution par une limite d'utilisation ;
ce n'était pas un rejet de sécurité ni une demande de permission.
aucun fichier 277 existant n'a été retrouvé lors de la reprise. Premier test du
9 octobre : **1 failed, 2 passed, 1,25 s**, assertion textuelle « distincte »
absente du prérequis disant déjà « nouvelle facture ACH0-277 ». Prérequis
clarifié ; première relance **9 passed, 1,84 s**. Après précision des champs UI
et de la saisie bancaire : 9 passed, 1,56 s. Après revue, le cas bancaire attend
la confirmation de sauvegarde de chaque solde et limite la protection contre
une réponse obsolète à une autre période/société/compte, sans promettre la
protection des champs non sauvegardés contre une lecture de même portée :
9 passed, 1,53 s. Après ajustement des titres PDF : 9 passed, 1,84 s.
Après remplacement des clés internes par des libellés français dans PDF et
en-têtes Excel (positions et formules inchangées), résultat final ci-dessus.
Documents livrés rouverts ; nouveaux en-têtes vérifiés et page TVA rerendue/vue.

## Périmètre et livraison

Six fichiers nouveaux : générateur, test, ce rapport et
`docs/recette/ANNEXE_RECETTE_CORRECTIONS_20261009.{md,pdf,xlsx}`.
Aucune modification de l'application, des autres cahiers, du journal ou d'une
base. Aucun nouveau test PostgreSQL/E2E exécuté dans ce lot documentaire ; les
tests de correction antérieurs sont liés comme preuves distinctes, pas relancés.
La recette utilisateur reste à effectuer. Sans prérequis, déclarer Bloqué avec
motif. Préparation/vérification du ZIP différentiel assurée par l'agent principal.
