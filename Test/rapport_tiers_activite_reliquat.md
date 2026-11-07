# Activité clients/fournisseurs — 8 octobre 2026

## Correction

L'activité de la page Tiers utilise l'identifiant réel `tiers_id`. Deux tiers
portant le même nom ne partagent plus leurs factures. Les factures historiques
sans rattachement restent signalées ; leur nom ne suffit jamais à les attribuer.

Seules les factures validées non annulées participent à la fréquence et à la
dernière activité. Les brouillons et proformas sont exclus. Les indicateurs
restent limités à l'exercice sélectionné, indiqué dans les filtres.

Les impayés proviennent du `solde_restant` de l'API existante des règlements,
incluant ses règles actuelles d'avoirs, acomptes et RAS. Une facture TTC 1 200
réglée à hauteur de 400 affiche 800 à recevoir. Créances clients et dettes
fournisseurs restent séparées, y compris pour un tiers ayant les deux rôles.
Une erreur de chargement ou un solde nul/indéterminable affiche un diagnostic,
sans remplacer celui-ci par le TTC ou zéro. Les dates futures ne sont pas
classées dans les tiers actifs récemment.

Pagination complète des tiers et factures, supprimant les anciennes limites
silencieuses de 200 tiers et 2 000 factures. Le chargement est lié au token de
société ; une réponse d'une société quittée ne remplace pas les données.

## Tests exécutés

- `node --test Test/test_tiers_activite.mjs` : **8 réussis**, 113 ms.
  Homonymes, reliquats, créances/dettes, exclusions, absence de rapprochement
  nominal, RAS null/erreurs, dates, 2 001 lignes paginées et concurrence bornée.
- `python -X utf8 Test/run_unit_tests.py Test/test_e2e_tiers_activite_isole.py` :
  **2 réussis, 28,59 s**. Edge avec connexion réelle, FastAPI et PostgreSQL
  éphémère. Paiements partiels réels, homonymes séparés, tiers aux deux rôles,
  201 tiers visibles, pagination skip=200, fréquence sans brouillon et filtres.
  Historique ID absent et RAS NaN signalés sans montant inventé. Aucun appel
  métier mocké, aucune écriture comptable créée.
- `npm run build` : **OK**, 139 modules, 4,62 s ; avertissements existants xlsx
  importé statiquement/dynamiquement et taille de bundle.

Premier essai E2E : 2 échecs en 32,25 s. Le séparateur de milliers fr-MA était
un point, et la fixture tentait d'ajouter des lignes après l'état validé ; le
garde réel PostgreSQL a refusé. Le sélecteur accepte le format observé et la
fixture crée ses lignes avant de figer les pièces synthétiques. Aucun garde,
trigger, contrat API ou comportement métier n'a été assoupli.

## Limites et suite

Une requête de détail est encore nécessaire par facture ouverte rattachée,
avec au maximum quatre requêtes simultanées. Sur un exercice très volumineux,
une future agrégation backend pourrait réduire ce coût ; aucune pagination
tronquée ou zéro par défaut ne masque ce temps de chargement.

La qualification juridique de la RAS et la RAS estimée avant règlement restent
les limites du rapport d'audit RAS. Le présent lot réutilise les soldes existants,
sans les recalculer ou modifier la règle fiscale. Les factures sans tiers_id
nécessitent une décision ou une réparation historique traçable indépendante.
PostgreSQL réel non utilisé ; données comptables réelles jamais modifiées.
