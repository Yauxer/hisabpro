# Recette des exports de balances — 8 octobre 2026

## Périmètre livré

Le premier lot fournit CSV, Excel et PDF pour les balances générale, auxiliaire et âgée. Les filtres clients/fournisseurs sont conservés pour les deux dernières. Le complément final décrit plus bas ajoute les exports Résultat et Comparative.

Le classeur reprend les lignes, colonnes, montants numériques et totaux affichés, avec société, devise et période ou date d'arrêté. Les codes de comptes et les noms de tiers restent du texte, y compris un nom commençant par `=`. Les PDF sont produits côté serveur à partir des moteurs de balance définitive et de recouvrement existants : aucun montant client n'est accepté. Le PDF âgé distingue sa date d'arrêté de la période comptable des autres balances.

## Exécution réelle

Commande :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_balances_exports_isole.py Test/test_balance_grand_livre_final.py -x
```

Résultat final : **10 tests réussis en 36,71 secondes**, aucun échec ni test ignoré. Deux scénarios nouveaux utilisent la vraie API FastAPI et PostgreSQL éphémère protégé par nonce ; le premier utilise Microsoft Edge et télécharge réellement dix fichiers, ouverts ensuite avec openpyxl et pypdf. Les huit tests connexes contrôlent le reporting et les interfaces de balance/grand livre existants.

Build Vite : **138 modules, réussi en 5,22 secondes**. Compilation Python du routeur et du service PDF : réussie. Les avertissements existants concernent les bundles Vite et les dépréciations Pydantic/python-multipart.

## Contrôles chiffrés indépendants

Sociétés fictives distinctes ; capital de 10 000 MAD en janvier, vente de 1 200 MAD TTC, achat de 600 MAD TTC et règlement client de 400 MAD en mars. Écritures réellement validées par les routes normales, sans altération d'écritures après validation.

Pour mars : ouverture équilibrée de 10 000 MAD ; mouvements débit/crédit de 2 200 MAD ; soldes finaux débit/crédit de 11 800 MAD. Banque : ouverture 10 000 MAD, débit de mars 400 MAD, solde final 10 400 MAD. Client : débit 1 200 MAD, crédit 400 MAD, solde débiteur 800 MAD. Fournisseur : crédit 600 MAD et solde créditeur 600 MAD. Au 31 mars, les deux factures à échéance du 15 mars sont ventilées dans la tranche 1–30 jours, respectivement 800 et 600 MAD.

Les dix téléchargements couvrent la générale, l'auxiliaire clients/fournisseurs et l'âgée clients/fournisseurs, chacun en Excel et PDF. Les assertions contrôlent les dates, la séparation clients/fournisseurs, les montants, les totaux, les types de cellules et la présence des données dans le texte PDF. Les écritures/lignes comptables avant et après export sont identiques. Aucun appel API 500 ni erreur JavaScript observé pendant le parcours.

Le second scénario vérifie l'accès PDF du rôle lecture, le rejet d'un genre inconnu et d'une période inversée (422), ainsi que l'absence de données de la première société dans le PDF d'une autre société vide.

## Échecs intermédiaires consignés

- Premier run : un échec en 29,29 secondes ; le test saisissait les dates avant la fin de l'initialisation du contexte exercice. Synchronisation avec l'affichage initial et la réponse API de la période demandée, sans changement métier.
- Deuxième run : un scénario réussi et un échec en 33,43 secondes ; le test attendait 400 pour une période inversée alors que le contrôle existant utilise 422. Attente alignée sur le contrat partagé, sans modification de la règle.
- Deux scripts locaux de préparation ont échoué avant l'écriture de Balances.jsx (marqueur Unicode puis syntaxe f-string). Le fichier final a été écrit atomiquement et compilé. Les scripts temporaires ne font pas partie de la livraison.

## Limites et suite

Aucun PostgreSQL réel ni donnée comptable réelle utilisés. Recette utilisateur à réaliser avec les présentations et volumes propres au dossier ; aucune conformité réglementaire automatique revendiquée. Les PDF recomputent les mêmes sources au moment du téléchargement : une écriture validée entre l'affichage et l'export peut légitimement actualiser les montants.

## Complément — libellés de la balance générale

Le défaut certain concernait les comptes historiques inactifs et le PDF : la recherche locale de l'interface recevait déjà le plan actif propre à la société via Layout, et pouvait donc respecter les renommages actifs ; elle excluait les comptes désactivés. Le PDF utilisait exclusivement la référence globale et ignorait le plan société. Le libellé de la générale vient désormais du rapport API : priorité au plan propre à la société, comptes inactifs inclus pour l'historique ; à défaut, référence globale puis nomenclature livrée puis diagnostic « Compte non référencé ». L'écran, Excel et PDF générale utilisent ce même libellé. La résolution emploie deux requêtes groupées limitées aux numéros présents dans la balance ; aucun plan n'est complété et aucune donnée n'est écrite lors d'un export.

Test supplémentaire `test_libelles_societe_inactifs_subdivisions_et_pdf_pagine` : renommer 5141, créer par API 25 subdivisions valides 5141900 à 5141924 avec noms longs, enregistrer et valider une ventilation de 25 MAD, puis désactiver 5141 et une subdivision. Les libellés restent présents dans l'API, l'écran, le vrai classeur téléchargé et le PDF de plusieurs pages. Chaque page conserve l'en-tête. Une autre société utilisant le même 5141 reçoit exclusivement son propre libellé. La subdivision 51399 envisagée n'a pas été utilisée : la racine correspondante n'existe pas dans le plan livré, et la garde métier est conservée.

Même commande ciblée et connexe : **11 tests réussis en 41,21 secondes**, aucun échec ni test ignoré. Build complet : **139 modules, réussi en 5,90 secondes** ; compilation Python routeur/service/test réussie. Les douze téléchargements réels des deux parcours navigateur sont ouverts et contrôlés.

À la livraison de ce complément, Résultat et Comparative utilisaient encore la recherche locale du plan actif. Le lot suivant les aligne également sur les libellés du rapport API avant d'ajouter leurs exports.

## Complément final — Résultat et Comparative

Les cinq onglets ont désormais des exports Excel et PDF. Résultat et Comparative proposent aussi CSV. Les libellés du rapport API sont propagés aux mouvements N et N-1 ; aucune recherche locale indépendante ne remplace un libellé société.

Les définitions déjà présentes sont conservées : Résultat porte sur les charges classe 6 et les produits classe 7 des mouvements de la période ; Comparative compare les nets débit moins crédit des mouvements N/N-1 pour la même période décalée d'un an. Ce document analytique n'est pas présenté comme un bilan comparatif officiel. Les soldes d'ouverture ne sont pas ajoutés aux deux vues. La variation relative utilise la valeur absolue de la base N-1 ; si la base vaut zéro, Excel et PDF affichent N/A. Le classeur conserve une valeur numérique de 25 pour 25 %, avec un format littéral `0.0"%"` : aucune multiplication implicite par cent. Il n'y a pas de total artificiel des variations en pourcentage.

Le PDF serveur réutilise le reporting définitif pour N et N-1. Les deux dates sont décalées comme dans l'interface, avec le dernier jour de février si le 29 n'existe pas dans N-1. Les colonnes PDF occupent 265 mm au total, dans les marges du format A4 paysage. Les libellés sont échappés et les nombres viennent du serveur. Le classeur Résultat comprend les colonnes Charges/Produits, leurs totaux et une synthèse du bénéfice/perte et du résultat net signé.

Nouveau test `test_resultat_comparative_dates_n1_variations_et_exports_reels` : exercice N-1 créé par API, charges de 400 MAD et produits de 600 MAD en mars, comparés aux charges 500 MAD et produits 1 000 MAD de N. Résultat N attendu : 500 MAD. Variation charges : +100 MAD, +25 %. Produits nets crédit : -600 à -1 000 MAD, variation -400 MAD, -66,7 %. Un compte présent uniquement en N produit N/A. Renommages société, dont un libellé commençant par `=`, vérifiés à l'écran et dans les vrais Excel/PDF téléchargés. Vérification de la période mars N/N-1, du format numérique pourcentage et du décalage 29 février 2024 vers 28 février 2023 ; date malformée rejetée en 422.

Même commande ciblée et connexe : **12 tests réussis en 44,97 secondes**, aucun échec ni test ignoré. Les trois parcours Edge téléchargent seize fichiers XLSX/PDF réellement ouverts et contrôlés. Build : **139 modules, réussi en 4,54 secondes**. Compilation Python du routeur, service et test réussie après les dernières modifications. Aucune base réelle utilisée.
