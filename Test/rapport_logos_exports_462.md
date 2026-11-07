# Logos des documents — lot 462

Le logo facultatif des paramètres est maintenant repris dans les états financiers
PDF (bilan/CPC/ESG/financement), les cinq balances PDF, la préparation depuis
balances importées, la liasse PDF, le livre d'inventaire PDF et les préparations
des ventes PDF/XLSX. Les pièces commerciales utilisaient déjà le logo.

Le chargement commun accepte uniquement les images PNG/JPEG intégrées validées,
limitées à 512 Ko et quatre millions de pixels. Aucun accès à un chemin local ou
une URL historique. Une valeur ancienne incompatible n'empêche pas l'export.
Le logo est proportionné, placé sur la première page ; dans le XLSX des ventes,
une feuille d'identité garde toutes les cellules de données à leurs coordonnées.

Les nouvelles données de liasse incluent le logo dans leur identité et leur
empreinte. Une ancienne archive sans logo reste sans logo ; aucun logo courant
n'est injecté dans son snapshot. Aucun chiffre ni écriture n'est modifié.
Le livre d'inventaire utilise l'identité courante comme auparavant ; son snapshot
comptable reste intact. Une éventuelle identité intégralement figée du livre est
un travail distinct, non déclaré réalisé par ce lot.

## Vérifications exécutées

- Avant correctif : huit échecs reproduits sur PDF financiers, liasse,
  préparation et inventaire (PNG/JPEG) ; huit cas déjà réussis.
- Après correctif : les seize tests ciblés réussissent, exit 0.
- Suite regroupée : **51 réussis**, 29 avertissements, **66,25 s**, exit 0.
  Commande : `python -X utf8 Test/run_unit_tests.py Test/test_logos_exports_pdf.py Test/test_logos_exports_runtime_isole.py Test/test_logo_societe.py Test/test_balance_preparation_pdf.py Test/test_fact9_documents_pdf.py Test/test_ventes_exports_isole.py Test/test_patch131_liasse_pdf_identite.py -ra`.
- Le nouveau test API utilise le serveur réel, PostgreSQL jetable 091 et LOGIN
  limité : deux sociétés aux logos différents, images réellement présentes dans
  les PDF et le ZIP XLSX ; écritures identiques avant/après.

Les anciens tests connexes de préparation utilisent leur propre laboratoire
isolé ; aucune base utilisateur n'a été consultée. La recette humaine reste à
effectuer. Les autres XLSX générés dans le navigateur restent à compléter au
lot suivant. CSV/FEC et pièces jointes originales restent dans leur format et
conservent leur contenu ; on ne décore pas des justificatifs importés.

Prochaine étape : logos des classeurs générés dans le navigateur, puis modèles
d'écritures supplémentaires avec références et tests, sans réappliquer 451–461.
