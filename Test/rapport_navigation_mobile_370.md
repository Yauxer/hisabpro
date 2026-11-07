# Navigation mobile et largeur utile — lot370

## Défaut et correction

À390px, la navigation fixe220px ne laissait que170px au contenu.
L'oracle navigateur avant correction conserve1échec/3désélectionnés,
27,25s,code1. Les captures368 confirment ce défaut de présentation.

Sous768px, le menu devient un panneau repliable avec bouton explicite,
fermeture après navigation, croix, clic extérieur et Échap. Le clavier reste
dans le panneau ouvert et le focus revient au bouton. Le bandeau société
et exercice s'adapte sur plusieurs lignes. Le menu desktop reste visible.
Les sous-menus fermés ne gardent plus leurs liens dans le parcours clavier.

Un filtre Effets débordait également de sa carte :bord droit370 contre362.
Un nouvel oracle conserve1échec/3désélectionnés,25,07s,code1.
La largeur de ses champs est maintenant limitée au conteneur sur mobile.

## Tests réellement exécutés

- Première tentative :2échoués/2réussis,63,80s. Le helper de connexion
  supposait Déconnexion toujours visible. Il ouvre désormais le vrai menu
  mobile, vérifie le contrôle puis ferme par Échap. Deux recettes de
  déconnexion mobile suivent ce même parcours. Aucun contrôle métier réduit.
- Quatre parcours390/767/768/1365 :4réussis,33,96s,code0.
  Largeur utile, bureau inchangé, Tab/Maj+Tab, Échap, clic extérieur,
  fermeture par route, retour du focus et conservation des sources.
- Connexes avant la dernière correction du filtre :40réussis,
  26avertissements,275,54s,code0. Navigation, règlements, administration,
  paie/GRH, pièces client, icônes, liasse et cache du plan comptable.
- Sources finales après le filtre :18réussis/10désélectionnés,
  26avertissements,103,34s,code0. Quatreparcours navigation,8Commercial,
  6Effets/Chèques connectés avec vérification de conservation des sources.
- BuildVite final :code0,5,00s ; avertissements xlsx/bundle déjà présents.
- Compilation des quatre fichiers de tests modifiés :code0.

Les suites se recoupent ; les résultats ne s'additionnent pas.
Le snapshot final couvre692sources et doit rester identique à la livraison.
Captures390/767 inspectées et captures finales des règlements/effets disponibles
dans le cache de recette. Les tables larges gardent un défilement horizontal
quand leur page le nécessite ; ceci n'est pas une recette exhaustive mobile.

## Limites et reprise

Aucun modèle, SQL, migration ou donnée comptable réelle modifié.
Les tests connectés utilisent uniquement PostgreSQL éphémère nonce gardé.
La globale365 précède368 et370 ; les suites ciblées couvrent ces changements.
Recette sur les appareils réels et préparation de production restent à faire.

Reprendre ensuite la recette annuelle intégrée et les règlements multi-factures,
avec les limites réglementaires et justificatifs manquants conservés.
