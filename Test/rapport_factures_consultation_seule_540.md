# Lot540 — Factures en consultation seule

## Problème et périmètre

La page Factures n'utilisait pas la vérification de rôle déjà employée par le
Journal. Elle proposait au lecteur la création, duplication, modification,
validation, conversion de proforma, comptabilisation, création de livraison,
règlement et avoir. Le composant des pièces jointes était aussi affiché en
mode modifiable. Ces commandes ne correspondent pas au rôle de consultation.

La correction réutilise `peutEcrire()` et le paramètre `readOnly` existants.
Les actions d'écriture de la liste et du détail sont retirées pour le lecteur,
le bouton Nouvelle facture est désactivé avec une explication. Les formulaires
de mutation ne sont pas montés sans droit d'écriture. Les filtres, indicateurs,
détails, CSV, PDF et téléchargements des justificatifs d’achat restent disponibles.
Les rôles administrateur/comptable gardent les commandes existantes.
Aucun droit serveur, calcul, migration ou donnée comptable n'est modifié.

## Tests et preuves

- Avant correction : **6échecs,29avertissements,86.68s**,code1.
  Quatre lecteurs trouvent Nouvelle facture active ; les deux comptables
  révèlent le vrai défaut proforma traité séparément et livré dans541.
  Après541, premier sous-ensemble comptable :1échec/1réussite,4désélectionnés,
  53.23s. Un test cherchait à tort des pièces jointes sur les ventes ; cet
  écran les propose uniquement sur les achats. Fixture précisée, sans ajouter
  de fonction produit : **2réussites,4désélectionnés,41.44s**,code0.
  Le statut proforma et ses commandes sont effectivement retrouvés.
- Après correction : **6réussites,29avertissements,64.92s**,code0.
- Consolidation finale : **352réussites,29avertissements,745.89s**,code0.
  `Test/run_unit_tests.py Test/test_consolidation_factures540_isole.py -ra`.
  Les352cas comprennent les344précédents, les2API541 et les6Edge540 : les
  nombres ciblés ne sont donc pas ajoutés une nouvelle fois à la consolidation.
- Connexes externes : **247réussites,29avertissements,195.58s**,code0.
  Liste de25fichiers et commande décrites dans le [rapport538](rapport_factures_comptabilisation_concurrence_538.md).
  Deux commandes distinctes sur les mêmes sources figées : **599exécutions**,
  aucun échec/erreur/ignoré. La qualification538 reste historique sur le schéma
  antérieur à541 ; ces deux dernières commandes qualifient ensemble540/541.
  Les tests de calcul pur et anciens bacs propriétaires restent distingués du
  wrapper LOGIN non propriétaire. Restauration098 :74tables, source préservée,
  cibles supprimées et trois fonctions098 identiques.
- `npm run build` : réussi,**9.03s**,code0. Avertissements de découpage et
  taille de certains bundles conservés ; aucune correction de performance
  revendiquée. Deux Python du lot compilés ;98SQL et115guides inchangés.

Commande ciblée : `Test/run_unit_tests.py
Test/test_e2e_factures_lecture_isole.py -ra`, avec `PYTHON_DOTENV_DISABLED=1`.

Les six cas utilisent de vrais comptes, une société fictive par cas, trois
factures (brouillon, validée, proforma) et un justificatif PDF fictif pour les achats :
vente/achat pour le lecteur en390/1440px et le comptable en1440px.
Ils vérifient les commandes, l'ouverture du détail, le téléchargement exact
du justificatif, un vrai PDF de facture et l'absence de mutation métier.
Le comptable peut ouvrir le formulaire d'avoir sans l'enregistrer.
Le lecteur ne doit émettre aucune requête de mutation depuis la consultation ;
des appels API directs distincts doivent rester refusés403 (validation,
comptabilisation, suppression de facture, règlement, avoir et pièce jointe).

## Limites et livraison

Tests sur PostgreSQL nonce temporaire et Edge local, rôle API non propriétaire.
Aucune connexion au PostgreSQL réel et aucun envoi de courriel.
La protection serveur reste la source de vérité des permissions ; le masquage
de boutons ne crée aucun droit supplémentaire. Les autres écrans ne sont pas
déclarés couverts par ce lot. Recette utilisateur sur l'installation réelle
à effectuer ; le point6 soumis au retour humain reste en attente.

Après copie du fichier `src/pages/Factures.jsx`, reconstruire le frontend
avec `npm run build` pour une distribution compilée, ou laisser Vite recharger
la source en développement. Aucun SQL à exécuter pour ce lot.
