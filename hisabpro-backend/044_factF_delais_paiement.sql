BEGIN;

-- FACT-F — données complémentaires strictement déclaratives.
-- Elles ne modifient ni le montant, ni la date, ni les comptes d'une facture
-- validée et peuvent donc être complétées après émission.
ALTER TABLE factures ADD COLUMN IF NOT EXISTS date_livraison_service DATE;
ALTER TABLE factures ADD COLUMN IF NOT EXISTS litige_judiciaire BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE factures ADD COLUMN IF NOT EXISTS reference_litige VARCHAR(200);
ALTER TABLE factures ADD COLUMN IF NOT EXISTS delais_paiement_hors_champ BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE factures ADD COLUMN IF NOT EXISTS delais_paiement_motif_hors_champ VARCHAR(300);

-- Cohérence minimale sans rendre les données legacy bloquantes.
ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_factures_factf_litige_reference;
ALTER TABLE factures ADD CONSTRAINT ck_factures_factf_litige_reference
CHECK (NOT litige_judiciaire OR NULLIF(BTRIM(reference_litige), '') IS NOT NULL) NOT VALID;

ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_factures_factf_hors_champ_motif;
ALTER TABLE factures ADD CONSTRAINT ck_factures_factf_hors_champ_motif
CHECK (NOT delais_paiement_hors_champ OR NULLIF(BTRIM(delais_paiement_motif_hors_champ), '') IS NOT NULL) NOT VALID;

CREATE INDEX IF NOT EXISTS idx_factures_factf_achats_echeance
ON factures(societe_id, type, est_validee, date_echeance)
WHERE est_proforma = FALSE;

COMMIT;
