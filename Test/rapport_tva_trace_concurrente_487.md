# Lot487 — Trace de clôture concurrente, avec ou sans ligne d'exercice

## Fonctionnement

La migration097 ajoute un verrou transactionnel par société/année, indépendant
de l'existence d'une ligne d'exercice. Les mutations de paramètres TVA prennent
ce verrou en partage ; l'insertion d'une trace de clôture et les modifications
de statut/identité/création/suppression d'exercice le prennent exclusivement.
Les verrous de ligne096 et les contrôles de clôture094 sont conservés.

L'acquisition du verrou de périmètre n'attend pas : un conflit annule l'opération
avec SQLSTATE40001 et le diagnostic nommé `ck_tva_cloture_concurrence`. Cette
stratégie évite d'attendre un verrou applicatif après avoir pris des verrous de
lignes. Elle repose sur les [verrous advisory transactionnels PostgreSQL18](https://www.postgresql.org/docs/18/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS).
Après un conflit SQL direct, le client doit annuler puis rejouer toute sa
transaction. Aucun retry automatique ne masque une erreur métier.

La dépendance `get_db` traduit uniquement ce diagnostic et le refus nommé des
paramètres TVA d'un exercice clos en HTTP409, après rollback. Le message ne
contient pas de SQL ni de donnée privée. Les autres erreurs DB restent inchangées.
La seconde traduction couvre aussi une clôture confirmée entre le contrôle HTTP
initial et le passage du trigger. Les routes existantes utilisent cette même
dépendance, notamment la création d'exercice ; aucune période partielle ne doit
subsister après un conflit.

Une trace seule non confirmée provoque un conflit temporaire ; après son rollback,
la nouvelle tentative est autorisée. Après son commit, le refus de clôture devient
définitif pour les paramètres. Une année ou société distincte reste indépendante.
Quand le statut d'une ligne existante est déjà en cours de modification, le verrou
de ligne096 peut toujours attendre avant ce contrôle de périmètre.

## Périmètre de migration

- Aucun DML, nouveau taux, écriture, montant ni ligne d'exercice créée par097.
- Trois fonctions invoker nouvelles et deux triggers nouveaux ; la fonction
  de protection TVA est renforcée sans réécrire096 ni les migrations antérieures.
- EXECUTE explicite sur les trois nouvelles fonctions pour le LOGIN applicatif,
  sans privilège supplémentaire sur tables, colonnes ou séquences.
- Rejeu : données et droits conservés. Les traces de clôture restent immuables
  selon les protections existantes ; leur modification/suppression n'est pas activée.

La clé est construite depuis le préfixe HisabPro, la société et l'année. Les
verrous sont libérés à la fin de transaction, sans verrou de session à nettoyer.
Le [mécanisme PostgreSQL](https://www.postgresql.org/docs/18/explicit-locking.html#ADVISORY-LOCKS)
ne nécessite aucune ligne support ni donnée historique inventée.

## Reproductions et tests ciblés réellement exécutés

| Passage | Résultat | Portée |
|---|---|---|
| Sous096 avant correction |12 échecs /1 réussite,27,03s|Concurrence sans ligne reproduite ; témoin d'isolation indépendant réussi.|
| Traduction DB avant correction |2 échecs /4 réussites,0,55s|Conflits nommés non traduits ; autres erreurs et fermeture normale conservées.|
| Première correction097 |19 réussis,28,94s|Treize cas PG et six tests de dépendance sans connexion.|
| Extension |39 réussis,39,84s|Présence/absence, commits/rollbacks, les deux ordres, droits invoker.|

Les échecs initiaux restent consignés. Ils ne sont pas présentés comme une
validation réussie. Les tests sont exécutés avec `PYTHON_DOTENV_DISABLED=1`
sur des clusters PostgreSQL nonce et des sociétés synthétiques ; jamais sur
la base utilisateur.

Qualification finale de la version livrée : **118 réussis,29 avertissements,
0 échec/erreur/ignoré en179,03s**. Répartition :76 cas095/096 réutilisés,35 casPG097,
six tests unitaires de traduction/fermeture et une restauration froide097.
Compilation Python des cinq fichiers ajoutés/modifiés réussie.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_tva097_isole.py Test/test_restauration_tva097_isole.py -ra
```

Cas complémentaires inclus dans la qualification finale : contrôle API initial
dépassé par une trace confirmée, refus409 sans paramètre créé ; création API
d'exercice refusée409 pendant un paramètre en cours, puis reprise201 avec douze
périodes et aucune création partielle. Les SQL de laboratoire créent seulement
les états nécessaires à ces courses, sans les présenter comme un exercice réel.

Les oracles095/096 sont réutilisés sans modification : TVA navigateur, clôture et
à-nouveaux, droits, montants finis, avances par salarié, contre-récupération,
annulations, accès lecteurs et changement de société. Les invariants comptables,
sources, ACL et les quatre corps de fonction sont comparés en fin de fixture.

La restauration reprend intégralement452 et le registre095 renseigné : arrêt API
source, copie froide sur cible vide marquée,74tables/schéma/données/séquences/ACL,
quatre pièces et FEC2025 conservés. Les quatre fonctions097 sont comparées. Sur
la copie, une trace non confirmée provoque réellement409 puis un rollback permet
une sauvegarde200 du paramètre. La reprise du registre passe de600 à500MAD.

## Installation et limites

Arrêter l'API, sauvegarder et vérifier la capacité de restauration ; installer
`database.py` et appliquer097 avec le rôle de migration après096, puis redémarrer.
Le script n'est pas lancé par le bootstrap. Aucun accès à la base réelle n'a eu lieu.

La protection couvre la mutation des paramètres face à une trace ou à un statut
concurrent. Le calcul préalable complet de clôture n'est pas verrouillé par ce
lot ; les autres écrivains comptables et fiscaux n'adoptent pas tous ce protocole.
Une transaction SQL arbitraire sur plusieurs objets peut encore nécessiter une
analyse de son ordre de verrous. Aucune absence universelle d'interblocage n'est
revendiquée. Niveau READ COMMITTED PostgreSQL18.3 testé ; autres niveaux/versions
et charge de production à qualifier.

Le frontend reste inchangé : aucun nouveau build annoncé. L'installation et la
recette utilisateur restent à effectuer. Les115 fichiers guide/recette, les
limites FEC/ETIC documentaires, le référentiel social et le point6 sont préservés.
