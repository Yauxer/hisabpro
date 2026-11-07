# Lot 267 — Achat fournisseur, retour partiel, règlement et lettrage

## Périmètre et données fictives

Deux parcours réels Edge headless, API/JWT et PostgreSQL nonce : écran desktop 1365 × 1000 et mobile 390 × 1000. Aucun clic forcé, aucun PostgreSQL utilisateur, aucune donnée réelle. Seuls un test nouveau et ce rapport sont ajoutés ; aucun fichier d’application modifié.

Fournisseur rattaché au compte collectif 4411 ; article stockable avec stock initial 0 et compte d’achat 6111. Achat de deux unités à 500 MAD HT chacune, TVA saisie 20 %, qualification achat courant et déductibilité 100 % **explicitement sélectionnées dans les options fiscales de l’interface** puis vérifiées dans la réponse API. Aucun acompte, RAS, escompte ou remise dans ce scénario. Les taux choisis sont des données de recette, sans règle fiscale nouvelle.

Oracle indépendant : achat HT 1000 + TVA 200 = TTC 1200 ; retour d’une unité HT 500 + TVA 100 = avoir 600 ; fournisseur payé 1200 − 600 = 600. Stock initial 0 → achat validé 2 → retour comptabilisé 1.

| Opération | Débit | Crédit |
|---|---|---|
| Achat | 6111 : 1000 ; 34552 : 200 | 4411 : 1200 |
| Avoir fournisseur | 4411 : 600 | 6111 : 500 ; 34552 : 100 |
| Règlement | 4411 : 600 | 5141 : 600 |

Résultat attendu : **3 écritures, 8 lignes, débit = crédit = 2400 MAD**, soldes 6111 = 500, 34552 = 100, 4411 = 0 et 5141 = −600. Lettrage AAA sur les trois lignes 4411, toutes réellement rattachées au fournisseur et à son snapshot auxiliaire.

## Parcours et contrôles

La société, le fournisseur et l’article fictifs sont préparés par API. Toutes les opérations suivantes passent par l’interface : création de la facture d’achat, validation, comptabilisation, validation de son écriture dans le Journal ; création de l’avoir physique partiel ; comptabilisation et validation de son écriture ; règlement du reliquat 600 ; validation de son écriture puis lettrage des trois lignes 4411. L’état lettré persiste après rechargement.

La création du brouillon de facture laisse le stock à 0 ; sa validation le porte à 2. La création de l’avoir laisse le stock à 2 et ne génère aucune écriture. Sa comptabilisation ramène le stock à 1. Le test final compare les deux mouvements exacts : entrée 2 de 0 à 2 liée à la facture, puis sortie 1 de 2 à 1 liée à l’avoir. Aucune double consommation de stock.

Refus réels API : deuxième comptabilisation du même avoir 409 ; tentative de créditer deux unités supplémentaires alors qu’une seule reste disponible 409 ; rôle lecteur 403 ; autre société 404. Les écritures d’achat déjà validées restent intactes lors des opérations suivantes. Les snapshots finaux comparent **toutes les colonnes persistées** des écritures et lignes avant/après lettrage ; le lettrage est conservé dans une table distincte. Aucune erreur JavaScript ou API serveur inattendue n’est admise.

## Tests réellement exécutés

Python : `hisabpro-backend/.venv/Scripts/python.exe`, `PYTHON_DOTENV_DISABLED=1`. La fixture vérifie le nonce et le répertoire PostgreSQL isolé avant utilisation. Le brouillon a été préparé sans exécution, puis installé seulement après livraison du lot 266 et feu vert du principal.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_avoir_fournisseur_isole.py
```

Essais de mise au point du test, explicitement échoués :

- 2 échecs en 63,50 s, session 50457 : sélecteur relatif Playwright mal construit pour l’option de qualification TVA.
- 1 échec en 41,37 s, session 41321 (`-x`) : contrôle fiscal trouvé mais masqué dans les options avancées ; ajout du clic normal sur « Options commerciales & fiscales ».
- 1 échec en 42,57 s, session 11371 (`-x`) : action de validation du Journal déclenchée avant chargement du brouillon ; ajout de l’attente du bouton de validation de la ligne, comme dans les tests connexes.

Ces corrections concernent uniquement la fixture, ses sélecteurs et ses attentes, sans contourner une règle métier ni forcer un clic. Aucun de ces essais n’est déclaré réussi.

Après corrections : **2 tests réussis en 37,67 s**, 25 avertissements de dépendances existants, session 51088, code 0. Le test a ensuite été renforcé pour vérifier toutes les colonnes persistées et les deux mouvements exacts.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_avoir_fournisseur_isole.py Test/test_e2e_avoir_retour_isole.py Test/test_e2e_acompte_fournisseur_isole.py
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_avoir_fournisseur_isole.py
```

Résultat final renforcé et connexe : **5 tests Edge/API/PostgreSQL isolé réussis en 96,40 s**, 25 avertissements de dépendances existants, session 32927, code 0. Deux nouveaux parcours plus retour client/contrepassation et deux parcours acomptes fournisseur connexes ; aucun échec ou test ignoré. Compilation : code 0.

## Limites et prochaine étape

Scénario de retour d’une marchandise avec TVA achat entièrement déductible. La TVA partiellement/non déductible, les avoirs de réduction commerciale ou correction de prix, la RAS et les effets ne sont pas couverts par ce lot. La recette utilisateur n’est pas prévalidée par les tests développeur.

Prochaine étape : intégrer ce parcours dans la matrice de couverture et le cahier de recette fournisseur, puis poursuivre les variantes indépendantes.
