# Édition de la qualification TVA des achats — lot 275

Correction limitée à `FormulaireEditionFacture` dans `src/pages/Factures.jsx`,
nouveau test `Test/test_e2e_facture_achat_tva_edition_isole.py` et ce rapport.
Les choix et règles de comptabilisation existants sont réutilisés ; aucune règle
fiscale, aucun compte, aucun taux, aucune migration ajoutés.

## Cause et comportement corrigé

La création de facture proposait déjà la nature TVA achat et le pourcentage
déductible ; l'éditeur de brouillon ne les présentait pas et ne les envoyait pas.
Le lot 271 avait donc dû les renseigner par API pour sa recette connectée.

L'éditeur achat affiche maintenant une section TVA avec les valeurs persistées :
charge / achat courant, TVA non déductible, pourcentage déductible. Une ancienne
qualification immobilisation reste affichée comme valeur historique ; aucun nouvel
achat immobilisé n'est dérivé depuis cet éditeur. Le module Immobilisations reste
le parcours existant d'acquisition. La section n'apparaît pas sur une vente.

Les champs sont envoyés uniquement après un choix explicite, sur un brouillon.
Le pourcentage doit être renseigné, fini et compris entre 0 et 100, sans clamp.
Le choix explicite non déductible pose 0 comme dans le formulaire de création.
Les contrôles sont désactivés sur une facture verrouillée et les champs TVA
sont alors omis du payload. Les factures validées n'offrent déjà plus l'action
d'édition dans la liste normale.

Une nature inconnue, un pourcentage NULL ou hors bornes sont signalés et affichés
à renseigner ; aucune qualification charge ni déductibilité 100/0 n'est inventée.
Une simple modification d'un autre champ omet les deux paramètres TVA et conserve
les valeurs historiques en base, y compris les valeurs invalides finies.

## Recette réelle et oracle indépendant

Deux parcours Edge headless, bureau 1 365 px et mobile 390 px. Chaque parcours
utilise une société fictive créée par l'API réelle, un fournisseur et plusieurs
brouillons, avec authentification réelle, frontend Vite et API HTTP. PostgreSQL
est éphémère et gardé par répertoire et nonce ; aucun PostgreSQL réel utilisé.

Un achat de deux services à 500 MAD HT et TVA 20 % donne 1 000 MAD HT,
200 MAD TVA et 1 200 MAD TTC. Dans l'éditeur, la référence fournisseur est saisie
et la déductibilité passe explicitement de 100 à 80 %. Le PATCH navigateur contient
`nature_tva_achat=charge` et `tva_deductible_pct=80`. La réouverture conserve 80.
Sans autre prorata annuel configuré, l'oracle indépendant est :

- TVA récupérable : 200 × 80 % = 160 MAD ;
- TVA non déductible incorporée au coût d'achat : 40 MAD ;
- compte 6111 : débit total 1 040 MAD ;
- compte 34552 : débit 160 MAD ;
- compte 4411 : crédit 1 200 MAD ; débit = crédit = 1 200 MAD.

L'écriture réellement générée par l'interface est contrôlée puis validée depuis
le Journal. La tentative API de changer sa qualification après validation reçoit
409 et toutes les colonnes persistées de l'écriture et de ses lignes restent
inchangées. L'action Modifier le brouillon est absente de cette facture validée.

La saisie `1e309` est refusée par l'éditeur avant tout PATCH. Un autre brouillon
choisi non déductible affiche un 0 désactivé et persiste explicitement cette paire.
Deux variantes historiques sont construites uniquement dans le PostgreSQL nonce :
NULL/NULL et nature `ancienne_inconnue` / pourcentage 150. Modifier seulement la
référence fournisseur conserve exactement ces valeurs ; le PATCH omet les champs
TVA. Un brouillon vente n'affiche pas la section. Aucune erreur JavaScript ou 5xx
observée dans les deux parcours finaux.

## Historique des exécutions

Commande ciblée, depuis la racine, avec `PYTHON_DOTENV_DISABLED=1` :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_e2e_facture_achat_tva_edition_isole.py -x
```

- Avant correction, 8 octobre : session 87226, sortie 1, **1 failed**,
  25 avertissements, **26,60 s** ; le contrôle de qualification manque dans l'éditeur.
- Premier ajout UI, 8 octobre : session 1737, sortie 1, **1 failed**,
  25 avertissements, **26,23 s** ; nom accessible du select implicite incluant ses
  options, incompatible avec la recherche exacte. Ajout d'`aria-label` explicites
  pour les deux contrôles. Cette correction était envisagée mais non exécutée au
  blocage quota ; elle a effectivement été appliquée lors de la reprise du 9 octobre.
- Reprise 9 octobre : session 69706, sortie 0, **2 passed**, 25 avertissements,
  **33,84 s** ; les deux largeurs passent. Puis renforcement du test historique
  invalide et du contrôle persistant non déductible.
- Ciblés renforcés et connexes :

```powershell
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_e2e_facture_achat_tva_edition_isole.py Test/test_e2e_cycle_achat_isole.py Test/test_e2e_avoir_fournisseur_isole.py
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 -m py_compile Test/test_e2e_facture_achat_tva_edition_isole.py
npm.cmd run build
```

Session 65743, sortie 0 : **6 passed**, 25 avertissements, **106,47 s**.
Deux éditions TVA, deux cycles BC → BR → facture et deux avoirs fournisseurs.
Compilation Python : sortie 0. Build Vite partagé après stabilisation des autres
lots : sortie 0, **138 modules**, **7,07 s**. Avertissements existants multipart /
Pydantic et, pour Vite, imports XLSX mixtes et taille du chunk.

## Limites

Les choix TVA ne préjugent pas du droit fiscal à déduction : l'utilisateur doit
qualifier son cas avec ses pièces. Le test de prorata 80 % concerne la part propre
à cette facture ; il ne valide pas un nouveau prorata annuel de société.
La variante historique immobilisation est conservée par le code mais n'a pas fait
l'objet d'un nouveau parcours navigateur dédié. La désactivation de contrôles
sur facture verrouillée est implémentée ; la recette navigateur suit le parcours
normal, où l'éditeur d'une facture définitive n'est plus proposé, puis vérifie
le refus API et l'intégrité des écritures. Aucune réparation historique ni recette
sur les données utilisateur n'a été effectuée.
