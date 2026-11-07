# RAS historique : diagnostic dans l’éditeur

Lot `RAS-EDITEUR-DIAGNOSTIC-20261008`, 7 octobre UTC / 8 octobre 2026 Europe/Paris.

## Correction minimale

L’API expose déjà une RAS historique invalide sous forme de taux/montant/net `null` et de `ras_anomalie`. L’éditeur convertissait pourtant ce taux en zéro à son initialisation et dans son PATCH (`|| 0`). Le champ reste désormais vide et affiche le diagnostic. L’enregistrement d’un brouillon nécessite un choix explicite numérique fini entre 0 et 100 ; zéro est accepté seulement s’il est effectivement choisi. Un taux valide existant hors des presets, par exemple 7 %, reste visible et conservé. Aucune nouvelle règle fiscale ou liste légale de taux n’est introduite.

Le diagnostic est visible dans le tableau et le détail. La duplication d’une pièce diagnostiquée est désactivée afin de ne pas convertir le taux manquant en zéro lors d’une copie. Une facture validée conserve les interdictions existantes de modification financière ; l’éditeur comporte aussi une garde défensive si une telle pièce lui était transmise. Le PDF continue à refuser une RAS historique invalide avec HTTP 409. Aucun backend, migration, écriture ou historique réel n’a été modifié.

## Tests exécutés réellement

- `Test/run_unit_tests.py Test/test_e2e_ras_editeur_diagnostic_isole.py` : **3 réussis en 33,28 s**, Edge connecté à FastAPI réel et PostgreSQL éphémère protégé. Brouillon historique NaN : champ vide, diagnostic visible, tentative d’enregistrement sans choix sans aucun PATCH ni mutation ; choix explicite zéro : un PATCH réel, taux zéro conservé et diagnostic disparu. Pièce historique validée : diagnostic visible, édition et duplication indisponibles, PDF 409, aucune écriture supplémentaire ni PATCH. Taux existant 7 % : affichage et sauvegarde réels conservent 7.
- Tests connexes `Test/test_ras_lecture_conservation.py` : les **7 cas ont réussi** dans chacune des deux exécutions conjointes, comprenant sortie API, conservation par PATCH, cinq taux historiques invalides et PDF refusé, éditeur conservant 10 %.
- `npm run build` : **OK**, 139 modules, 5,96 s ; avertissements XLSX/bundle existants.
- `python -m py_compile Test/test_e2e_ras_editeur_diagnostic_isole.py` : **OK**.

Échecs de préparation de fixture, explicitement distingués des validations finales : première exécution **1 échec / 2 réussites en 34,67 s** (validation API exigeant un tiers enregistré) ; deuxième **1 échec / 9 réussites en 63,90 s** (le trigger interdit de modifier la RAS après validation) ; troisième **1 échec / 9 réussites en 63,14 s** (le trigger interdit d’insérer des lignes dans une pièce déjà validée). Ces règles ont été conservées, sans changement de production ni désactivation de trigger. La fixture finale insère les données et les lignes historiques synthétiques dans un état préparatoire, puis fixe leur état validé ; toutes les opérations suivantes sont des lectures. Ce cas est explicitement une représentation de donnée historique, pas le flux normal de création/validation par API. Les autres cas utilisent l’API normale pour créer les brouillons. Aucune base réelle n’est utilisée.

## Limites et prochaine étape

Une correction d’une RAS invalide sur une pièce réellement validée demeure une opération humaine contrôlée distincte ; ce lot ne la simule pas et ne la réalise pas. La recette visuelle et financière sur les données réelles de l’utilisateur reste à effectuer. Prochain lot proposé : recalcul explicite de l’échéance lorsqu’un utilisateur change le délai de paiement, en conservant les échéances saisies manuellement lors d’un simple changement de date.

## Différentiel

- `src/pages/Factures.jsx`
- `Test/test_e2e_ras_editeur_diagnostic_isole.py`
- `Test/rapport_ras_editeur_diagnostic.md`

Journal et ZIP vérifié assurés par l’agent principal.
