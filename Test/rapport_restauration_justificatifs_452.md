# Restauration conjointe des justificatifs et droits — lot 452

Recette du 15 octobre 2026. Deux clusters PostgreSQL nonce distincts ; aucun
PostgreSQL utilisateur, dossier réel ou document comptable réel utilisé.

## Périmètre et méthode

La source utilise le vrai serveur `main:app` sous LOGIN `hisabpro` non propriétaire,
après 82 scripts distincts appliqués sur des tables métier vides, jusqu'à 091.
Cette préparation explicite du banc ne modifie pas le CLI 090 ni le bootstrap.

La recette annuelle bancaire existante est réutilisée avec ses oracles et son
parcours Edge : clôture 2025, à-nouveaux, paiements 2026 et lettrage. Une décision
fictive d'affectation de perte de 3 000 est créée par le flux déjà testé du lot 448.
Ce jeu ne constitue pas une décision sociale réelle ni une validation fiscale.

Quatre PDF sont ajoutés : deux homonymes sur une écriture définitive, une pièce de
brouillon et un PV fictif rattaché à l'écriture d'affectation. Références manuelles,
priorités, auteurs et historique sont présents avant la sauvegarde.

Seul le processus API créé par ce banc est arrêté avant la copie et `pg_dump` :
aucun auteur de mutation ne subsiste pendant cette fenêtre. Le dump et les pièces
restent dans le répertoire nonce ; ils ne sont pas livrés. La cible est vide et le
LOGIN limité est préparé séparément. `inclure_droits=True` est explicite aux deux
extrémités ; le défaut sans ACL des outils existants reste inchangé.

## Contrôles réellement réussis

- Schéma, 73 tables, données brutes, séquences et leurs états identiques avant
  toute reprise HTTP. Comparaison native des ACL : 1 205 entrées sur relations,
  26 sur colonnes, 140 sur fonctions, quatre entrées de droits sur le seul schéma
  `public`, zéro privilège par défaut supplémentaire. Il ne s'agit pas de quatre
  schémas.
- Quatre fichiers : même arborescence, taille et SHA256. Les PDF homonymes ont des
  noms physiques distincts et des contenus distincts. Copie et dump refusent
  l'écrasement ; une deuxième restauration sur la cible remplie est refusée.
- Second vrai `main:app`, `HISABPRO_CREATE_TABLES=false`, LOGIN effectif sans
  SUPERUSER/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS, sans propriété d'objet ni
  appartenance au migrateur. Aucune migration historique rejouée après restore.
- Authentification réelle, catalogue de modèles, références et PDF restitués.
  Le lecteur télécharge mais ne dépose pas de pièce et n'ajoute pas de référence
  (403) ; une autre société ne voit pas le document (404).
- FEC annuel 2025 identique octet par octet. L'autre dossier contenant un brouillon
  reste refusé en 409 avec le même diagnostic : aucun contournement du contrôle.
- Décision 091 et PV restitués, état post-clôture identique. Nouvelle référence
  prioritaire et nouveau fichier ajoutés après restore sans réécrire les lignes
  ou écritures définitives. Suppression définitive refusée ; pièce brouillon
  supprimée par le flux normal. Triggers append-only et refus SQL de suppression
  de décision toujours effectifs.
- Source entièrement préservée ; écritures, lignes, clôtures et décisions de la
  cible inchangées après les opérations documentaires. Deux clusters, fichiers et
  processus créés nettoyés ; assertion réelle des répertoires après sortie.

## Tests et preuves

- Premier essai : un échec en 56,74 s, répertoire temporaire du banc absent avant
  écriture du FEC. Corrigé par création du répertoire, sans changement produit.
- Ciblé final : **1 réussi en 69,37 s**, 29 avertissements, zéro échec/erreur/ignoré.
- Suite connexe : **24 réussis en 140,17 s**, 29 avertissements,
  zéro échec/erreur/ignoré. Inclut cette recette, les sept cas 451, la restauration
  ACL existante, les gardes de restauration et les permutations d'ordre FEC.
- Compilation Python du nouveau fichier : code 0.

Preuves locales exclues du ZIP : `restauration452_cible.*`,
`restauration452_v2.*`, `restauration452_connexes.*` et
`restauration452_preuve.json`. Les tests sont livrés pour rejouer le banc.
Les suites recouvrantes ne s'additionnent pas.

## Limites et suite

Cette recette qualifie une restauration sur cible nonce vide, avec même nom de
migrateur propriétaire. Elle ne fournit pas de restauration automatique en
production, de sauvegarde à chaud coordonnée ou de validation sur d'autres
propriétaires. Aucun secret ni rôle global n'est inclus dans `pg_dump`.

La recette utilisateur, l'installation réelle et le plan d'exploitation restent
à valider. Aucun livrable humain n'est marqué réussi automatiquement. Point 6
reste en attente. Suite : contrôler les erreurs de téléchargement documentaire,
puis actualiser couverture/procédures et fournir le cumulatif différentiel.
