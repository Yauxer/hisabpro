-- HisabPro Patch 02B — TVA : avoirs, acomptes, crédit reportable, prorata
-- PostgreSQL — exécuter UNE FOIS après sauvegarde de la base.

BEGIN;

-- Qualification fiscale des achats.
ALTER TABLE factures
    ADD COLUMN IF NOT EXISTS nature_tva_achat VARCHAR(30) NOT NULL DEFAULT 'charge';
ALTER TABLE factures
    ADD COLUMN IF NOT EXISTS tva_deductible_pct NUMERIC(5,2) NOT NULL DEFAULT 100;

ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_facture_tva_deductible_pct;
ALTER TABLE factures ADD CONSTRAINT ck_facture_tva_deductible_pct
    CHECK (tva_deductible_pct >= 0 AND tva_deductible_pct <= 100);

-- Acomptes : montant TTC + taux TVA figé + date d'imputation.
ALTER TABLE acomptes
    ADD COLUMN IF NOT EXISTS tva_applicable BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE acomptes
    ADD COLUMN IF NOT EXISTS taux_tva NUMERIC(5,2) NOT NULL DEFAULT 20;
ALTER TABLE acomptes
    ADD COLUMN IF NOT EXISTS date_imputation DATE NULL;

ALTER TABLE acomptes DROP CONSTRAINT IF EXISTS ck_acompte_taux_tva;
ALTER TABLE acomptes ADD CONSTRAINT ck_acompte_taux_tva
    CHECK (taux_tva >= 0 AND taux_tva <= 100);

-- Paramètres TVA propres à une société et à un exercice.
CREATE TABLE IF NOT EXISTS tva_parametres_exercice (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    exercice INTEGER NOT NULL,
    credit_ouverture NUMERIC(18,2) NOT NULL DEFAULT 0,
    prorata_deduction_pct NUMERIC(5,2) NOT NULL DEFAULT 100,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_tva_param_societe_exercice UNIQUE (societe_id, exercice),
    CONSTRAINT ck_tva_credit_ouverture_non_negatif CHECK (credit_ouverture >= 0),
    CONSTRAINT ck_tva_prorata_pct CHECK (prorata_deduction_pct >= 0 AND prorata_deduction_pct <= 100)
);

CREATE INDEX IF NOT EXISTS ix_tva_param_societe_exercice
    ON tva_parametres_exercice(societe_id, exercice);

COMMIT;
