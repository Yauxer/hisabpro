# Règlements au centime — lot 642

## Anomalie reproduite avant correction

Sur PostgreSQL natif isolé, un règlement de **0,005 MAD** était accepté par
l'API individuelle (201), conservé en double à 0,005, tandis que ses deux
lignes comptables Numeric(18,2) portaient 0,01. Le test de reproduction a
réellement échoué avant correction ; aucune base utilisateur n'a été utilisée.

## Correction minimale

Le validateur partagé de création/modification refuse un vrai sous-centime
avant mutation et conserve les contrôles existants : montant fini, positif,
numérique et non booléen. Il ne réalise pas d'arrondi implicite. Une tolérance
limitée à quatre ULP, plafonnée à 1e-8 MAD, préserve le seul bruit de calcul
binaire des doubles historiques, par exemple 0.1 + 0.2. Une valeur réellement
fractionnaire telle que 0.300000000001 est refusée.

Une modification de note seule reste autorisée. Aucun SQL, aucune réécriture
des règlements historiques ni des écritures définitives. Le test de lecture
historique 641 injecte désormais son ancien 0,005 dans sa seule base fictive,
après création d'un règlement valide non comptabilisé : le suivi conserve
l'alerte et ne présente jamais un faux zéro.

## Tests réellement exécutés

- Reproduction avant correction : un échec attendu, API 201 au lieu de 422,
  montants constatés 0,005 / débit 0,01 / crédit 0,01.
- Version finale : **35 réussis en 102,535 s**, sans échec, erreur ou ignoré :
  21 cas de validation, 3 cas API natifs, 10 cas de suivi et l'oracle chiffré.
- Non-régression connexe finale : **82 réussis en 164,890 s**, sans échec,
  erreur ou ignoré. Sources surveillées et témoin non vide inchangés.
- Preuve historique 635 conservée à l'identique ; nouvelle preuve de cette
  campagne enregistrée séparément. Les suites connexes se recouvrent avec
  les campagnes précédentes et ne constituent pas un total de tests uniques.

Commandes exécutées avec `PYTHON_DOTENV_DISABLED=1` :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_reglements_centimes642.py Test/test_reglements_centimes642_isole.py Test/test_suivi_correspondances641_isole.py Test/test_oracle_societes639_isole.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_consolidation_factures635_isole.py -q -x
```

Les refus POST/PATCH à 0,005 préservent les données métier. Le règlement
comptabilisé de 0,01 donne exactement 0,01 dans les deux lignes du Journal.
Compilation Python vérifiée à la livraison. Aucun frontend modifié par ce lot ;
le dernier build 641 reste celui exécuté en 5,22 s.

Installation et recette sur l'environnement utilisateur non exécutées.
Les migrations 101/102 restent à installer explicitement pour les fonctionnalités
de sociétés liées ; ce correctif de validation ne nécessite aucune migration.
