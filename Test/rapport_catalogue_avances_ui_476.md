# Catalogue Paie — cinq modèles utilisables depuis l'interface

**Deux parcours Edge réussis, 39,85 s, 29 avertissements, code 0** en 1440 et
390 pixels. Aucune correction produit n'a été nécessaire dans ce complément.

Chaque parcours ouvre Journal → Nouvelle écriture → Choisir un modèle
d'écriture → Paie. Les cinq modèles 092 sont réellement visibles dans cette
catégorie, puis choisis successivement. Avec 100 MAD fictifs, le test contrôle :

| Modèle | Journal | Débit attendu | Crédit attendu |
|---|---|---|---|
| Versement bancaire | BQ | 3431 : 100 | 5141 : 100 |
| Versement en espèces | CA | 3431 : 100 | 5161 : 100 |
| Récupération sur rémunération due | SA | 4432 : 100 | 3431 : 100 |
| Remboursement bancaire | BQ | 5141 : 100 | 3431 : 100 |
| Remboursement en espèces | CA | 5161 : 100 | 3431 : 100 |

Les comptes, côtés débit/crédit, contreparties recalculées et journal sont
vérifiés dans le formulaire réel. Chaque formulaire est ensuite annulé.
Les empreintes des quatre tables `ecritures`, `lignes_ecriture`,
`modeles_ecritures` et `lignes_modele` restent identiques : aucune écriture ni
modification de catalogue enregistrée. Aucun appel API métier remplacé ;
aucune erreur JavaScript ni réponse serveur 500 pendant ces deux parcours.

```powershell
python -X utf8 Test/run_unit_tests.py Test/test_e2e_catalogue_avances_isole.py -ra
```

Le runtime réel applique 092 dans un cluster PostgreSQL jetable, sous LOGIN
limité. Ce complément est exécuté après les 143 cas de 478, sans modification
de leurs sources produit. Il ajoute une preuve de navigation et de saisie,
pas un nouveau cycle comptabilisé ni une recette utilisateur validée. Les
enregistrements/validations et le cycle chiffré sont couverts séparément en 464.
Les nombres des suites recouvrantes ne sont pas additionnés.

Compilation du test exécutée avant livraison. Dernier build Vite 474 : code 0,
7,39 s. Aucun PostgreSQL utilisateur, ni bulletin réel, ni retenue automatique.
Point 6 et vérification sur l'installation du partenaire restent en attente.
