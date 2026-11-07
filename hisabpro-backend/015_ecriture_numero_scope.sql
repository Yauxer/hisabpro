-- Patch 07B.2 — Verrouillage du périmètre du numéro interne
-- À exécuter APRÈS 014_ecriture_metadata.sql avec un rôle propriétaire.
--
-- Le numéro interne est attribué dès la création et encode :
--   société (par son compteur isolé), exercice et journal.
-- Une écriture AC-2026-0004 ne doit donc jamais pouvoir devenir VT/2026,
-- passer en 2027, ni changer de société tout en conservant ce numéro.

BEGIN;

-- Préflight : refuse d'installer le verrou si des incohérences héritées existent
-- déjà. Elles doivent être examinées explicitement, pas renumérotées en silence.
DO $$
DECLARE
    v_bad RECORD;
BEGIN
    SELECT id, societe_id, exercice, journal::text AS journal, numero_ecriture
      INTO v_bad
      FROM ecritures
     WHERE numero_ecriture IS NULL
        OR BTRIM(numero_ecriture) = ''
        OR numero_ecriture NOT LIKE journal::text || '-' || exercice::text || '-%'
     ORDER BY id
     LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'Patch 07B.2 bloqué : écriture id=% incohérente (journal=%, exercice=%, numero=%). Corrigez cette donnée avant de relancer la migration.',
            v_bad.id, v_bad.journal, v_bad.exercice, v_bad.numero_ecriture
            USING ERRCODE = '23514';
    END IF;
END $$;

-- Durcit l'allocation : un client applicatif ou une requête SQL ordinaire ne
-- peut plus imposer son propre numéro. Une restauration exceptionnelle doit
-- passer par une procédure d'administration contrôlée (trigger désactivé).
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

    IF NEW.numero_ecriture IS NOT NULL AND BTRIM(NEW.numero_ecriture) <> '' THEN
        RAISE EXCEPTION 'Le numéro interne d''écriture est attribué automatiquement par HisabPro.'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.date_piece IS NULL THEN
        NEW.date_piece := NEW.date;
    END IF;

    INSERT INTO ecriture_sequences (societe_id, exercice, journal, dernier_numero)
    VALUES (NEW.societe_id, NEW.exercice, v_journal, 1)
    ON CONFLICT (societe_id, exercice, journal)
    DO UPDATE SET dernier_numero = ecriture_sequences.dernier_numero + 1
    RETURNING dernier_numero INTO v_num;

    NEW.numero_ecriture :=
        v_journal || '-' || NEW.exercice || '-' || LPAD(v_num::text, 4, '0');

    RETURN NEW;
END;
$$;

-- Un seul garde-fou protège le numéro ET son périmètre. La date comptable et
-- la date du justificatif restent modifiables selon les règles applicatives,
-- tant que l'écriture demeure dans le même exercice.
CREATE OR REPLACE FUNCTION hisabpro_proteger_numero_ecriture()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
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

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_proteger_numero_ecriture ON ecritures;
CREATE TRIGGER trg_hisabpro_proteger_numero_ecriture
BEFORE UPDATE OF numero_ecriture, societe_id, exercice, journal ON ecritures
FOR EACH ROW
EXECUTE FUNCTION hisabpro_proteger_numero_ecriture();

-- Le numéro complet doit être unique dans une société. Les mêmes codes peuvent
-- naturellement exister dans deux sociétés différentes.
CREATE UNIQUE INDEX IF NOT EXISTS ux_ecritures_societe_numero_interne
    ON ecritures (societe_id, numero_ecriture);

COMMIT;
