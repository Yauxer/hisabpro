# Montée de version de la base locale `hisabpro` — lot 961 (30 octobre 2026)

L'utilisateur a indiqué que la base locale ne contient que des données de test et a autorisé ce travail.
**La base locale n'a pas été modifiée** : tout a été fait sur une copie restaurée dans un cluster PostgreSQL éphémère isolé.

## 1. Ce qui a été testé sur la copie

| Contrôle | Résultat |
|---|---|
| Copie : `pg_dump` avec propriétaires et droits, par le rôle applicatif | Réussie, 723 Ko. Exclusions dues aux droits du rôle applicatif : table `decisions_affectation_resultat` (structure recréée depuis le modèle, contenu non testé) et valeurs de 2 séquences (recalées sur le plus grand identifiant) |
| Restauration fidèle (rôles `postgres` et `hisabpro` recréés) | Réussie |
| `constater --jusqua 70` | 64 scripts enregistrés. Réparations historiques 065, 067 et 070 ni enregistrées ni rejouées |
| `appliquer --suivantes` | **60 scripts, 071 → 130, sans erreur** ; 70 → 112 tables |
| Second `appliquer --suivantes` | Aucun script réexécuté |
| Données existantes | Toutes les tables d'origine sont identiques, sauf ajouts de la migration 092 (+5 modèles d'écriture « avance au personnel », +10 lignes ; insertions uniquement) |
| Écritures validées déséquilibrées | 0 |
| API sous le rôle `hisabpro` (comme en production) | 94 routes GET × 5 couples société/exercice, plus TVA mensuelle, FEC, états, ETIC, clôture et grand livre : **666 requêtes, 0 erreur serveur, journal sans erreur** |
| Refus 409 observés | 96 : Personnel/Paie, dont la protection n'est pas activée (hors MVP, attendu). 8 : export FEC 2026/2027 bloqué par les contrôles Avis n°24 à cause d'anomalies **dans les données de test** (refus voulu, à traiter côté données) |

Outil rejouable : `python -X utf8 ops/verifier_montee_version_copie.py <sauvegarde.dump> <dossier_rapport>`.

## 2. Procédure pour la base locale (PowerShell)

À exécuter par vous, avec le rôle d'administration `postgres`. Le rôle applicatif ne peut pas modifier les tables appartenant à `postgres`.

1. Arrêter le backend HisabPro.
2. Sauvegarde complète, à conserver hors du dépôt :
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -Fc -f "C:\Users\Y_N_e\hisabpro_avant_961.dump" hisabpro
   ```
3. Optionnel mais recommandé : rejouer la vérification sur cette sauvegarde complète.
   ```powershell
   .\hisabpro-backend\.venv\Scripts\python.exe -X utf8 ops\verifier_montee_version_copie.py "C:\Users\Y_N_e\hisabpro_avant_961.dump" "C:\Users\Y_N_e\rapport_961"
   ```
4. Montée de version, avec la connexion d'administration dans une variable et jamais en argument :
   ```powershell
   $env:HISABPRO_MIGRATION_URL = 'postgresql://postgres:<mot de passe>@localhost:5432/hisabpro'
   .\hisabpro-backend\.venv\Scripts\python.exe ops\migrations_hisabpro.py constater --url-env HISABPRO_MIGRATION_URL --base-attendue hisabpro --jusqua 70
   .\hisabpro-backend\.venv\Scripts\python.exe ops\migrations_hisabpro.py appliquer --url-env HISABPRO_MIGRATION_URL --base-attendue hisabpro --suivantes
   .\hisabpro-backend\.venv\Scripts\python.exe ops\migrations_hisabpro.py etat --url-env HISABPRO_MIGRATION_URL --base-attendue hisabpro
   Remove-Item Env:HISABPRO_MIGRATION_URL
   ```
   Attendu : 60 lignes « exécutée », puis un état sans « en_attente », hormis les réparations 065, 067 et 070, qui restent volontairement non rejouées.
5. **Base de test uniquement** : finaliser les données pour l'export FEC. Cette étape valide les brouillons par date, puis ajoute des tiers et des références **fictifs marqués « TEST-À-REMPLACER »**, en ajout seul. Elle a été autorisée par l'utilisateur le 31/10/2026 pour cette base de test.
   ```powershell
   $env:HISABPRO_APP_URL = 'postgresql://hisabpro:<mot de passe applicatif>@localhost:5432/hisabpro'
   .\hisabpro-backend\.venv\Scripts\python.exe -X utf8 ops\finaliser_donnees_test.py --url-env HISABPRO_APP_URL --base-attendue hisabpro --valeurs-fictives-test OUI-BASE-DE-TEST --rapport C:\Users\Y_N_e\finalisation_963.json
   Remove-Item Env:HISABPRO_APP_URL
   ```
   Résultat attendu, prouvé sur copie :
   - société 3 / 2026 : 16 → 0 bloquant ;
   - société 3 / 2027 : 7 → 0 ;
   - société 11 / 2026 : 2 → 0 ;
   - export FEC à 200 partout ;
   - aucune écriture déséquilibrée.
6. Redémarrer le backend avec le code 957/959/963, puis ouvrir Factures, Journal, Déclaration TVA et Lettrage.

## 4. Lot 963 — correctif et finalisation des données de test

- Correctif produit : le contrôle FEC `SEQUENCE_NON_CHRONOLOGIQUE` signalait à tort un même jour validé dans un autre ordre que la création des brouillons. La règle est désormais : en suivant les numéros, la date comptable ne recule jamais (`services/fec_service.py`, `Test/test_fec_sequence_chronologique963.py`).
- Finalisation prouvée sur copie avec `ops/finaliser_donnees_test.py` :
  - 24 valeurs fictives marquées ;
  - 666 requêtes, 0 erreur serveur.
  - Seul refus FEC restant : la société 9, sans aucune écriture en 2026.
- **Les valeurs « TEST-À-REMPLACER » ne doivent jamais être utilisées sur des données réelles.**

**En cas d'échec à l'étape 4** : ne rien forcer. Restaurer la sauvegarde de l'étape 2 dans une nouvelle base pour comparaison, et conserver la sortie de la commande.

## 3. Points restant à traiter après la montée de version

- **Export FEC 2026/2027 bloqué** par les contrôles Avis n°24 sur les données de test. Consulter l'aperçu FEC et traiter les anomalies par les flux prévus (compléments historiques, réparations traçables), sans modifier d'écriture définitive.
- La table `decisions_affectation_resultat` n'a pas pu être lue par le rôle applicatif : son contenu n'a pas été testé (structure seulement). La vérification de l'étape 3, avec la sauvegarde `postgres`, couvre ce point.
- Personnel/Paie : migrations installées (105–124), module non activé ; hors MVP.

## 5. Exécution sur la base de test locale — 31 octobre 2026 (lot 965)

Réalisée par l'agent avec l'autorisation et le mot de passe administrateur fournis par l'utilisateur.

1. Sauvegarde complète : `C:\Users\Y_N_e\hisabpro_sauvegardes\hisabpro_avant_965.dump` (731 600 octets, propriétaires et droits inclus). **Point de retour si besoin.**
2. Répétition générale sur copie isolée depuis cette sauvegarde : conforme.
   - 64 scripts constatés, 60 exécutés.
   - Données d'origine identiques, hors ajouts 092.
   - Finalisation : 5 FEC sur 5 conformes ; 0 écriture déséquilibrée ; 0 erreur 5xx.
3. Montée de version de la base `hisabpro` :
   - 60 scripts exécutés (071 → 130) ; un second passage n'exécute rien ;
   - 112 tables ; 0 écriture validée déséquilibrée ;
   - registre : 64 constatés, 60 exécutés, réparations 065, 067 et 070 volontairement non rejouées.
4. Finalisation des données de test :
   - société 3 / 2026 : 16 → 0 bloquant ;
   - société 3 / 2027 : 7 → 0 ;
   - société 11 / 2026 : 2 → 0 ;
   - 24 valeurs fictives « TEST-À-REMPLACER », listées dans `C:\Users\Y_N_e\hisabpro_sauvegardes\finalisation_965.json`.
5. Contrôle final, toutes les routes GET pour chaque société et exercice, sous le rôle applicatif :
   - 545 requêtes, 0 erreur 5xx ;
   - export FEC 200 pour les 5 couples société/exercice ;
   - les 409 restants concernent Personnel/Paie, non activé et hors MVP.

À faire par l'utilisateur :
- changer le mot de passe `postgres`, communiqué dans la conversation ;
- démarrer le backend avec le code 965 ;
- faire la recette dans le navigateur.
