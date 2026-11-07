# Annulation des règlements : origine contrôlée — 532

## Anomalies et correction minimale

L'annulation acceptait un lien vers une pièce manuelle ou une autre pièce
de règlement, même incohérent avec la société, la date ou le montant attendu.
Un lien explicite étranger pouvait être remplacé silencieusement par une
recherche historique locale. Une correction déjà créée dans le Journal
provoquait une erreur 500 à l'unicité des contrepassations. Enfin, suppression
du brouillon dans le Journal et annulation pouvaient s'interbloquer.

Le seul fichier produit modifié est `routers/commercial.py` :

- Le lien technique explicite reste prioritaire. Un lien incohérent est
  refusé 409 ; aucune recherche historique ne le remplace silencieusement.
- La récupération historique reste possible en l'absence de lien, uniquement
  pour une source `reglement` de même société, référence et date, unique.
- Origine, date, totaux débit/crédit et montant doivent recouper le règlement.
  Une pièce déjà liée à un autre règlement de la société est refusée.
- Une correction existante entraîne un refus 409, sans deuxième impact ni
  changement artificiel du statut commercial. Une décision humaine reste
  nécessaire si la correction avait été créée séparément dans le Journal.
- La pièce source est verrouillée avant lecture de ses lignes et recherche
  de correction. Le verrou est non bloquant : une pièce déjà en cours de
  mutation donne 409. Cela évite l'inversion de verrous entre Journal et
  règlement. Seul le code PostgreSQL 55P03 est traduit en ce refus ; les
  autres erreurs ne sont pas masquées.

Aucun original, justificatif, audit ou montant historique n'est réparé.
Une référence renommée reste utilisable lorsqu'un lien natif fiable existe.
Les annulations usuelles et les contrepassations conservent leurs règles.

## Tests et preuves

Avant correction :

- Première campagne : 9 échecs et 5 réussites, 29 avertissements, 54,33 s.
- Le refus « autre société » venait initialement d'une ambiguïté locale de
  référence. Test précisé avec fallback local unique et ajout d'une source
  déjà liée à un autre règlement : 4 échecs, 12 désélectionnés, 34,97 s.
- Deux courses avec un brouillon en mutation : première campagne 2 échecs,
  32,69 s, dont une erreur d'observation du test (une modification du seul
  libellé ne touche pas les lignes). Le test soumet ensuite explicitement les
  lignes et observe le bon verrou : 2 échecs réels, 16 désélectionnés,
  36,92 s. Suppression500 et annulation indûment acceptée reproduites.

Qualification ciblée : **18 réussites, 29 avertissements, 62.17 s**, code 0.

Qualification connexe : **128 réussites, 169 désélectionnés,
29 avertissements, 314.44 s**, code 0. Aucun échec/erreur/ignoré.
Commande : `Test/run_unit_tests.py Test/test_consolidation_annulations532_isole.py
-k "recette530 or annulation532" -ra`.
Les 169 cas non sélectionnés ne sont pas déclarés exécutés dans cette commande.
Sources figées et ACL identiques ; trois Python du lot compilés,
98 migrations et 115 guides de recette inchangés. Frontend inchangé.

Les dix-huit cas API/PostgreSQL couvrent vente et achat pour les six sources
incohérentes/déjà corrigées ; références renommées et historique unique ; les
deux ordres Journal/annulation ; modification ou suppression du brouillon en
cours suivie d'une nouvelle annulation après stabilisation.

Les négatifs comparent toutes les tables métier avant/après, hors journal
technique d'actions. Les courses vérifient une seule correction et la
conservation exacte de l'original, de ses lignes et de son audit.
Le wrapper réexécute également les 110 cas de règlements530, RAS, ventilation,
lettrage, banque et annulations dans Edge. Les campagnes ne sont pas additionnées.

## Installation et limites

Installer `routers/commercial.py`532 après le lot530, ou utiliser le cumulatif
de session, puis redémarrer l'API. Aucune nouvelle migration.

Les tests utilisent exclusivement des sociétés fictives dans des clusters
PostgreSQL nonce. Les liens incohérents sont introduits par le propriétaire
du seul bac de test ; l'API utilise un LOGIN non propriétaire. Aucune base
réelle connectée. Une origine historique incomplète reste explicitement
à vérifier, sans choix arbitraire ni données inventées.

Les accès directs hors API, la libération des autres documents sources et
les autres générateurs sont des périmètres distincts. La recette utilisateur,
la mise en production et le point6 humain restent en attente.
