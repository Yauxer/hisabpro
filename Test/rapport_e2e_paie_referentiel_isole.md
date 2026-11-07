# Référentiel documentaire annuel Paie / GRH — 8 octobre 2026

## Modification

La carte « Paramètres et sources » présente désormais une traçabilité propre à la société et à l'année : Non vérifié, Preuves partielles ou Périmé, empreinte actuelle, version documentaire courante et versions précédentes. Chaque preuve conserve son titre, son URL facultative, sa référence, ses dates documentées, son périmètre et ses limites. L'historique reste consultable sans réécrire la version initiale.

L'autorisation de consignation provient du serveur (`peut_consigner`). Le formulaire ne saisit aucun taux ou montant ; le backend capture ses paramètres actuels. L'empreinte attendue reste attachée au formulaire initial. URL et dates non renseignées sont transmises null ; aucune date de consultation n'est présumée. La date réelle de consignation est celle de la version créée côté serveur.

Le loader du contexte protège les réponses et erreurs par génération. Le formulaire est réinitialisé au changement de société ou d'année et ses réponses de mutation sont protégées par scope/version, y compris au démontage. Une réponse POST arrivée après un changement de scope ne restaure ni l'ancienne version ni un faux message de succès. Les erreurs GET sont distinctes des erreurs de préparation de paie.

L'état reste documentaire : une preuve partielle ne valide aucun taux, calcul, bulletin, déclaration ou paiement. La page rappelle que la paie définitive est indisponible. Les taux incomplets ou invalides gardent leurs diagnostics ; aucun zéro n'est substitué à une information absente.

## Recette réelle

Deux parcours Microsoft Edge, aux largeurs 1440 et 390 px, utilisent FastAPI et PostgreSQL éphémère protégé par nonce. Le fixture applique 080 et 082 exclusivement sur ce cluster. Une seule rubrique de taux, volontairement fictive et incomplète, est créée dans le laboratoire puis modifiée par le PATCH admin existant. Elle ne permet pas une préparation de paie valide. Aucune société réelle, comptabilité réelle ou PostgreSQL utilisateur n'est utilisé.

Chaque parcours vérifie :

- GET initial Non vérifié, absence de version et paie définitive non autorisée ;
- consignation réelle admin, source sans URL ni dates, statut Preuves partielles et actualisation immédiate ;
- formulaire sans champ numérique et carte accessible sans troncature à sa largeur ;
- modification du taux fictif par API, statut Périmé et première version identique, paramètres capturés inclus ;
- seconde consignation avec vraie réponse HTTP retenue après commit, changement d'année puis libération : formulaire disparu, ancien succès et ancienne version absents ;
- ancienne empreinte envoyée à une autre année : HTTP 409 ;
- retour à l'année initiale, version suivante et ancienne preuve lisibles ;
- rechargement GET annuel réel retenu, changement d'année puis libération : la réponse historique tardive ne remplace pas le référentiel de l'année courante ;
- création d'une autre société par l'interface, référentiel vierge distinct, ancienne empreinte A refusée sous le jeton B : HTTP 409 ;
- connexion d'un lecteur A, historique accessible, bouton de consignation absent et POST refusé HTTP 403 ;
- préparation CSV désactivée, aucune activation de paie, zéro écriture comptable et aucune erreur JavaScript/API 500.

La latence n'utilise aucun JSON fabriqué : `route.fetch()` obtient la vraie réponse puis seul son ordre de livraison est contrôlé. Les valeurs historiques sont comparées à une copie indépendante de la réponse initiale, sans modifier l'oracle après le changement du taux.

## Commandes et résultats

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_paie_referentiel_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_paie_grh_isole.py Test/test_e2e_grh_absences_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_paie_referentiel_isole.py
npm run build
```

Résultats de préparation conservés : une erreur setup de fixture récursive en 1,06 s, corrigée uniquement dans le nouveau test. Ensuite 1 réussi / 1 échoué en 28,62 s : le parcours desktop passe, le mobile révèle une vraie troncature de la nouvelle carte. Le diagnostic mobile seul échoue en 18,29 s : une carte de 100 px contenait des éléments non repliables atteignant 146 px, avec la sidebar existante.

Correction minimale limitée au CSS documentaire : largeur maximum, min-width zéro, retour à la ligne des titres/badges/boutons et wrapping des actions. Aucun élément masqué. Les deux parcours passent ensuite en 27,20 s. La date de consultation est enfin laissée vide par défaut ; les deux parcours passent en 24,51 s avec contrôle explicite des dates null.

Le run avec contrôle explicite du jour réel de `created_at` réussit en 24,24 s. Le test est ensuite complété par la rétention d'une vraie réponse GET pour les deux largeurs : **run final 2 réussis en 25,41 s**, exit 0. Les cinq tests connexes Paie/GRH et congés sont **réussis en 51,50 s**, exit 0. Le build final est **réussi : 139 modules, 4,47 s**, avec avertissements existants de bundle/SheetJS. Compilation Python du test final : exit 0.

## Limites

Les preuves de cette recette sont fictives et ne constituent aucune validation réglementaire. Le référentiel de taux sous-jacent reste global ; sa modification peut périmer plusieurs captures documentaires de sociétés, ce que le statut rend visible. La consignation conserve la portée société/année sans rendre ce référentiel de calcul propre à chaque société. Aucun bulletin définitif, paiement de salaire ou déclaration sociale n'est activé. La recette utilisateur sur ses dossiers réels reste distincte.
