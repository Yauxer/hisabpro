# Lot516 — Cycles commerciaux et logos sous rôle applicatif

## Objectif et périmètre

Après les protections de clôture/fiscalité514, réutiliser les oracles navigateur
existants sur le rôle PostgreSQL LOGIN non propriétaire, avec le schéma098.
Les dix scénarios sont exécutés ensemble dans un environnement éphémère nonce.
Les tests de facturation, règlements et lettrage sont déjà présents dans les
256cas de la consolidation514 : ils ne sont pas rejoués dans ce complément.

Aucun changement fonctionnel ou comptable ajouté dans ce lot. Le nouveau
module de qualification réutilise les scénarios existants et vérifie leurs
empreintes ainsi que celles des sources fiscales et des fixtures précédentes.

## Dix scénarios supplémentaires

- Vente : devis→BC→BL→facture, liens de lignes et conversions uniques,
  stock10→8, facture1000HT+200TVA=1200TTC et écriture équilibrée.
- Achat sur ordinateur et mobile : BC→réception→facture, stock0→2,
  débits6111/34552 et crédit4411, rattachement fournisseur et refus des doubles
  conversions/comptabilisations ; conservation après rechargement.
- Logo société : import, aperçu, inclusion dans le PDF, effacement, droits
  insuffisants et conservation d'une ancienne référence externe sans chargement.
- Deux parcours Excel ordinateur/mobile : téléchargements réels des classeurs
  balance, liasse et préparation ; image intégrée, lignes et montants contrôlés.
- Quatre parcours impression/PDF Journal/TVA : PNG ordinateur, JPEG mobile,
  sans logo et ancienne référence ; pièces sources inchangées.

Les documents et sociétés sont entièrement fictifs. Cette qualification porte
sur les exports cités ; elle ne démontre pas à elle seule la présence du logo
dans chaque document téléchargeable de l'application.

Qualification navigateur : **10réussites,29avertissements,95.45s**, code0,
aucun échec/erreur/ignoré. Véritable Edge, API et PostgreSQL18.3, rôle LOGIN
hisabpro non propriétaire, schéma098 et sources figées. Invariants comptables
à zéro, ACL/fonctions intactes, cluster éphémère supprimé par la fixture.
Commande : `Test/run_unit_tests.py Test/test_commerce_logos_runtime516_isole.py -ra`.

Les **256réussites** de la commande de consolidation514 (493,36s) restent une
preuve distincte : aucun fichier source de son application n'a changé entre
les deux commandes. Les dix cas supplémentaires ne sont pas comptés comme
une nouvelle exécution des256cas précédents.98SQL et115guides intacts.

Build Vite : `npm.cmd run build`, **code0,9,82s**. Avertissement de taille
du bundle principal (1,75Mo minifié) ; pas d'erreur de compilation. Aucun
bundle construit, environnement ou capture de données inclus dans le ZIP.

## Limites et reprise

Aucune migration, base réelle ou document de recette utilisateur modifié.
L'installation cumulée514 reste nécessaire ; ce lot ajoute seulement un module
de tests et des preuves de couverture. Recette utilisateur et mise en production
restent distinctes. Point6 inchangé, conformément à l'attente de retour humain.

Prochaine analyse : mouvements de stock directs pendant clôture, recomptage et
comptabilisation, en distinguant les snapshots d'inventaire des mouvements.
