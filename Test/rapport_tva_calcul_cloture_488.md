# Lot488 — Paramètres TVA stables pendant le calcul de clôture API

La route de clôture prend maintenant le verrou exclusif société/année097 **avant
`ensure_exercice` et avant les calculs**. Il reste détenu jusqu'au commit ou
rollback de la transaction de clôture. Les paramètres TVA ne peuvent plus être
modifiés entre les contrôles initiaux et les écritures finales. Une autre clôture
du même périmètre est refusée409 ; une autre société/année reste disponible.

La modification porte sur six lignes dans `routers/cloture.py`. Elle utilise
le built-in transactionnel PostgreSQL et la même clé que097, sans nouvelle
migration ni dépendance à une fonction SQL nouvellement installée. L'adoption
du protocole par les mutations TVA nécessite toujours097. Le verrou entre deux
requêtes de clôture API fonctionne aussi sur l'ancien banc PostgreSQL sans097.
Voir les [verrous transactionnels PostgreSQL18](https://www.postgresql.org/docs/18/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS).

Aucune formule fiscale, écriture attendue, politique d'exonération, période ou
source historique n'est changée par cette correction. Aucun retry automatique
ne relance une transaction de clôture en arrière-plan.

## Tests de concurrence

Les trois scénarios exécutent de vraies routes et retiennent la table
`immobilisations` du seul laboratoire pour observer une clôture pendant ses calculs.
Les réponses métier ne sont pas simulées.

1. Une modification TVA en cours possède le verrou partagé : la clôture renvoie
   409 avant de toucher les calculs. Les tables métier restent inchangées après
   annulation de la modification temporaire.
2. La clôture possède le verrou exclusif puis attend réellement la table retenue :
   une modification TVA HTTP, une trace SQL et une seconde clôture sont refusées.
   Les autres périmètres restent accessibles. La libération du banc permet la
   clôture200, le FEC reste exportable et les lignes originales restent identiques.
3. Une clôture refusée400 à cause d'un brouillon libère le verrou ; une nouvelle
   modification TVA réussit et le brouillon reste inchangé.

Le jeu IS fictif reste non exonéré selon les paramètres existants du laboratoire :
capital1000MAD, résultat avant impôt0, cotisation minimale existante3000 comptabilisée
par6705D/4453C, résultat net-3000. Cet oracle décrit cette configuration de test ;
il ne vérifie pas l'éligibilité d'une entreprise réelle à une exonération.

## Exécutions et correction du banc

- Avant correction :2 échecs/1 réussite en25,26s. Les paramètres restaient
  modifiables pendant le calcul ; le conflit n'était pas refusé avant celui-ci.
- Premier passage après correction :2 échecs/1 réussite en203,24s. Le contrôle
  d'empreintes relisait la table encore verrouillée par le banc. Cette seule
  requête SELECT a été annulée après vérification du nonce, du PID et du SQL.
  L'autre échec était un oracle0 erroné qui omettait la CM déjà calculée par le
  produit. Les tables sont désormais relues après libération du verrou, et la CM
  est contrôlée explicitement ; aucune règle métier n'a été neutralisée.
- Passage corrigé :**3 réussis,29 avertissements en24,50s**, aucun échec/erreur/ignoré.

Le passage interrompu n'est jamais compté réussi. Aucune donnée ni processus
utilisateur n'a été touché. La qualification finale réutilise les oracles097,
les trois courses nouvelles, la restauration renseignée et l'ancien E2E autonome
sans097 pour vérifier la compatibilité du point d'entrée.

## Qualification finale

**122 exécutions réussies,29 avertissements,0 échec/erreur/ignoré en208,29s.**
Répartition :120 cas regroupés sous097,une restauration097 sur le backend final
et l'ancien E2E autonome de clôture sans097. Le même parcours historique est donc
exécuté dans deux configurations différentes ;122 cas métier distincts ne sont
pas revendiqués. Les invariants comptables restent nuls, sources/ACL/fonctions
inchangées pendant l'exécution. Trois fichiers Python compilés.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_calcul_cloture_tva_isole.py Test/test_restauration_tva097_isole.py Test/test_e2e_cloture_isole.py -ra
```

## Limites

Le contrôle couvre les paramètres TVA et les autres clôtures qui utilisent cette
route ou le protocole097. Il ne sérialise pas tous les écrivains du Journal,
factures, paiements, stocks ou immobilisations pendant le calcul. Une clôture
SQL arbitraire qui ignore le protocole n'est pas rendue sûre par ce seul changement.
La qualification globale de tous les écrivains reste une tâche distincte.

Installer le fichier backend modifié avec le lot487/097 pour la garantie complète
TVA. Aucune migration supplémentaire. Frontend inchangé, aucun nouveau build
annoncé. Recette utilisateur/production et point6 restent en attente ; les115
fichiers de guide/recette et les limites documentaires sont conservés.
