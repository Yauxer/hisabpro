# Contraintes ETIC et empreinte des archives — migration 076

L'expérience d'installation sur une base vierge a montré que `create_all` crée les tables avant les migrations 026/027. Leur `CREATE TABLE IF NOT EXISTS` laisse alors absents deux CHECK pourtant prévus : la liste des codes ETIC et le format de l'empreinte SHA-256.

La migration additive 076 ajoute seulement les contraintes manquantes, en identifiant la table et le nom. Elle reprend exactement les valeurs déjà présentes dans 026/027. Elle ne change aucun document, chiffre ou règle fiscale. `NOT VALID` conserve les anciennes lignes invalides ; les nouvelles insertions sont contrôlées. La qualification des données historiques reste une opération distincte.

## Tests exécutés

- Avant correction : 5 échecs en 10,50 s, démontrant l'acceptation de nouveaux codes/empreintes invalides.
- Après migration : `pytest Test/test_contraintes_etic_archives_postgres.py -q` : **8 réussis en 19,78 s**, aucun échec ni test ignoré.
- Connexes ETIC, liasse et exports : `Test/run_unit_tests.py Test/test_patch09_2_etic.py Test/test_patch09_3_liasse_fiscale.py Test/test_patch120_liasse_exports_ventilations.py Test/test_patch131_liasse_pdf_identite.py` : **24 réussis en 0,67 s**.
- Compilation Python du test : code de sortie 0.

Les tests PostgreSQL utilisent uniquement des clusters éphémères protégés par nonce. Ils vérifient deux applications de la migration, la conservation exacte de lignes anciennes fictives invalides, les refus 23514 avec le nom de contrainte attendu, les insertions valides `B2bis`/SHA en minuscules, le catalogue `convalidated=false` et l'absence de rôle applicatif.

## Limites

Aucune migration n'a été appliquée au PostgreSQL réel. Les contraintes nouvelles ne certifient pas les données historiques et ne valident pas le dossier fiscal. Aucune donnée réelle n'a été modifiée. Une validation globale des anciennes lignes nécessite un examen séparé ; elle n'est volontairement pas exécutée ici.
