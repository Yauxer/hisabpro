-- ============================================================
-- HisabPro — Référentiel fiscal marocain 2025 / 2026
-- Sources de référence : CGI 2026 / LF 2025 / LF 2026.
-- Ce script est volontairement idempotent : il remplace les valeurs
-- HisabPro des exercices 2025 et 2026 au lieu de créer des doublons.
-- ============================================================

BEGIN;

-- ── Barème IR annuel 2025 et 2026 ───────────────────────────────────────────
-- Barème applicable depuis le 01/01/2025 (CGI art. 73-I).
DELETE FROM bareme_ir WHERE annee IN (2025, 2026);

INSERT INTO bareme_ir (annee, tranche_min, tranche_max, taux, deduction) VALUES
  (2025,      0,  40000, 0.00,     0),
  (2025,  40000,  60000, 0.10,  4000),
  (2025,  60000,  80000, 0.20, 10000),
  (2025,  80000, 100000, 0.30, 18000),
  (2025, 100000, 180000, 0.34, 22000),
  (2025, 180000,   NULL, 0.37, 27400),
  (2026,      0,  40000, 0.00,     0),
  (2026,  40000,  60000, 0.10,  4000),
  (2026,  60000,  80000, 0.20, 10000),
  (2026,  80000, 100000, 0.30, 18000),
  (2026, 100000, 180000, 0.34, 22000),
  (2026, 180000,   NULL, 0.37, 27400);

-- ── Taux CNSS/AMO actuellement utilisés par HisabPro ────────────────────────
-- Ces paramètres restent centralisés en base et doivent être revus à chaque
-- changement réglementaire avant utilisation en paie réelle.
DELETE FROM taux_cotisations WHERE annee IN (2025, 2026);

INSERT INTO taux_cotisations (annee, code, libelle, taux_sal, taux_pat, plafond) VALUES
  (2025, 'cnss_retraite',  'CNSS — Retraite et invalidité-décès', 0.0448, 0.0798, 72000),
  (2025, 'cnss_prest_fam', 'CNSS — Prestations familiales',       0.0000, 0.0692, 72000),
  (2025, 'amo',            'AMO — Assurance maladie obligatoire', 0.0226, 0.0226,  NULL),
  (2025, 'accidents',      'Assurance accidents de travail',      0.0000, 0.0100,  NULL),
  (2025, 'formation_prof', 'Taxe de formation professionnelle',   0.0000, 0.0160,  NULL),
  (2026, 'cnss_retraite',  'CNSS — Retraite et invalidité-décès', 0.0448, 0.0798, 72000),
  (2026, 'cnss_prest_fam', 'CNSS — Prestations familiales',       0.0000, 0.0692, 72000),
  (2026, 'amo',            'AMO — Assurance maladie obligatoire', 0.0226, 0.0226,  NULL),
  (2026, 'accidents',      'Assurance accidents de travail',      0.0000, 0.0100,  NULL),
  (2026, 'formation_prof', 'Taxe de formation professionnelle',   0.0000, 0.0160,  NULL);

-- ── Réduction IR pour charges de famille ────────────────────────────────────
-- 2025 : 500 MAD/personne, plafond total 3 000 MAD (6 personnes).
-- 2026 : 600 MAD/personne, plafond total 3 600 MAD (6 personnes).
DELETE FROM deductions_ir WHERE annee IN (2025, 2026);

INSERT INTO deductions_ir (annee, code, libelle, montant_an, max_beneficiaires) VALUES
  (2025, 'conjoint', 'Réduction IR par personne à charge — conjoint', 500, 6),
  (2025, 'enfant',   'Réduction IR par personne à charge — enfant',   500, 6),
  (2026, 'conjoint', 'Réduction IR par personne à charge — conjoint', 600, 6),
  (2026, 'enfant',   'Réduction IR par personne à charge — enfant',   600, 6);

COMMIT;

-- Vérification rapide
SELECT annee, COUNT(*) AS nb_tranches FROM bareme_ir
WHERE annee IN (2025, 2026) GROUP BY annee ORDER BY annee;
SELECT annee, code, montant_an, max_beneficiaires FROM deductions_ir
WHERE annee IN (2025, 2026) ORDER BY annee, code;
