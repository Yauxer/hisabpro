# Annulation collective : réponse de preview devenue obsolète — lot388

## Anomalie reproduite et correction

Le GET de prévisualisation pouvait revenir après un changement d'exercice ou de jeton. L'ancienne réponse demandait encore confirmation ; le POST suivant lisait le jeton courant, ce qui était dangereux si le même UUID était utilisé dans deux sociétés.

Garde minimale dans `Commercial.jsx` : génération de l'action, exercice, cycle et jeton sont capturés. Après la lecture, avant le POST et après sa réponse, le contexte doit rester identique. Le nettoyage invalide les anciennes actions ; elles ne demandent plus confirmation, n'envoient pas de POST et ne rafraîchissent pas le nouveau contexte. Une ancienne opération ne peut pas libérer le bouton d'une nouvelle action. Le backend reste inchangé.

## Tests réels

Edge et vraie API sur PostgreSQL nonce temporaire. Le GET réel est récupéré puis retenu avant livraison au navigateur. Changement d'exercice via le sélecteur ; pour le cas session, remplacement du jeton dans le navigateur de test par celui d'une seconde société fictive, qui possède un lot avec le même UUID. Il ne s'agit pas d'une recette du sélecteur multi-société complet.

- Avant garde : **1 échec réel**, 26 avertissements, 23,76 s ; confirmation obsolète observée après changement d'exercice.
- Copie corrigée : **26 réussites**, 26 avertissements, 74,53 s — quatre contextes Edge bureau/mobile et les 22 cas d'annulation normales.
- Version intégrée à la racine : **4 réussites**, 26 avertissements, 33,44 s, code0. Aucune confirmation ni POST, conservation des sources des deux sociétés.
- Build final Vite : code0,4,83s, avertissements xlsx/taille habituels. Compilation Python du test : code0.

Les suites se recoupent, leurs effectifs ne sont pas additionnés. La précédente consolidation385,228réussites/701empreintes stables, précède ce lot. La consolidation389 vérifie ensuite les versions finales avec le nouveau banc inclus.

Aucun PostgreSQL réel, donnée comptable réelle, modèle ou migration modifié. Les annulations déjà envoyées dans un contexte valide ne sont pas prétendues annulables par un changement d'écran ; la garde empêche seulement une ancienne preview de déclencher une nouvelle action. Recette utilisateur à effectuer ; point6 en attente.
