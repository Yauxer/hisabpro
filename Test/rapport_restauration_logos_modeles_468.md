# Restauration des logos et du catalogue 092 —468

Le scénario de restauration conjointe 452 a été rejoué avec la migration 092 et
des logos PNG intégrés sur les sociétés fictives du laboratoire. Les assertions
historiques sont inchangées ; le wrapper ajoute des contrôles d'identité, de
catalogue et d'image PDF lors des connexions source/cible.

**1 réussi 74,71 s**,29 avertissements, exit 0. La première tentative 61,15 séchouait
dans le banc : mot de passe optionnel non conservé par le wrapper. Correction
des préparatifs uniquement ; aucune règle produit ou assertion native relâchée.

Vérifications réelles : deux clusters PostgreSQL nonce distincts ; dump natif
avec ACL, copie des quatre pièces, source mise au repos par arrêt de son seul
processusAPI. **73 tables, schéma, données, séquences et droits identiques** à
la restauration ; FEC 2025 identique octet pour octet, refus FEC du brouillon
préservé, décision/PVrestitués, originaux conservés et reprise append-only.
ACL :1205 entrées de relations,26 de colonnes,140 de fonctions,4 de schéma public,
0 par défaut. Six connexions vérifient 64 modèles et un logo réellement rendu dans
un PDF du serveur ; cinq de ces contrôles ont lieu sur la cible restaurée.

Le LOGIN SQL applicatif n'est ni propriétaire ni superutilisateur. Les logos
sont préparés uniquement sur la source avant le dump ; la cible n'est jamais
réparée pour faire passer un contrôle. Les deux cibles jetables ont été nettoyées
par leurs contextes nonce ; aucun ancien répertoire ou processus utilisateur
n'a été supprimé. Preuve locale :`.codex-tests/restauration468_preuve.json`.

Commande : `python -X utf8 Test/run_unit_tests.py Test/test_restauration_logos_modeles_isole.py -ra`.
Le moteur de sauvegarde n'a pas changé. Compilation du nouveau banc avant ZIP.
Cette preuve ne qualifie pas une restauration de production, une copie à chaud,
des propriétaires différents ou une migration utilisateur. Recette humaine à faire.
