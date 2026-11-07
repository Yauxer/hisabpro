-- Patch 07B.3 — Robustesse de la séquence des numéros d'écriture
-- À exécuter APRÈS 015_ecriture_numero_scope.sql.
--
-- Correction ciblée : LPAD(text, 4, '0') tronque une valeur qui dépasse
-- 4 caractères. Sans ce correctif, la 10 000e écriture d'un même
-- société/exercice/journal pourrait produire un suffixe incorrect.
--
-- Le compteur reste transactionnel et atomique grâce à l'UPSERT sur
-- ecriture_sequences ; cette migration ne renumérote aucune écriture existante.

BEGIN;

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

    -- Minimum 4 chiffres, sans jamais tronquer à partir de 10 000.
    NEW.numero_ecriture :=
        v_journal || '-' || NEW.exercice || '-' ||
        LPAD(v_num::text, GREATEST(4, LENGTH(v_num::text)), '0');

    RETURN NEW;
END;
$$;

COMMIT;
