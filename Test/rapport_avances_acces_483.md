# Lot 483 — Accès au registre des avances dans le navigateur

Le produit livré en482 reste inchangé. Ce lot complète sa recette par quatre
scénarios Edge réels, FastAPI et PostgreSQL temporaire sous LOGIN limité.
Aucune réponse métier n'est simulée ou remplacée. Les CDN décoratifs inaccessibles
sont bloqués par le support existant ; les assets locaux et API restent réels.

## Résultats exécutés

**4 réussis, 29 avertissements, 0 échec / erreur / ignoré en 33,91 s.**

- Lecteur en1440 et390 : consultation d'un versement affecté1000 MAD et d'un
  versement200 MAD non affecté, solde lisible, aucun bouton d'affectation ou
  d'annulation. Deux POST réels depuis le navigateur sont refusés403.
  L'actualisation conserve le même solde.
- Changement de société en1440 et390 : même utilisateur, sociétéA avec111 MAD
  affectés et22 MAD non affectés, sociétéB avec333 MAD affectés à un autre salarié.
  Un formulaireA rempli mais non enregistré est abandonné au changement réel
  de société. Le registreB ne présente ni bénéficiaire ni formulaireA. Deux
  POST portant des identifiantsA sont refusés404 sousB. Le retourA retrouve
 111 MAD, sa ligne22 MAD non affectée et aucun formulaire résiduel.

Dans chaque cas, les écritures/lignes et toutes les lignes du registre sont
comparées avant/après : aucun changement. Les mutations de connexion, changement
de société et tentatives refusées restent journalisées par l'audit habituel.
Aucune erreur JavaScript ni réponse API500 observée. Les processus et clusters
créés sont arrêtés et nettoyés par les fixtures.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_avances_acces_isole.py -ra
```

Compilation du nouveau fichier Python réussie. Les86 tests du lot482, son build
final5,23 s et sa restauration renseignée sont des exécutions distinctes ; aucune
commande unique de90 tests n'est revendiquée. Aucun nouveau build requis : ce
lot n'a changé aucun fichier frontend ou backend produit.

## Limites et reprise

La migration095 reste manuelle après sauvegarde et migrations précédentes jusqu'à094.
Le changement de société du produit recharge réellement la page ; ces tests ne
qualifient pas un futur changement de contexte sans rechargement ni toutes les
courses réseau possibles. L'installation réelle, la recette utilisateur et la
paie réglementaire complète restent à qualifier. Les115 fichiers de guide/recette
et le point6 restent conservés.

Prochaine tâche technique indépendante : examiner la sérialisation des paramètres
TVA lors d'une clôture SQL directe concurrente, dont la limite est documentée
dans480. Ne pas rejouer les lots462–483 ni inventer les sources sociales manquantes.
