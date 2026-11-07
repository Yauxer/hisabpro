# Lot 485 — Paramètres TVA et statut d'exercice concurrents

## Changement

Le contrôle094 refusait une modification lorsque la clôture était déjà visible,
mais ne verrouillait pas la ligne d'exercice pendant une modification SQL directe.
La migration **096_verrou_parametres_tva.sql** renforce le corps de cette fonction
sans réécrire094, modifier une donnée ou ajouter un privilège.

Le trigger prend un verrou **FOR SHARE** sur les lignes d'exercice existantes
correspondant à l'ancien et au nouveau périmètre. Les deux périmètres d'une
relocation propriétaire sont verrouillés dans l'ordre société/année. Le statut
retourné après une attente est contrôlé, puis les contrôles094 restent appliqués.
Le verrou dure jusqu'à la fin de transaction. Une clôture confirmée provoque23514 ;
une clôture annulée permet l'opération ; une modification déjà engagée fait
attendre le changement de statut.

L'API utilise le même verrou partagé. Garder son ancien verrou exclusif provoquait
un interblocage réel avec une modification SQL du même paramètre. Les lecteurs
du statut sont maintenant compatibles, tandis qu'une mise à jour du statut attend.
Ces propriétés s'appuient sur la [documentation PostgreSQL18 des verrous de ligne](https://www.postgresql.org/docs/18/explicit-locking.html#LOCKING-ROWS)
et sont vérifiées par les tests natifs décrits ci-dessous.

Deux premières saisies API peuvent désormais lire le même statut ensemble.
Un **UPSERT PostgreSQL atomique** conserve une seule ligne société/exercice et
évite l'erreur500 d'une double création. `RETURNING` restitue à chaque requête
les montants de sa propre opération. Les conversions `money`/`D`, contrôles
numériques, permissions et champs autorisés restent identiques. Le compteur
de séquence peut avancer même sur une mise à jour, comme documenté pour
[INSERT ON CONFLICT et les séquences](https://www.postgresql.org/docs/18/functions-sequence.html) ;
aucun identifiant existant n'est réattribué.

Aucun taux, calcul de déclaration, écriture comptable ou montant historique
n'est changé par la migration. Aucun droit SQL nouveau, nouvelle table ou colonne.

## Tests exécutés pendant l'analyse et la correction

| Passage | Résultat réel | Interprétation |
|---|---|---|
| Sous095, avant096 | 9 échoués / 1 réussi,26,37s | Les neuf opérations finissaient avant le verrou attendu ; course reproduite. |
|096 seule, ancienne API exclusive |9 réussis /1 échoué,29,80s|Les courses de statut passent ; interblocage SQL/API40P01 reproduit.|
|096 et API partagée |13 réussis,49,10s|Dix courses et les trois anciens scénarios477.|
|Consolidation intermédiaire |62 réussis,143,57s|Inclut la restauration096, avant correction supplémentaire de double création.|
|Deux premières saisies API |1 échoué,21,37s|Deux INSERT retenus réellement : réponses200/500, anomalie reproduite.|
|Après UPSERT |28 réussis,92,95s|Double création200/200, courses SQL/API,477 et nombres finis.|

Ces passages sont distincts ; les échecs ne sont pas effacés ni présentés comme
des réussites. La qualification finale de la dernière version figure plus bas.

## Qualification finale de la version livrée

**77 réussis,29 avertissements,0 échec / erreur / ignoré en147,74s.**
Commande unique incluant76 cas regroupés sous096 et une restauration froide
séparée :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_tva096_isole.py Test/test_restauration_tva096_isole.py -ra
```

Répartition : dix nouvelles courses SQL/statut/API,22 cas094 réutilisés sous096,
25 cas du registre095,quatre accès Edge,une double création API,14 validations
numériques TVA et une restauration096. Les oracles historiques ne sont pas réécrits.
Compilation Python des cinq fichiers ajoutés/modifiés réussie. Le frontend reste
inchangé ; la recette navigateur utilise les composants existants.

## Oracles

- INSERT/UPDATE sous LOGIN limité et DELETE propriétaire, chacun face à une
  modification de statut non confirmée : attente observée dans `pg_stat_activity`,
  puis refus23514 après commit ou réussite après rollback.
- Ordre inverse pour les trois opérations : le statut attend le commit des
  paramètres ; les changements suivants sur l'exercice fermé restent refusés.
- SQL et API sur le même paramètre : rétention de ligne réelle, deux rédacteurs
  observés en attente, libération puis deux réussites, sans interblocage.
- Deux premières saisies : un verrou de table de laboratoire permet les SELECT
  mais retient les deux INSERT. Après libération, deux réponses200 et une seule
  ligne ; chaque réponse contient les valeurs écrites par son opération.
- Réutilisation sans modification des oracles094 : clôture visible, ancien/nouveau
  périmètre, trace seule, témoins ouverts, droits, lecture, TVA navigateur et clôture.
- Réutilisation des oracles095 : affectations, récupération excessive, annulation,
  concurrence HTTP/SQL, lecture et changement réel de société dans Edge.

Les tests positifs regroupés contrôlent en fin de fixture l'absence de pièce
déséquilibrée, montant non fini et écriture définitive sans numéro/date. Les ACL,
sources et corps final de fonction restent identiques durant l'exécution.
Un résultat de fixture ne remplace pas le code retour et le résumé pytest.

La restauration froide conserve toutes les assertions452 et l'enrichissement095 :
source API arrêtée, cible nonce vide, schéma/données/ACL/séquences comparés,74tables,
quatre pièces, FEC2025 identique, registre renseigné et reprise de600 à500MAD.
Le corps096 restauré est comparé à la source. Aucune sauvegarde réelle n'est utilisée.
La course de concurrence n'est pas rejouée séparément sur la cible restaurée.

## Installation et limites

Arrêter l'API, sauvegarder et vérifier la procédure de restauration. Installer
le fichier backend modifié et appliquer manuellement096, par le rôle de migration,
après les migrations précédentes jusqu'à095 ; redémarrer l'API. Aucun script
n'a été exécuté sur la base utilisateur. Le bootstrap n'applique pas096.

Qualification locale : PostgreSQL18.3, isolation READ COMMITTED, boucle locale et
LOGIN non propriétaire. Autres versions, niveaux d'isolation et charge de production
restent à qualifier. Le frontend est inchangé ; aucun nouveau build n'est revendiqué.

La sérialisation vise le **statut d'une ligne d'exercice existante**. Elle ne couvre
pas une ligne absente, la création concurrente d'une trace de clôture seule sans
changement de ce statut, ni tout le calcul préalable du workflow de clôture.
Le refus d'une trace de clôture déjà visible reste assuré par094. Les transactions
SQL arbitraires sur plusieurs objets et leur ordre de verrous ne sont pas toutes
qualifiées. Le registre GRH garde son propre contrôle de clôture visible095 ;
aucune protection concurrente globale de tous les modules n'est revendiquée.

La recette utilisateur, l'installation/restauration de production, les sources
sociales manquantes et le point6 restent en attente. Les115 fichiers guide/recette
et toutes les migrations antérieures sont préservés.
