# Lot549 — registre GRH après sauvegarde et restauration

## Périmètre vérifié

Le scénario de restauration froide098 est réellement exécuté avec deux clusters
PostgreSQL distincts, créés dans le workspace et vérifiés par nonce. Les seules
enveloppes du laboratoire (création du client et lancement de la cible) sont
étendues pour préparer des données GRH puis contrôler la reprise. Les API,
`pg_dump`, `pg_restore` et calculs existants ne sont pas interceptés.

La société fictive RESTAURATION contient deux salariés, trois demandes et les
décisions approuvée/refusée, avec leurs événements et un logo intégré. Après
arrêt du seul serveur source créé par le banc, la sauvegarde native et les
fichiers sont restaurés sur une cible vide. Le vrai `main:app` redémarre sous
LOGIN SQL non propriétaire.

## Résultat exécuté

**1 test réussi,29avertissements,61.21s**,code0 :

`Test/run_unit_tests.py Test/test_restauration_grh_registre_isole.py -ra`,
avec `PYTHON_DOTENV_DISABLED=1`.

- 74tables, schéma/données/ACL/séquences vérifiés par le scénario parent.
- Source préservée, fichiers et fonctions098 conservés ; conflit409 et reprise
  du journal contrôlés par le banc existant.
- Liste JSON des demandes et historiques identique avant/après copie.
- Logo présent dans les deux PDF ; contenu textuel identique en neutralisant
  uniquement l'heure d'édition. Les octets PDF ne sont pas déclarés identiques.
- Lecture GRH sans mutation des tables métier après connexion.
- Cibles temporaires nettoyées ; sources de code figées.

Aucun fichier produit, modèle ou migration modifié pour cette qualification.
Les29avertissements de configuration/import sont conservés dans le log.

## Aperçu et limites

Un [exemple PDF entièrement fictif](../docs/audit/exemples/REGISTRE_GRH_FICTIF_20261018.pdf)
issu de cette exécution est joint comme preuve. Son aperçu local d'une page
a été inspecté : logo de test, tableau et historique lisibles, sans découpe.
Les noms, logo de test et montants du laboratoire ne sont pas des données réelles.

Ce contrôle ne constitue pas une restauration de production ou une recette
utilisateur. Les rôles, secrets et dossiers d'une installation réelle restent
à qualifier. Aucun PostgreSQL de l'utilisateur n'a été interrogé ou modifié.
Le point6 humain et les guides existants restent réservés/inchangés.
