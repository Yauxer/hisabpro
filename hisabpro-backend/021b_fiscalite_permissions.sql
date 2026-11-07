-- ==========================================================================
-- HisabPro — Patch 08.1 hotfix permissions
-- Corrige les droits PostgreSQL des objets fiscaux créés par 021_fiscalite_is.sql
-- À exécuter avec le même compte administrateur que les migrations SQL.
-- ===========================================================================
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        RAISE EXCEPTION 'Le rôle PostgreSQL "hisabpro" est introuvable. Vérifiez le rôle utilisé dans DATABASE_URL.';
    END IF;
END
$$;

GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE fiscal_parametres_exercice
    TO hisabpro;

GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE fiscal_retraitements
    TO hisabpro;

GRANT USAGE, SELECT, UPDATE
    ON SEQUENCE fiscal_parametres_exercice_id_seq
    TO hisabpro;

GRANT USAGE, SELECT, UPDATE
    ON SEQUENCE fiscal_retraitements_id_seq
    TO hisabpro;

COMMIT;
