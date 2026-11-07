-- ============================================================================
-- HisabPro — Patch 08.4
-- Cotisation minimale (CM) — paramètres historisés par exercice
-- Référentiel : CGI 2026, article 144
-- À exécuter après 022. Le patch 020 reste volontairement reporté.
-- PostgreSQL
-- ============================================================================
BEGIN;

ALTER TABLE fiscal_parametres_exercice
    ADD COLUMN IF NOT EXISTS cm_base_exclue NUMERIC(18,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS cm_justification_base_exclue TEXT,
    ADD COLUMN IF NOT EXISTS cm_base_taux_reduit_015 NUMERIC(18,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS cm_justification_taux_reduit TEXT,
    ADD COLUMN IF NOT EXISTS cm_exoneration_totale BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS cm_justification_exoneration TEXT,
    ADD COLUMN IF NOT EXISTS cm_minimum_3000_exonere BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS cm_justification_minimum_exonere TEXT;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fiscal_cm_base_exclue_non_negative') THEN
        ALTER TABLE fiscal_parametres_exercice
            ADD CONSTRAINT ck_fiscal_cm_base_exclue_non_negative CHECK (cm_base_exclue >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fiscal_cm_base_reduite_non_negative') THEN
        ALTER TABLE fiscal_parametres_exercice
            ADD CONSTRAINT ck_fiscal_cm_base_reduite_non_negative CHECK (cm_base_taux_reduit_015 >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fiscal_cm_base_exclue_justifiee') THEN
        ALTER TABLE fiscal_parametres_exercice
            ADD CONSTRAINT ck_fiscal_cm_base_exclue_justifiee CHECK (
                cm_base_exclue = 0 OR NULLIF(TRIM(cm_justification_base_exclue), '') IS NOT NULL
            );
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fiscal_cm_taux_reduit_justifie') THEN
        ALTER TABLE fiscal_parametres_exercice
            ADD CONSTRAINT ck_fiscal_cm_taux_reduit_justifie CHECK (
                cm_base_taux_reduit_015 = 0 OR NULLIF(TRIM(cm_justification_taux_reduit), '') IS NOT NULL
            );
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fiscal_cm_exoneration_justifiee') THEN
        ALTER TABLE fiscal_parametres_exercice
            ADD CONSTRAINT ck_fiscal_cm_exoneration_justifiee CHECK (
                cm_exoneration_totale = FALSE OR NULLIF(TRIM(cm_justification_exoneration), '') IS NOT NULL
            );
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fiscal_cm_minimum_exonere_justifie') THEN
        ALTER TABLE fiscal_parametres_exercice
            ADD CONSTRAINT ck_fiscal_cm_minimum_exonere_justifie CHECK (
                cm_minimum_3000_exonere = FALSE OR NULLIF(TRIM(cm_justification_minimum_exonere), '') IS NOT NULL
            );
    END IF;
END
$$;

-- Le rôle applicatif possède déjà les droits sur la table depuis 021/021b ;
-- on les réaffirme pour les installations hétérogènes.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_parametres_exercice TO hisabpro;
    END IF;
END
$$;

COMMIT;
