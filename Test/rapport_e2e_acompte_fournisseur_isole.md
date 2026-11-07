# Acompte fournisseur connecté — 8 octobre 2026

Lot de recette uniquement : aucune source applicative, migration partagée ou donnée réelle modifiée dans ce lot. Réutilisation du serveur API, de PostgreSQL nonce et du stockage temporaire existants. Les deux largeurs Edge exécutées sont 1365 et 390 px. La recette complète réussit après les corrections de scroll des lots distincts 253 et 257.

## Oracle fixé avant le premier test

Société et fournisseur fictifs, compte collectif fournisseur explicitement 4411. Achat de marchandises de 1 000 MAD HT, TVA 20 % soit 200 MAD et TTC 1 200 MAD. Ces comptes et cette nature correspondent au parcours existant de l'application ; ce test ne crée aucune nouvelle règle fiscale.

| Phase | Débit | Crédit |
|---|---|---|
| Avance fournisseur de 400 | 3411 : 400 | 5141 : 400 |
| Facture achat de 1 200 | 6111 : 1 000 ; 34552 : 200 | 4411 : 1 200 |
| Imputation de 400 | 4411 : 400 | 3411 : 400 |
| Règlement du solde de 800 | 4411 : 800 | 5141 : 800 |

Calcul indépendant Decimal : 400 + 1 200 + 400 + 800 = 2 800 MAD au débit et au crédit, quatre écritures et neuf lignes. Soldes finaux : 3411 et 4411 nuls, 5141 créditeur de 1 200, 6111 débiteur de 1 000, 34552 débiteur de 200. Les lignes fournisseurs sont réellement rattachées au tiers et à leur auxiliaire.

Création de l'avance, création/validation/comptabilisation de la facture achat, imputation, règlement, validation des quatre brouillons et lettrage des trois lignes 4411 sont réalisés dans l'interface. Le lettrage attendu AAA est relu après rafraîchissement. Un snapshot des champs comptables et références des écritures définitives reste inchangé avant/après lettrage. Seul le code de lettrage peut évoluer.

Contrôles négatifs prévus : imputation répétée HTTP 409, lecteur autorisé en consultation mais refusé en mutation HTTP 403, autres sociétés sans visibilité et HTTP 404 sur le document. Tous les refus doivent préserver les originaux comptables.

## Exécution

La recette est ajoutée après la collecte de la globale de l'agent principal et exécutée séparément. Compilation Python initiale : exit 0.

Premier run : **1 failed en 40,30 s**, arrêt sur un sélecteur qui supposait le mode brouillon sélectionné par défaut. L'interface réelle propose le choix « Enregistrer en brouillon » et affiche par défaut la validation directe ; le test a été corrigé pour choisir explicitement le brouillon et saisir une référence fournisseur fictive. Aucun oracle comptable n'a changé.

Deuxième run : **1 passed et 1 failed en 47,55 s**. Le parcours desktop 1365 px exécute l'ensemble du scénario et les refus API. Le parcours 390 px échoue sur le clic de validation de la facture brouillon ; il n'est donc pas validé jusqu'au règlement et au lettrage. Aucun clic forcé, changement de viewport ou appel API substitué au clic n'est utilisé pour masquer cet échec.

Diagnostic mobile séparé : **1 failed et 1 deselected en 39,68 s**, avec capture fictive locale et géométrie après échec. Le groupe d'actions est bien déplacé horizontalement (`scrollLeft=963`, `clientWidth=112`, `scrollWidth=1079`). Le centre du bouton Valider est situé à x 304,64 / y 984,5, mais `elementFromPoint` retourne le conteneur de la carte plutôt que le bouton. Les cinq KPI et les filtres empilés consomment la hauteur disponible ; la zone de tableau est écrasée par le flex avec hauteur minimale nulle, et le contenu principal reste masqué par `overflow:hidden`. Il s'agit d'un défaut de hauteur/scroll vertical, pas d'une différence dans l'oracle métier.

L'agent principal a été alerté avant toute correction applicative. Les sources applicatives restent figées pendant la globale ; une correction CSS minimale est proposée dans un lot distinct 253, suivie d'une reprise réelle de cette même recette. Aucune écriture validée n'est modifiée.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_acompte_fournisseur_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_acompte_fournisseur_isole.py -k 390 -x
```

À ce stade historique, le rapport était provisoire : la recette mobile et sa reprise après correction n'étaient pas encore exécutées. Les résultats de reprise finale sont consignés ci-dessous. La recette utilisateur sur ses propres justificatifs et opérations reste à effectuer.

Reprise desktop après ajout des contrôles d'imputation unique et règlement unique : **1 passed et 1 deselected en 23,33 s** (`-k 1365 -x`). Le seul test non sélectionné est le cas mobile connu en échec, dont le résultat n'est pas transformé en réussite. Compilation Python répétée : exit 0.

À la reprise de 17:52 UTC, après la correction distincte 253 de la liste des factures, le scénario est relancé sans modifier son oracle : **1 passed et 1 failed en 56,25 s**. Le mobile franchit désormais la validation et la comptabilisation de la facture, l'imputation de 400 MAD, le règlement de 800 MAD et la validation des quatre écritures. Il rencontre un nouveau défaut de hauteur dans le lettrage après la première case cochée : la barre de sélection réduit le tableau et son en-tête fixe intercepte la deuxième case. Le clic n'est pas forcé et le lettrage mobile n'est pas déclaré réussi.

Capture fictive de diagnostic : `.codex-tests/acompte_fournisseur_390_fe3c3fe1.png`. L'agent principal a été alerté avant toute modification de Lettrage. L'analyse montre le même mécanisme de flex à hauteur minimale nulle et parent en overflow masqué dans cette autre page. Le correctif et sa recette appartiennent au lot distinct 257. Les quatre écritures et leurs montants étaient déjà contrôlés avant l'étape de lettrage bloquée.

## Validation finale après les corrections 253 et 257

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_acompte_fournisseur_isole.py Test/test_e2e_acompte_imputation_isole.py Test/test_e2e_lettrage_concurrence_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_acompte_fournisseur_isole.py Test/test_e2e_lettrage_table_scroll_isole.py
```

Résultat : **13 passed en 106,24 s**, zéro échec et zéro test ignoré. Ce run inclut les **deux nouvelles recettes fournisseur réussies**, le cycle client existant, les refus de montants non finis et la course GET du lettrage. La compilation Python des deux tests est réussie, exit 0.

Les deux largeurs réalisent effectivement la création de l'avance, l'achat brouillon avec référence fournisseur, la validation/comptabilisation, l'imputation, le paiement du solde, la validation des quatre écritures et le lettrage AAA persistant. Les quatre oracles par écriture, neuf lignes, cumul débit = crédit = 2 800 MAD, soldes du 3411/4411 nuls et banque créditeur de 1 200 sont vérifiés. L'imputation est unique/active et comptabilisée, le règlement est unique. Les refus 409/403/404 laissent inchangés les originaux définitifs. Les échecs de préparation et les défauts UX rencontrés restent visibles dans l'historique ci-dessus ; aucun oracle n'a été ajusté au moteur.

Statut : tests automatisés locaux de ce parcours validés ; recette utilisateur restant à effectuer. Aucun PostgreSQL, fichier ou document comptable utilisateur réel n'a été utilisé. Cette recette ne constitue pas une certification comptable ou fiscale.
