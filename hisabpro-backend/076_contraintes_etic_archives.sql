-- Contraintes déjà prévues par 026/027, absentes après création du socle ORM.
-- Additif/idempotent : aucune réécriture de données ou d'archives.
-- NOT VALID protège les nouvelles lignes sans rejeter une migration sur
-- d'anciennes données incomplètes. Leur validation historique reste distincte.
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
        WHERE conname='ck_etic_section_code' AND conrelid='etic_sections_exercice'::regclass) THEN
        ALTER TABLE etic_sections_exercice ADD CONSTRAINT ck_etic_section_code CHECK (
            code IN ('A1','A2','A3','B1','B2','B2bis','B3','B4','B5','B6','B7','B8','B9',
                     'B10','B11','B12','B13','B14','C1','C2','C3','C4','C5')
        ) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
        WHERE conname='ck_liasse_archive_sha256' AND conrelid='liasses_fiscales_archives'::regclass) THEN
        ALTER TABLE liasses_fiscales_archives ADD CONSTRAINT ck_liasse_archive_sha256
            CHECK (empreinte_sha256 ~ '^[0-9a-f]{64}$') NOT VALID;
    END IF;
END $$;

COMMIT;
