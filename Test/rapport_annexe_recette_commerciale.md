# Lot 247 — Annexe de recette commerciale

## Livrables et périmètre

Annexe autonome PDF/XLSX/Markdown, complément des cahiers annuel et GRH sans modification de leurs fichiers. Les données sont fictives et les cinq cas ne sont pas prévalidés : quatre « Non testé », un « Bloqué ». Aucun accès à PostgreSQL ni modification de données métier par le générateur ou ses tests.

- COM-001 : deux lignes du même produit, 3 + 3 unités demandées pour un stock physique de 5, et un service non stockable. Alerte manque 1, devis autorisé sans réservation ; HT 70,00, TVA 14,00, TTC 84,00 MAD.
- COM-002 : modification en 1 + 1 unité du produit et 1 service ; HT 30,00, TVA 6,00, TTC 36,00 MAD, stock physique inchangé à 5.
- COM-003 : devis accepté → commande → BL en préparation, puis dépôt/relecture de PDF et PNG fictifs. Comparaison des états avant/après le dépôt, sans confirmer l’expédition ni créer une facture.
- COM-004 : lecture/téléchargement sans dépôt ni suppression, isolation d’une seconde société par l’interface.
- COM-005 : stock historique NULL, initialement bloqué car sa préparation nécessite un opérateur sur laboratoire isolé. Aucun champ UI fictif, aucune correction de données réelles, aucun zéro inventé.

Le classeur conserve les résultats réels, anomalies et observations vides ; les preuves attendues sont renseignées. Six feuilles, listes de validation des statuts et tableau de synthèse COUNTIF. Le PDF comporte 12 pages. Les numéros réels générés doivent être relevés pendant la recette, sans forcer un format.

## Vérifications réellement exécutées

Environnement Python : `hisabpro-backend/.venv/Scripts/python.exe`. Le premier appel visant `.venv/Scripts/python.exe` à la racine n’a pas exécuté de tests : chemin inexistant. L’appel avec le Python système a donné 1 réussite / 3 échecs : dépendance openpyxl absente de cet environnement et assertion visant le champ contrôles au lieu du prérequis. Aucun test réussi n’en a été déduit. L’assertion a été corrigée et l’environnement du dépôt utilisé.

Commande finale ciblée et connexe, avec `PYTHON_DOTENV_DISABLED=1` :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py -q Test/test_annexe_recette_commerciale.py Test/test_annexe_recette_grh.py
```

Résultat : **4 tests réussis**, code de sortie 0 (2,74 s, puis 2,07 s après clarification rédactionnelle du cas NULL). Les deux tests nouveaux vérifient les identifiants, les statuts, les champs attendus et les calculs Decimal indépendants, puis génèrent et ouvrent réellement PDF/XLSX/Markdown. Les deux tests GRH connexes restent réussis sans modification du cahier GRH.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/generer_annexe_recette_commerciale.py
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/generer_annexe_recette_commerciale.py Test/test_annexe_recette_commerciale.py
```

Génération et compilation : code de sortie 0. Réouverture indépendante des artefacts livrables par pypdf/openpyxl : **12 pages PDF, 6 feuilles XLSX, 5 cas dont 4 Non testé / 1 Bloqué, résultats/anomalies/observations tous vides**.

## Limites et reprise

Ces contrôles valident la fabrication et la cohérence du cahier ; ils ne réalisent pas la recette utilisateur dans le navigateur. Les alertes et pièces client doivent être livrées ensemble avant cette recette. COM-005 reste bloqué sans opérateur/laboratoire dédié. Les valeurs extrêmes de quantité restent des tests développeur et ne sont pas proposées à une personne non développeuse. Aucun changement fiscal, aucune certification ou conformité réglementaire affirmée.

Prochaine étape : suivre COM-001 à COM-004 dans un dossier fictif, inscrire résultats et preuves dans Excel, puis préparer COM-005 seulement dans un laboratoire isolé.
