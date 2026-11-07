# Support simulé de l'édition facture — lot 285

La globale 278 a réellement terminé avec 2 575 réussites et quatre échecs.
Trois échecs provenaient du support Node du test 073 : il extrait le vrai
`handleSave` de React, mais ne déclarait pas le nouvel état
`tvaDeductiblePctEdit`. L'exception précédait la requête PATCH ; les assertions
de rafraîchissement ne pouvaient donc pas être exécutées.

Correction minimale dans le support seulement : déclaration des trois états
React de qualification TVA et du type vente de la facture fictive verrouillée.
La fonction applicative, les assertions d'ordre PATCH → rechargement → fermeture,
les cas d'erreur et la protection RAS restent inchangés.

Commande réelle, Python `.venv` backend, `PYTHON_DOTENV_DISABLED=1` :

```text
Test/run_unit_tests.py Test/test_patch073_actualisation_edition_facture.py Test/test_patch072_actualisation_factures.py Test/test_patch074_journal_apres_comptabilisation.py Test/test_patch075_journal_apres_reglement.py --tb=short --show-capture=no
```

Résultat : **20 passed in 1.59s**, code retour 0. Ces supports sont synthétiques
et ne constituent pas vingt parcours PostgreSQL ou navigateur connectés.
Compilation Python du fichier modifié réellement exécutée : code retour 0.

La globale 278 reste un échec historique ; cette réussite ciblée ne la transforme
pas en réussite globale. Le quatrième échec mobile du lot 280 est traité
séparément dans 283. Aucun fichier applicatif, migration ou donnée réelle modifié.
