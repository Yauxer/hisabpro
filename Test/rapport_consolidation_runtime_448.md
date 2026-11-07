# Recette regroupée sur schéma complet — lot 448

Les scénarios existants sont maintenant exécutés ensemble sur une seule
application complète etun seul LOGIN SQL non propriétaire. Le schéma090 est
préparé explicitement, puis091 corrige un dernier refus de lecture découvert
dans l'écran de clôture. Cela représente82scripts distincts dans ce banc.
Le CLI090 conserve son propre manifeste81SQL/17rejeux ;091 n'est pas annoncé
automatiquement appliqué par ce CLI ou par le démarrage de l'application.

## Cause reproduite et correction minimale

Le premier passage donne11réussites puis1échec104.50s :l'année avec stock/TVA/
inventaire est clôturée mais l'écran ne peut pas relire son état. SQL42501sur
decisions_affectation_resultat ;052 créait la table protégée,sans permissions.
091 ajoute SELECT/INSERT et USAGE/SELECT de sa séquence,aucun UPDATE/DELETE/
TRUNCATE/CREATE ou nouveau SETVAL. Aucun groupe,justificatif ou montant existant
modifié par la migration. Les contrôles de décision etles règles052 sont inchangés.

## Tests réellement exécutés

Après091 :17ciblés réussis97.09s, puis 44 connexes réussis en97.187s XML,
zéro échec/erreur/ignoré ;compilation code0. Avertissements existants.
Les suites se recouvrent etne s'additionnent pas ;ce n'est pas une globale3426.

Sur la même application main:app sous LOGIN limité :

- Dix parcours Edge :facture vente/achat jusqu'au Journal etlettrage ;importCSV
  bancaire ;propositions simple/lot bureau/mobile ;dégressif5ans normal/latence ;
  année2025→2026bancaire, création/switch de société etannée avec stocks/TVA/
  inventaire/immobilisation/clôture/AN/FEC/exports.
- Deux parcours API :création de seconde société etgestion d'accès secondaires
  avec rôles relus,révocation/isolation etprotection du compte personnel.
- Deux oracles indépendants existants inchangés :année etamortissement dégressif.
- Affectation distincte d'une perte3000 du scénario :PV fictif daté30/06/2026,
  OD1169débit3000/1199crédit3000,décision etjustificatif conservés,écriture
  définitive,doublon409 etoriginaux AN/clôture inchangés. Ce PV n'est pas une
  décision sociale réelle ni une approbation humaine obtenue par le logiciel.
- ACL091 fermées,droits des autres tables etUPDATEdes séquences inchangés,
  refus de modifier/supprimer/tronquer la preuve sous runtime etimmutabilité
  propriétaireP0001 sur une décision réellement enregistrée. Rejeu sans mutation,
  rôle absent,double application sans création d'objet. Le casACL possède son
  prérequis de décision explicite etne dépend pas d'un ordre accidentel de tests.

L'année avec stock conserve son oracle :achat10unités à100,vente4à200,
stock6/CMUP100/valeur600,TVA etpaiements contrôlés,immobilisation1200 etdotation400,
10pièces/23lignes/D=C26760 avant impôt, résultat0 puis perte nette3000laboratoire,
à-nouveaux25000 etexports relus. Aucune règle fiscale nouvelle déduite de ces nombres.

Commande connexe :Test/run_unit_tests.py avec test_e2e_runtime_session_isole.py,
test_patch052_conformite_normative.py,test_patch04_cloture_service.py,
test_compta2_cloture_resultat.py,test_patch101_comptabilisation_is_cloture.py.
732 sources antérieures contrôlées par SHA inchangées pendant448.
Seuls le nouveau test et091 sont ajoutés dans le périmètre code ;aucun refactoring
des scénarios d'origine ou de leurs calculs. XML/log/exit etcontrôleSHA dans le bac.

## Limites et suite

PostgreSQL nonce etpièces fictives uniquement ;aucune base réelle.
091 reste manuelle après052/protections existantes,horsbootstrap. La restitution
des ACL090 est déjà testée447 ;la restauration d'une décision091 nouvellement
affectée n'est pas ajoutée à ce lot. Pas de recette utilisateur218casprévalidée,
de source sociale/fiscale nouvelle ou de validation de production.
Le développement global reste partiel ;point6 toujours en attente.
Prochaine tâche :couverture/procédures/rapportssession etZIPcumulatif vérifié,
puis pièces justificatives/modèles d'écritures sous LOGIN lors de la reprise.
