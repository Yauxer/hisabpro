# Multi-société sous LOGIN SQL applicatif — lot 447

La création d'une seconde société échouait SQL42501 sur utilisateurs_societes
sous le vrai LOGIN non propriétaire. La migration manuelle090 ajoute uniquement
SELECT/INSERT/DELETE sur cette table et UPDATE(role,actif) par colonne.
La séquence reçoit USAGE/SELECT ;aucun nouveau UPDATE/SETVAL,CREATE ouTRUNCATE.
L'identité id/utilisateur_id/societe_id etcreated_at ne sont pas modifiables.
Le DELETE correspond au retrait d'un accès secondaire par les routes existantes ;
aucun DELETE sur utilisateurs principaux ajouté. Aucun rôle métier ou contrôle
d'administration n'est supprimé. Les comptes personnels etles données comptables
restent distincts des liaisons d'accès.

## Tests réellement exécutés

Baseline :1échec15.90s,HTTP500 etSQL42501réel. Les huit tables de société/modules/
plan/exercices/périodes/écritures sont inchangées après l'échec,confirmant le
rollback ;la trace HTTP d'échec appartient à l'audit séparé etreste présente.
Après090 :6ciblés réussis63.47s,puis 27 connexes réussis en203.580s XML,zéro échec,
erreur ou ignoré ;compilation2fichiers code0 etCLI090réelle17.58s.
Les suites se recouvrent,ne pas additionner. Avertissements existants conservés.

- Seconde société créée via API,puis switch réel JWT,plan1111/5141/3421/4411,
  premier exercice courant et12périodes. Liste des seules deux sociétés autorisées.
- Création etsélection dans Edge,saisie de la nouvelle société,plan visible puis
  rechargement conservant la société active ;aucune API métier interceptée.
- Invitation d'un utilisateur existant enlecture,écriture403,puis rôlecomptable
  effectif avec le même JWT etcréation d'un brouillon10/10 dans la bonne société.
  Une modification du profil personnel de l'invité est refusée403.
- Désactivation d'accès révoquant le JWT secondaire,reprise de la société
  principale autorisée,réactivation puis suppression de la seule liaison.
  Compte personnel toujours actif etprincipal accessible ;autre société403,
  journal de la société principale vide etdernier administrateur protégé400.
- Toutes les autres ACL restent identiques,UPDATE global de liaison absent,
  seules role/actif modifiables ;identités,TRUNCATE etDELETE utilisateur refusés.
  Rejeu sans mutation des73tables ni des ACL ;rôle absent,double SQLsansobjet créé.
- Vraie année bancaire088/089 rejouée sur la cible090,puis dump/restore avec ses
  ACL :26droits de colonnes (dont les deux nouveaux),schéma/données/FEC identiques,
  nouveau cycle API360/lettrage sous LOGIN limité etsource/originaux préservés.
  La preuve finale447 est copiée séparément ;la preuve finale446089reste intacte.
- Installation àvide090 :81SQLdistincts,17rejeux,36tables métier vides ;schéma,
  données,séquences inchangés par090,ACL hors liaison inchangées. Aucun bootstrap.

Commande connexe :Test/run_unit_tests.py avec test_multi_societes_runtime_isole.py,
test_e2e_administration_isole.py,test_e2e_runtime_consolide_isole.py,
test_support_e2e_runtime.py ettest_lettrage_identite_auxiliaire_postgres.py.
Preuves runtime447_avant/cibles/connexes XML/log/exit,installation447_cli et
.codex-tests/restauration447_preuve_final.json. Les anciens parcours administratifs
sont réexécutés avec leur fixture d'origine,les nouveaux sous LOGIN limité.

## Limites

090 et085–089 sont des migrations manuelles,horsbootstrap etnonappliquées sur
base réelle. La recette090 ne reçoit aucune connexion externe. Les anciennes
migrations etles oracles comptables restent inchangés. Le plan minimal de l'ancien
E2E132 àquatre comptes n'est pas confondu avec le référentiel consolidé complet.
La suppression d'un utilisateur principal n'est pas nouvellement provisionnée.
Pas de comptabilité de groupe automatique oufacture miroir inter-société ajoutée.
Tous les rôles d'un parcours annuel exhaustif etles autres modules restent à
qualifier. Aucune donnée réelle,mise enproduction ourecette humaine validée.
Point6toujours enattente. Prochaine étape :couverture,procédures etcumulatif
différentiel vérifiés ;puis pièces justificatives/modèles sous LOGIN etvariantes
annuelles restantes lors de la reprise.
