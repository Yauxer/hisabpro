# Audit indépendant du MVP facturation/comptabilité — lot 957 (30 octobre 2026)

**Question :** le MVP facturation/comptabilité est-il assez fiable pour un pilote accompagné ?

**Réponse : oui, sous conditions,** une fois les correctifs 957 appliqués et les trois préalables ci-dessous remplis. Avant 957, la réponse était **non** : une facture ordinaire pouvait produire une écriture déséquilibrée, impossible à valider (anomalie F1).

Préalables au pilote :

1. Sur une **copie restaurée** de la base cible : constater l'existant puis appliquer 126, 127 et 128 avec `ops/migrations_hisabpro.py` (voir `docs/EXPLOITATION_HISABPRO.md`, complément 957). Rejouer ensuite les tests 953 et 957. Le code 957 exige la migration 127.
2. Configurer la cible : `APP_ENV=production`, un `SECRET_KEY` privé, HTTPS et une liste CORS exacte. Le `.env` local contient un secret qui ressemble à une valeur d'exemple.
3. Tant que les déclarations TVA déposées ne sont pas figées (limitation `gel_declaration_deposee`), l'accompagnant conserve le PDF de chaque déclaration déposée et ferme la période comptable après dépôt.

Aucune base PostgreSQL réelle n'a été utilisée. Tous les tests ont tourné sur des clusters éphémères (`Test/postgres_isole.py`, port ≠ 5432) avec des données fictives.

## 1. Ce qui a été réellement vérifié

| Nature | Contenu | Résultat |
|---|---|---|
| Tests existants rejoués | `test_compensations_tva953_isole.py` | 13 réussis |
| Tests existants rejoués | lettrage (codes, identité auxiliaire) et ventilation inter-exercices | 20 réussis |
| Sondes indépendantes (hors dépôt) | 12 scénarios : annulation/TVA, chèque impayé, avoirs, arrondis, sur-paiement, période fermée, isolation | 7 anomalies reproduites |
| Nouveaux tests de non-régression 957 | arrondis, annulation de règlement/TVA, bornes et dates | 14 réussis après correctif |
| Non-régression connexe | voir `CODEX_PROGRESS.md`, étape AUDIT-CLAUDE-957 | voir journal |
| Validation 957 — E2E navigateur | `Test/test_e2e_impaye_encaisse957_isole.py`, Effets, 1365 et 390 px | 2 réussis, sans erreur console ni serveur |
| Validation 957 — non-régression | consolidation 543 (inclut 536/538/540) seule ; 10 fichiers consolidation TVA/RAS/règlements/factures635 | 356/356 ; 1 018 réussis + 2 rejoués seuls après arrêt mémoire |
| Validation 957 — campagne finale | 111 fichiers restants (lots 01 à 11), rejoués sur le code 957 final | **1 413 réussis, 4 échecs préexistants**, depuis corrigés : `test_patch072` ×2, `test_patch073`, `test_patch075`. Ces tests statiques ont été actualisés sur l'état actuel de l'interface : date de facturation d'un BL, `BadgeEcheance`, gardes `peutModifier`. Aucun fichier produit modifié ; lot 04 rejoué à 46/46 |
| Build Vite | 214 modules, 10,62 s, sortie hors dépôt | réussi (frontend non modifié) |
| Analyse statique | cycle facture → règlement → lettrage, avoirs, TVA, permissions, migrations, configuration | — |

**Non vérifié ici :** navigation sur ordinateur et mobile (des preuves Edge antérieures existent mais n'ont pas été rejouées), restauration annuelle complète, PostgreSQL réel. La recette humaine reste entière : 262 fiches « Non testé » et 10 « Bloqué » côté humain dans `SUIVI_AUTOMATISATION_CAHIER_955.xlsx`.

## 2. Anomalies

### F1 — Bloquant, corrigé en 957 : écriture de facture ou d'avoir déséquilibrée de 0,01

- **Scénario :** vente, 1 ligne, quantité 7 × 13,4567 MAD, TVA 18 % (2025). Valider, puis comptabiliser.
- **Attendu :** 3421 = 4455 + 7111, écriture validable.
- **Observé :** 3421 = 111,15 ; 4455 = 16,96 ; 7111 = 94,20. La validation refuse avec « Écriture déséquilibrée (débit 246.36 / crédit 246.35) » dans le cas multi-lignes. Le défaut a été reproduit sur 11 combinaisons sur 30, avec ou sans remise globale.
- **Cause :** `services/tva_service.py`, `ventilation_facture` et `ventilation_avoir` calculaient TTC = arrondi(HT brut + TVA brute) au lieu de HT arrondi + TVA arrondie.
- **Correctif :** TTC = `money(base) + money(tva)`, appliqué aussi à l'affichage par ligne (`routers/factures.py`).
- **Preuve :** `Test/test_arrondis_ttc957_isole.py`, 5 cas vente et achat, avoir total inclus.
- **Effet sur l'historique :** le TTC affiché d'une facture ancienne concernée peut changer de 0,01. Comme ces écritures étaient invalidables, aucune écriture validée n'est modifiée. À contrôler sur la copie de base : rechercher les écritures `source='facture'` en brouillon et déséquilibrées.

### F2 — Majeur, corrigé en 957 : annuler un règlement réécrit la TVA des périodes passées (régime des encaissements)

- **Scénario :** facture de janvier (1 000 HT, TVA 20 %), virement du 20/01, puis annulation datée du 05/03.
- **Attendu :** TVA de janvier inchangée (200) et régularisation de -200 en mars.
- **Observé :** janvier recalculé à 0, mars à 0. Même chose en achat, ce qui revient à une déduction perdue ou jamais reversée.
- **Correctif :** nouvelle colonne `reglements.date_annulation_effective` (migration additive `127_reglements_annulation_effective.sql`), alimentée à l'annulation. `routers/tva.py` compte le paiement jusqu'à sa date d'annulation. Pour l'historique, la date est lue sur l'écriture de contrepassation. Sans écriture, aucune date n'est inventée : une alerte « date d'annulation inconnue » s'affiche.
- **Preuve :** `Test/test_annulation_reglement_tva957_isole.py`, 5 cas, migration rejouée deux fois.

### F3 — Moyen, corrigé en 957 : sur-règlement et sur-imputation d'un centime acceptés

- **Observé :** un règlement de 500,01 sur un solde de 500 est accepté. Une imputation d'avoir de 1 200,01 pour un crédit de 1 200 aussi : crédit tiers de 0,01, avoir négatif.
- **Correctif :** comparaison au centime arrondi dans `routers/commercial.py` (création et modification) et dans `avoirs.py`.

### F4 — Moyen, corrigé en 957 : imputation d'avoir antérieure aux pièces acceptée

- **Observé :** une imputation datée du 05/01 est acceptée alors que la facture cible date du 01/03 et l'avoir du 10/02.
- **Correctif :** refus 422 si la date est antérieure à la facture cible ou à l'avoir.

### F5 — Mineur, corrigé en 957 : un taux TVA hors catalogue renvoie une erreur 500

- **Observé :** une facture en brouillon datée de 2025 à 14 % ou 7 % renvoie une 500. Le trigger 033 refuse bien, mais le message est perdu.
- **Correctif :** le même contrôle `valider_tva` est appliqué avant insertion et renvoie un 422 explicite. Les taux sont vérifiés dans le CGI 2026, art. 99, copie locale `.codex-tests/CGI2026_CRI.pdf` : 20 % et 10 %.

### F6 — Moyen, corrigé en 957 : un chèque ou un effet déjà encaissé ne pouvait plus être constaté impayé

- **Observé avant 957 :** après `encaisser`, `rejeter` renvoyait 400 et `annuler` renvoyait 409.
- **Correctif :** `rejeter` est désormais accepté depuis `encaisse`. L'écriture BQ datée du rejet contient :
  - 3421 au débit (montant + frais) ;
  - la banque au crédit (montant + frais) ;
  - les frais bancaires en 6147, refacturés en 7127.

  La date d'encaissement est conservée et `date_rejet_effective` ajoutée (migration 127). La TVA sur encaissements reste due jusqu'au rejet, puis est régularisée dans la période du rejet. Un rejet antérieur à l'encaissement est refusé. Le bouton est ajouté dans `src/pages/Effets.jsx`.
- **Preuve :** `Test/test_impaye_apres_encaissement957_isole.py` (2 cas).

### F7 — Majeur pour l'exploitation, corrigé en 957 : aucun suivi des migrations appliquées

- **Correctif :** table `hisabpro_migrations` (128) et script `ops/migrations_hisabpro.py` avec les actions `etat`, `constater` et `appliquer --suivantes`.
- **Garde-fous :** nom de base confirmé, `--jusqua` réservé aux bases vierges, réparations 065/067/070 exclues, empreinte modifiée bloquante.
- **Preuve :** `Test/test_registre_migrations957_isole.py`.
- **Reste à faire :** le manifeste de la base réelle, c'est-à-dire la liste exacte des scripts déjà présents, doit être établi par l'administrateur.

### F8 — Information : TVA recalculée à chaque consultation

- Rien n'enregistre une déclaration TVA déposée. Les saisies ultérieures datées d'une période encore ouverte modifient donc son recalcul.
- La fermeture des périodes comptables (testée : 423 sur un règlement ou une annulation daté d'une période fermée) atténue le risque.

## 2 bis. Lot 959 — compléments réalisés

| Chantier | Réalisation | Preuve |
|---|---|---|
| F8 — gel des déclarations TVA | Dépôt figé : instantané, date et référence, rectificative motivée, immuabilité SQL (129). Un écart avec le recalcul est signalé sans réécriture. Le crédit reporté est le crédit déclaré. Sans 129 : alerte et refus 503. Bandeau de dépôt dans l'écran TVA | `test_tva_depot959_isole` 2/2, `test_tva_sans129_959_isole` 1/1 |
| Restauration du dossier annuel fictif (HP-EXP-003/004) | Année 2025 complète avec clôture et à-nouveaux 2026, sauvegarde native, restauration sur base vierge isolée, seconde API : 72 tables (2 084 lignes), 67 séquences et 28 sorties métier identiques. Défaut trouvé et corrigé : ordre non déterministe des détails TVA | `test_restauration_annuelle959_isole` 1/1 |
| Navigation complète (HP-SEC-004) | 27 écrans MVP en 1366×768 et 390×844 : aucun débordement horizontal, titre présent, aucune erreur JavaScript ni 5xx. Les formulaires en fenêtre modale ne sont pas tous ouverts | `test_e2e_navigation_complete959_isole` 2/2 |
| Lettrage partiel | Case « lettrage partiel », mention « partiel », action « Compléter XXX ». Code déséquilibré admis seulement si toutes ses lignes sont partielles (130) ; garde SQL conservée sinon. Le FEC exporte le code d'un lettrage partiel comme les autres, **à valider par le responsable comptable** | `test_lettrage_partiel959_isole` 2/2 |

Non-régression 959, fichier par fichier sur le code final :
- TVA : 451/451 ;
- lettrage (unitaires, navigateur et partiel) : 44 réussis ;
- installations vierges 098/100/103/104 : réussies ;
- registre des migrations : 1/1 ;
- build Vite : 214 modules.

Un premier passage TVA à 58 échecs était antérieur au correctif « migration 129 absente » et a écrit dans le même journal qu'un second passage : il est invalidé et n'a pas été retenu.

## 3. Points solides constatés

- **Isolation des sociétés :** un utilisateur B reçoit 404 sur le règlement, l'annulation, la lecture, le PDF et la comptabilisation des objets de A.
- **Écritures définitives :** protégées par trigger (072), dévalidation impossible, contrepassation tracée.
- **Lettrage :** même compte, même tiers, même exercice, équilibre strict, lignes définitives uniquement. Pas de lettrage partiel.
- **Périodes :** fermées ou clôturées, elles refusent règlements et annulations.
- **Compensation d'avoir (126) :** signature confirmée explicitement, sans date inventée.

## 4. Périmètre MVP / hors MVP

- **Nécessaire au pilote :** devis, commandes, livraisons, factures, avoirs, règlements, lettrage, banque, TVA, FEC, balance, grand livre, clôture.
- **Hors MVP, incomplet ou bloqué par des sources :** XML/EDI SIMPL-IS, référentiel DGI exhaustif, état des ventes, liasse « prête à déposer », ETIC B6/B13/B14, variantes de cession, Personnel/Paie.

## 5. Prochaines étapes recommandées

1. Appliquer 126 et 127 sur une copie restaurée de la base réelle, puis rejouer les tests 953 et 957.
2. Valider F6 en navigateur (écran Effets, ordinateur et mobile) et établir le manifeste des migrations de la base réelle.
3. Recette humaine accompagnée sur ordinateur et mobile pour les fiches facturation, paiements et comptabilité.
