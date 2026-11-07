-- FACT.7 hotfix — droits du rôle applicatif sur le module de recouvrement
-- À exécuter si 034_recouvrement.sql a déjà été appliqué sans les GRANT.
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        RAISE EXCEPTION 'Le rôle PostgreSQL "hisabpro" est introuvable. Vérifiez DATABASE_URL.';
    END IF;

    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE relances_recouvrement TO hisabpro;
    GRANT USAGE, SELECT, UPDATE ON SEQUENCE relances_recouvrement_id_seq TO hisabpro;
END $$;

COMMIT;
