# Sociétés liées — association commerciale explicite

Dans **Paramètres → Sociétés liées**, l'administrateur de la société active
vendeuse choisit une autre société où il est également administrateur. Il
sélectionne le client qui représente l'acheteur chez le vendeur et le fournisseur
qui représente le vendeur chez l'acheteur, indique la justification et confirme
avoir vérifié l'association. Les tiers doivent déjà exister et être actifs.

Un ICE connu dans les deux fiches doit correspondre. L'absence d'ICE n'est pas
remplacée par une valeur présumée ; le choix reste une déclaration explicite de
l'administrateur, sans qualification fiscale de groupe ou de consolidation.

L'enregistrement de cette liaison **ne crée aucune facture, écriture ou mouvement
de stock**. Une seule liaison active est admise pour un vendeur et un acheteur.
Pour le sens inverse, préparer une liaison distincte avec les tiers appropriés.
Les droits sont relus dans les deux sociétés à chaque commande ; disposer d'un
ancien jeton ne conserve pas des droits retirés.

Les utilisateurs qui peuvent consulter les deux sociétés voient les liaisons
accessibles. Les lecteurs ne disposent pas des commandes d'administration.
Une société peut retirer son consentement avec un motif, même après perte de
droits chez l'autre société. L'historique est conservé ; une nouvelle association
peut ensuite être créée et ne réécrit pas l'ancienne. Un retrait n'annule pas une
pièce comptable existante et ne constitue pas une suppression de données.

La migration **101_societes_liees.sql** est additive, explicite, et dépend de la
fonction d'immutabilité083. Elle n'est pas appliquée automatiquement au démarrage.
Sans101, l'onglet affiche une indisponibilité explicite. Aucun script ne doit être
appliqué à une base réelle par analogie avec un banc de test ; suivre les
[procédures d'exploitation](EXPLOITATION_HISABPRO.md) avec sauvegarde et rôle dédié.

Qualification locale : PostgreSQL natif jetable sous LOGIN non propriétaire,
Edge1440/390 et consultation seule ; registre et retrait immuables, rejeu sur
données non vides. Voir le [rapport633](../Test/rapport_societes_liees633.md).
L'installation utilisateur et la recette humaine restent à effectuer.

Prochaine étape : préparer une facture d'achat correspondante à partir d'une
facture de vente validée, avec choix des articles de l'acheteur et aperçu. Ce
pont n'est pas encore inclus dans le lot633. RH/paie restent différées.
