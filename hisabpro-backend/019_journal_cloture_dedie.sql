-- Patch 07C.3 — Journal de clôture dédié (Avis n°24 CNC, §2.3.c)
--
-- Objectifs :
--   1) ajouter le code journal système CL à l'énumération PostgreSQL utilisée
--      par ecritures.journal ;
--   2) réserver CL exclusivement aux écritures générées par le moteur de clôture ;
--   3) empêcher qu'une future écriture CLOTURE-N soit enregistrée dans OD ou
--      dans un autre journal ;
--   4) ne modifier AUCUNE écriture historique existante.
--
-- Important : les anciennes clôtures déjà enregistrées sous OD restent intactes.
-- Le contrôle FEC 07C.3 les signalera comme anomalie de conformité historique.

BEGIN;

-- SQLAlchemy crée normalement un TYPE ENUM natif pour JournalEnum. On retrouve
-- le type réellement attaché à ecritures.journal au lieu de supposer son nom.
DO $$
DECLARE
    v_type_oid oid;
    v_type_name text;
    v_type_schema text;
    v_typtype "char";
BEGIN
    SELECT a.atttypid, t.typname, n.nspname, t.typtype
      INTO v_type_oid, v_type_name, v_type_schema, v_typtype
      FROM pg_attribute a
      JOIN pg_class c ON c.oid = a.attrelid
      JOIN pg_namespace cn ON cn.oid = c.relnamespace
      JOIN pg_type t ON t.oid = a.atttypid
      JOIN pg_namespace n ON n.oid = t.typnamespace
     WHERE c.relname = 'ecritures'
       AND a.attname = 'journal'
       AND a.attnum > 0
       AND NOT a.attisdropped
     ORDER BY CASE WHEN cn.nspname = current_schema() THEN 0 ELSE 1 END
     LIMIT 1;

    IF v_type_oid IS NULL THEN
        RAISE EXCEPTION 'Patch 07C.3 : colonne ecritures.journal introuvable.';
    END IF;

    IF v_typtype = 'e' THEN
        IF NOT EXISTS (
            SELECT 1
              FROM pg_enum
             WHERE enumtypid = v_type_oid
               AND enumlabel = 'CL'
        ) THEN
            EXECUTE format(
                'ALTER TYPE %I.%I ADD VALUE %L',
                v_type_schema, v_type_name, 'CL'
            );
        END IF;
    ELSE
        -- Compatibilité avec une installation qui stockerait le journal en
        -- VARCHAR/TEXT : aucun ALTER TYPE n'est nécessaire.
        RAISE NOTICE 'ecritures.journal n''est pas un ENUM PostgreSQL : ajout de CL non requis au niveau du type.';
    END IF;
END $$;

-- Garde-fou base de données. Le contrôle ne dépend pas de l'interface : un appel
-- SQL direct ne peut pas détourner le journal CL pour une opération ordinaire.
CREATE OR REPLACE FUNCTION hisabpro_controler_journal_cloture()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_journal text := COALESCE(NEW.journal::text, '');
    v_source text := LOWER(COALESCE(NEW.source, ''));
    v_reference text := COALESCE(NEW.reference, '');
BEGIN
    IF v_journal = 'CL' AND v_source <> 'cloture' THEN
        RAISE EXCEPTION
            'Le journal CL est réservé exclusivement aux écritures de clôture générées par HisabPro.';
    END IF;

    -- L'écriture de détermination/arrêté de résultat appartient obligatoirement
    -- au journal dédié. L'écriture d'ouverture N+1 reste dans AN et n'est donc
    -- pas concernée par cette règle.
    IF v_source = 'cloture'
       AND v_reference LIKE 'CLOTURE-%'
       AND v_journal <> 'CL' THEN
        RAISE EXCEPTION
            'Une écriture de clôture CLOTURE-* doit être enregistrée dans le journal dédié CL (journal reçu : %).',
            NULLIF(v_journal, '');
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_01_hisabpro_journal_cloture ON ecritures;
CREATE TRIGGER trg_01_hisabpro_journal_cloture
BEFORE INSERT OR UPDATE OF journal, source, reference ON ecritures
FOR EACH ROW
EXECUTE FUNCTION hisabpro_controler_journal_cloture();

COMMIT;
