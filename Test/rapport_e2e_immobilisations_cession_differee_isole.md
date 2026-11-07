# Lot 258 — Cession d’immobilisation à encaissement différé

## Périmètre et oracle indépendant

Test nouveau uniquement : aucun changement d’application, de migration, de taux ou d’historique. Exécution sur API/JWT, navigateur Edge headless et PostgreSQL nonce réels, avec contrôle préalable de l’isolation. Le PostgreSQL utilisateur et ses processus restent exclus.

Jeu fictif : acquisition HT 10 000 le 01/01/2024, mise en service le même jour, amortissement linéaire sur cinq ans. Calcul indépendant : 10 000 / 5 = 2 000 par an ; deux années complètes donnent un cumul 4 000 et une VNC 6 000. Cession le 31/12/2025 pour HT 7 500, TVA saisie 20 % = 1 500, TTC 9 000 ; gain comptable 7 500 − 6 000 = 1 500. Encaissement total différé au 15/01/2026. Ces taux sont ceux choisis pour le cas fictif, sans affirmation d’une obligation nouvelle.

Écritures attendues et réellement comparées ligne par ligne :

| Opération | Débit | Crédit |
|---|---|---|
| Acquisition | 2355 : 10 000 ; 34551 : 2 000 | 4481 : 12 000 |
| Dotation 2024 | 61935 : 2 000 | 28355 : 2 000 |
| Dotation 2025 | 61935 : 2 000 | 28355 : 2 000 |
| Sortie | 28355 : 4 000 ; 6513 : 6 000 | 2355 : 10 000 |
| Produit de cession | 3481 : 9 000 | 7513 : 7 500 ; 4455 : 1 500 |
| Encaissement 2026 | 5141 : 9 000 | 3481 : 9 000 |

## Parcours réellement couvert

L’acquisition et la dotation 2024 sont créées/validées via l’API. Dans le navigateur : sortie au 31/12/2025, décocher « Cession encaissée immédiatement », comptabiliser, lire les six montants de l’oracle, constater l’état Cédé et le bouton Encaisser. Trois brouillons 2025 sont validés depuis le Journal. Aucune écriture d’encaissement n’existe avant paiement.

Après fermeture administrative de janvier 2026 par l’API, la tentative d’encaissement donne HTTP 423 ; réouverture administrative, puis encaissement via le bouton et les deux dialogues date/compte dans le navigateur. Le bouton disparaît et reste absent après rechargement. La nouvelle écriture appartient à 2026, porte la date du 15/01/2026, et est validée depuis le Journal. Les six écritures sont équilibrées et validées ; le solde du compte 3481 est nul.

Cas négatifs : date précédant la cession → HTTP 400 ; période fermée → 423 ; double encaissement → 409 ; accès depuis une autre société → 404. Des snapshots complets de l’immobilisation, des écritures et de leurs lignes montrent l’absence de mutation lors des refus. Les cinq écritures antérieures à l’encaissement et les deux originaux validés 2024 restent identiques après le règlement. Aucune erreur navigateur/serveur observée.

## Commandes et résultats

Environnement : `hisabpro-backend/.venv/Scripts/python.exe`, `PYTHON_DOTENV_DISABLED=1`.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_immobilisations_cession_differee_isole.py
```

Premier test réel : **1 réussite en 26,90 s**, 25 avertissements de dépendances existants ; session 33876, code 0. Le test a ensuite été renforcé pour comparer aussi toutes les colonnes du registre d’immobilisation lors des refus.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_immobilisations_cession_differee_isole.py Test/test_e2e_immobilisations_sortie_isole.py
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_immobilisations_cession_differee_isole.py
```

Relance finale : **3 tests Edge/API/PG nonce réussis en 61,85 s**, 25 avertissements, session 75597, code 0 : nouveau scénario renforcé plus cession immédiate et rebut du lot 243. Aucun test ignoré. Compilation : code 0.

## Limites

Le flux de cession ne comporte pas d’acheteur rattaché : les lignes 3481 de la créance et de l’encaissement n’ont ni tiers_id ni snapshot auxiliaire. Aucun client n’est inventé et aucun lettrage de tiers n’est simulé. Le test démontre le solde comptable nul, **pas un lettrage client**. Aucune facture de cession n’est créée par ce flux, ce que le test vérifie explicitement. La couverture concerne un encaissement total, pas des fractions, des devises ou une qualification TVA différente. Le régime dégressif n’est pas testé ici.

La recette utilisateur et les justificatifs réels restent à effectuer séparément. Prochaine étape : inscrire cette variante dans le suivi de couverture, puis examiner le besoin métier d’un acheteur et d’une facture de cession avant tout élargissement du contrat.
