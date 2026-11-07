-- HisabPro — FACT.11
-- Durcissement production : RBAC, piste d'audit applicative append-only,
-- contraintes de rôle et permissions du journal.

BEGIN;

CREATE TABLE IF NOT EXISTS audit_actions (
    id          BIGSERIAL PRIMARY KEY,
    societe_id  INTEGER,
    acteur_id   INTEGER,
    acteur_nom  VARCHAR(200),
    acteur_email VARCHAR(200),
    acteur_role VARCHAR(40),
    methode     VARCHAR(10) NOT NULL,
    chemin      VARCHAR(300) NOT NULL,
    statut_http INTEGER NOT NULL,
    succes      BOOLEAN NOT NULL DEFAULT TRUE,
    ip          VARCHAR(80),
    request_id  VARCHAR(64),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

ALTER TABLE audit_actions ADD COLUMN IF NOT EXISTS acteur_nom VARCHAR(200);
ALTER TABLE audit_actions ADD COLUMN IF NOT EXISTS acteur_email VARCHAR(200);

CREATE INDEX IF NOT EXISTS ix_audit_actions_societe_date
    ON audit_actions (societe_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_actions_acteur_date
    ON audit_actions (acteur_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_actions_request_id
    ON audit_actions (request_id);

-- Le journal ne peut jamais être réécrit ou supprimé.
CREATE OR REPLACE FUNCTION hisabpro_audit_actions_append_only()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'audit_actions est append-only : UPDATE/DELETE interdit';
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_audit_actions_append_only ON audit_actions;
CREATE TRIGGER trg_hisabpro_audit_actions_append_only
BEFORE UPDATE OR DELETE ON audit_actions
FOR EACH ROW EXECUTE FUNCTION hisabpro_audit_actions_append_only();

-- Point d'entrée unique utilisé par l'API. La fonction SECURITY DEFINER permet
-- de ne pas donner INSERT direct au rôle applicatif sur le journal d'audit.
CREATE OR REPLACE FUNCTION hisabpro_journaliser_action(
    p_societe_id INTEGER,
    p_acteur_id INTEGER,
    p_acteur_role TEXT,
    p_methode TEXT,
    p_chemin TEXT,
    p_statut_http INTEGER,
    p_succes BOOLEAN,
    p_ip TEXT,
    p_request_id TEXT
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_nom TEXT;
    v_email TEXT;
BEGIN
    IF p_acteur_id IS NOT NULL THEN
        SELECT u.nom, u.email INTO v_nom, v_email FROM utilisateurs u WHERE u.id=p_acteur_id;
    END IF;
    INSERT INTO audit_actions (
        societe_id, acteur_id, acteur_nom, acteur_email, acteur_role, methode, chemin,
        statut_http, succes, ip, request_id
    ) VALUES (
        p_societe_id, p_acteur_id, v_nom, v_email, NULLIF(BTRIM(p_acteur_role), ''),
        UPPER(BTRIM(p_methode)), LEFT(p_chemin, 300), p_statut_http,
        COALESCE(p_succes, FALSE), LEFT(p_ip, 80), LEFT(p_request_id, 64)
    );
END;
$$;

-- Les rôles applicatifs autorisés sont désormais aussi contrôlés au niveau DB.
UPDATE utilisateurs
   SET role = 'lecture'
 WHERE role IS NULL OR role NOT IN ('admin','comptable','lecture');
UPDATE utilisateurs_societes
   SET role = 'lecture'
 WHERE role IS NULL OR role NOT IN ('admin','comptable','lecture');

ALTER TABLE utilisateurs DROP CONSTRAINT IF EXISTS ck_utilisateurs_role_hisabpro;
ALTER TABLE utilisateurs ADD CONSTRAINT ck_utilisateurs_role_hisabpro
    CHECK (role IN ('admin','comptable','lecture'));
ALTER TABLE utilisateurs_societes DROP CONSTRAINT IF EXISTS ck_utilisateurs_societes_role_hisabpro;
ALTER TABLE utilisateurs_societes ADD CONSTRAINT ck_utilisateurs_societes_role_hisabpro
    CHECK (role IN ('admin','comptable','lecture'));

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON audit_actions FROM hisabpro;
        GRANT SELECT ON audit_actions TO hisabpro;
        GRANT EXECUTE ON FUNCTION hisabpro_journaliser_action(
            INTEGER, INTEGER, TEXT, TEXT, TEXT, INTEGER, BOOLEAN, TEXT, TEXT
        ) TO hisabpro;
        GRANT USAGE, SELECT ON SEQUENCE audit_actions_id_seq TO hisabpro;
    END IF;
END $$;

COMMIT;
