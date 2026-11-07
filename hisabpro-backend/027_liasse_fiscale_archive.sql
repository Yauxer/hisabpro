-- Patch 09.3 - Archive immuable de la liasse fiscale finalisee
-- A executer apres 026_etic_exercice.sql.
BEGIN;

CREATE TABLE IF NOT EXISTS liasses_fiscales_archives (
    id                SERIAL PRIMARY KEY,
    societe_id        INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice          INTEGER NOT NULL,
    version           INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    contenu_json      TEXT NOT NULL,
    empreinte_sha256  VARCHAR(64) NOT NULL,
    date_finalisation TIMESTAMP NOT NULL DEFAULT NOW(),
    finalisee_par     INTEGER NULL REFERENCES utilisateurs(id) ON DELETE SET NULL,
    CONSTRAINT uq_liasse_archive_societe_exercice_version UNIQUE (societe_id, exercice, version),
    CONSTRAINT ck_liasse_archive_sha256 CHECK (empreinte_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE INDEX IF NOT EXISTS ix_liasse_archive_societe_exercice
    ON liasses_fiscales_archives (societe_id, exercice, version DESC);

-- Une archive finalisee ne se reecrit pas : une correction future devra creer
-- une nouvelle version, sous controle administratif/audit (Patch 10).
CREATE OR REPLACE FUNCTION hisabpro_liasse_archive_immutable()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Une liasse fiscale finalisee est immuable. Creez une nouvelle version via la procedure administrative.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_hisabpro_liasse_archive_immutable ON liasses_fiscales_archives;
CREATE TRIGGER trg_hisabpro_liasse_archive_immutable
BEFORE UPDATE OR DELETE ON liasses_fiscales_archives
FOR EACH ROW EXECUTE FUNCTION hisabpro_liasse_archive_immutable();

-- Permissions du role applicatif, si ce role existe dans l'installation.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT ON TABLE liasses_fiscales_archives TO hisabpro;
        GRANT USAGE, SELECT ON SEQUENCE liasses_fiscales_archives_id_seq TO hisabpro;
    END IF;
END $$;

COMMIT;
