# E2E connecté — Cycle commercial vente

Lot `E2E-CYCLE-COMMERCIAL-20261007`, exécuté le 7 octobre 2026.
Test : `Test/test_e2e_cycle_commercial_isole.py`.

## Environnement

Navigateur Edge headless, vraie application React, API FastAPI réelle et
PostgreSQL éphémère via le banc partagé de facturation. Société fictive créée
dans ce cluster isolé, client fictif et article fictif préparés par API.
Aucun appel API simulé, aucune lecture de `.env`, aucune utilisation de la base
réelle et aucune modification de données comptables historiques.

Les tests E2E existants couvraient facturation directe, règlements, lettrage,
banques et immobilisations. Ce lot ajoute les transformations préalables depuis
le devis et leur traçabilité, auparavant couvertes notamment par les assertions
de code des tests fact2/factC.

## Scénario exécuté dans l'interface

Préparation : client avec délai de paiement configuré 30 jours ; article stockable
avec prix de vente HT 500 MAD, prix d'achat HT 300 MAD, stock initial 10 unités,
compte de vente 7111 et TVA configurée à 20 %. Le déclencheur existant du stock
de vente est « facture ». Ces paramètres de recette n'introduisent aucune
obligation fiscale nouvelle.

1. Créer un devis pour deux unités en choisissant le vrai client et l'article
   dans les listes de suggestions. Total HT 1 000 MAD.
2. Marquer le devis accepté, créer un BC depuis celui-ci, vérifier le lien au devis.
3. Créer le BL depuis le reliquat du BC : deux unités.
4. Confirmer l'expédition puis la remise au client. Le stock reste à 10 unités
   et aucune écriture n'existe, conformément au déclencheur « facture ».
5. Créer le brouillon de facture depuis le BL. TTC 1 200 MAD ; pas de numéro
   définitif, pas de stock mouvementé ni d'écriture à ce stade.
6. Valider définitivement la facture : stock 8 unités, une seule sortie de deux
   unités en plus du mouvement de stock initial.
7. Comptabiliser la facture, puis valider l'écriture dans le Journal.
8. Revenir aux BC et BL, vérifier la progression 100 % et l'absence des actions
   de nouvelle livraison/facturation du reliquat soldé. Recharger et vérifier
   la persistance ainsi que l'intégrité des montants et des lignes validées.

## Preuves vérifiées automatiquement

| Domaine | Vérification |
|---|---|
| Montants | 2 × 500 = 1 000 HT ; TVA 200 ; TTC 1 200 |
| Sources | Ligne BC → ligne devis ; ligne BL → ligne BC ; ligne facture → lignes BC et BL |
| Tiers | Client natif conservé sur la ligne 3421, snapshot auxiliaire présent |
| Comptabilité | Une écriture validée : D3421 1 200 / C7111 1 000 / C4455 200 |
| Stock | Une sortie de deux unités, avant 10 / après 8 ; source facture et ligne exactes, clé d'idempotence présente |
| Brouillon | Aucune sortie ni écriture avant validation de la facture |
| Logistique | BL livré, lié au BC et à la facture |
| Devis | Statut API « converti » dérivé du BC existant ; lien BC conservé |
| Rechargement | Progression 100 %, stock 8, même écriture et mêmes comptes/débits/crédits |
| Navigateur | Aucune erreur JavaScript ni réponse serveur en erreur |

Le statut « converti » du devis est dérivé par le sérialiseur à partir du lien
BC : le stockage interne peut rester « accepte ». Le test contrôle le statut
API réel plutôt que d'imposer une mutation non prévue par le code.

## Tests réellement exécutés

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_cycle_commercial_isole.py -x
```

Exécution finale : **1 passed, 25 warnings in 19.91s**, code retour 0.
Les avertissements sont les dépréciations existantes Pydantic/python_multipart.
Deux exécutions initiales ont échoué sur des erreurs du test : présomption
du statut interne du devis (20,66 s), puis absence du paramètre API obligatoire
`exercice` lors de sa vérification finale (19,27 s). Ces erreurs sont corrigées.
Aucun défaut produit ni modification du code produit dans ce lot.

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_fact2_cycle_commercial.py Test/test_factC_cycle_documentaire.py Test/test_patch071_detail_bon_livraison.py Test/test_stock_integrite_mouvements.py
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile Test/test_e2e_cycle_commercial_isole.py
```

Connexes : **50 passed in 2.35s**, code retour 0. Compilation : code retour 0.
Les tests connexes ne remplacent pas la preuve PostgreSQL : celle-ci provient
du scénario connecté exécuté ci-dessus.

## Limites

Ce scénario couvre une vente et une livraison complètes, avec déclenchement
du stock à la validation de facture. Les livraisons/facturations partielles,
les achats, le déclencheur BL, les retours, remises et annulations ne sont pas
déclarés validés par ce nouveau test. Il vérifie la disparition des actions de
doublon dans l'interface ; il ne simule pas ici une concurrence API.
Aucun e-mail n'a été préparé ou envoyé. Recette utilisateur et conformité
réglementaire restent distinctes de ces tests automatisés.
