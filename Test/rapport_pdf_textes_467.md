# Textes des PDF financiers et d'inventaire —467

Les noms de société, adresses, titres, sous-titres et libellés des PDF financiers
sont échappés avant leur passage à ReportLab. Le nom en en-tête du livre
d'inventaire reçoit le même traitement. Les caractères`<`, `>`et`&`restent
littéraux ; seules les images du mécanisme de logo peuvent illustrer ces textes.
Les montants, données sources et archives ne sont pas réécrits.

Avant correction : **6 échecs/1 réussi 0,77 s**, dont cinq lectures d'une image PNG
fictive locale depuis une balise saisie dans un texte. Aucun chemin système ni
document réel n'a été utilisé. L'oracle d'identité du livre a ensuite été
resserré à la première page pour éviter de compter plusieurs pieds de page.

Après correction : **79 réussis 87,77 s**,27 avertissements, exit 0. Les sept nouveaux
cas vérifient les identités et l'absence d'image parasite dans de vrais PDF ;
les connexes couvrent les logos PNG/JPEG, documents commerciaux, valeurs
numériques extrêmes, préparations de balances, identité liasse et historiques
du livre d'inventaire. Compilation des trois fichiers avant livraison.

Commande : `python -X utf8 Test/run_unit_tests.py Test/test_pdf_textes_litteraux.py Test/test_logos_exports_pdf.py Test/test_fact9_documents_pdf.py Test/test_logo_societe.py Test/test_documents_pdf_limites_numeriques.py Test/test_balance_preparation_pdf.py Test/test_patch131_liasse_pdf_identite.py Test/test_livre_inventaire_nombres_historique.py -ra`.

Les tests de fonctions pures et leurs fixtures locales ne qualifient pas une
installation PostgreSQL utilisateur ; aucune base réelle n'a été consultée.
Cette correction ciblée ne prétend pas couvrir tous les champs de tous les
générateurs. Recette visuelle des documents réels à effectuer.
