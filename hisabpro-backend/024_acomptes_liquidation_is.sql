-- Patch 08.5 — Acomptes provisionnels et liquidation IS
-- A exécuter après 023_cotisation_minimale.sql.
BEGIN;

ALTER TABLE fiscal_parametres_exercice
    ADD COLUMN IF NOT EXISTS acomptes_reference_forcee NUMERIC(18,2),
    ADD COLUMN IF NOT EXISTS acomptes_justification_reference_forcee TEXT;

DO $$ BEGIN
    ALTER TABLE fiscal_parametres_exercice
        ADD CONSTRAINT ck_fiscal_acomptes_reference_non_negative
        CHECK (acomptes_reference_forcee IS NULL OR acomptes_reference_forcee >= 0);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE fiscal_parametres_exercice
        ADD CONSTRAINT ck_fiscal_acomptes_reference_justifiee
        CHECK (
            acomptes_reference_forcee IS NULL
            OR NULLIF(TRIM(acomptes_justification_reference_forcee), '') IS NOT NULL
        );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS fiscal_liquidations_is (
    id BIGSERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice INTEGER NOT NULL,
    benefice_fiscal_imposable NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (benefice_fiscal_imposable >= 0),
    is_theorique NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (is_theorique >= 0),
    cm_exigible NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (cm_exigible >= 0),
    impot_du NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (impot_du >= 0),
    nature_impot VARCHAR(10) NOT NULL CHECK (nature_impot IN ('IS','CM')),
    acomptes_imputables NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (acomptes_imputables >= 0),
    solde_a_payer NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (solde_a_payer >= 0),
    excedent_acomptes NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (excedent_acomptes >= 0),
    confirmee_par INTEGER REFERENCES utilisateurs(id),
    date_confirmation TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_fiscal_liquidation_societe_exercice UNIQUE (societe_id, exercice)
);

CREATE TABLE IF NOT EXISTS fiscal_acomptes_is (
    id BIGSERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice INTEGER NOT NULL,
    numero INTEGER NOT NULL CHECK (numero BETWEEN 1 AND 4),
    montant_verse NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (montant_verse >= 0),
    date_versement DATE,
    reference_paiement VARCHAR(120),
    dispense BOOLEAN NOT NULL DEFAULT FALSE,
    reference_dispense VARCHAR(200),
    commentaire TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_fiscal_acompte_societe_exercice_numero UNIQUE (societe_id, exercice, numero),
    CONSTRAINT ck_fiscal_acompte_paiement_ou_dispense CHECK (
        (montant_verse > 0 AND date_versement IS NOT NULL) OR dispense = TRUE
    ),
    CONSTRAINT ck_fiscal_acompte_dispense_justifiee CHECK (
        dispense = FALSE OR NULLIF(TRIM(reference_dispense), '') IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS ix_fiscal_liquidations_societe_exercice
    ON fiscal_liquidations_is (societe_id, exercice);
CREATE INDEX IF NOT EXISTS ix_fiscal_acomptes_societe_exercice
    ON fiscal_acomptes_is (societe_id, exercice, numero);

-- Une liquidation confirmée devient une photographie immuable. Les corrections
-- devront passer par une procédure administrative auditée (Patch 10/RBAC).
CREATE OR REPLACE FUNCTION hisabpro_fiscal_liquidation_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'La liquidation fiscale confirmée est immuable. Une correction administrative auditée est requise.';
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_fiscal_liquidation_immutable ON fiscal_liquidations_is;
CREATE TRIGGER trg_hisabpro_fiscal_liquidation_immutable
BEFORE UPDATE OR DELETE ON fiscal_liquidations_is
FOR EACH ROW EXECUTE FUNCTION hisabpro_fiscal_liquidation_immutable();

-- Permissions du rôle applicatif (évite le problème rencontré sur 021).
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_parametres_exercice TO hisabpro;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_liquidations_is TO hisabpro;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_acomptes_is TO hisabpro;
GRANT USAGE, SELECT ON SEQUENCE fiscal_liquidations_is_id_seq TO hisabpro;
GRANT USAGE, SELECT ON SEQUENCE fiscal_acomptes_is_id_seq TO hisabpro;

COMMIT;
