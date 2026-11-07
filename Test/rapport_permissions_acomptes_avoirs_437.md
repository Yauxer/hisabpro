# Acomptes et avoirs sous rôle applicatif — lot437

La migration manuelle additive086 complète les seuls droits manquants du socle :
SELECT/INSERT/UPDATE sur acomptes etavoirs ;SELECT/INSERT sur lignes_avoir.
Les traces imputations_acomptes etutilisations_avoirs avaient déjà leurs droits
par035/045 :aucun GRANT supplémentaire ni retrait arbitraire sur ces tables.
Aucun nouveau DELETE/TRUNCATE/CREATE ou UPDATE/SETVAL de séquence. Les droits
hérités de suppression des traces restent identiques etne sont pas annoncés absents.
SHA256 duSQL086 :`49be8127e4ef0b53cef7518a5f09d6d7558dcd837e00b8af544fa8b1be79be33`. Aucun bootstrap ni schéma métier modifié.

Une erreur serveur a également été reproduite sur PostgreSQL :l’annulation
d’une utilisation d’avoir verrouillait le côté nullable du LEFT JOIN chargé
avec les lignes. `avoirs.py` utilise maintenant `FOR UPDATE OF avoirs`,comme
le flux d’utilisation existant. Une seule ligne applicative corrigée.

## Résultats réellement exécutés

49 tests connexes réussis, zéro échec, erreur ou ignoré, 174.255 s ; ciblés :8réussis29.81s ; compilation2fichiers code0.

Commande connexe :`Test/run_unit_tests.py
Test/test_permissions_acomptes_avoirs_postgres.py
Test/test_permissions_documents_commerciaux_postgres.py
Test/test_factG_acomptes_avoirs.py Test/test_avoirs_ras_societe_postgres.py
Test/test_e2e_acompte_imputation_isole.py Test/test_e2e_acompte_fournisseur_isole.py
Test/test_e2e_avoir_fournisseur_isole.py`.

Les quatre nouveaux cycles vente/achat utilisent des JWT réels etune connexion
LOGIN hisabpro nonpropriétaire, sans remplacement de l’authentification :

- Acompte60 imputé40 puis20 sur deux factures120 ;restes80/100,puis annulation
  des deux imputations etde l’avance :restes120/120,huit pièces définitives
  120+120+60+40+20+40+20+60,débit=crédit=480. Traces etoriginaux conservés.
- Avoir60 sur facture120 déjàpayée ;imputation30 àla seconde facture et
  remboursement20,disponible10. Annulations d’abord des utilisations,puis
  de l’avoir :source toujours payée,seconde facture due120 ;sept pièces
  120+120+120+60+20+20+60,débit=crédit=520. Chaque pièce contrôlée séparément.

Les annulations prématurées refusent409,les DELETE publics409 etSQL42501,
les UPDATE de lignes_avoir42501,le lecteur403 etl’autre société404.
Toutes les ACL hors des trois tables etles UPDATE de séquences sont identiques
avant/après. Rejeu sur dix tables documentaires/comptables :octets JSON inchangés.
Rôle absent :aucun objet ni rôle créé. Les E2E connexes contrôlent aussi les écrans
client/fournisseur,stocks,retours,règlements etlettrage existants.

## Échecs intermédiaires conservés

Avant086 :quatre échecsHTTP500,14.68s. Après086 :quatre échecs/une réussite,
17.22s,dont deux relectures erronées du banc etdeux erreursSQL. Diagnosticv2 :
deux échecs/trois réussites,19.46s,exceptionPG0A000sur le verrou nullable.
Après correction du verrou :deux échecs/trois réussites,17.85s ;seul l’oracle
du test d’avoir additionnait620 au lieu de520. Il est désormais calculé et
contrôlé par pièce ci-dessus. Aucun montant produit ni règle métier changé
pour rendre les tests réussis. Les preuves ciblées/connexes ne sont pas additionnées.

## Limites

PostgreSQL nonce uniquement,aucune base réelle ni donnée comptable réelle.
086reste une application manuelle àqualifier pour la cible,comme085,horsbootstrap.
Pas de règle fiscale nouvelle,justification inventée ou réparation historique.
Production etrecette utilisateur nonvalidées ;globale430antérieure àce lot.
La concurrence entre consommation,comptabilisation etannulation d’un avoir
reste la prochaine vérification précise,avant une validation exhaustive de ce cycle.
