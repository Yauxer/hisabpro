# Consultation des notes de devis — 8 octobre 2026

## Analyse et périmètre

La fonctionnalité existe déjà dans `Commercial.jsx` : le bouton « Voir détail / note » ouvre le détail des lignes et la note multiligne. Les formulaires de création et d'édition saisissent les notes. La route PDF transmet les notes du devis brouillon ou leur snapshot documentaire après acceptation. Aucune réimplémentation ni modification applicative n'est nécessaire pour ce périmètre.

Les devis existent dans le cycle Vente. Le cycle Achat commence par les bons de commande et ne contient pas d'onglet devis ; l'API DevisCreate ne possède aucun type achat/vente et résout un client. Le test vérifie cette navigation réelle, sans déclarer un devis achat testable. Un éventuel devis fournisseur nécessiterait une décision de périmètre distincte.

## Test réel

Deux parcours indépendants sont exécutés dans Microsoft Edge aux largeurs 1365 et 390 pixels, avec FastAPI et PostgreSQL éphémère protégé par nonce. Les sociétés et clients sont fictifs, créés par API ; aucune base réelle ni donnée comptable réelle n'est touchée.

Le navigateur crée un devis de deux prestations à 100 HT, TVA 20 %, TTC 240. Note initiale exacte :

```text
Offre valable trente jours.
Livraison sur rendez-vous.
```

Le bouton de consultation reçoit le focus puis est activé par Entrée ; la note doit être visible. Le formulaire d'édition recharge cette note puis enregistre :

```text
Offre valable trente jours.
Livraison sur rendez-vous confirmé.
```

La nouvelle note apparaît sans F5 et l'ancienne disparaît. Après acceptation et rechargement, le détail présente encore la note exacte. Le PDF est réellement téléchargé, ouvert par pypdf et contrôlé : note finale complète, numéro du devis et montant 240,00. L'aller-retour Achat/Vente vérifie l'absence de devis en Achat et la consultation persistante en Vente. La liste API et la lecture PostgreSQL confirment la note ainsi que son snapshot accepté. Le nombre d'écritures comptables reste zéro. Aucune erreur JavaScript ni réponse API 500 n'est observée.

## Commandes et résultats

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_devis_notes_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_devis_notes_isole.py
```

Premier run : **1 échec en 32,08 s**, avant création du devis. Le test reprenait le placeholder et la classe de l'éditeur de factures ; le cycle commercial utilise « Article ou description... » et `.hp-commercial-line-editor`. Les sélecteurs ont été corrigés uniquement dans le nouveau test après inspection du composant.

Second run : **2 réussis en 23,73 s, exit 0**. Compilation Python : exit 0. Aucun fichier applicatif modifié ; le fixture a construit l'application pour le test réel. Les avertissements Pydantic/python_multipart sont ceux des dépendances existantes.

## Limites

Ce lot couvre les notes de devis vente en création, édition brouillon, consultation et document accepté. Il ne prouve pas tous les scénarios d'accessibilité ni toutes les tailles d'écran. Après acceptation, le PDF utilise le snapshot des notes documentaires ; une modification interne ultérieure ne fait pas partie du scénario. Le devis achat n'existe pas dans le périmètre actuel. La recette utilisateur sur son propre dossier et toute validation réglementaire restent distinctes.
