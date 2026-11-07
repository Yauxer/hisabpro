BEGIN;

-- Patch 05B — versionnement des archives du Livre d'inventaire.
-- Les archives v1 restent conservées. Une archive v2 peut être créée après
-- les nouveaux contrôles de non-compensation et de rapprochement des immobilisations.

ALTER TABLE livres_inventaire_archives
    DROP CONSTRAINT IF EXISTS uq_livre_inventaire_societe_exercice;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_livre_inventaire_societe_exercice_version'
          AND conrelid = 'livres_inventaire_archives'::regclass
    ) THEN
        ALTER TABLE livres_inventaire_archives
            ADD CONSTRAINT uq_livre_inventaire_societe_exercice_version
            UNIQUE (societe_id, exercice, version);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_livres_inventaire_archives_societe_exercice_version
    ON livres_inventaire_archives (societe_id, exercice, version DESC);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT ON TABLE livres_inventaire_archives TO hisabpro;
        GRANT USAGE, SELECT ON SEQUENCE livres_inventaire_archives_id_seq TO hisabpro;
    END IF;
END $$;

COMMIT;
