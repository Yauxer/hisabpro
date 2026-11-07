# Logos des classeurs navigateur —463

Les trois exports XLSX du navigateur (balances, liasse, préparation de balances)
reprennent le logo intégré de la société dans une première feuille « Logo société ».
Les feuilles comptables gardent leurs noms, coordonnées, valeurs et formats.
La liasse utilise son identité source : une ancienne archive sans logo ne reçoit
pas le logo actuel. Aucun logo n'est ajouté aux justificatifs importés originaux.

L'export utilise le ZIP OOXML de SheetJS déjà installé, sans dépendance ajoutée.
PNG/JPEG intégrés uniquement, contrôle de taille et de dimensions, proportions
conservées, aucune résolution d'URL ou chemin local. Le classeur source est
copié avant sérialisation car SheetJS peut modifier ses métadonnées internes.

Une course a été reproduite sur 390 px : l'export de balance pouvait démarrer
avant le chargement de l'identité société. Les boutons attendent maintenant
son identifiant ; aucun délai artificiel n'est ajouté à la recette.

## Tests réellement exécutés

- Node/openpyxl :6 réussis 1,99 s, exit 0. Image réellement incorporée au ZIP,
  montants 1234,56 et−10,01, numéro 001234, textes commençant par`=`, formats et
  source inchangés ; absence/anciennes références invalides sans image.
- Suite finale : **13 réussis 98,33 s**,29 avertissements, exit 0.
  `python -X utf8 Test/run_unit_tests.py Test/test_logos_xlsx_navigateur.py Test/test_e2e_logos_xlsx_isole.py Test/test_e2e_balances_exports_isole.py Test/test_e2e_balance_isole.py -ra`
- Les deux nouveaux parcours Edge 1440/390 utilisent l'API réelle 091 et un LOGIN
  SQL limité : trois téléchargements XLSX chacun, image relue avec openpyxl,
  montants de balance et préparation inchangés, aucune erreur JS/HTTP 500.
- Le buildVite a réussi avant les dernières gardes ; un build final est exécuté
  avant livraison. Les avertissements existants sur SheetJS/chunks restent.

Les échecs initiaux sont conservés :6 cas de mise au point CFB, puis 2, puis 0 ;
deux sélecteurs de test incorrects corrigés, puis la course produit 390 corrigée.
Les tests historiques des exports sans logo restent réussis. Aucun PostgreSQL
réel ; l'ouverture et le rendu dans la version Excel du partenaire restent à
vérifier manuellement. CSV/FEC ne peuvent contenir d'image ; leurs octets et
leur structure ne sont pas modifiés. Aucune fonctionnalité RH absente n'est
présentée comme exportable.

Utilisation : Paramètres → Société → Logo(PNG/JPEG), enregistrer, puis exporter
le PDF ou le XLSX du module. La feuille « Logo société » contient l'identité ;
les autres feuilles contiennent les données habituelles.
