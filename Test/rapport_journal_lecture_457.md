# Journal en consultation seule — lot 457

## Défaut et correction

Le serveur protégeait déjà les mutations par 403, mais l'interface du Journal
proposait encore création, validation, modification, suppression, contrepassation
et ajout documentaire au lecteur. L'export FEC tentait aussi une réparation
automatique non autorisée avant d'afficher les diagnostics.

La correction réutilise `peutEcrire`, déjà utilisé dans le produit. Création et
validation globale sont désactivées en consultation seule ; les commandes de
mutation des lignes et les formulaires de complément sont masqués. Le composant
de pièces jointes reçoit son mode lecture seule. Aucun POST de réparation FEC
n'est tenté pour le lecteur et la notice explique le contrôle sans réparation.

Les anomalies restent toutes visibles. Lecture du Journal, des pièces et de
l'historique, téléchargement, audit et diagnostics FEC restent accessibles. Le
comptable conserve son ajout de référence. Aucune nouvelle permission backend,
aucune règle comptable ou condition obligatoire de validation ajoutée.

## Tests réels

Vrai `main:app`, PostgreSQL nonce 091, LOGIN SQL non propriétaire, comptes
lecture/comptable fictifs. Mobile 390 px et ordinateur 1 440 px.

- Avant : un échec/un réussi en 31,59 s ; bouton de création actif pour le lecteur,
  parcours comptable complet déjà réussi.
- Après : **2 réussis en 25,96 s**, 29 avertissements, zéro échec/erreur/ignoré.
- Trois écritures, dont une sans référence volontairement : la validation légère
  reste autorisée, le diagnostic FEC de référence manquante reste visible. Aucun
  complément arbitraire n'est ajouté pour masquer ce contrôle.
- Le lecteur lit et télécharge le vrai PDF, sans requête de mutation depuis ces
  commandes UI. Deux tentatives API explicites de validation/justification restent
  refusées en 403. Le comptable ajoute réellement une référence. Écritures/lignes
  brutes inchangées pour les deux profils.
- Connexes : **94 réussis en 227,11 s**, 29 avertissements,
  zéro échec/erreur/ignoré. Modèles choisis/détectés, justificatifs, téléchargements,
  lettrage, FEC, facturation, erreurs de saisie et CSV réel du Journal inclus.
- Build Vite : code 0, **4,70 s** ; avertissements de taille de bundle et
  d'import statique/dynamique xlsx conservés. Compilation Python du test : code 0.

Preuves locales `journal457_avant.*`, `journal457_apres.*`,
`journal457_connexes.*`, `journal457_build.*`, exclues du ZIP. Les suites
recouvrantes ne s'additionnent pas.

## Limites et suite

Le rôle d'interface ne remplace jamais l'autorisation côté serveur, relue en base
à chaque requête. Modifier le cache local ne donne pas un droit d'écriture. Ce lot
ne prétend pas qualifier l'ergonomie de tous les autres écrans ni le rafraîchissement
instantané d'un rôle changé par un autre administrateur.

Aucun PostgreSQL réel touché. Installation, recette utilisateur et production
non prévalidées ; point 6 en attente. Suite : compléter les bornes techniques des
montants entrants, regrouper les parcours de reprise et actualiser la couverture.
