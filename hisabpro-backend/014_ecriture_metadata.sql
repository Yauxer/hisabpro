-- Patch 07B — Numérotation interne & métadonnées de pièce
-- À exécuter avec un rôle propriétaire (ex. postgres).
-- Objectifs :
--   1) numéro interne séquentiel immuable par société/exercice/journal ;
--   2) séparation claire entre N° écriture et référence du justificatif ;
--   3) date de pièce distincte de la date de comptabilisation ;
--   4) attribution automatique à toute écriture, y compris celles générées
--      par les autres modules HisabPro.

BEGIN;

ALTER TABLE ecritures
    ADD COLUMN IF NOT EXISTS numero_ecriture VARCHAR(40),
    ADD COLUMN IF NOT EXISTS date_piece DATE;

-- Le backfill est une opération de structure : on évite de polluer la piste
-- d'audit 07A avec une "modification métier" artificielle de chaque écriture.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
          FROM pg_trigger
         WHERE tgname = 'trg_hisabpro_audit_ecritures'
           AND tgrelid = 'ecritures'::regclass
           AND NOT tgisinternal
    ) THEN
        EXECUTE 'ALTER TABLE ecritures DISABLE TRIGGER trg_hisabpro_audit_ecritures';
    END IF;
END $$;

UPDATE ecritures
   SET date_piece = date
 WHERE date_piece IS NULL;

WITH numerotees AS (
    SELECT id,
           journal::text AS journal_code,
           exercice,
           ROW_NUMBER() OVER (
               PARTITION BY societe_id, exercice, journal
               ORDER BY date, id
           ) AS rn
      FROM ecritures
)
UPDATE ecritures e
   SET numero_ecriture = n.journal_code || '-' || n.exercice || '-' || LPAD(n.rn::text, 4, '0')
  FROM numerotees n
 WHERE e.id = n.id
   AND (e.numero_ecriture IS NULL OR BTRIM(e.numero_ecriture) = '');

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
          FROM pg_trigger
         WHERE tgname = 'trg_hisabpro_audit_ecritures'
           AND tgrelid = 'ecritures'::regclass
           AND NOT tgisinternal
    ) THEN
        EXECUTE 'ALTER TABLE ecritures ENABLE TRIGGER trg_hisabpro_audit_ecritures';
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS ecriture_sequences (
    societe_id      INTEGER NOT NULL,
    exercice        INTEGER NOT NULL,
    journal         VARCHAR(10) NOT NULL,
    dernier_numero  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (societe_id, exercice, journal),
    CONSTRAINT ck_ecriture_sequences_numero CHECK (dernier_numero >= 0)
);

-- Aligne les compteurs sur les écritures existantes.
INSERT INTO ecriture_sequences (societe_id, exercice, journal, dernier_numero)
SELECT societe_id, exercice, journal::text, COUNT(*)::int
  FROM ecritures
 GROUP BY societe_id, exercice, journal
ON CONFLICT (societe_id, exercice, journal)
DO UPDATE SET dernier_numero = GREATEST(
    ecriture_sequences.dernier_numero,
    EXCLUDED.dernier_numero
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ecritures_numero_interne
    ON ecritures (societe_id, exercice, journal, numero_ecriture);

CREATE OR REPLACE FUNCTION hisabpro_attribuer_numero_ecriture()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_num INTEGER;
    v_journal TEXT;
BEGIN
    v_journal := NEW.journal::text;

    IF NEW.date_piece IS NULL THEN
        NEW.date_piece := NEW.date;
    END IF;

    IF NEW.numero_ecriture IS NULL OR BTRIM(NEW.numero_ecriture) = '' THEN
        INSERT INTO ecriture_sequences (societe_id, exercice, journal, dernier_numero)
        VALUES (NEW.societe_id, NEW.exercice, v_journal, 1)
        ON CONFLICT (societe_id, exercice, journal)
        DO UPDATE SET dernier_numero = ecriture_sequences.dernier_numero + 1
        RETURNING dernier_numero INTO v_num;

        NEW.numero_ecriture :=
            v_journal || '-' || NEW.exercice || '-' || LPAD(v_num::text, 4, '0');
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_numero_ecriture ON ecritures;
CREATE TRIGGER trg_hisabpro_numero_ecriture
BEFORE INSERT ON ecritures
FOR EACH ROW
EXECUTE FUNCTION hisabpro_attribuer_numero_ecriture();

CREATE OR REPLACE FUNCTION hisabpro_proteger_numero_ecriture()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.numero_ecriture IS DISTINCT FROM NEW.numero_ecriture THEN
        RAISE EXCEPTION 'Le numéro interne d''écriture est immuable (%).', OLD.numero_ecriture
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_proteger_numero_ecriture ON ecritures;
CREATE TRIGGER trg_hisabpro_proteger_numero_ecriture
BEFORE UPDATE OF numero_ecriture ON ecritures
FOR EACH ROW
EXECUTE FUNCTION hisabpro_proteger_numero_ecriture();

ALTER TABLE ecritures
    ALTER COLUMN numero_ecriture SET NOT NULL,
    ALTER COLUMN date_piece SET NOT NULL;

-- Le rôle applicatif ne doit que consulter le compteur ; les incréments passent
-- par la fonction SECURITY DEFINER du trigger.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT ON TABLE ecriture_sequences TO hisabpro;
        GRANT SELECT ON TABLE ecritures TO hisabpro;
    END IF;
END $$;

COMMIT;
