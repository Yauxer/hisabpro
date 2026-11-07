-- ============================================================================
-- HisabPro — Patch 08.3
-- Déficits fiscaux reportables par millésime + imputations historisées
-- Référentiel : CGI 2026, article 12
-- À exécuter après 021/021b. Le patch 020 reste volontairement reporté.
-- PostgreSQL
-- ============================================================================
BEGIN;

CREATE TABLE IF NOT EXISTS fiscal_deficits (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice_origine INTEGER NOT NULL,
    montant_ordinaire NUMERIC(18,2) NOT NULL DEFAULT 0,
    montant_amortissements NUMERIC(18,2) NOT NULL DEFAULT 0,
    source VARCHAR(30) NOT NULL DEFAULT 'manuel',
    commentaire TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_fiscal_deficit_societe_origine UNIQUE (societe_id, exercice_origine),
    CONSTRAINT ck_fiscal_deficit_ordinaire_non_negatif CHECK (montant_ordinaire >= 0),
    CONSTRAINT ck_fiscal_deficit_amort_non_negatif CHECK (montant_amortissements >= 0),
    CONSTRAINT ck_fiscal_deficit_total_positif CHECK (montant_ordinaire + montant_amortissements > 0),
    CONSTRAINT ck_fiscal_deficit_source CHECK (source IN ('manuel','calcul'))
);

CREATE TABLE IF NOT EXISTS fiscal_deficit_imputations (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    deficit_id INTEGER NOT NULL REFERENCES fiscal_deficits(id) ON DELETE RESTRICT,
    exercice_cible INTEGER NOT NULL,
    montant_ordinaire NUMERIC(18,2) NOT NULL DEFAULT 0,
    montant_amortissements NUMERIC(18,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_fiscal_deficit_imputation_cible UNIQUE (deficit_id, exercice_cible),
    CONSTRAINT ck_fiscal_imputation_ordinaire_non_negatif CHECK (montant_ordinaire >= 0),
    CONSTRAINT ck_fiscal_imputation_amort_non_negatif CHECK (montant_amortissements >= 0),
    CONSTRAINT ck_fiscal_imputation_total_positif CHECK (montant_ordinaire + montant_amortissements > 0)
);

CREATE INDEX IF NOT EXISTS ix_fiscal_deficits_societe_origine
    ON fiscal_deficits(societe_id, exercice_origine);
CREATE INDEX IF NOT EXISTS ix_fiscal_deficit_imputations_societe_cible
    ON fiscal_deficit_imputations(societe_id, exercice_cible);
CREATE INDEX IF NOT EXISTS ix_fiscal_deficit_imputations_deficit
    ON fiscal_deficit_imputations(deficit_id);

-- Cohérence inter-tables : une imputation ne peut pas viser le même exercice
-- ou un exercice antérieur à l'exercice déficitaire, ni appartenir à une autre société.
CREATE OR REPLACE FUNCTION hisabpro_check_fiscal_deficit_imputation()
RETURNS TRIGGER AS $$
DECLARE
    v_societe INTEGER;
    v_origine INTEGER;
    v_ordinaire_initial NUMERIC(18,2);
    v_amort_initial NUMERIC(18,2);
    v_ordinaire_deja NUMERIC(18,2);
    v_amort_deja NUMERIC(18,2);
BEGIN
    SELECT societe_id, exercice_origine, montant_ordinaire, montant_amortissements
      INTO v_societe, v_origine, v_ordinaire_initial, v_amort_initial
      FROM fiscal_deficits
     WHERE id = NEW.deficit_id
     FOR UPDATE;

    IF v_societe IS NULL THEN
        RAISE EXCEPTION 'Déficit fiscal % introuvable.', NEW.deficit_id;
    END IF;
    IF NEW.societe_id <> v_societe THEN
        RAISE EXCEPTION 'Société incohérente pour l''imputation du déficit fiscal %.', NEW.deficit_id;
    END IF;
    IF NEW.exercice_cible <= v_origine THEN
        RAISE EXCEPTION 'Un déficit de % ne peut être imputé qu''à partir de l''exercice %.', v_origine, v_origine + 1;
    END IF;
    IF NEW.montant_ordinaire > 0 AND NEW.exercice_cible > v_origine + 4 THEN
        RAISE EXCEPTION 'La fraction ordinaire du déficit % est expirée après l''exercice %.', v_origine, v_origine + 4;
    END IF;

    SELECT COALESCE(SUM(montant_ordinaire), 0), COALESCE(SUM(montant_amortissements), 0)
      INTO v_ordinaire_deja, v_amort_deja
      FROM fiscal_deficit_imputations
     WHERE deficit_id = NEW.deficit_id
       AND id IS DISTINCT FROM NEW.id;

    IF v_ordinaire_deja + NEW.montant_ordinaire > v_ordinaire_initial THEN
        RAISE EXCEPTION 'Imputation ordinaire supérieure au solde du déficit fiscal %.', NEW.deficit_id;
    END IF;
    IF v_amort_deja + NEW.montant_amortissements > v_amort_initial THEN
        RAISE EXCEPTION 'Imputation de la fraction amortissements supérieure au solde du déficit fiscal %.', NEW.deficit_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_hisabpro_check_fiscal_deficit_imputation ON fiscal_deficit_imputations;
CREATE TRIGGER trg_hisabpro_check_fiscal_deficit_imputation
BEFORE INSERT OR UPDATE ON fiscal_deficit_imputations
FOR EACH ROW EXECUTE FUNCTION hisabpro_check_fiscal_deficit_imputation();

-- Droits du rôle applicatif.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_deficits TO hisabpro;
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_deficit_imputations TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE fiscal_deficits_id_seq TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE fiscal_deficit_imputations_id_seq TO hisabpro;
        GRANT EXECUTE ON FUNCTION hisabpro_check_fiscal_deficit_imputation() TO hisabpro;
    END IF;
END
$$;

COMMIT;
