-- HisabPro — Patch 07A
-- Piste d'audit append-only des écritures comptables et de leurs lignes.
--
-- Cette migration ne modifie aucune écriture existante. Elle commence à tracer
-- les mutations réalisées après son installation. Les écritures déjà validées
-- restent protégées par les garde-fous applicatifs existants.

BEGIN;

CREATE TABLE IF NOT EXISTS audit_ecritures (
    id              BIGSERIAL PRIMARY KEY,
    societe_id      INTEGER NOT NULL,
    ecriture_id     INTEGER,
    table_cible     VARCHAR(40) NOT NULL,
    ligne_id        INTEGER,
    action          VARCHAR(60) NOT NULL,
    acteur_id       INTEGER,
    acteur_nom      VARCHAR(200),
    acteur_email    VARCHAR(200),
    acteur_role     VARCHAR(40),
    motif           TEXT,
    ancien          JSONB,
    nouveau         JSONB,
    transaction_id  BIGINT NOT NULL DEFAULT txid_current(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS ix_audit_ecritures_societe_date
    ON audit_ecritures (societe_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_ecritures_ecriture
    ON audit_ecritures (societe_id, ecriture_id, id);
CREATE INDEX IF NOT EXISTS ix_audit_ecritures_action
    ON audit_ecritures (societe_id, action);

-- Point de départ explicite pour les données déjà présentes au moment du
-- déploiement. Il ne prétend pas reconstruire leur historique antérieur : il
-- fige seulement leur état connu à l'installation de 07A.
INSERT INTO audit_ecritures (
    societe_id, ecriture_id, table_cible, ligne_id, action,
    acteur_id, acteur_nom, acteur_email, acteur_role, motif,
    ancien, nouveau, transaction_id, created_at
)
SELECT e.societe_id, e.id, 'ecritures', NULL, 'baseline_initiale',
       NULL, NULL, NULL, NULL,
       'État initial constaté lors de l’installation du Patch 07A',
       NULL, to_jsonb(e), txid_current(), clock_timestamp()
  FROM ecritures e
 WHERE NOT EXISTS (
       SELECT 1 FROM audit_ecritures a
        WHERE a.societe_id = e.societe_id
          AND a.ecriture_id = e.id
          AND a.table_cible = 'ecritures'
 );

INSERT INTO audit_ecritures (
    societe_id, ecriture_id, table_cible, ligne_id, action,
    acteur_id, acteur_nom, acteur_email, acteur_role, motif,
    ancien, nouveau, transaction_id, created_at
)
SELECT e.societe_id, l.ecriture_id, 'lignes_ecriture', l.id, 'baseline_ligne',
       NULL, NULL, NULL, NULL,
       'État initial constaté lors de l’installation du Patch 07A',
       NULL, to_jsonb(l), txid_current(), clock_timestamp()
  FROM lignes_ecriture l
  JOIN ecritures e ON e.id = l.ecriture_id
 WHERE NOT EXISTS (
       SELECT 1 FROM audit_ecritures a
        WHERE a.societe_id = e.societe_id
          AND a.ecriture_id = l.ecriture_id
          AND a.table_cible = 'lignes_ecriture'
          AND a.ligne_id = l.id
 );

-- La fonction s'exécute avec les droits du propriétaire de la migration. Ainsi,
-- le rôle applicatif peut rester en lecture seule sur audit_ecritures tout en
-- laissant les triggers écrire dans le journal.
CREATE OR REPLACE FUNCTION hisabpro_tracer_ecriture()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_ecriture_id INTEGER;
    v_societe_id  INTEGER;
    v_ligne_id    INTEGER;
    v_action      TEXT;
    v_acteur_txt  TEXT;
    v_acteur_id   INTEGER;
    v_acteur_nom  TEXT;
    v_acteur_mail TEXT;
    v_acteur_role TEXT;
    v_motif       TEXT;
    v_ancien      JSONB;
    v_nouveau     JSONB;
BEGIN
    v_acteur_txt := NULLIF(current_setting('hisabpro.audit_actor_id', true), '');
    IF v_acteur_txt ~ '^[0-9]+$' THEN
        v_acteur_id := v_acteur_txt::INTEGER;
    END IF;
    v_acteur_role := NULLIF(current_setting('hisabpro.audit_actor_role', true), '');
    v_motif       := NULLIF(current_setting('hisabpro.audit_motif', true), '');
    v_action      := NULLIF(current_setting('hisabpro.audit_action', true), '');

    IF v_acteur_id IS NOT NULL THEN
        SELECT u.nom, u.email
          INTO v_acteur_nom, v_acteur_mail
          FROM utilisateurs u
         WHERE u.id = v_acteur_id;
    END IF;

    IF TG_OP = 'INSERT' THEN
        v_nouveau := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        v_ancien  := to_jsonb(OLD);
        v_nouveau := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        v_ancien := to_jsonb(OLD);
    END IF;

    IF TG_TABLE_NAME = 'ecritures' THEN
        IF TG_OP = 'DELETE' THEN
            v_ecriture_id := OLD.id;
            v_societe_id  := OLD.societe_id;
        ELSE
            v_ecriture_id := NEW.id;
            v_societe_id  := NEW.societe_id;
        END IF;
        v_ligne_id := NULL;

        IF v_action IS NULL THEN
            IF TG_OP = 'INSERT' THEN
                v_action := 'creation_systeme';
            ELSIF TG_OP = 'DELETE' THEN
                v_action := 'suppression';
            ELSIF OLD.est_validee IS DISTINCT FROM NEW.est_validee THEN
                IF NEW.est_validee THEN
                    v_action := 'validation';
                    IF v_acteur_id IS NULL AND NEW.validee_par IS NOT NULL THEN
                        v_acteur_id := NEW.validee_par;
                        SELECT u.nom, u.email, u.role
                          INTO v_acteur_nom, v_acteur_mail, v_acteur_role
                          FROM utilisateurs u WHERE u.id = v_acteur_id;
                    END IF;
                ELSE
                    v_action := 'devalidation';
                END IF;
            ELSE
                v_action := 'modification_systeme';
            END IF;
        END IF;

    ELSIF TG_TABLE_NAME = 'lignes_ecriture' THEN
        IF TG_OP = 'DELETE' THEN
            v_ecriture_id := OLD.ecriture_id;
            v_ligne_id    := OLD.id;
        ELSE
            v_ecriture_id := NEW.ecriture_id;
            v_ligne_id    := NEW.id;
        END IF;

        SELECT e.societe_id INTO v_societe_id
          FROM ecritures e
         WHERE e.id = v_ecriture_id;

        -- En cas de cascade exceptionnelle où le parent ne serait déjà plus
        -- visible, on reprend le tenant posé par l'application.
        IF v_societe_id IS NULL THEN
            v_acteur_txt := NULLIF(current_setting('hisabpro.audit_societe_id', true), '');
            IF v_acteur_txt ~ '^[0-9]+$' THEN
                v_societe_id := v_acteur_txt::INTEGER;
            END IF;
        END IF;

        -- Pour les lignes on conserve la nature technique du changement ;
        -- l'identité et le motif viennent toujours du contexte métier courant.
        v_action := CASE TG_OP
            WHEN 'INSERT' THEN 'ligne_ajoutee'
            WHEN 'UPDATE' THEN 'ligne_modifiee'
            WHEN 'DELETE' THEN 'ligne_supprimee'
            ELSE lower(TG_OP)
        END;
    END IF;

    -- Ne jamais casser une opération métier parce que le contexte utilisateur
    -- manque : un événement système reste préférable à une absence de trace.
    IF v_societe_id IS NOT NULL THEN
        INSERT INTO audit_ecritures (
            societe_id, ecriture_id, table_cible, ligne_id, action,
            acteur_id, acteur_nom, acteur_email, acteur_role, motif,
            ancien, nouveau, transaction_id, created_at
        ) VALUES (
            v_societe_id, v_ecriture_id, TG_TABLE_NAME, v_ligne_id, v_action,
            v_acteur_id, v_acteur_nom, v_acteur_mail, v_acteur_role, v_motif,
            v_ancien, v_nouveau, txid_current(), clock_timestamp()
        );
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_audit_ecritures ON ecritures;
CREATE TRIGGER trg_hisabpro_audit_ecritures
BEFORE INSERT OR UPDATE OR DELETE ON ecritures
FOR EACH ROW EXECUTE FUNCTION hisabpro_tracer_ecriture();

DROP TRIGGER IF EXISTS trg_hisabpro_audit_lignes_ecriture ON lignes_ecriture;
CREATE TRIGGER trg_hisabpro_audit_lignes_ecriture
BEFORE INSERT OR UPDATE OR DELETE ON lignes_ecriture
FOR EACH ROW EXECUTE FUNCTION hisabpro_tracer_ecriture();

-- Le journal lui-même est append-only. Même une suppression accidentelle par
-- le rôle applicatif est bloquée au niveau PostgreSQL.
CREATE OR REPLACE FUNCTION hisabpro_audit_append_only()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'audit_ecritures est append-only : UPDATE/DELETE interdit';
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_audit_append_only ON audit_ecritures;
CREATE TRIGGER trg_hisabpro_audit_append_only
BEFORE UPDATE OR DELETE ON audit_ecritures
FOR EACH ROW EXECUTE FUNCTION hisabpro_audit_append_only();

-- Le compte applicatif n'a besoin que de consulter la piste d'audit. Les INSERT
-- sont effectués par la fonction SECURITY DEFINER ci-dessus.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON audit_ecritures FROM hisabpro;
        GRANT SELECT ON audit_ecritures TO hisabpro;
    END IF;
END $$;

COMMIT;
