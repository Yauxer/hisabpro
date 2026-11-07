# Recette 09A — PostgreSQL en lecture seule

Contrôle du 2026-10-06T12:43:01+00:00, société 3, exercice 2026.

Connexion protégée par `default_transaction_read_only=on` ; transactions annulées et connexions fermées.
Aucune migration, réparation, confirmation ou mutation comptable exécutée.

## Contrôles de la liasse

Prête à finaliser : False ; bloquants : 4.

| Contrôle | Résultat | Détail |
| --- | --- | --- |
| IDENTITE_IF | À vérifier | Renseignez l'IF dans les paramètres société. |
| IDENTITE_ICE | À vérifier | Renseignez l'ICE dans les paramètres société. |
| SOURCE_BALANCE | OK | Écart : 0.00 MAD |
| BROUILLONS | OK | 0 brouillon(s) exclu(s). |
| EXERCICE_CLOTURE | OK | La liasse peut être prévisualisée avant clôture, mais pas finalisée. |
| BILAN_EQUI | OK | Écart : 0.00 MAD |
| FEC_CONFORME | À vérifier | 16 anomalie(s) bloquante(s), 1 avertissement(s). |
| ETIC_COMPLETE | À vérifier | 9/23 sections complètes. |
| LIQUIDATION_IS | OK | Confirmez la liquidation fiscale avant finalisation. |
| RESULTAT_COMPTABLE_FISCAL | OK | CPC 124864.88 / Fiscal 124864.88 MAD |
| COMPARATIF_N1 | À vérifier | Aucune donnée N-1 ; acceptable pour un premier exercice ou une reprise. |
| TABLEAU_FINANCEMENT | OK | Premier exercice / reprise sans comparatif N-1 : contrôle de variation non applicable. |

FEC : 16 anomalies bloquantes ; 1 avertissements.
ETIC : 9/23 sections complètes.

### Détail des anomalies FEC

- bloquants / AUXILIAIRE_MANQUANT / écriture 106 : Compte collectif 3421 sans compte auxiliaire client/fournisseur explicite.
- bloquants / AUXILIAIRE_MANQUANT / écriture 1 : Compte collectif 4411 sans compte auxiliaire client/fournisseur explicite.
- bloquants / AUXILIAIRE_MANQUANT / écriture 2 : Compte collectif 3421 sans compte auxiliaire client/fournisseur explicite.
- bloquants / REFERENCE_PIECE_MANQUANTE / écriture 3 : Référence de pièce justificative manquante. Ajoutez-la depuis le Journal ; la validation de l'écriture reste inchangée.
- bloquants / REFERENCE_PIECE_MANQUANTE / écriture 4 : Référence de pièce justificative manquante. Ajoutez-la depuis le Journal ; la validation de l'écriture reste inchangée.
- bloquants / AUXILIAIRE_MANQUANT / écriture 4 : Compte collectif 4411 sans compte auxiliaire client/fournisseur explicite.
- bloquants / REFERENCE_PIECE_MANQUANTE / écriture 5 : Référence de pièce justificative manquante. Ajoutez-la depuis le Journal ; la validation de l'écriture reste inchangée.
- bloquants / AUXILIAIRE_MANQUANT / écriture 8 : Compte collectif 3421 sans compte auxiliaire client/fournisseur explicite.
- bloquants / AUXILIAIRE_MANQUANT / écriture 9 : Compte collectif 3421 sans compte auxiliaire client/fournisseur explicite.
- bloquants / AUXILIAIRE_MANQUANT / écriture 46 : Compte collectif 3421 sans compte auxiliaire client/fournisseur explicite.
- bloquants / REFERENCE_PIECE_MANQUANTE / écriture 66 : Référence de pièce justificative manquante. Ajoutez-la depuis le Journal ; la validation de l'écriture reste inchangée.
- bloquants / REFERENCE_PIECE_MANQUANTE / écriture 83 : Référence de pièce justificative manquante. Ajoutez-la depuis le Journal ; la validation de l'écriture reste inchangée.
- bloquants / REFERENCE_PIECE_MANQUANTE / écriture 84 : Référence de pièce justificative manquante. Ajoutez-la depuis le Journal ; la validation de l'écriture reste inchangée.
- bloquants / AUXILIAIRE_MANQUANT / écriture 96 : Compte collectif 4411 sans compte auxiliaire client/fournisseur explicite.
- bloquants / AUXILIAIRES_COLLECTIF_DESEQUILIBRES / écriture globale : Compte collectif 3421 : les mouvements auxiliaires ne recoupent pas le compte collectif.
- bloquants / AUXILIAIRES_COLLECTIF_DESEQUILIBRES / écriture globale : Compte collectif 4411 : les mouvements auxiliaires ne recoupent pas le compte collectif.
- avertissements / ECRITURE_CLOTURE_HISTORIQUE_HORS_CL / écriture 138 : Clôture historique CLOTURE-2026 conservée dans OD ; les nouvelles clôtures HisabPro utilisent le journal CL.

## B6 — Tableau des créances

Section complète : False.

| Compte | Solde | Source factures | Échéances documentées et recoupées | Source non qualifiée | Préremplissage |
| --- | ---: | ---: | ---: | ---: | --- |
| 3421 | 161302.80 | 105110.80 | 70412.80 | 34698.00 | Partiel |
| 3427 | 4000.00 | À compléter | À compléter | À compléter | Aucun |
| 3453 | 50.00 | À compléter | À compléter | À compléter | Aucun |
| 34551 | 6200.00 | À compléter | À compléter | À compléter | Aucun |
| 34552 | 7820.00 | À compléter | À compléter | À compléter | Aucun |
| 3491 | 1200.00 | À compléter | À compléter | À compléter | Aucun |

Sources à vérifier (les montants ci-dessus ne justifient aucune reclassification) :

- 3421 / facture 39 (666665) : Règlement 6 : réduction sans écriture validée recoupant le compte exact à la clôture.
- 3421 / facture 17 (45) : Règlement 14 : réduction sans écriture validée recoupant le compte exact à la clôture.
- 3421 / facture 40 (FA-12) : Règlement 16 : réduction sans écriture validée recoupant le compte exact à la clôture. Règlement 7 : réduction sans écriture validée recoupant le compte exact à la clôture.
- 3421 / facture 56 (FA-2026-006) : Règlement 28 : réduction sans écriture validée recoupant le compte exact à la clôture.
- 3421 / facture 52 (FA-2026-002) : Imputation d'acompte 1 : réduction sans écriture validée recoupant le compte exact à la clôture.
- 3421 / facture 55 (FA-2026-005) : Règlement 26 : Rejet sans date historique liée : effet sur le solde à la clôture à vérifier. Règlement 27 : Rejet sans date historique liée : effet sur le solde à la clôture à vérifier.
- 3421 / facture 38 (FAAA-2026-001) : Règlement 5 : réduction sans écriture validée recoupant le compte exact à la clôture. Écriture principale absente ou non unique sur date, référence et TTC.
- 3421 / facture 62 (FA-2026-012) : Écriture principale absente ou non unique sur date, référence et TTC.
- 3421 / facture 69 (FA-2026-019) : Écriture principale absente ou non unique sur date, référence et TTC.
- 3421 / facture 41 (FA-deez-01) : Règlement 15 : réduction sans écriture validée recoupant le compte exact à la clôture. Règlement 9 : réduction sans écriture validée recoupant le compte exact à la clôture.
- 3421 / facture 54 (FA-2026-004) : Règlement 25 : Rejet sans date historique liée : effet sur le solde à la clôture à vérifier.
- 3421 / facture 36 (FA989) : Règlement 2 : réduction sans écriture validée recoupant le compte exact à la clôture. Règlement 1 : réduction sans écriture validée recoupant le compte exact à la clôture.
- 3421 / facture 53 (FA-2026-003) : Règlement 24 : Rejet sans date historique liée : effet sur le solde à la clôture à vérifier.
- 3421 / facture 44 (FATEST) : Règlement 12 : réduction sans écriture validée recoupant le compte exact à la clôture. Règlement 11 : réduction sans écriture validée recoupant le compte exact à la clôture.
- 3421 / facture 58 (FA-2026-008) : Règlement 30 : Rejet sans date historique liée : effet sur le solde à la clôture à vérifier. Règlement 35 : Rejet sans date historique liée : effet sur le solde à la clôture à vérifier.
- 3421 / facture 49 (FA-testest-1) : Règlement 23 : réduction sans écriture validée recoupant le compte exact à la clôture. Règlement 22 : réduction sans écriture validée recoupant le compte exact à la clôture. Avoir AV-2026-007 : écriture AV absente, non unique ou non recoupée à la clôture.
- 3421 / facture 45 (TEST-01) : Avoir AV-2026-003 : écriture AV absente, non unique ou non recoupée à la clôture. Avoir AV-2026-004 : écriture AV absente, non unique ou non recoupée à la clôture. Avoir AV-2026-005 : écriture AV absente, non unique ou non recoupée à la clôture. Écriture principale absente ou non unique sur date, référence et TTC.
- 3421 / facture 13 (067) : Règlement 13 : réduction sans écriture validée recoupant le compte exact à la clôture.

Contrôles de ventilation :

- 3421 : la ventilation par échéance doit totaliser 161302.80 MAD.
- 3421 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 3421 : renseignez Etat / organismes publics ou confirmez que les autres analyses sont néant.
- 3421 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 3421 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 3427 : renseignez la ventilation + d'un an.
- 3427 : renseignez la ventilation - d'un an.
- 3427 : renseignez la ventilation échues et non recouvrées.
- 3427 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 3427 : renseignez Etat / organismes publics ou confirmez que les autres analyses sont néant.
- 3427 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 3427 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 3453 : renseignez la ventilation + d'un an.
- 3453 : renseignez la ventilation - d'un an.
- 3453 : renseignez la ventilation échues et non recouvrées.
- 3453 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 3453 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 3453 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 34551 : renseignez la ventilation + d'un an.
- 34551 : renseignez la ventilation - d'un an.
- 34551 : renseignez la ventilation échues et non recouvrées.
- 34551 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 34551 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 34551 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 34552 : renseignez la ventilation + d'un an.
- 34552 : renseignez la ventilation - d'un an.
- 34552 : renseignez la ventilation échues et non recouvrées.
- 34552 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 34552 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 34552 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 3491 : renseignez la ventilation + d'un an.
- 3491 : renseignez la ventilation - d'un an.
- 3491 : renseignez la ventilation échues et non recouvrées.
- 3491 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 3491 : renseignez Etat / organismes publics ou confirmez que les autres analyses sont néant.
- 3491 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 3491 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.

## B7 — Tableau des dettes

Section complète : False.

| Compte | Solde | Source factures | Échéances documentées et recoupées | Source non qualifiée | Préremplissage |
| --- | ---: | ---: | ---: | ---: | --- |
| 4411 | 45960.00 | 33960.00 | 33960.00 | 0.00 | Partiel |
| 4417 | 2500.00 | À compléter | À compléter | À compléter | Aucun |
| 4453 | 24972.98 | À compléter | À compléter | À compléter | Aucun |
| 4455 | 28410.80 | À compléter | À compléter | À compléter | Aucun |
| 4481 | 154000.00 | À compléter | À compléter | À compléter | Aucun |
| 4491 | 3000.00 | À compléter | À compléter | À compléter | Aucun |

Sources à vérifier (les montants ci-dessus ne justifient aucune reclassification) :

- 4411 / facture 4 (02) : Règlement 18 : réduction sans écriture validée recoupant le compte exact à la clôture. Règlement 17 : réduction sans écriture validée recoupant le compte exact à la clôture.
- Compte source 44110001 absent des soldes affichés : 960.00 MAD.
- 44110001 / facture 66 (FA-2026-016) : Le compte source 44110001 ne recoupe pas le compte exact de l'écriture principale.
- 44110001 / facture 59 (FA-2026-009) : Règlement 29 : réduction sans écriture validée recoupant le compte exact à la clôture. Le compte source 44110001 ne recoupe pas le compte exact de l'écriture principale.

Contrôles de ventilation :

- 4411 : la ventilation par échéance doit totaliser 45960.00 MAD.
- 4411 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 4411 : renseignez Etat / organismes publics ou confirmez que les autres analyses sont néant.
- 4411 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 4411 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 4417 : renseignez la ventilation + d'un an.
- 4417 : renseignez la ventilation - d'un an.
- 4417 : renseignez la ventilation échues et non payées.
- 4417 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 4417 : renseignez Etat / organismes publics ou confirmez que les autres analyses sont néant.
- 4417 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 4417 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 4453 : renseignez la ventilation + d'un an.
- 4453 : renseignez la ventilation - d'un an.
- 4453 : renseignez la ventilation échues et non payées.
- 4453 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 4453 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 4453 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 4455 : renseignez la ventilation + d'un an.
- 4455 : renseignez la ventilation - d'un an.
- 4455 : renseignez la ventilation échues et non payées.
- 4455 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 4455 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 4455 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 4481 : renseignez la ventilation + d'un an.
- 4481 : renseignez la ventilation - d'un an.
- 4481 : renseignez la ventilation échues et non payées.
- 4481 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 4481 : renseignez Etat / organismes publics ou confirmez que les autres analyses sont néant.
- 4481 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 4481 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.
- 4491 : renseignez la ventilation + d'un an.
- 4491 : renseignez la ventilation - d'un an.
- 4491 : renseignez la ventilation échues et non payées.
- 4491 : renseignez montant en devises ou confirmez que les autres analyses sont néant.
- 4491 : renseignez Etat / organismes publics ou confirmez que les autres analyses sont néant.
- 4491 : renseignez entreprises liées ou confirmez que les autres analyses sont néant.
- 4491 : renseignez montant représenté par effets ou confirmez que les autres analyses sont néant.

## Limites et prochaine étape

Ces constats ne valident ni les pièces historiques ni les saisies extra-comptables.
Les incohérences réelles nécessitent les justificatifs et une décision comptable avant toute réparation tracée.
Vérifier dans le navigateur connecté la conservation des saisies et les exports ; les tests React synthétiques ne remplacent pas ce parcours.
09A reste ouverte tant que les contrôles bloquants ne sont pas levés. Ne pas démarrer 09B/EDI sur une recette non validée.

## Rapprochement des références 02 et 002

Les références sont comparées littéralement ; aucun zéro initial supprimé.

| Type | Facture | Référence | Écriture(s) principale(s) recoupée(s) |
| --- | ---: | --- | --- |
| achat | 4 | 02 | 7 |
| achat | 10 | 002 | 13 |

## Exports vérifiés en mémoire

PDF généré et relu : 34 pages ; XLSX écrit/relu : 9 feuilles et 12 lignes de ventilation B6/B7 vérifiées.
Source inchangée ; aucun PDF/XLSX sauvegardé ni archive comptable créée.
