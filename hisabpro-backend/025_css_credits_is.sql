-- Patch 08.6 — Contribution sociale de solidarité + retenues/crédits IS
-- A exécuter après 024_acomptes_liquidation_is.sql.
BEGIN;

ALTER TABLE fiscal_parametres_exercice
    ADD COLUMN IF NOT EXISTS css_benefice_reference_forcee NUMERIC(18,2),
    ADD COLUMN IF NOT EXISTS css_justification_reference_forcee TEXT,
    ADD COLUMN IF NOT EXISTS css_exoneration_permanente BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS css_justification_exoneration TEXT;

DO $$ BEGIN
    ALTER TABLE fiscal_parametres_exercice
        ADD CONSTRAINT ck_fiscal_css_reference_non_negative
        CHECK (css_benefice_reference_forcee IS NULL OR css_benefice_reference_forcee >= 0);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE fiscal_parametres_exercice
        ADD CONSTRAINT ck_fiscal_css_reference_justifiee
        CHECK (
            css_benefice_reference_forcee IS NULL
            OR NULLIF(TRIM(css_justification_reference_forcee), '') IS NOT NULL
        );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE fiscal_parametres_exercice
        ADD CONSTRAINT ck_fiscal_css_exoneration_justifiee
        CHECK (
            css_exoneration_permanente = FALSE
            OR NULLIF(TRIM(css_justification_exoneration), '') IS NOT NULL
        );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS fiscal_credits_is (
    id BIGSERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice INTEGER NOT NULL,
    type VARCHAR(30) NOT NULL CHECK (type IN ('pprf','retenue_tiers','autre')),
    montant NUMERIC(18,2) NOT NULL CHECK (montant > 0),
    montant_deja_impute_acomptes NUMERIC(18,2) NOT NULL DEFAULT 0,
    date_retenue DATE,
    reference VARCHAR(160) NOT NULL,
    commentaire TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT ck_fiscal_credit_is_imputation_acomptes CHECK (
        montant_deja_impute_acomptes >= 0 AND montant_deja_impute_acomptes <= montant
    ),
    CONSTRAINT ck_fiscal_credit_is_reference CHECK (NULLIF(TRIM(reference), '') IS NOT NULL),
    CONSTRAINT ck_fiscal_credit_is_autre_justifie CHECK (
        type <> 'autre' OR NULLIF(TRIM(commentaire), '') IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS ix_fiscal_credits_is_societe_exercice
    ON fiscal_credits_is (societe_id, exercice, type);

DO $$ BEGIN
    ALTER TABLE fiscal_credits_is
        ADD CONSTRAINT ck_fiscal_credit_is_autre_justifie
        CHECK (type <> 'autre' OR NULLIF(TRIM(commentaire), '') IS NOT NULL);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS fiscal_css_paiements (
    id BIGSERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    annee INTEGER NOT NULL,
    montant_verse NUMERIC(18,2) NOT NULL CHECK (montant_verse > 0),
    date_versement DATE NOT NULL,
    reference_paiement VARCHAR(160) NOT NULL,
    commentaire TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_fiscal_css_paiement_societe_annee UNIQUE (societe_id, annee),
    CONSTRAINT ck_fiscal_css_paiement_reference CHECK (NULLIF(TRIM(reference_paiement), '') IS NOT NULL)
);

ALTER TABLE fiscal_liquidations_is
    ADD COLUMN IF NOT EXISTS credits_is_imputables NUMERIC(18,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS excedent_credits_is NUMERIC(18,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS excedent_total NUMERIC(18,2) NOT NULL DEFAULT 0;

DO $$ BEGIN
    ALTER TABLE fiscal_liquidations_is
        ADD CONSTRAINT ck_fiscal_liq_credits_non_negatifs
        CHECK (credits_is_imputables >= 0 AND excedent_credits_is >= 0 AND excedent_total >= 0);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Les liquidations existantes restent inchangées et immuables ; les nouvelles
-- colonnes sont initialisées à zéro sur l'historique.

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_parametres_exercice TO hisabpro;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_credits_is TO hisabpro;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_css_paiements TO hisabpro;
GRANT SELECT ON TABLE fiscal_liquidations_is TO hisabpro;
GRANT USAGE, SELECT ON SEQUENCE fiscal_credits_is_id_seq TO hisabpro;
GRANT USAGE, SELECT ON SEQUENCE fiscal_css_paiements_id_seq TO hisabpro;

COMMIT;
