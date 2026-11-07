-- Patch 07C.2 — Numérotation définitive à la validation
-- À exécuter APRÈS 017_ecriture_numero_large_sequence.sql avec un rôle propriétaire.
--
-- Objectif Avis n°24 : les brouillons ne consomment plus de numéro comptable.
-- Le numéro séquentiel est attribué transactionnellement au moment où
-- l'écriture devient définitive (est_validee = TRUE), sans doublon ni rupture.
--
-- Cette migration :
--   1) vérifie les numéros déjà définitifs sans les renuméroter ;
--   2) retire le numéro des brouillons qui n'ont jamais été validés ;
--   3) réaligne les compteurs sur les seuls numéros définitifs/conservés ;
--   4) attribue désormais le numéro à la validation ;
--   5) interdit la suppression d'une écriture ayant déjà reçu un numéro ;
--   6) verrouille date/journal/exercice/société une fois le numéro attribué.

BEGIN;

ALTER TABLE ecriture_sequences
    ADD COLUMN IF NOT EXISTS derniere_date DATE;

-- Identifie les écritures dont le numéro a déjà acquis un caractère définitif.
-- Une écriture actuellement dévalidée conserve son numéro si la piste d'audit
-- prouve qu'elle a déjà été validée auparavant.
CREATE TEMP TABLE hp_07c2_numeros_a_conserver ON COMMIT DROP AS
SELECT e.id
  FROM ecritures e
 WHERE COALESCE(e.est_validee, FALSE)
    OR EXISTS (
        SELECT 1
          FROM audit_ecritures a
         WHERE a.ecriture_id = e.id
           AND a.table_cible = 'ecritures'
           AND (
               a.nouveau->>'est_validee' = 'true'
               OR a.ancien->>'est_validee' = 'true'
           )
    );

-- Préflight 1 : tout numéro définitif existant doit correspondre à son
-- journal/exercice et posséder un suffixe numérique exploitable.
DO $$
DECLARE
    v_bad RECORD;
BEGIN
    SELECT e.id, e.societe_id, e.exercice, e.journal::text AS journal,
           e.numero_ecriture
      INTO v_bad
      FROM ecritures e
      JOIN hp_07c2_numeros_a_conserver c ON c.id = e.id
     WHERE e.numero_ecriture IS NULL
        OR BTRIM(e.numero_ecriture) = ''
        OR e.numero_ecriture !~ ('^' || e.journal::text || '-' || e.exercice::text || '-[0-9]+$')
     ORDER BY e.id
     LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'Patch 07C.2 bloqué : écriture définitive id=% incohérente (journal=%, exercice=%, numero=%). Aucun numéro définitif n''a été modifié.',
            v_bad.id, v_bad.journal, v_bad.exercice, v_bad.numero_ecriture
            USING ERRCODE = '23514';
    END IF;
END $$;

-- Préflight 2 : parmi les numéros déjà définitifs, la séquence doit déjà être
-- continue. On refuse de renuméroter silencieusement un historique comptable.
DO $$
DECLARE
    v_bad RECORD;
BEGIN
    WITH nums AS (
        SELECT e.societe_id,
               e.exercice,
               e.journal::text AS journal,
               split_part(e.numero_ecriture, '-', 3)::INTEGER AS seq
          FROM ecritures e
          JOIN hp_07c2_numeros_a_conserver c ON c.id = e.id
    ), controles AS (
        SELECT societe_id, exercice, journal,
               MIN(seq) AS min_seq,
               MAX(seq) AS max_seq,
               COUNT(*) AS nb
          FROM nums
         GROUP BY societe_id, exercice, journal
    )
    SELECT *
      INTO v_bad
      FROM controles
     WHERE min_seq <> 1 OR max_seq <> nb
     ORDER BY societe_id, exercice, journal
     LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'Patch 07C.2 bloqué : séquence définitive avec rupture (société=%, exercice=%, journal=%, min=%, max=%, nombre=%). Aucun historique n''a été renuméroté.',
            v_bad.societe_id, v_bad.exercice, v_bad.journal,
            v_bad.min_seq, v_bad.max_seq, v_bad.nb
            USING ERRCODE = '23514';
    END IF;
END $$;

-- Préflight 3 : la date comptable doit être non décroissante quand le numéro
-- augmente à l'intérieur d'un même journal.
DO $$
DECLARE
    v_bad RECORD;
BEGIN
    WITH nums AS (
        SELECT e.id,
               e.societe_id,
               e.exercice,
               e.journal::text AS journal,
               e.date,
               split_part(e.numero_ecriture, '-', 3)::INTEGER AS seq
          FROM ecritures e
          JOIN hp_07c2_numeros_a_conserver c ON c.id = e.id
    ), ordonnes AS (
        SELECT *,
               LAG(date) OVER (
                   PARTITION BY societe_id, exercice, journal
                   ORDER BY seq
               ) AS date_precedente
          FROM nums
    )
    SELECT *
      INTO v_bad
      FROM ordonnes
     WHERE date_precedente IS NOT NULL
       AND date < date_precedente
     ORDER BY societe_id, exercice, journal, seq
     LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'Patch 07C.2 bloqué : numérotation définitive non chronologique à l''écriture id=% (société=%, exercice=%, journal=%, date=% < date précédente=%).',
            v_bad.id, v_bad.societe_id, v_bad.exercice, v_bad.journal,
            v_bad.date, v_bad.date_precedente
            USING ERRCODE = '23514';
    END IF;
END $$;

-- Le numéro devient nullable : un brouillon n'a pas encore de numéro comptable.
ALTER TABLE ecritures
    ALTER COLUMN numero_ecriture DROP NOT NULL;

-- Le changement de statut/numéro pendant la migration ne doit pas polluer la
-- piste d'audit métier. On réactive le trigger immédiatement après.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'trg_hisabpro_audit_ecritures'
           AND tgrelid = 'ecritures'::regclass
           AND NOT tgisinternal
    ) THEN
        EXECUTE 'ALTER TABLE ecritures DISABLE TRIGGER trg_hisabpro_audit_ecritures';
    END IF;
END $$;

DROP TRIGGER IF EXISTS trg_hisabpro_proteger_numero_ecriture ON ecritures;
DROP TRIGGER IF EXISTS trg_hisabpro_numero_ecriture ON ecritures;
DROP TRIGGER IF EXISTS trg_hisabpro_numero_validation ON ecritures;
DROP TRIGGER IF EXISTS trg_00_hisabpro_numero_ecriture ON ecritures;
DROP TRIGGER IF EXISTS trg_00_hisabpro_numero_validation ON ecritures;
DROP TRIGGER IF EXISTS trg_hisabpro_interdire_suppression_numero ON ecritures;

-- Les numéros donnés à de simples brouillons avant 07C.2 n'étaient pas encore
-- définitifs : ils sont libérés. Une écriture ayant déjà été validée conserve
-- en revanche son numéro, même si elle est actuellement dévalidée.
UPDATE ecritures e
   SET numero_ecriture = NULL
 WHERE NOT EXISTS (
       SELECT 1 FROM hp_07c2_numeros_a_conserver c WHERE c.id = e.id
 );

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'trg_hisabpro_audit_ecritures'
           AND tgrelid = 'ecritures'::regclass
           AND NOT tgisinternal
    ) THEN
        EXECUTE 'ALTER TABLE ecritures ENABLE TRIGGER trg_hisabpro_audit_ecritures';
    END IF;
END $$;

-- Réinitialise les compteurs à partir des seuls numéros conservés. Cette table
-- est transactionnelle : un rollback de validation restitue le numéro.
DELETE FROM ecriture_sequences;

INSERT INTO ecriture_sequences (
    societe_id, exercice, journal, dernier_numero, derniere_date
)
SELECT DISTINCT ON (e.societe_id, e.exercice, e.journal)
       e.societe_id,
       e.exercice,
       e.journal::text,
       split_part(e.numero_ecriture, '-', 3)::INTEGER AS dernier_numero,
       e.date AS derniere_date
  FROM ecritures e
 WHERE e.numero_ecriture IS NOT NULL
 ORDER BY e.societe_id, e.exercice, e.journal,
          split_part(e.numero_ecriture, '-', 3)::INTEGER DESC;

-- Réserve atomiquement le prochain numéro d'un journal. La date du compteur
-- garantit qu'une nouvelle validation ne peut pas revenir en arrière dans le
-- temps, y compris sous concurrence.
CREATE OR REPLACE FUNCTION hisabpro_reserver_numero_ecriture(
    p_societe_id INTEGER,
    p_exercice INTEGER,
    p_journal TEXT,
    p_date DATE
)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_num INTEGER;
    v_derniere_date DATE;
BEGIN
    INSERT INTO ecriture_sequences (
        societe_id, exercice, journal, dernier_numero, derniere_date
    )
    VALUES (p_societe_id, p_exercice, p_journal, 1, p_date)
    ON CONFLICT (societe_id, exercice, journal)
    DO UPDATE SET
        dernier_numero = ecriture_sequences.dernier_numero + 1,
        derniere_date = EXCLUDED.derniere_date
    WHERE ecriture_sequences.derniere_date IS NULL
       OR EXCLUDED.derniere_date >= ecriture_sequences.derniere_date
    RETURNING dernier_numero, derniere_date
         INTO v_num, v_derniere_date;

    IF v_num IS NULL THEN
        SELECT derniere_date
          INTO v_derniere_date
          FROM ecriture_sequences
         WHERE societe_id = p_societe_id
           AND exercice = p_exercice
           AND journal = p_journal;

        RAISE EXCEPTION
            'Validation non chronologique : la date comptable % est antérieure à la dernière date validée % du journal %/% .',
            p_date, v_derniere_date, p_journal, p_exercice
            USING ERRCODE = '23514';
    END IF;

    RETURN p_journal || '-' || p_exercice || '-' ||
           LPAD(v_num::text, GREATEST(4, LENGTH(v_num::text)), '0');
END;
$$;

-- Préparation des INSERT : une valeur fournie manuellement est toujours
-- refusée. Un brouillon reste sans numéro ; une création directement validée
-- reçoit son numéro dans la même transaction.
CREATE OR REPLACE FUNCTION hisabpro_attribuer_numero_ecriture()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    IF NEW.numero_ecriture IS NOT NULL AND BTRIM(NEW.numero_ecriture) <> '' THEN
        RAISE EXCEPTION 'Le numéro interne d''écriture est attribué automatiquement par HisabPro lors de la validation.'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.date_piece IS NULL THEN
        NEW.date_piece := NEW.date;
    END IF;

    IF COALESCE(NEW.est_validee, FALSE) THEN
        NEW.numero_ecriture := hisabpro_reserver_numero_ecriture(
            NEW.societe_id, NEW.exercice, NEW.journal::text, NEW.date
        );
    ELSE
        NEW.numero_ecriture := NULL;
    END IF;

    RETURN NEW;
END;
$$;

-- Préfixe 00 : ce trigger s'exécute avant le trigger d'audit alphabétiquement,
-- afin que l'audit voie déjà le numéro final lors d'une création validée.
CREATE TRIGGER trg_00_hisabpro_numero_ecriture
BEFORE INSERT ON ecritures
FOR EACH ROW
EXECUTE FUNCTION hisabpro_attribuer_numero_ecriture();

-- Lors du passage brouillon -> validée, attribue le numéro si l'écriture n'en
-- possède pas déjà un. Une écriture exceptionnellement dévalidée garde son
-- ancien numéro et le récupère à la revalidation.
CREATE OR REPLACE FUNCTION hisabpro_numero_a_la_validation()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    IF COALESCE(NEW.est_validee, FALSE)
       AND NOT COALESCE(OLD.est_validee, FALSE)
       AND OLD.numero_ecriture IS NULL THEN

        IF NEW.numero_ecriture IS NOT NULL THEN
            RAISE EXCEPTION 'Le numéro interne d''écriture ne peut pas être fourni manuellement.'
                USING ERRCODE = '23514';
        END IF;

        NEW.numero_ecriture := hisabpro_reserver_numero_ecriture(
            NEW.societe_id, NEW.exercice, NEW.journal::text, NEW.date
        );
    END IF;

    RETURN NEW;
END;
$$;

-- Même priorité avant le trigger d'audit : l'événement de validation conserve
-- le numéro définitif dans son JSON « nouveau ».
CREATE TRIGGER trg_00_hisabpro_numero_validation
BEFORE UPDATE OF est_validee ON ecritures
FOR EACH ROW
EXECUTE FUNCTION hisabpro_numero_a_la_validation();

-- Tant qu'une écriture est un vrai brouillon sans numéro, journal/date/exercice
-- restent corrigeables. Dès qu'un numéro définitif existe, son périmètre et sa
-- date comptable deviennent immuables.
CREATE OR REPLACE FUNCTION hisabpro_proteger_numero_ecriture()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.numero_ecriture IS NULL THEN
        IF NEW.numero_ecriture IS NOT NULL THEN
            RAISE EXCEPTION 'Le numéro interne d''écriture est attribué uniquement par le mécanisme de validation HisabPro.'
                USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    END IF;

    IF OLD.numero_ecriture IS DISTINCT FROM NEW.numero_ecriture THEN
        RAISE EXCEPTION 'Le numéro interne d''écriture est immuable (%).', OLD.numero_ecriture
            USING ERRCODE = '23514';
    END IF;

    IF OLD.societe_id IS DISTINCT FROM NEW.societe_id THEN
        RAISE EXCEPTION 'La société est verrouillée par le numéro interne d''écriture (%).', OLD.numero_ecriture
            USING ERRCODE = '23514';
    END IF;

    IF OLD.exercice IS DISTINCT FROM NEW.exercice THEN
        RAISE EXCEPTION 'L''exercice est verrouillé par le numéro interne d''écriture (%) : % -> %.',
            OLD.numero_ecriture, OLD.exercice, NEW.exercice
            USING ERRCODE = '23514';
    END IF;

    IF OLD.journal IS DISTINCT FROM NEW.journal THEN
        RAISE EXCEPTION 'Le journal est verrouillé par le numéro interne d''écriture (%) : % -> %.',
            OLD.numero_ecriture, OLD.journal, NEW.journal
            USING ERRCODE = '23514';
    END IF;

    IF OLD.date IS DISTINCT FROM NEW.date THEN
        RAISE EXCEPTION 'La date comptable est verrouillée par le numéro interne d''écriture (%) : % -> %.',
            OLD.numero_ecriture, OLD.date, NEW.date
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_hisabpro_proteger_numero_ecriture
BEFORE UPDATE OF numero_ecriture, societe_id, exercice, journal, date ON ecritures
FOR EACH ROW
EXECUTE FUNCTION hisabpro_proteger_numero_ecriture();

-- Un numéro définitif ne doit jamais disparaître par DELETE. Une correction
-- passe par une écriture d'annulation/contrepassation et reste traçable.
CREATE OR REPLACE FUNCTION hisabpro_interdire_suppression_numero()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.numero_ecriture IS NOT NULL THEN
        RAISE EXCEPTION 'Suppression interdite : l''écriture % possède le numéro définitif %. Utilisez une écriture d''annulation/contrepassation.',
            OLD.id, OLD.numero_ecriture
            USING ERRCODE = '23514';
    END IF;
    RETURN OLD;
END;
$$;

CREATE TRIGGER trg_hisabpro_interdire_suppression_numero
BEFORE DELETE ON ecritures
FOR EACH ROW
EXECUTE FUNCTION hisabpro_interdire_suppression_numero();

-- Les index uniques existants restent valides : PostgreSQL autorise plusieurs
-- NULL mais interdit tout doublon parmi les numéros définitifs.
CREATE UNIQUE INDEX IF NOT EXISTS ux_ecritures_numero_interne
    ON ecritures (societe_id, exercice, journal, numero_ecriture);
CREATE UNIQUE INDEX IF NOT EXISTS ux_ecritures_societe_numero_interne
    ON ecritures (societe_id, numero_ecriture);

COMMIT;
