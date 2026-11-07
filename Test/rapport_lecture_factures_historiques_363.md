# Lecture qualifiée des factures historiques — lot363

Le GET de liste conserve désormais chaque facture et ses identifiants de lignes.
Une source NaN, infinie, manquante ou un calcul non représentable produit des
montants JSON `null`, `montants_valides:false` et des diagnostics explicites.
La facture saine de la même société reste lisible avec HT100/TVA20/TTC120.
Un prix explicitement zéro reste zéro. Aucune échéance artificielle à zéro
n'est créée pour une pièce dont le total est inconnu ; les échéances persistées
restent dans la projection de lecture.

Les schémas de lecture sont séparés des validateurs stricts de création.
Le calcul financier partagé refuse les sources inconnues avant validation,
règlement ou émission du PDF. Les avoirs liés et sommes de règlements sont
également qualifiés. Les anciennes règles de calcul et de RAS ne sont pas
remplacées : une RAS invalide continue de laisser lisible un TTC connu.

Dans Factures, les pièces restent visibles ; le détail défaillant est en lecture
seule et indique « À vérifier ». Les actions dépendantes des montants et le CSV
contenant une pièce défaillante sont désactivés. Les indicateurs de la période
sont indisponibles plutôt que calculés avec des zéros. Réessayer relance la
lecture réelle. Le cycle commercial conserve les factures et affiche aussi
« À vérifier » ; sa sélection de règlement désactive une facture défaillante.
Les alertes du tableau de bord ne présentent plus son TTC comme zéro.

## Tests réellement exécutés

Toutes les commandes utilisent le Python du venv avec `-X utf8`,
`PYTHON_DOTENV_DISABLED=1` et `Test/run_unit_tests.py`. Les tests connectés
utilisent uniquement PostgreSQL éphémère contrôlé par URL, répertoire et nonce.

- Avant correction : diagnostic359, cas NaN seul, **1échec**,7désélectionnés,
  25avertissements,22,60s,code1 ; GET500, photographie inchangée.
- Premier essai : **8échecs**,37,86s,code1 ; import Decimal manquant, corrigé.
- Diagnostic original après correction : **8réussites**,31,82s,code0,
  dont un Edge connecté conservant la visibilité de la facture saine.
- RAS, validation historique et diagnostic : **73réussites**,144,83s,code0.
  Cette suite précède la qualification supplémentaire des avoirs liés.
- Premier nouveau banc :20échecs/10réussites,116,05s,code1. La photographie
  était comparée après l'inscription d'une seconde société fictive, qui crée
  normalement sa société et son exercice. Le prérequis a été figé avant ses
  requêtes ; aucune assertion d'intégrité n'a été supprimée.
- Contrats de lecture, reprise UI et cycles vente/achat, avoir fournisseur,
  acompte fournisseur, RAS et lettrage : **40réussites**,287,81s,code0.
  Les ventes/achats et proformas couvrent NaN/+inf/-inf/1e308/quantitéNULL,
  les refus financiers, zéro connu et isolation entre sociétés.
- Sources globales NaN et avoirs liés défaillants : **6réussites**,
  22désélectionnés,27,01s,code0.
- Après la mise en forme finale du détail : **8réussites Edge connectées**,
  56,27s,code0, sur1365px/390px. Deux pièces visibles, détail avec diagnostics,
  actions bloquées, absence de faux zéro et reprise sans F5 après remise en état
  du seul jeu fictif. Le zéro d'une liste réellement vide reste vérifié.
- Compilation Python des deux fichiers backend :code0.
- Build final Vite :code0,4,79s ; avertissements de taille et import XLSX conservés.

Les suites sont distinctes et ne s'additionnent pas. La consolidation365 sur
690sources figées possède son propre journal et rapport ; aucun résultat final
ne lui est attribué avant achèvement. Les anciens échecs359 restent conservés.

## Intégrité et limites

Aucune migration, aucune connexion à PostgreSQL réel et aucune réparation de
données historiques. Les tests photographient les tables avant/après les lectures
et refus. Le cas d'avoir ajoute une photographie des avoirs et de leurs lignes.
Les injections sont uniquement des prérequis négatifs fictifs du banc isolé.
Les écritures définitives des parcours normaux restent conservées après lettrage.

Le statut de paiement enregistré n'est pas recalculé lors du GET. La projection
des montants devient conservatrice si un document financier lié est défaillant.
Les endpoints de calcul de règlement/échéancier répondent422 explicitement ;
ils ne prétendent pas calculer un solde inconnu. Un PDF de proforma défaillante
est refusé422 ; le refus409 du PDF de brouillon reste prioritaire.

Les fixtures défaillantes sont des brouillons ou proformas. Aucun trigger
d'immuabilité n'est désactivé pour fabriquer un historique définitif invalide.
La réparation contrôlée d'une pièce historique, la qualification exhaustive
des autres listes métier, la recette humaine et la production restent distinctes.

Prochaine étape : achever365, actualiser le guide et la couverture, livrer le
cumulatif différentiel. Puis étendre la lecture qualifiée des situations de
règlement avec leurs preuves, sans inventer de montants historiques.
