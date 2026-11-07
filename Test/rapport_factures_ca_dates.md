# Factures : période et indicateurs documentaires complets

Lot `FACTURES-CA-DATES-20261008`, exécuté le 7 octobre 2026 UTC (8 octobre en Europe/Paris).

## Analyse et correction

Les champs de période filtraient principalement l’export, tandis que les indicateurs utilisaient l’exercice entier. Le contexte ne chargeait que les 100 premières factures : un exercice de plus de 100 pièces pouvait donc afficher des totaux incomplets.

La période inclusive porte maintenant sur la date de chaque facture et de chaque avoir, dans le tableau, l’export CSV et les indicateurs. Une note de crédit de février rattachée à une facture de janvier diminue bien février ; une note de crédit de mars ne diminue pas février. Les indicateurs prennent les factures validées, hors proformas et annulations, et les avoirs actifs (`emis`, `utilise`, `rembourse`). Les brouillons restent consultables dans le tableau sans alimenter les montants validés.

Le nouveau libellé « Facturation nette HT » désigne les montants HT des documents, remises et avoirs compris, avant escompte. « Ventes nettes TTC » et « Achats nets TTC » désignent leurs montants TTC. Les totaux proviennent de l’API existante. Ils incluent donc les dépôts de consignation lorsque le document les inclut : ces dépôts sont présentés séparément des articles dans le détail. Aucun de ces indicateurs ne prétend remplacer le chiffre d’affaires comptable. Le coût moyen d’achat indicatif conserve sa définition existante et ne constitue pas un CMUP comptable.

La ventilation tient compte des remises et des montants des lignes d’avoirs. Une ligne explicite « Frais et écarts d’arrondi » réconcilie les lignes avec les totaux documentaires. Un avoir seul peut produire une ligne et un total négatifs. Les barres visuelles sont bornées sans modifier les montants.

Le contexte collecte toutes les pages de 100 pièces. À exactement 100 pièces, une deuxième requête vide termine la collecte ; à 101 pièces, elle récupère la dernière. Une page répétée ou une erreur de chargement provoque une erreur visible plutôt qu’un total partiel. Le jeton, la société et l’exercice sont surveillés pour écarter un chargement devenu obsolète. Une période inversée ou un chargement incomplet affiche des indicateurs indisponibles. Les deux libellés « Échéance contractuelle » deviennent « Échéance » sans modifier les dates ni leur règle de calcul.

## Oracle indépendant de la recette connectée

Deux sociétés fictives isolées testent respectivement 100 et 101 factures, avec quatre factures créées puis validées par l’API réelle :

| Date | Document HT | Document TTC | Cas |
|---|---:|---:|---|
| 01/01 | 100,00 | 120,00 | Source antérieure d’un avoir de février |
| 01/02 | 182,00 | 218,40 | Article 200 − remise ligne 10 % − remise globale 10 % = 162 ; transport 20 |
| 28/02 | 300,00 | 360,00 | Borne supérieure incluse |
| 01/03 | 400,00 | 480,00 | Hors février |
| 10/02 | −25,00 | −30,00 | Avoir actif, facture source du 01/01 |
| 01/03 | −16,20 | −19,44 | Avoir actif, facture source du 01/02 |

Un autre avoir de février est réellement annulé par API. Les pièces de remplissage sont des brouillons fictifs ; trois cas de février représentent brouillon, proforma et facture annulée. Aucune donnée réelle n’est utilisée.

Oracle février : HT = 182 + 300 − 25 = **457,00 MAD** ; TTC = 218,40 + 360 − 30 = **548,40 MAD**. Oracle exercice : HT = 100 + 182 + 300 + 400 − 25 − 16,20 = **940,80 MAD**. Oracle 01/02 seul : 182 ; 28/02 seul : 300 ; 10/02 seul : −25 et aucune facture à cette date. L’export CSV téléchargé dans Edge contient uniquement les dates retenues. Le détail conserve l’article crédité même si sa facture source est hors période.

## Tests réellement exécutés

- `Test/run_unit_tests.py Test/test_factures_periode.py Test/test_e2e_factures_ca_dates_isole.py` : **3 réussis en 36,91 s**. Node exécute les helpers ; Edge appelle FastAPI réel et PostgreSQL éphémère protégé par les garde-fous du dépôt. Aucun PostgreSQL réel de l’utilisateur, aucune interception simulant les réponses métier.
- Complément du test Node pour achats nets et escompte, puis `Test/run_unit_tests.py Test/test_factures_periode.py` : **1 réussi en 0,25 s**. HT avant escompte 100, TTC après escompte 10 % et TVA 20 % = 108 ; achats 120 moins avoir 24 = 96.
- `Test/run_unit_tests.py Test/test_e2e_facturation_isole.py Test/test_e2e_administration_isole.py` : **4 réussis en 66,16 s**. Cycles vente/achat avec validation, règlements et lettrage ; administration, permissions et changement de société réels.
- `npm run build` : **OK**, 138 modules, 6,57 s. Avertissements connus concernant le regroupement XLSX et la taille du bundle.
- `python -m py_compile Test/test_factures_periode.py Test/test_e2e_factures_ca_dates_isole.py` : **OK**.

Échecs rencontrés puis corrigés : première préparation de fixture invalide (2 échecs en 24,78 s : facture déclarée validée sans échéance) corrigée en conservant ces pièces comme brouillons ; sélecteur de carte TTC incompatible avec l’icône du détail (2 échecs en 44,23 s), remplacé par un identifiant stable ; assertion de zéro ligne sur un tableau conservant sa ligne vide « Aucune facture trouvée » (2 échecs et 1 réussite en 46,25 s), corrigée en contrôlant l’état vide et l’absence de pièces. Aucun garde-fou métier n’a été contourné. La dernière exécution ciblée réussit les deux cas 100/101.

## Limites et suite

La pagination actuelle de l’API ne fournit pas de snapshot transactionnel de l’ensemble des pages : une insertion concurrente détectable par doublon conduit à recharger, sans inventer de total. Cette étape ne change pas les statuts de retard, les règles fiscales, les montants historiques ou la définition du coût moyen indicatif. La recette sur les données de production de l’utilisateur n’a pas été exécutée. La protection de l’éditeur face à une RAS historique invalide doit faire l’objet d’un lot distinct après livraison de celui-ci.

## Fichiers différentiels

- `src/pages/Factures.jsx`
- `src/data/FacturesContext.jsx`
- `src/services/api.js`
- `src/utils/collecterPages.js`
- `src/utils/facturesPeriod.js`
- `Test/test_factures_periode.py`
- `Test/test_e2e_factures_ca_dates_isole.py`
- `Test/rapport_factures_ca_dates.md`

Le journal et le ZIP différentiel sont consignés et vérifiés par l’agent principal.
