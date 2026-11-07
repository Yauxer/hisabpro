# Préparer une réception depuis la commande — lot669

Le bouton « Nouveau BR » de la liste des réceptions ouvrait en réalité un
formulaire de commande. Une commande créée restait ensuite invisible dans la
liste des BR, ce qui rendait l’action trompeuse. Le bouton est remplacé par
**Préparer depuis une commande**, qui ouvre les commandes achat. Le formulaire
mal placé et son état local sont retirés.

La navigation ne crée rien. L’utilisateur choisit une commande existante ou
crée explicitement un Nouveau BC, puis utilise Créer un bon de réception sur
le reliquat. L’entrée de préparation est réservée au rôle autorisé ; Actualiser
et la consultation restent disponibles. Aucune permission serveur changée.

La bascule Vente/Achat pouvait aussi être comprimée par le titre sur mobile.
Le bandeau se replie et la bascule conserve sa largeur ; les deux boutons
sont entièrement visibles, sans modifier la charte graphique.

## Résultats réellement exécutés

Avant correction, **1échec attendu en34,91s** : l’ancien bouton reste présent.
Les quatre nouveaux profils passent en45,74s, build6,87s. Admin1440 et
Comptable390 créent, après navigation sans effet, un BC achat de2×500HT,
TVA200, TTC1200, puis un BR lié à cette commande. Lecture1440/390 ne voit
aucune entrée de création ; un POSTBC direct est refusé403. Dans le profil
de stock sur facture utilisé par le jeu, aucun stock, mouvement ou écriture
n’est créé par la navigation, le BC ou ce BR non facturé.

16 parcours connexes réussis en 210,93 s après les 4 profils ciblés45,74 s ;zéro échec/erreur/ignoré. Réceptions/années/jetons, achats complets et partiels, rôles des règlements vérifiés sur PostgreSQL nonce et Edge. Build6,87 s code0, Python compilé. Capture Comptable390 inspectée : bascule entière et BR lié visible. Campagnes recouvrantes non additionnées.

Les comparaisons portent sur de vraies tables et de vraies API PostgreSQL091
nonce sous LOGIN non propriétaire. Les tests contrôlent aussi les rectangles
visibles des deux boutons de mode et l’absence de débordement horizontal.
La capture finale mobile du comptable est inspectée. Aucune réponse métier
fabriquée ; aucune donnée réelle ni migration touchée.

Les autres commandes des BC/BR et les mutations tardives restent des périmètres
distincts ; ce lot ne certifie pas tout le RBAC commercial. Recette utilisateur
et production non validées ; RH/paie et point6 humain différés.
