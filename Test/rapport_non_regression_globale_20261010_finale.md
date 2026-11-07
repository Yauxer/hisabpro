# Non-régression finale — HisabPro — 10 octobre 2026 — lot311

Le principal a lancé cette nouvelle commande vers09:40UTC, après livraison
des correctifs309 et du lot310. La preuve300 reste conservée séparément :
2627réussites et12échecs, avec sources inchangées. Elle n'est pas réécrite.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test -vv --tb=short --junitxml=.codex-tests/global_RAS_20261010_0814.xml
```

La commande est suivie sous session25978 ; log, XML et code retour utilisent
le préfixe local `.codex-tests/global_RAS_20261010_0814`. Le nom0814 identifie
la reprise pendant laquelle le lanceur a été préparé, pas l'heure de lancement.
Le jeu d'empreintes est `.codex-tests/source_figee_20261010_0814.json`.

**649sources figées** avant exécution : application, tests, SQL et configurations.
Aucun fichier de ce périmètre n'est modifié pendant la commande. Les documents
Markdown et les livraisons peuvent avancer séparément. Les sources ajoutées,
supprimées et modifiées seront contrôlées après l'achèvement.

## Résultat

**Commande terminée avec échecs : 2 734 réussites, 4 échecs, 0 erreur,
0 ignoré, 32 avertissements ; code retour 1.** Pytest indique 3 150,16 s
(52 min 30 s), le XML 3 150,074 s pour 2 738 cas. Le principal a relu le
log, le XML et le code de sortie après l'achèvement de la session25978.

Les **649 empreintes restent identiques** : aucun fichier ajouté, supprimé
ou modifié dans le périmètre figé pendant cette exécution.

### Échecs constatés et diagnostic

- Articles historiques, bureau et mobile : le compteur de mutations inclut
  les POST `/api/devis/diagnostic-stock`. Les traces montrent ces lectures
  supplémentaires, aucune erreur JavaScript/API et le refus attendu dans
  le formulaire. La route ne fait qu'une photographie indicative du stock.
  La mesure doit distinguer précisément cette lecture des POST/PATCH métier,
  tout en conservant les contrôles d'absence de modification des documents,
  des stocks et des écritures. Cette correction relève d'un lot distinct312.
- Réception partielle d'achat, mobile : délai de 20 s sur la navigation
  vers `/factures`, en attente de `load`. Le diagnostic secondaire échoue
  aussi ; une exception tardive `Dialog.accept` est conservée dans le log.
  Aucune cause métier n'est prouvée par cette trace.
- Historique des relances : délai de 20 s avant la saisie du login ; écran
  vide, aucune erreur JavaScript ni réponse API500 observée. Le log API
  comporte un `ConnectionResetError` Windows. La cause reste non établie.

Une relance ciblée du module articles, **sans correction**, a donné 3 réussites
en 47,34 s (25 avertissements, code 0). Elle ne transforme pas cette globale
en succès. Les relances et la correction de mesure sont documentées séparément.

## Périmètre et limites

Les fixtures PostgreSQL utilisent exclusivement des clusters éphémères nonce
et des adresses loopback distinctes des services utilisateur. Dotenv est désactivé.
Le runner exclut le banc historique non isolé de séquences PostgreSQL.
Les tests unitaires purs, supports simulés et parcours API/Edge réels conservent
leurs périmètres distincts ; SQLite ne constitue jamais une preuve PostgreSQL.

Les tests ciblés qui se recouvrent ne sont pas additionnés à cette commande.
Les erreurs intermédiaires et le résultat300 sont conservés dans le journal
et les rapports de leurs lots. Cette preuve ne valide ni recette humaine,
ni déploiement sur une base réelle, ni certification réglementaire.
