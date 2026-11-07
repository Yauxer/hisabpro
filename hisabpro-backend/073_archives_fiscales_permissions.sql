-- Protection additive des archives fiscales, y compris les ACL historiques.
-- À appliquer après 027_liasse_fiscale_archive.sql par le rôle de migration.
-- Aucun contenu archivé n'est modifié ; script idempotent.
BEGIN;

-- Un trigger par ligne UPDATE/DELETE ne protège pas contre TRUNCATE.
-- Réutiliser la fonction existante garantit le même refus métier.
DROP TRIGGER IF EXISTS trg_hisabpro_liasse_archive_truncate ON liasses_fiscales_archives;
CREATE TRIGGER trg_hisabpro_liasse_archive_truncate
BEFORE TRUNCATE ON liasses_fiscales_archives
FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_liasse_archive_immutable();

REVOKE UPDATE, DELETE, TRUNCATE ON TABLE liasses_fiscales_archives FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        REVOKE UPDATE, DELETE, TRUNCATE ON TABLE liasses_fiscales_archives FROM hisabpro;
    END IF;
END $$;

COMMIT;
