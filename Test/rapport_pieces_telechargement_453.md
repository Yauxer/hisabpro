# Refus de téléchargement des pièces — lot 453

Deux cas reproduits dans Edge, sur le vrai `main:app` et PostgreSQL nonce 091
avec LOGIN SQL limité. Aucun endpoint intercepté, document réel ou PostgreSQL
utilisateur utilisé.

## Défaut et correction

Après affichage d'une pièce, un autre client supprime le document brouillon ou
l'administrateur désactive le compte comptable. Le GET de téléchargement répond
respectivement 404 sur ordinateur (1 440 px) et 401 sur mobile (390 px).

Avant correction, le composant appelait `res.blob()` quel que soit le statut.
Chaque refus déclenchait réellement un téléchargement sous le nom PDF demandé,
contenant `{"detail":"Fichier introuvable"}` ou le message de compte désactivé.
Deux échecs réels en 36,15 s ont été conservés.

Le statut est maintenant contrôlé avant de créer le Blob ou le lien. Le refus
affiche « Téléchargement impossible » avec le détail disponible ; aucun document
fictivement réussi n'est enregistré. Les erreurs réseau sont également capturées.
L'ancre temporaire et l'URL objet sont libérées après le clic d'un téléchargement
réussi. Aucune modification du backend, des droits ou du format des documents.

## Tests réellement exécutés

- Deux ciblés : **2 réussis en 25,33 s**, 29 avertissements,
  zéro échec/erreur/ignoré. GET 404/401 effectivement reçus, aucun événement download,
  message visible et données de l'écriture inchangées.
- Suite connexe : **46 réussis en 142,69 s**, 29 avertissements,
  zéro échec/erreur/ignoré. Inclut les téléchargements positifs du Journal et des
  réceptions client, la restauration documentaire, les erreurs de saisie, le FEC,
  les modèles et les permissions. Les PDF téléchargés sont réellement relus.
- Build Vite : code 0, **4,81 s** ; avertissement de taille de bundle conservé.
- Compilation Python du nouveau fichier de test : code 0.

Preuves exclues du ZIP : `telechargements453_avant.*`,
`telechargements453_apres.*`, `telechargements453_connexes.*` et
`telechargements453_build.*` dans `.codex-tests/`. Les tests livrés permettent
de rejouer les deux parcours. Les suites recouvrantes ne s'additionnent pas.

## Limites et suite

Edge est réellement testé ; la recette manuelle sur les autres navigateurs reste
à faire. Ce lot ne modifie ni le contenu autorisé à l'upload ni le mécanisme global
de reconnexion. Il ne qualifie pas un archivage légal. La base réelle reste intacte,
la recette utilisateur et la production ne sont pas prévalidées. Point 6 en attente.

Suite : étendre le parcours des modèles achat/vente et trésorerie jusqu'au lettrage
et au FEC sous le même rôle limité, puis actualiser la couverture et le cumulatif.
