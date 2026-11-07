# Recette connectée clôture et à-nouveaux — 7 octobre 2026

La vraie interface React compilée localement a été parcourue dans Edge headless,
avec FastAPI réellement authentifié et PostgreSQL éphémère. Aucun appel métier
ni réponse API n'est simulé. Aucun fichier `.env`, serveur PostgreSQL existant
ou donnée comptable réelle n'est utilisé.

Le contexte `application` de `test_e2e_facturation_isole.py` applique les
migrations déjà éprouvées sur un cluster neuf identifié par nonce, chemin,
rôle, nom et port loopback distinct de 5432. La sortie de fixture contrôle
l'arrêt des serveurs et la suppression des seuls répertoires éphémères créés.

## Parcours et oracle

Les prérequis proviennent du scénario API existant session132 : achat de dix
unités à 100 HT, vente de quatre unités à 200 HT, règlement client de 360,
avoir d'une unité et inventaire final de sept unités valorisées à 700.
Un apport synthétique de 10 000 est ajouté en brouillon. Le résultat avant
impôt est calculé indépendamment : ventes nettes 600 − achats 1 000 + stock
final 700 = 300. L'impôt automatique de 3 000 reprend strictement l'hypothèse
du test session133, sans nouvelle règle ou taux fiscal ; résultat net −2 700.

Parcours navigateur exécuté : connexion, sélection 2025, bouton clôture
désactivé à cause du brouillon, validation définitive dans le Journal,
retour Clôture avec contrôle FEC favorable, confirmation de clôture, affichage
du statut définitif, sélection 2026, Journal AN, rechargement et persistance
de la sélection 2026.

Vérifications PostgreSQL et API réelles : toutes les périodes 2025 fermées,
trace de clôture, écritures d'activité soldées, lignes originales inchangées,
à-nouveaux définitifs avec tiers et snapshots auxiliaires, contrôles FEC des
deux exercices et exports HTTP 200, refus de double clôture HTTP 400 et de
nouvelle écriture datée en 2025 HTTP 423. Aucune erreur JavaScript ou HTTP 5xx.

| Compte AN 2026 | Débit − crédit attendu, MAD |
| --- | ---: |
| 1111 | −10 000 |
| 3111 | 700 |
| 3421 | 360 |
| 34552 | 200 |
| 4411 | −1 200 |
| 4453 | −3 000 |
| 4455 | −120 |
| 5141 | 10 360 |
| 1199 | 2 700 |

Total débit = total crédit = 14 320 MAD ; somme des soldes = zéro.

## Commandes réellement exécutées

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_cloture_isole.py -x
```

Essai final : **1 réussi, 0 échec, 0 ignoré, 19,48 s**. Les trois essais
précédents ont échoué uniquement sur le montage du test : sélecteur AN ambigu
(20,65 s), label de sélection absent sur Journal (39,52 s), puis lecture avant
chargement du sélecteur (18,51 s). Ils ne sont pas comptés comme réussites.
Aucune correction du produit n'a été nécessaire.

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_cloture_isole.py Test/test_session133_cloture_postgres.py
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile Test/test_e2e_cloture_isole.py
```

Non-régression finale : **3 réussis, 0 échec, 0 ignoré, 33,23 s** : ce parcours
navigateur et les deux scénarios PostgreSQL clôture session133, dont les soldes
auxiliaires individuels opposés malgré un collectif nul. Compilation : OK.

## Limites

Scénario réduit synthétique ; les achats, ventes et l'inventaire préalables
sont préparés par API, pas parcourus dans cette UI. Le test ne couvre pas
l'exercice annuel complet, l'affectation du résultat, les régularisations,
les immobilisations, l'archivage du dossier fiscal ou la recette humaine.
L'export FEC est contrôlé par le moteur existant et son statut HTTP ; ce test
ne remplace pas une certification réglementaire ni un audit exhaustif du
contenu. Les avertissements de dépréciation Pydantic/multipart restent visibles.
