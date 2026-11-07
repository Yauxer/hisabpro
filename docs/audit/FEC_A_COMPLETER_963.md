# Compléments FEC à saisir après montée de version — lot 963 (données de test locales)

Origine : contrôle `GET /api/fec/apercu` sur une copie migrée de la base locale, après :

- récupération automatique `POST /api/fec/reparer-sources-factures` : **0 sur 10 récupérables**, aucune facture source n'étant exactement rapprochable ;
- validation des brouillons. Trois ont été refusés parce qu'ils n'étaient pas soumis dans l'ordre chronologique.

Ces informations ne sont **pas déterminables** depuis les données : elles doivent être saisies par vous via les compléments historiques de l'écran FEC/Journal (ajout uniquement, écriture définitive inchangée). Ne pas inventer de tiers ni de référence.

## À faire dans l'application, une fois la base migrée

1. Société 3, exercice 2027 : valider les brouillons restants **par date croissante**. L'écriture 144 demande d'abord son fournisseur sur le compte 4411.
2. Pour chaque ligne ci-dessous, renseigner le tiers ou la référence de pièce réels.
3. Relancer l'aperçu FEC : l'export devient disponible quand il n'y a plus de bloquant.

| Société-exercice | Anomalie | Écriture | Journal | Compte / détail |
|---|---|---|---|---|
| 3-2026 | AUXILIAIRE_MANQUANT | VT-2026-0001 | VT | compte 3421, ligne 275 |
| 3-2026 | AUXILIAIRE_MANQUANT | AC-2026-0001 | AC | compte 4411, ligne 3 |
| 3-2026 | AUXILIAIRE_MANQUANT | VT-2026-0002 | VT | compte 3421, ligne 6 |
| 3-2026 | REFERENCE_PIECE_MANQUANTE | AC-2026-0002 | AC | compte  |
| 3-2026 | REFERENCE_PIECE_MANQUANTE | AC-2026-0003 | AC | compte  |
| 3-2026 | AUXILIAIRE_MANQUANT | AC-2026-0003 | AC | compte 4411, ligne 12 |
| 3-2026 | REFERENCE_PIECE_MANQUANTE | VT-2026-0003 | VT | compte  |
| 3-2026 | AUXILIAIRE_MANQUANT | VT-2026-0004 | VT | compte 3421, ligne 19 |
| 3-2026 | AUXILIAIRE_MANQUANT | VT-2026-0005 | VT | compte 3421, ligne 22 |
| 3-2026 | AUXILIAIRE_MANQUANT | VT-2026-0031 | VT | compte 3421, ligne 129 |
| 3-2026 | REFERENCE_PIECE_MANQUANTE | BQ-2026-0004 | BQ | compte  |
| 3-2026 | REFERENCE_PIECE_MANQUANTE | AE-2026-0012 | AE | compte  |
| 3-2026 | REFERENCE_PIECE_MANQUANTE | OD-2026-0012 | OD | compte  |
| 3-2026 | AUXILIAIRE_MANQUANT | AC-2026-0014 | AC | compte 4411, ligne 253 |
| 3-2026 | AUXILIAIRES_COLLECTIF_DESEQUILIBRES | — | — | écart collectif/auxiliaires  (se résout avec les tiers manquants) |
| 3-2026 | AUXILIAIRES_COLLECTIF_DESEQUILIBRES | — | — | écart collectif/auxiliaires  (se résout avec les tiers manquants) |
| 3-2027 | Brouillons à valider | 141, 142, 144, 145 | — | par date croissante |
| 3-2027 | AUXILIAIRE_MANQUANT | AN-2027-0001 | AN | compte 3421, ligne 452 |
| 3-2027 | AUXILIAIRE_MANQUANT | AN-2027-0001 | AN | compte 4411, ligne 460 |
| 3-2027 | REFERENCE_PIECE_MANQUANTE | BQ-2027-0001 | BQ | compte  |
| 3-2027 | REFERENCE_PIECE_MANQUANTE | BQ-2027-0002 | BQ | compte  |
| 3-2027 | AUXILIAIRES_COLLECTIF_DESEQUILIBRES | — | — | écart collectif/auxiliaires  (se résout avec les tiers manquants) |
| 3-2027 | AUXILIAIRES_COLLECTIF_DESEQUILIBRES | — | — | écart collectif/auxiliaires  (se résout avec les tiers manquants) |
| 11-2026 | REFERENCE_PIECE_MANQUANTE | BQ-2026-0003 | BQ | compte  |

Sociétés 6 (2025) et 10 (2026) : FEC déjà conforme. La copie a été jetée après contrôle ; votre base n'a pas été modifiée.
