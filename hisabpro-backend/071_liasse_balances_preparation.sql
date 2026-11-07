-- Préparations externes versionnées, sans écritures ni archive fiscale.
-- Additif/idempotent : aucune réparation ou modification des sources comptables.
BEGIN;
CREATE TABLE IF NOT EXISTS liasse_balances_preparation (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    exercice INTEGER NOT NULL,
    exercice_id INTEGER NOT NULL REFERENCES exercices_comptables(id),
    version INTEGER NOT NULL CHECK (version > 0),
    contenu JSONB NOT NULL,
    empreinte_sha256 VARCHAR(64) NOT NULL,
    created_by INTEGER REFERENCES utilisateurs(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_liasse_balance_version UNIQUE(societe_id, exercice, version)
);
CREATE INDEX IF NOT EXISTS ix_liasse_balances_preparation_societe_id ON liasse_balances_preparation(societe_id);
CREATE INDEX IF NOT EXISTS ix_liasse_balances_preparation_exercice ON liasse_balances_preparation(exercice);
CREATE OR REPLACE FUNCTION hisabpro_balance_preparation_immuable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Preparation de balance immuable : creer une nouvelle version';
END;
$$;
DROP TRIGGER IF EXISTS trg_balance_preparation_immuable ON liasse_balances_preparation;
CREATE TRIGGER trg_balance_preparation_immuable BEFORE UPDATE OR DELETE
ON liasse_balances_preparation FOR EACH ROW EXECUTE FUNCTION hisabpro_balance_preparation_immuable();
DO $$ BEGIN
    IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        GRANT SELECT, INSERT ON liasse_balances_preparation TO hisabpro;
        GRANT USAGE, SELECT ON SEQUENCE liasse_balances_preparation_id_seq TO hisabpro;
        REVOKE UPDATE, DELETE, TRUNCATE ON liasse_balances_preparation FROM hisabpro;
    END IF;
END $$;
COMMIT;
