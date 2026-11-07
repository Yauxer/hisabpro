-- ==========================================================================
-- HisabPro — Patch 08.1
-- Résultat fiscal + moteur IS versionné par exercice
-- À exécuter après 019. Le patch 020 (périodes Avis 24) est volontairement
-- reporté et n'est PAS requis pour cette migration.
-- PostgreSQL
-- ==========================================================================
BEGIN;

CREATE TABLE IF NOT EXISTS fiscal_parametres_exercice (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice INTEGER NOT NULL,
    categorie_is VARCHAR(40) NOT NULL DEFAULT 'droit_commun',
    justification_regime TEXT,
    maintien_taux_35_transition BOOLEAN NOT NULL DEFAULT FALSE,
    deficit_reportable_disponible NUMERIC(18,2) NOT NULL DEFAULT 0,
    taux_is_force NUMERIC(6,3),
    justification_taux_force TEXT,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_fiscal_param_societe_exercice UNIQUE (societe_id, exercice),
    CONSTRAINT ck_fiscal_categorie_is CHECK (
        categorie_is IN ('droit_commun','industrielle','cfc_zai','convention_investissement','avantage_20_transition','financier_40','exonere')
    ),
    CONSTRAINT ck_fiscal_deficit_non_negatif CHECK (deficit_reportable_disponible >= 0),
    CONSTRAINT ck_fiscal_regime_special_justifie CHECK (
        categorie_is = 'droit_commun' OR NULLIF(TRIM(justification_regime), '') IS NOT NULL
    ),
    CONSTRAINT ck_fiscal_taux_force CHECK (taux_is_force IS NULL OR (taux_is_force >= 0 AND taux_is_force <= 100)),
    CONSTRAINT ck_fiscal_taux_force_justifie CHECK (
        taux_is_force IS NULL OR NULLIF(TRIM(justification_taux_force), '') IS NOT NULL
    )
);

CREATE TABLE IF NOT EXISTS fiscal_retraitements (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    categorie VARCHAR(50) NOT NULL DEFAULT 'autre',
    libelle VARCHAR(250) NOT NULL,
    montant NUMERIC(18,2) NOT NULL,
    compte_source VARCHAR(20),
    reference VARCHAR(120),
    commentaire TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_fiscal_retraitement_type CHECK (type IN ('reintegration','deduction')),
    CONSTRAINT ck_fiscal_retraitement_montant_positif CHECK (montant > 0)
);

CREATE INDEX IF NOT EXISTS ix_fiscal_param_exercice
    ON fiscal_parametres_exercice(societe_id, exercice);
CREATE INDEX IF NOT EXISTS ix_fiscal_retraitements_exercice
    ON fiscal_retraitements(societe_id, exercice);

-- Droits du rôle applicatif HisabPro.
-- Les migrations sont généralement exécutées avec un rôle administrateur,
-- tandis que FastAPI se connecte avec le rôle limité `hisabpro`.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_parametres_exercice TO hisabpro;
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_retraitements TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE fiscal_parametres_exercice_id_seq TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE fiscal_retraitements_id_seq TO hisabpro;
    END IF;
END
$$;

COMMIT;
