-- Patch 094 — Détail immuable de la liquidation IS
-- A exécuter après 065_reparation_liquidations_is_reference_acomptes.sql.
BEGIN;

ALTER TABLE fiscal_liquidations_is
    ADD COLUMN IF NOT EXISTS snapshot_detail JSONB;

COMMENT ON COLUMN fiscal_liquidations_is.snapshot_detail IS
    'Photographie détaillée figée à la confirmation : référence et 4 acomptes, paiements/références, retenues-crédits et calcul de liquidation.';

-- Le trigger trg_hisabpro_fiscal_liquidation_immutable créé par la migration 024
-- protège aussi cette nouvelle colonne contre UPDATE/DELETE après insertion.

GRANT SELECT, INSERT ON TABLE fiscal_liquidations_is TO hisabpro;

COMMIT;
