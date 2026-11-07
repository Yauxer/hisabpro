# RAS — validation technique des pourcentages

## Anomalie reproduite

Le 7 octobre 2026, une expérience utilisant la vraie API FastAPI et un PostgreSQL
éphémère a envoyé cinq créations de factures fictives avec ras_taux égal à NaN,
Infinity, true, -1 et 150. Les cinq réponses étaient **201** et chaque facture
était persistée avec la valeur indiquée (true converti en 1,0).
Le POST ne renvoyait pas 500 : le schéma de sortie filtrant le champ masquait
l'anomalie. Aucune facture réelle n'a été utilisée.

La reproduction unitaire formalisée avant correction : 18 échecs attendus,
4 réussis, 20 désélectionnés, 1,35 s. FactureCreate et FactureUpdate laissaient
passer NaN, infinis, booléens et pourcentages hors plage.

## Correction minimale

Les deux schémas utilisent un validateur before commun réutilisant _nombre_fini,
et vérifient les bornes mathématiques 0 à 100. Le validateur rejette les booléens
avant leur coercition en 0/1. PATCH ras_taux=null garde sa signification existante
(ne pas changer le taux enregistré). Une création avec null est refusée.

Cette validation **ne définit aucun barème fiscal** et n'affirme pas qu'un taux
quelconque dans cet intervalle est applicable légalement. Les taux non entiers
restent autorisés ; aucune nouvelle liste de taux réglementaires n'est installée.
Il n'y a aucune migration ni correction automatique des données historiques.

## Tests réellement exécutés

- 42 ciblés réussis, aucun échec/ignoré, 33,82 s : 31 unitaires et 11 API réellement
  connectés à PostgreSQL isolé. Les dix requêtes POST/PATCH invalides renvoient
  422 sans modifier les factures, leurs lignes ou les écritures. Le dernier test
  confirme qu'une modification de notes avec ras_taux=null conserve 10 %.
- Compilation de schemas.py et test_ras_taux_finis.py : OK.
- Après correction, suite connexe RAS/ETIC/recouvrement/acomptes et documents
  numériques : 165 réussis, aucun échec/ignoré, 67,63 s.

Les tests passent par l'authentification réelle, une société fictive par cas et
des clusters temporaires marqués sous .codex-tests, jamais le port 5432 ni une
base réelle. Les limites métier de qualification de RAS HT/TVA, de chronologie
du paiement et de justificatifs restent distinctes dans l'audit fonctionnel.
