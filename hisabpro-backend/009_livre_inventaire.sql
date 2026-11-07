BEGIN;

CREATE TABLE IF NOT EXISTS livres_inventaire_archives (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    exercice INTEGER NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    date_etablissement TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    contenu_json TEXT NOT NULL,
    empreinte_sha256 VARCHAR(64) NOT NULL,
    cree_par INTEGER NULL REFERENCES utilisateurs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_livre_inventaire_societe_exercice UNIQUE (societe_id, exercice),
    CONSTRAINT ck_livre_inventaire_version_positive CHECK (version > 0)
);

CREATE INDEX IF NOT EXISTS ix_livres_inventaire_archives_societe_id
    ON livres_inventaire_archives(societe_id);
CREATE INDEX IF NOT EXISTS ix_livres_inventaire_archives_exercice
    ON livres_inventaire_archives(exercice);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT ON TABLE livres_inventaire_archives TO hisabpro;
        GRANT USAGE, SELECT ON SEQUENCE livres_inventaire_archives_id_seq TO hisabpro;
    END IF;
END $$;

COMMIT;
