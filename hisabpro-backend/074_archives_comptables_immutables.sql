-- Additif/idempotent, après 011 et 071. Aucun contenu existant n'est réécrit.
-- Un propriétaire/migrateur distinct du rôle applicatif reste nécessaire.
BEGIN;

CREATE OR REPLACE FUNCTION hisabpro_livre_inventaire_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Un livre d''inventaire archivé est immuable. Créez une nouvelle version par le flux contrôlé.';
END;
$$;

DROP TRIGGER IF EXISTS trg_livre_inventaire_immutable ON livres_inventaire_archives;
CREATE TRIGGER trg_livre_inventaire_immutable
BEFORE UPDATE OR DELETE ON livres_inventaire_archives
FOR EACH ROW EXECUTE FUNCTION hisabpro_livre_inventaire_immutable();
DROP TRIGGER IF EXISTS trg_livre_inventaire_truncate ON livres_inventaire_archives;
CREATE TRIGGER trg_livre_inventaire_truncate
BEFORE TRUNCATE ON livres_inventaire_archives
FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_livre_inventaire_immutable();

DROP TRIGGER IF EXISTS trg_balance_preparation_truncate ON liasse_balances_preparation;
CREATE TRIGGER trg_balance_preparation_truncate
BEFORE TRUNCATE ON liasse_balances_preparation
FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_balance_preparation_immuable();

REVOKE UPDATE, DELETE, TRUNCATE ON livres_inventaire_archives, liasse_balances_preparation FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        REVOKE UPDATE, DELETE, TRUNCATE ON livres_inventaire_archives, liasse_balances_preparation FROM hisabpro;
    END IF;
END $$;

COMMIT;
