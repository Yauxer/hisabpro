# Chèque impayé et règlement de remplacement — recette connectée

Lot : `E2E-CHEQUE-IMPAYE-20261010-307`.

## Périmètre

Ce lot ajoute uniquement une recette automatisée ; aucune source applicative, règle fiscale, migration ou donnée réelle n'est modifiée. Il complète les tests existants de dates et modales des effets, qui utilisent SQLite ou une API simulée, par le parcours complet sur FastAPI et PostgreSQL nonce réels.

Les prérequis société, client et facture sont préparés par API réelle. La facture fictive est validée et comptabilisée ; son écriture est validée avant photographie. Toutes les actions du scénario ensuite sont natives dans Edge aux largeurs 1365 et 390, sans clic forcé, réponse métier simulée ni modification de styles.

## Scénario et oracle indépendant

Facture de prestation fictive : 1 000 HT + 200 TVA = 1 200 TTC ; RAS zéro.

1. Dans Factures, réception d'un chèque de 1 200, référence `CHEQUE-IMPAYE-FICTIF`, date explicite du jour de recette. Il entre en portefeuille, sans encaissement bancaire effectif : total réglé 1 200, encaissé zéro, règlement en cours 1 200.
2. Dans Effets & Chèques, remise à l'encaissement avec date réelle du jour ; transfert de 51111 à 51112.
3. Déclaration de l'impayé à la même date, frais explicitement zéro. La créance de 1 200 est réouverte ; le chèque reste visible comme « Rejeté / Impayé » et « REJETÉ — non compté » dans l'historique de règlement de la facture.
4. Depuis Factures, virement de remplacement de 1 200, référence `VIREMENT-REMPLACEMENT-FICTIF`, date explicite du jour. Solde zéro et encaissé 1 200.
5. Dans Journal, validation explicite des quatre nouvelles écritures brouillons. Puis lettrage natif des quatre lignes du collectif sous AAA.

Oracle indépendant en Decimal : cinq écritures, onze lignes, débit = crédit = `1200 × 5 = 6000`. Banque 5141 : solde débiteur 1 200 ; comptes d'attente 51111 et 51112 : zéro ; collectif clients 3421 : zéro. Les quatre lignes du collectif totalisent débit = crédit = 2 400 et conservent le tiers et l'auxiliaire réels.

Les dates d'écritures et de pièces sont celles déclarées. L'écriture initiale reste identique pendant les transitions ; les cinq écritures restent physiquement identiques lors du lettrage, dont la piste est séparée. Les refus d'action en lecture seule (403) et depuis une autre société (404) ne modifient pas ces photographies.

## Commandes et résultats

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_cheque_impaye_isole.py -x --tb=short
```

Résultat ciblé : **2 réussis**, 25 avertissements de dépendances, **40,02 s**, code de sortie 0. Aucun échec intermédiaire.

Connexes :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_effets_dates_operations.py Test/test_effets_dates_navigateur.py Test/test_e2e_reglement_edition_isole.py -x --tb=short
```

Résultat connexe : **30 réussis**, 25 avertissements de dépendances, **46,34 s**, code de sortie 0. Les contrôles de dates backend sont sur ORM SQLite isolé, les modales anciennes sur navigateur avec API simulée, et les deux parcours d'édition de règlement sur Edge/FastAPI/PostgreSQL nonce ; ils restent distincts des deux nouvelles recettes intégralement connectées.

Compilation `python -X utf8 -m py_compile Test/test_e2e_cheque_impaye_isole.py` : code de sortie 0. Le build 303 déjà exécuté (138 modules, 9,88 s, code de sortie 0) inclut les mêmes sources applicatives, inchangées dans ce lot ; il ne constitue pas un nouveau build exécuté ici.

## Limites

Recette utilisateur à effectuer sur son installation. Aucun PostgreSQL réel ni donnée comptable réelle n'a été utilisé. Ce scénario n'aborde pas l'escompte, les frais non nuls ni une qualification fiscale nouvelle ; les tests connexes existants restent distincts de cette recette connectée.
