# MODE D’EMPLOI ET RECETTE — RECHERCHE D’ARTICLES COMMERCIAUX

Version 1 du 22 octobre 2026. Devis de vente et commandes d’achat, sans changement comptable.

## Ce qui change

Dans les formulaires commerciaux, le champ Article ou description recherche
dans la désignation et le code des articles disponibles de la société active.
La recherche ignore la casse et les espaces en début/fin. Sans correspondance,
la liste complète ne réapparaît plus. Vider la recherche affiche les articles.

Le chargement, un catalogue réellement vide, une recherche sans résultat et
une erreur de lecture sont distingués. Une erreur propose Réessayer le catalogue.
Après rétablissement du service, ce bouton recharge les articles sans F5 et
conserve la description saisie. La saisie d’une description libre reste possible.
Cela ne garantit pas un enregistrement tant que le backend est indisponible.

Une réponse ancienne ne doit pas remplacer la recherche courante ou les données
d’un nouveau contexte d’authentification. Les prix achat/vente, frais, TVA et
règles de stock existants ne sont pas modifiés. La sélection d’un article reste
distincte d’une description libre : un clic est nécessaire pour le rattacher.

## Données exactes de recette

Utiliser uniquement une société fictive Catalogue recette737, MAD, exercice2026,
avec un administrateur ou comptable. Créer un client Client fictif737 et un
fournisseur Fournisseur fictif737. Dans Articles, créer deux services non
stockables : code ALPHA737, désignation Alpha fictif737 ; code BETA737,
désignation Beta fictif737. Pour les deux : prix vente HT100, prix achat HT80,
TVA déclarée20%, emballage/transport0 si les champs sont renseignés.

Ces montants et taux servent exclusivement au test. Ils ne qualifient pas
fiscalement une prestation réelle. Pour tester le vrai catalogue vide, utiliser
une autre société fictive Catalogue vide737 sans article ; ne pas supprimer
les articles d’une société existante.

## Utilisation et vérification

1. Ouvrir Cycle commercial → Vente → Nouveau devis. Cliquer Article ou description. Attendre le chargement des deux services.
2. Saisir INEXISTANT737. Le message Aucun article ne correspond à la recherche apparaît ; Alpha et Beta ne sont pas proposés. Le texte reste modifiable.
3. Remplacer par bEtA ou par BETA737. Seul Beta fictif737 est proposé. Cliquer sa ligne : la désignation est reprise, prix HT100 et TVA20. Quantité1 donne100HT/20TVA/120TTC, sans enregistrer pour l’instant.
4. Fermer avec Annuler. Passer à Achat → Nouveau BC. Rechercher Beta et sélectionner le service : prix HT80, quantité1, TVA20, soit96TTC. Le champ utilise le prix d’achat du service, pas son prix de vente.
5. Pour une description libre, remplacer le texte par Prestation libre fictive737 et saisir le prix100. Choisir Fournisseur fictif737. Créer la commande :120TTC. Vérifier la nouvelle commande dans la liste puis son détail. Elle ne doit pas être rattachée à Beta par erreur. Aucun mouvement de stock ni écriture ne découle de cette seule commande de service.
6. Refaire le scénario Vente avec Client fictif737 : Prestation libre fictive737, quantité1, prix100, TVA20 ; Créer le devis. Vérifier120TTC dans le détail. Le numéro définitif est attribué par le serveur ; utiliser celui affiché pour la preuve, sans inventer de numéro.
7. Pour tester une panne, faire préparer l’indisponibilité temporaire du backend par le responsable sur un environnement de recette isolé. Ouvrir le formulaire après chargement de la page : Catalogue indisponible apparaît. Ne pas le confondre avec un catalogue vide. Saisir Description libre737 ; la saisie reste possible.
8. Après remise en service du bac de recette, cliquer Réessayer le catalogue. Le message d’erreur disparaît, les suggestions suivent le texte actuel. Rechercher Beta, vérifier son prix et annuler si aucune pièce n’est souhaitée. Ne jamais provoquer cette panne en production.

Dans une société fictive sans article, le message Aucun article disponible est
normal et distinct d’une panne. Une description libre, un prix et une TVA
explicitement saisis permettent de préparer la pièce sans créer un article.
Les contrôles de stock du devis restent indicatifs : un devis à approvisionner
peut être conservé selon la règle déjà choisie par l’utilisateur.

## Recette humaine à effectuer

Les tests automatisés ne remplissent pas les statuts de ce tableau. Prérequis
communs : société et données fictives ci-dessus. Aucun impact fiscal confirmé
ni écriture comptable attendu pour ces devis/commandes de service. L’absence de
mutation pendant une simple recherche doit être contrôlée. Conserver les
captures et détails des pièces créées dans le classeur de suivi.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|CAT737-01|Vente → Nouveau devis ; rechercher INEXISTANT737 parmi Alpha/Beta.|Message sans résultat, aucune suggestion Alpha/Beta, aucune pièce créée ; capture.|Non testé|
|CAT737-02|Rechercher bEtA puis BETA737 ; sélectionner en Vente puis Achat, quantité1.|Beta seul ; prix100/120TTC en vente et80/96TTC en achat ; captures, annuler les essais.|Non testé|
|CAT737-03|Créer une société fictive Catalogue vide737 sans article et ouvrir un devis.|Aucun article disponible, aucune erreur de chargement ; description libre possible ; capture.|Non testé|
|CAT737-04|Responsable prépare une panne sur le seul bac de recette ; saisir Description libre737 ; rétablir puis Réessayer.|Erreur distincte du vide, texte conservé, reprise sans F5 ; deux captures. Si bac indisponible, classer Bloqué.|Non testé|
|CAT737-05|Sur la société principale fictive, sélectionner Beta puis saisir Prestation libre fictive737, prix100, quantité1, TVA20 ; créer devis/BC avec les tiers indiqués.|Deux pièces120TTC, descriptions libres sans rattachement erroné à Beta ; aucun stock/écriture créé ; détails et Journal témoin.|Non testé|
|CAT737-06|Chercher Beta, fermer sans enregistrer ; changer de société par le sélecteur et ouvrir un nouveau devis dans Catalogue vide737.|Aucun article de la première société proposé ; catalogue vide courant, ancienne saisie non enregistrée ; captures et listes inchangées.|Non testé|

## Validation technique et limites

Les tests Edge connectés couvrent vente/achat sur1440/390pixels, refus SQL natif
uniquement dans un cluster nonce, réessai, création libre120TTC et réponses HTTP
réelles retenues pendant recherche/changement de jeton/fermeture.
Le test du jeton change directement le contexte d’authentification ; il ne
remplace pas une recette humaine du sélecteur multi-société complet.
Les prix et règles métier du backend restent inchangés. Aucune migration.

Recette utilisateur et installation cible restent à effectuer. La liquidation
fiscale externe et EDI attendent leurs sources officielles applicables ; ce lot
n’ajoute aucune règle fiscale. RH/paie etpoint6 humain restent différés.
