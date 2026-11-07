# Annexe utilisateur du bilan détaillé

Lot `ANNEXE-RECETTE-BILAN-20261008` (262), 8 octobre 2026.

Livrables PDF, XLSX et Markdown : `docs/recette/ANNEXE_RECETTE_BILAN_DETAILLE`. Quatre cas : N-1 absent, N-1 présent, exports et ancienne archive. Tous restent **Non testé** dans le suivi utilisateur ; les résultats automatisés du lot 256 ne prévalident pas cette recette.

Le jeu fictif indépendant reprend les six immobilisations brutes (1 000 à 6 000), les stocks 7 000, le client 8 000 et la banque 9 000 : brut 45 000, amortissements 300, net actif/passif 44 700 MAD. La variante N-1 comporte banque/capital 75 ; son ouverture N de 75 est complétée par banque 8 925 et capital 44 625, pour conserver les mêmes totaux N sans doubler l'ouverture. Les écritures sont explicitement des reprises fictives, aucune facture, acquisition, dotation fiscale ou TVA supplémentaire n'est présumée. Le client auxiliaire doit être réellement sélectionné sur 3421. Une archive ancienne absente rend le quatrième cas Bloqué, sans fabrication de snapshot.

Commandes réellement exécutées :

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/generer_annexe_recette_bilan.py
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_annexe_recette_bilan.py --tb=short
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_annexe_recette_bilan.py Test/test_annexe_recette_commerciale.py Test/test_annexe_recette_grh.py --tb=short
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/generer_annexe_recette_bilan.py Test/test_annexe_recette_bilan.py
```

Génération OK ; **2 tests ciblés réussis en 0,81 s**, puis **6 ciblés et connexes réussis en 1,59 s** ; compilation OK. Les tests ouvrent réellement les PDF et XLSX temporaires, contrôlent les calculs, identifiants, champs nécessaires, statuts, validations et formules de suivi. Les trois livrables générés dans le dépôt ont ensuite été ouverts et vérifiés avec pypdf, openpyxl et lecture UTF-8. Aucun échec ou test ignoré.

Aucun accès à une base, navigateur ou serveur applicatif pour ce lot documentaire. Aucun résultat de recette humaine n'est déclaré réussi. Le générateur ne modifie ni application ni cahiers déjà livrés.

Différentiel : générateur, test, ce rapport et trois livrables. Journal et vérification du ZIP par l'agent principal.
