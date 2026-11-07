# Restauration native des données et droits089 — lot 446

L'outil de sauvegarde ajoute une option explicite `--inclure-droits` et le
paramètre Python `inclure_droits=True`. Le défaut reste sans ACL, comme les
sauvegardes historiques. Aucun rôle, mot de passe ou propriétaire n'est créé
par le dump. La restauration reste limitée à une base vide d'un cluster nonce,
atomique (`--single-transaction --exit-on-error`) et sans suppression automatique.
Les mots de passe ne sont jamais passés en arguments de pg_dump/pg_restore.

Un défaut réel d'export a également été corrigé :l'ordre des lignes FEC dépendait
de l'ordre du JOIN PostgreSQL. Après restauration, le même dossier donnait un
FEC de contenu identique mais ordonné différemment. `lignes_fec` trie maintenant
une copie des lignes par leur identifiant persistant ;aucune collection ORM,
écriture ou archive existante n'est modifiée. Les fonctions pures sans identifiant
gardent leur ordre stable. Aucun montant ni format réglementaire nouveau.

## Tests réellement exécutés

8 ciblés réussis48.51s, puis 47 connexes réussis en298.645s XML,
zéro échec/erreur/ignoré ;compilation4fichiers etCLI--help codes0.
Les suites se recouvrent :ne pas additionner leurs résultats. Avertissements existants.

Deux clusters PostgreSQL jetables distincts, avec une vraie année2025→2026
factures/ventilations/lettrage/banque/clôture/AN/FEC :

- Schéma :981 colonnes, 961 contraintes, 376 index, 69 triggers, 60 fonctions, 68 sequences, 68 etats_sequences. Les CHECK sont comparés avec la normalisation PostgreSQL
  déjà validée434 ;prédicats,casts et NOT VALID conservés.
- Toutes les73tables et états de séquences égaux à la restauration ;aucune
  migration de données rejouée sur la cible. Données de référence inchangées.
- ACL canoniques :1201 entrées relations, 24 entrées colonnes, 140 entrées fonctions, 4 entrées schemas, 0 entrées defauts. Le chiffre schemas compte les droits du seul schéma
  public. Les permissions par colonne GRH sont restaurées :nom/statut modifiables,
  societe_id/employe_id protégés. Les UPDATE hérités des anciennes séquences
  restent exactement ceux de la source ;ils ne sont pas annoncés absents.
- Première restauration avec rôle hisabpro absent :échec natif et rollback
  complet, schéma encore vide etACLinitiales identiques. Après création explicite
  du seul LOGIN limité, la même archive est restaurée avec succès. Ni SUPERUSER,
  ni CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS,membre du migrateur ou propriétaire.
- Authentification réelle sur le dossier restauré etFEC2025 identique octet
  par octet. Nouvelle société, deux factures120,paiement120,validation etlettrage
  via les vraies routesAPI sous hisabpro :3pièces débit=crédit=360.
- Huit tentatives refusées :modifier écriture/ligne définitive,supprimer clôture,
  modifier taux global ou identité employé,TRUNCATE ventilation,SETVAL captureRAS
  etCREATEtable. Cible non vide refusée avant toute nouvelle restauration.
- Source intégralement identique et toutes ses anciennes lignes conservées
  dans la cible après le nouveau cycle ;écritures définitives non réécrites.
  Serveurs,clusters etdump nettoyés par les contextes de recette.

Le nouveau cycle cible utilise des routesFastAPI réelles avec JWT ;seule la
connexionDB est injectée et vérifie current_user. Ce n'est pas une recette du
middleware réseau/audit complet sur la cible ;la source annuelle utilise main:app.

Commande connexe :Test/run_unit_tests.py avec test_fec_ordre_lignes.py,
test_restauration_runtime_acl_089.py,test_session132_sauvegarde_postgres.py,
test_restauration_consolidee_084.py,test_sauvegarde_paie_grh_postgres.py,
test_sauvegarde_ras_reglements_isole.py,test_sauvegarde_rapprochement_ventilation_isole.py,
test_sauvegarde_pieces_documents_isole.py,test_patch07c1_fec_avis24.py,
test_patch053_comptabilite_auxiliaire_fec_avis24.py,test_compta4_justificatifs_fec.py,
test_e2e_annee_connectee_isole.py,test_e2e_archive_liasse_isole.py.
Les sauvegardes par défaut sansACL sont réellement réexécutées,ainsi que l'archiveEdge.

## Échecs conservés

Premier restore :1échec45.46s au FEC ordonné différemment,après schéma/données/ACL
déjàégaux. Baseline pure :5échecs/2réussites0.57s sur permutations de lignes.
Après tri :7réussites et1échec49.13s ;le banc attendait un refus sur un UPDATE
sans changement, légitimement autorisé. La probe tente désormais une modification
effective de libellé/débit. Aucune règle produit assouplie. Un futur SELECT du
banc supposait une colonne factures.ecriture_id absente ;il utilise maintenant
la référence exacte non ambiguë du seul jeu fictif. Aucune réparation historique.

Le banc consigne aussi pytest.Failed (BaseException) avant relance etinspecte
le nettoyage enfinally, même en échec. Les anciennes preuves JSON intermédiaires
ne remplacent pas leurs XML échoués. La preuve finale est copiée séparément dans
.codex-tests/restauration446_preuve_final.json. Aucun échec n'est masqué.

## Limites

Toutes les opérations ont utilisé uniquement les deux bacs nonce et données
fictives. La restauration hors bac reste refusée. Les rôles/mots de passe ne sont
pas sauvegardés ;leur préparation appartient à une procédure distincte. Le banc
utilise le même nom de migrateur/propriétaire sur les deux clusters ;un transfert
vers des propriétaires différents n'est pas validé. Les droits enregistrés sont
restitués, sans prétendre que tous les modules sont exhaustivement provisionnés.
Le scénario089 n'étend pas la sauvegarde conjointe des fichiers/pièces jointes.
Aucune base réelle, migration réelle, recette utilisateur/Office ou mise en
production validée. Point6enattente,qualification fiscale/sociale inchangée.
Prochaine étape :étendre le multi-société sous LOGIN puis couverture/cumulatif.
