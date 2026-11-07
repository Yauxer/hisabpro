# Réceptions fournisseurs : lecture et contexte — lot667

Deux défauts de l’écran Achat → Bons de réception ont été reproduits avant
correction : un refus SQL devenait « Aucun bon de réception », puis un vrai
GET2026 retenu remplaçait les BR2025 déjà chargés. **Deux échecs attendus en44,32s.**

L’écran distingue désormais chargement, erreur, vrai vide et liste disponible.
Réessayer et Actualiser relisent les données. Un refus n’affiche pas un compteur
zéro ; les réponses doivent encore correspondre à la génération, à l’exercice
et au jeton courants. Les réponses d’un composant démonté sont écartées.
La modification reste dans la lecture du composant ; aucun calcul, stock,
statut commercial ou génération de facture n’est changé.

## Vérifications réellement exécutées

8 Edge ciblés réussis en 62,69 s puis 12 connexes réussis en 199,70 s ;zéro échec/erreur/ignoré. BC/BR/facture et réceptions partielles, rôles et lectures de règlements vérifiés. Build6,25s code0, Python compilé. Capture erreur390 inspectée ; ACL et données métier après authentification préservées. Aucun stock, calcul, générateur comptable, SQL ou PostgreSQL réel modifié. Les campagnes recouvrent les précédentes.

Les huit cas ciblés utilisent PostgreSQL091 nonce sous LOGIN non propriétaire,
une vraie API et Edge en1440/390 pixels. Le SELECT de `bons_livraison`, table
partagée avec les réceptions de type achat, est temporairement révoqué puis
rétabli ; les ACL doivent être strictement identiques. Les réponses retenues
sont obtenues par de vraisGET, sans fabriquer leur contenu. Les données métier
avant/après lecture, hors audit des requêtes, restent identiques.

Deux cas intermédiaires ont échoué parce que le banc mélangeait un jeton de
sociétéB avec le contexte et le plan de sociétéA : Layout refuse ce mélange
avant de monter la liste. Ils ont été remplacés par un vrai renouvellement de
jeton du même compte/société suivi d’un changement d’exercice. L’injection ne
simule pas une réponse métier. Les six succès/deux échecs en93,22s de ce banc
restent consignés ; aucune validation d’un sélecteur multi-société complet
n’est déduite de ces deux cas.

Aucun PostgreSQL réel, migration ou source comptable modifié. Les cas de cycle
connexes vérifient que BC → BR → facture et les mouvements de stock restent
ceux du flux existant. Les campagnes se recouvrent et ne s’additionnent pas.

## Suite

Le bouton historique « Nouveau BR » ouvre une création de commande. Corriger
cette entrée dans un lot distinct669 : orienter explicitement vers les
commandes achat, puis préparer la réception depuis la commande. Les autres
listes commerciales et les mutations tardives restent des périmètres distincts.
Recette utilisateur et production non validées ; RH/paie différées.
