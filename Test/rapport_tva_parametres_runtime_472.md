# Paramètres TVA sous rôle SQL limité — lot 472

Le parcours connecté a reproduit un échec d'enregistrement : la migration 077
accordait seulement SELECT sur `tva_parametres_exercice`, tandis que l'API
existante doit créer et mettre à jour les paramètres d'un exercice.

La migration additive 093 accorde INSERT et UPDATE uniquement sur crédit
d'ouverture, prorata et horodatage, avec USAGE/SELECT de la séquence. Elle ne
donne aucun UPDATE global, droit de suppression, modification d'identité,
SETVAL ou privilège de création. Elle retire aussi le droit UPDATE hérité des
anciennes migrations 005/008 sur cette seule séquence. Aucun paramètre, taux ni calcul n'est changé.
Le rôle cible reste `hisabpro` ; les autres configurations doivent être qualifiées.

L'API refuse désormais la modification d'un exercice clôturé, selon le statut
de l'exercice ou la clôture annuelle existante. C'est un contrôle du flux API ;
la concurrence avec une clôture et la protection directe SQL des paramètres
clôturés restent à qualifier. Le lecteur continue à recevoir 403.

## Vérifications exécutées

- 500 avant 093 réellement reproduit avec le LOGIN limité, puis ajout de droits,
  schéma/données identiques et rejeu idempotent.
- **5 réussis en 47,45 s**,29 avertissements, exit 0 : création/update 200, isolation,
  refus 422/409, identités/suppression protégées et deux parcours Edge TVA.
  Une première suite 3 réussis/2 échecs 44,85 s incluait à tort la trace de refus dans
  les données inchangées ; le banc vérifie maintenant 72 tables stables et une
  seule trace ajoutée, anciennes traces intactes. Aucun audit n'a été supprimé.
- Les contrôles de séquence sont aussi inclus dans la recette regroupée finale.
- Après ajout du contrôle de séquence :135 réussites/1 échec 405,92 s dans la
  consolidation. Le SETVAL hérité a été retiré de 093 avant sa première livraison.
  **6 réussis en 117,62 s**,29 avertissements, exit 0, vérifient ensuite droits,
  séquence sans UPDATE, API/Edge et restauration de la version durcie.
- Restauration 093 : **1 réussi en 75,71 s**,29 avertissements, exit 0. Les assertions
  du lot 468 sont conservées, avec les nouvelles ACL :1206 entrées de relations,
  29 de colonnes.73 tables, données, schéma, séquences, droits, FEC et pièces
  identiques avant reprise API ; logos/64 modèles relus sur la cible.

La restauration finale incluse dans les six cas conserve 1205 entrées de relations
et 29 de colonnes, après retrait du SETVAL ; schéma, données, droits, séquences,
FEC et pièces restent identiques entre source et cible.

Commandes : `python -X utf8 Test/run_unit_tests.py Test/test_permissions_tva_runtime_isole.py -ra`
et `python -X utf8 Test/run_unit_tests.py Test/test_restauration_logos_modeles_isole.py -ra`.
La recette regroupée finale contrôle également les assertions de séquence
ajoutées après la suite ciblée. Compilation avant livraison.

La migration 093 est livrée pour application manuelle après 092, sous propriétaire
des tables et après sauvegarde. Elle n'a jamais été appliquée à une base
utilisateur. Les clôtures utilisées ici sont fictives. Aucune conformité fiscale
ni recette humaine validée automatiquement ; point 6 toujours en attente.
