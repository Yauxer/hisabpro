# Qualification d'installation et de restauration099

Le lot575 qualifie la migration additive099 et la conservation des dossiers de
capture TVA571/573. Aucun PostgreSQL utilisateur n'a été lu ou modifié.

## Installation vierge et rejeu

Commande : `Test/run_unit_tests.py Test/test_installation_vierge_099.py -ra`.
**1 test réussi,1 avertissement,33,15s, code0.**

La chaîne098 existante est exécutée puis099 appliquée et rejouée :90 fichiersSQL
distincts,26rejeux,116exécutions. Les74 tables antérieures conservent leurs
données et la nouvelle table est vide ;38 tables métier finales restent vides.
Le rejeu préserve schéma, séquences, empreintes et ACL. Le LOGIN applicatif
dispose de SELECT/INSERT, sans UPDATE/DELETE/TRUNCATE ou création du schéma.
La nouvelle fonction de contrôle ne reçoit pas EXECUTE pour PUBLIC.

Les scripts antérieurs, y compris leurs ajouts de référence098, ne sont pas
modifiés. Aucun nouveau salarié, bulletin ou mouvement comptable n'est créé
par l'installation. Le rapport complet produit par la vraie commande est
[rapport_installation_vierge_099.md](rapport_installation_vierge_099.md).

## Sauvegarde et restauration froide

Commande : `Test/run_unit_tests.py Test/test_restauration_ras_tva_capture_isole.py -ra`.
Premier passage :1 test réussi,29 avertissements,69,83s, code0.
Passage final avec garde TVA et immutabilité après reprise :**1 test réussi,
29 avertissements,79,00s, code0**. Le refus de soldeTVA incomplet et le trigger
interdisant UPDATE sont réellement vérifiés sur la base restaurée.

Deux clusters PostgreSQL nonce distincts, vraie sauvegarde et restauration,
API démarrées sous LOGIN non propriétaire. Les enveloppes de test prolongent
uniquement la fabrique et les callbacks de l'ancien banc091 ; aucun calcul ou
réponse métier simulé. Le test091 d'origine reste inchangé.

75 tables, schéma, données, séquences et ACL restitués à l'identique avant
redémarrage. Deux dossiers réels de laboratoire sont comparés via API : une
capture active et une capture annulée avec son écriture inverse. Le rejeu du
POST actif retourne son dossier sans mutation métier ; celui de la capture
annulée est refusé. Les justificatifs, FEC et décisions annuelles de l'ancien
banc continuent à être contrôlés réellement.

La preuve575 est conservée séparément, sans réécrire la preuve historique452.
Source préservée, cibles et processus créés par le banc supprimés. Aucun dump
livré dans le ZIP, aucune sauvegarde ou restauration de production effectuée.

## Installation cible et suite

Faire qualifier la sauvegarde et les versions déjà appliquées par
l'administrateur de l'installation réelle, puis lui faire appliquer099 avec
son rôle de migration. Aucun bootstrap ou modèle SQLAlchemy ne crée ces
détails implicitement. Les écrans indiquent la migration manquante.

Le fonctionnement de l'installation cible, ses propriétaires/rôles, secrets,
fichiers joints et sa recette utilisateur restent à vérifier. Imputation,
reversement et déclaration complète des retenues restent à qualifier.
RH/paie différées. Ne pas traiter un dossier conservé comme une preuve de dépôt.
