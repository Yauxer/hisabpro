# Recette E2E facturation connectée — 7 octobre 2026

## Périmètre exécuté

Deux parcours navigateur Microsoft Edge sans interface visible utilisent la vraie
application React complète, la vraie API FastAPI `main:app` et PostgreSQL éphémère.
Les API métier ne sont ni interceptées ni remplacées. Seuls les CDN décoratifs
inaccessibles sont interrompus, comme dans la recette administration existante.

Les prérequis sont fictifs : société et tiers créés par HTTP sur cette API isolée.
Chaque parcours crée sa propre société. Aucun `.env`, serveur applicatif réel ou
PostgreSQL existant n'est utilisé. Une garde contrôle URL, marqueur, rôle et chemin
du cluster avant les migrations. Les processus, dossiers et cluster créés par la
recette sont arrêtés/supprimés au `finally`, avec assertions après fermeture.

## Scénarios vente et achat

1. Connexion UI puis création d'un brouillon : deux unités à 500 MAD HT,
   TVA paramétrée à 20 %, total 1 200 MAD TTC. Ce taux sert à tester le calcul
   applicatif sur ce jeu synthétique, sans conclure à son applicabilité juridique.
2. Vérification PostgreSQL : brouillon sans numéro définitif et sans écriture.
3. Validation depuis la liste, puis génération comptable depuis son bouton dédié.
4. Oracle indépendant : vente D3421 1 200 / C7111 1 000 / C4455 200 ;
   achat D6111 1 000 / D34552 200 / C4411 1 200.
5. Virements saisis dans l'UI : 400 puis 800 MAD. Solde 1 200 → 800 → 0 ;
   statuts `partiellement_payee` puis `payee` réellement persistés ; montant du
   second règlement prérempli à 800 sans actualisation manuelle.
6. Chaque écriture est équilibrée ; les lignes du compte collectif conservent
   le tiers technique et son auxiliaire figé.
7. Passage par le Journal pour valider explicitement les trois écritures
   générées en brouillon. La validation facture et la validation comptable sont
   deux opérations distinctes dans le produit.
8. Sélection des trois lignes dans Lettrage, affectation d'un code unique,
   puis rechargement complet et vérification de sa conservation.
9. Les identifiants, comptes, montants et tiers des lignes définitives restent
   strictement identiques après lettrage ; les métadonnées de lettrage sont séparées.

## Commandes et résultats réellement exécutés

Commande ciblée depuis la racine :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_facturation_isole.py -x
```

Résultat ciblé avant renforcement des deux assertions d'oracle/immutabilité :
**2 réussis, 0 échec, 0 ignoré, 25,46 s**.

Les sept exécutions précédentes ont échoué pendant la construction du banc :
trois timeouts de validation causés par les fonctions de numérotation absentes
du fixture initial ORM + 036 ; une erreur de doublon de référence après
installation des migrations ; une assertion supposant à tort les écritures déjà
définitives ; une comparaison textuelle `1200`/`1200.00` ; un clic avant chargement
des écritures dans le Journal. Ces échecs ont été corrigés dans le test sans
modifier le comportement métier. La toute première commande utilisant `.venv`
à la racine échouait avant pytest : l'environnement réel est sous le backend.

Le fixture applique désormais la liste de migrations PostgreSQL déjà utilisée
par `test_session132_operations_postgres.py`, en complément du support E2E.
Les comptes absents sont ajoutés de façon idempotente au référentiel isolé.

Commande finale après renforcement des assertions :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_facturation_isole.py Test/test_e2e_administration_isole.py Test/test_e2e_balance_isole.py Test/test_e2e_isole_guard.py
```

Résultat : **6 réussis, 0 échec, 0 ignoré, 62,72 s** : deux parcours facturation,
deux parcours administration, un parcours balance/exports et une garde.
25 avertissements de dépréciation existants Pydantic/multipart.

Compilation : `.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile Test/test_e2e_facturation_isole.py`
— **OK**, code retour 0.

## Limites

- Aucune validation sur PostgreSQL réel ; aucune donnée comptable réelle modifiée.
- Ce lot couvre factures vente/achat, virements partiels/complets, journal et lettrage.
- Devis/BC/BL, avoirs, acomptes, chèques/effets, impayés, annulation, exports de
  facture, stocks, banques et clôture annuelle restent hors de ces deux parcours.
- Les données légales manquantes de la société fictive produisent les
  avertissements du produit ; aucune donnée légale n'est inventée pour les masquer.
- La compilation esbuild du support remplace le serveur Vite pendant cette recette.
  Le démarrage Vite et les ressources CDN ne sont pas validés par ce test.
- Recette utilisateur intégrale, conformité officielle et mise en production
  ne sont pas déclarées validées.
