# Permissions du cycle commercial — lot436

## Problème et correction

Sur le socle existant, le rôle PostgreSQL applicatif `hisabpro` peut lire les
documents commerciaux, mais leur création échoue. Le banc a réellement reproduit
les refus SQL42501 sur les six tables, puis deux erreurs de préparation des tests
vente/achat :HTTP500 sur création du devis ou de la commande,17.61s.

La migration additive et manuelle `085_permissions_documents_commerciaux.sql`
complète077/079 sur une liste fermée :devis,lignes_devis,bons_commande,
lignes_bon_commande,bons_livraison,lignes_bon_livraison. SELECT/INSERT/UPDATE/DELETE
permettent les flux etles suppressions de brouillons existants ;USAGE/SELECT sont
accordés sur leurs séquences. Aucun rôle,table,document ou écriture créé par085.
Empreinte SHA256 :`8d624003fced83890072e33b4bb20dd8a1f200884d87f396acb60fab34ba7ee6`.

Aucun droit ajouté sur les autres tables,audits ou archives. Aucun TRUNCATE,
CREATE de schéma ni nouveau UPDATE/SETVAL de séquence. Les droits hérités005
sur certaines séquences sont conservés etcomparés ;ils ne sont pas annoncés
supprimés. L’absence du rôle ne crée rien etle rejeu conserve les droits/données.

## Tests réellement exécutés

Après correction :6tests réussis27.25s,puis15tests étendus réussis31.68s.
73 tests connexes réussis, zéro échec, erreur ou ignoré, 146.876 s ; ciblés étendus :15réussis31.68s ; compilationPython code0.

Commande connexe :`Test/run_unit_tests.py
Test/test_permissions_documents_commerciaux_postgres.py
Test/test_permissions_cycle_facturation_postgres.py
Test/test_permissions_suppression_brouillons_postgres.py
Test/test_runtime_permissions_postgres.py
Test/test_e2e_cycle_commercial_isole.py Test/test_e2e_cycle_achat_isole.py`.

Le nouveau banc utilise le socle SQL puis078–084 et085 ;la seule dépendance
injectée est get_db vers une connexion LOGIN hisabpro nonpropriétaire.
AuthentificationJWT etpermissions API réelles, sans remplacement des rôles.
Quatre cycles :vente/achat ×service/article stockable ;devisvente→BC→BL,
BCachat→BR,puis facture,validationcomptable,règlement120 etlettrage à3lettres
minimum. Par société,deux écritures définitives,débit=crédit=240 ;stockvente3→2,
stockachat0→1,services sans mouvement. Traçabilité des lignes de source vérifiée.
Conversions en double refusées409,lecteur403,autre société404,modifications de
définitives refusées23514. Le rejeu conserve les13tables documentaires/comptables
photographiées. Création/modification/suppression des trois brouillons avec lignes
vérifiée. Les E2E connexes existants exécutent également les écransvente/achat.

## Installation et limites

085 est exclusivement une migration manuelle à examiner pour la cible après
077/079 etles protections déjà prévues. Elle n’est pas ajoutée au bootstrap.
Elle a été exécutée uniquement sur PostgreSQL nonce jetable ;aucune base réelle.
Les preuves historiques433/434 restent celles de l’installation/restauration084.
Les droits de tous les autres modules,notamment acomptes/avoirs,restent àqualifier.
Recette utilisateur etproduction nonvalidées ;la globale430précède ces sources.
