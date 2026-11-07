# Sauvegarde et restauration conjointes PostgreSQL et pièces documentaires

8 octobre 2026 — lot 246. Deux nouveaux fichiers de recette uniquement ; aucun
code applicatif, outil d'exploitation ou support partagé modifié.

## Dossier fictif et fenêtre de sauvegarde

La source utilise le support `application_isolee` : vrai serveur FastAPI,
PostgreSQL éphémère marqué, tables ORM et seule migration 036 nécessaire au
support d'audit. Deux comptes CGNC synthétiques complètent le référentiel de
laboratoire avant inscription. Aucune chaîne complète de migrations ni réparation
historique n'est lancée.

Les données sont créées par API : société fictive, administrateur, lecteur,
client, article stockable avec stock initial 5 et prix d'achat 40 MAD, BL vente
en préparation de 2 unités. Une seconde société fictive et son administrateur
servent à vérifier l'isolation après restauration. Aucune facture validée ni
écriture comptable n'est créée dans ce scénario.

Trois documents sont déposés par HTTP sur le BL : deux vrais PDF ayant le même
nom original mais des contenus fictifs distincts, et une image PNG. Les noms
physiques retournés sont tous distincts. Les PDF sont relus avec pypdf avant
upload. Les fichiers sont dans la racine `HISABPRO_UPLOAD_DIR` privée du test ;
le dossier réel `hisabpro-backend/uploads` n'est jamais utilisé.

Avant `pg_dump` et la copie des pièces, le test arrête exclusivement son propre
processus API source. Aucun autre auteur de mutation du laboratoire ne subsiste.
Cette fenêtre contrôlée permet une sauvegarde cohérente ; elle ne prétend pas
implémenter une sauvegarde à chaud atomique des fichiers et de PostgreSQL.

## Restauration réellement exécutée

1. Photographie intégrale de 9 tables : sociétés, utilisateurs, liens utilisateurs/
   sociétés, articles, BL, lignes BL, mouvements de stock, écritures et lignes
   d'écriture. Les fichiers déposés ne modifient aucune de ces lignes.
2. Copie de l'arborescence des pièces dans un nouveau dossier de sauvegarde.
   Comparaison du manifeste relatif taille/SHA-256 pour les trois fichiers.
3. `ops/postgres_sauvegarde.sauvegarder` exécute le vrai `pg_dump` custom dans ce
   dossier privé. Le fichier dump est présent et non vide ; la source reste
   identique à sa photographie.
4. `restaurer_isole` exécute le vrai `pg_restore` dans un **second cluster nonce**,
   à port distinct et base vide. Les neuf tables restaurées sont exactement
   égales aux tables sources, y compris identifiants, dates et valeurs.
5. Copie des pièces vers une nouvelle racine privée du second cluster, en
   conservant l'arborescence société/type/identifiant document. Aucun dossier
   ou fichier existant n'est écrasé. Taille et SHA-256 restent identiques.
6. Nouveau serveur FastAPI lancé avec connexion cible et `HISABPRO_UPLOAD_DIR`
   explicites. Authentification réelle avec les comptes restaurés : mêmes
   société, BL, numéro et fichiers visibles. Administrateur et lecteur
   téléchargent chacun les trois pièces par HTTP ; les six contenus ont
   exactement les empreintes des originaux.

Le lecteur reçoit 403 pour upload/suppression. L'administrateur de l'autre
société reçoit 404 pour liste, téléchargement et upload sur ce BL. Les pièces,
stocks, BL et écritures restent identiques après ces refus. Une seconde tentative
de restauration sur la cible devenue non vide est refusée avant toute suppression ;
le contenu restauré reste intact.

Les connexions utilisent le propriétaire du laboratoire pour préparer/restaurer
les bases. Cette recette valide les permissions applicatives réelles ; elle ne
certifie pas les ACL d'un rôle PostgreSQL de production. Les événements d'audit
des nouvelles connexions restent distincts des neuf tables métier comparées.

## Commandes et résultats réels

Exécutable : `hisabpro-backend/.venv/Scripts/python.exe -X utf8`.

| Commande après l'exécutable | Résultat |
|---|---|
| `Test/run_unit_tests.py Test/test_sauvegarde_pieces_documents_isole.py --tb=short` | Première exécution : 1 échec en 29,26 s. La requête du test listait les BL sans le paramètre exercice obligatoire, HTTP 422 ; restauration déjà effectuée, aucun défaut produit établi. |
| Même commande, requête corrigée avec exercice explicite | 1 réussi en 28,32 s, exit 0, aucun échec ou ignoré. |
| `Test/run_unit_tests.py Test/test_session132_sauvegarde_postgres.py Test/test_fact9_documents_pdf.py --tb=short` | 13 réussis en 11,11 s, exit 0. |
| `-m py_compile Test/test_sauvegarde_pieces_documents_isole.py` | Exit 0. |

Aucun navigateur n'est utilisé par cette recette conjointe : les API sont
appelées en HTTP sur de vrais serveurs séparés. Les parcours navigateur de dépôt
et téléchargement relèvent du lot 240 existant, sans être comptés à nouveau ici.

## Isolation, nettoyage et limites

Les deux clusters possèdent des marqueurs/nonce distincts vérifiés avant les
opérations. Les ports sont loopback et différents de 5432. Les dossiers source,
sauvegarde et cible sont résolus puis contrôlés comme descendants des racines
temporaires attendues. Les seuls processus arrêtés sont ceux créés par ce test.
Les deux clusters et les dossiers privés sont supprimés par leurs contextes à
la sortie ; leur absence est vérifiée.

Aucun PostgreSQL réel, fichier comptable réel, dossier d'upload réel ou processus
main/Vite de l'utilisateur n'est touché. Le test n'applique aucune migration sur
un déploiement réel. Les dumps et les pièces de laboratoire ne font pas partie
du ZIP différentiel.

Cette preuve établit une restauration conjointe réduite avec source arrêtée.
La politique de conservation, la programmation des sauvegardes, le chiffrement,
les copies hors site, la reprise après sinistre, les volumes importants et la
coordination d'une sauvegarde à chaud restent des validations d'exploitation.
Le scénario ne valide pas les protections SQL d'écritures définitives restaurées,
déjà testées séparément dans les lots dédiés.
