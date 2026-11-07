# Règlements en consultation seule — lot665

Le serveur refusait déjà les modifications d’un utilisateur Lecture.
L’interface affichait pourtant encore Modifier, Supprimer et Annuler par
contrepassation. L’absence de garde a été reproduite dans un vrai Edge
authentifié : **1échec attendu en43,87s**, bouton Modifier présent au lieu d’absent.

Les deux groupes de commandes utilisent maintenant `peutEcrire()`, comme la
ventilation et les autres écrans. La consultation RAS et Actualiser restent
disponibles. Les comptables conservent les commandes autorisées. Aucun droit
serveur, modèle ou migration modifié.

## Vérifications réellement exécutées

4 profils Edge/API/PostgreSQL102 réussis en 59,34 s, puis 12 parcours connexes réussis en 168,88 s ; zéro échec/erreur/ignoré. Lecture/Comptable, achat/vente,1440/390, GET200 et refus403 natifs, photographies comptables identiques et aucun POST navigateur. Build7,94 s, code0. Python compilé ; capture de liste Lecture390 inspectée. Campagnes recouvrantes non additionnées.

Quatre profils vente/achat, Lecture/Comptable, en1440/390 pixels : une facture
1200, un règlement non comptabilisé100 et un règlement comptabilisé200.
La facture et l’écriture bancaire sont validées avant la consultation.
Lecture ne voit aucune commande financière ; le comptable les retrouve.
Actualiser et consulter la RAS aboutissent à de vraisGET200. La RAS ne propose
aucune capture au lecteur. Les PATCH, DELETE et annulation directs du lecteur
renvoient403, sans changer la photographie comptable. Aucun POST/PATCH/DELETE
de règlements n’est émis automatiquement par le navigateur.

L’essai intermédiaire à quatre échecs provenait uniquement du sélecteur du
banc : Fermer désignait à la fois la croix et le bouton du dialogue.
La sélection par texte visible a été précisée ; aucun contournement de règle
métier. Les résultats initiaux restent consignés.

Ce lot harmonise cette liste et ses trois commandes ; il ne certifie pas
l’ensemble du RBAC de l’application ni les changements de rôle en cours de
session. Les tests utilisent PostgreSQL102 nonce sous LOGIN non propriétaire,
une vraie API et Edge. Aucun PostgreSQL réel ou donnée réelle touché.
Recette utilisateur et production restent à effectuer ; RH/paie différées.
