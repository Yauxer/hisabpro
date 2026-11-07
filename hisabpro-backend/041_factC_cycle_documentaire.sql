-- FACT-C — Cycle documentaire, acomptes et verrou de clôture
-- - numérotation atomique des acomptes
-- - unicité forte des numéros d'acompte par société
-- - piste d'audit des annulations d'acomptes
-- Migration idempotente / rejouable après 040_factB_identites_dates.sql.

BEGIN;

-- ── 1. Historique d'annulation des acomptes ────────────────────────────────
ALTER TABLE acomptes
    ADD COLUMN IF NOT EXISTS date_annulation TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS annule_par INTEGER NULL,
    ADD COLUMN IF NOT EXISTS ecriture_annulation_id INTEGER NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_acomptes_annule_par'
    ) THEN
        ALTER TABLE acomptes
            ADD CONSTRAINT fk_acomptes_annule_par
            FOREIGN KEY (annule_par) REFERENCES utilisateurs(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_acomptes_ecriture_annulation'
    ) THEN
        ALTER TABLE acomptes
            ADD CONSTRAINT fk_acomptes_ecriture_annulation
            FOREIGN KEY (ecriture_annulation_id) REFERENCES ecritures(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_acomptes_societe_numero
    ON acomptes (societe_id, numero)
    WHERE numero IS NOT NULL AND BTRIM(numero) <> '';

-- ── 2. Étendre le séquenceur commercial aux acomptes ──────────────────────
ALTER TABLE commercial_sequences
    DROP CONSTRAINT IF EXISTS ck_commercial_sequences_type;

ALTER TABLE commercial_sequences
    ADD CONSTRAINT ck_commercial_sequences_type
    CHECK (type_doc IN ('devis', 'bc', 'bl', 'br', 'avoir', 'acompte'));

-- Reprendre le plus grand suffixe historique pour chaque société/exercice.
WITH maxima AS (
    SELECT societe_id, exercice, 'acompte'::VARCHAR AS type_doc,
           MAX(CASE
               WHEN numero ~ '[0-9]+$' THEN substring(numero FROM '([0-9]+)$')::BIGINT
               ELSE 0
           END) AS derniere_sequence
      FROM acomptes
     GROUP BY societe_id, exercice
)
INSERT INTO commercial_sequences (societe_id, exercice, type_doc, derniere_sequence, updated_at)
SELECT societe_id, exercice, type_doc, COALESCE(derniere_sequence, 0), NOW()
  FROM maxima
ON CONFLICT (societe_id, exercice, type_doc)
DO UPDATE SET
    derniere_sequence = GREATEST(commercial_sequences.derniere_sequence, EXCLUDED.derniere_sequence),
    updated_at = NOW();

CREATE OR REPLACE FUNCTION hisabpro_reserver_numero_commercial(
    p_societe_id INTEGER,
    p_exercice INTEGER,
    p_type_doc VARCHAR,
    p_prefixe VARCHAR
) RETURNS VARCHAR
LANGUAGE plpgsql
AS $$
DECLARE
    v_seq BIGINT;
    v_existant BIGINT := 0;
    v_prefixe VARCHAR;
    v_seq_txt VARCHAR;
BEGIN
    IF p_type_doc NOT IN ('devis', 'bc', 'bl', 'br', 'avoir', 'acompte') THEN
        RAISE EXCEPTION 'Type de document commercial invalide : %', p_type_doc;
    END IF;

    v_prefixe := NULLIF(BTRIM(p_prefixe), '');
    IF v_prefixe IS NULL THEN
        v_prefixe := CASE p_type_doc
            WHEN 'devis' THEN 'DV'
            WHEN 'bc' THEN 'BC'
            WHEN 'bl' THEN 'BL'
            WHEN 'br' THEN 'BR'
            WHEN 'avoir' THEN 'AV'
            WHEN 'acompte' THEN 'AC'
        END;
    END IF;

    INSERT INTO commercial_sequences (societe_id, exercice, type_doc, derniere_sequence, updated_at)
    VALUES (p_societe_id, p_exercice, p_type_doc, 0, NOW())
    ON CONFLICT (societe_id, exercice, type_doc) DO NOTHING;

    SELECT derniere_sequence
      INTO v_seq
      FROM commercial_sequences
     WHERE societe_id = p_societe_id
       AND exercice = p_exercice
       AND type_doc = p_type_doc
     FOR UPDATE;

    IF p_type_doc = 'devis' THEN
        SELECT COALESCE(MAX(CASE WHEN numero ~ '[0-9]+$'
                                 THEN substring(numero FROM '([0-9]+)$')::BIGINT ELSE 0 END), 0)
          INTO v_existant FROM devis
         WHERE societe_id = p_societe_id AND exercice = p_exercice;
    ELSIF p_type_doc = 'bc' THEN
        SELECT COALESCE(MAX(CASE WHEN numero ~ '[0-9]+$'
                                 THEN substring(numero FROM '([0-9]+)$')::BIGINT ELSE 0 END), 0)
          INTO v_existant FROM bons_commande
         WHERE societe_id = p_societe_id AND exercice = p_exercice;
    ELSIF p_type_doc IN ('bl', 'br') THEN
        SELECT COALESCE(MAX(CASE WHEN numero ~ '[0-9]+$'
                                 THEN substring(numero FROM '([0-9]+)$')::BIGINT ELSE 0 END), 0)
          INTO v_existant FROM bons_livraison
         WHERE societe_id = p_societe_id
           AND exercice = p_exercice
           AND ((p_type_doc = 'br' AND type = 'achat') OR (p_type_doc = 'bl' AND type <> 'achat'));
    ELSIF p_type_doc = 'avoir' THEN
        SELECT COALESCE(MAX(CASE WHEN numero ~ '[0-9]+$'
                                 THEN substring(numero FROM '([0-9]+)$')::BIGINT ELSE 0 END), 0)
          INTO v_existant FROM avoirs
         WHERE societe_id = p_societe_id AND exercice = p_exercice;
    ELSIF p_type_doc = 'acompte' THEN
        SELECT COALESCE(MAX(CASE WHEN numero ~ '[0-9]+$'
                                 THEN substring(numero FROM '([0-9]+)$')::BIGINT ELSE 0 END), 0)
          INTO v_existant FROM acomptes
         WHERE societe_id = p_societe_id AND exercice = p_exercice;
    END IF;

    v_seq := GREATEST(COALESCE(v_seq, 0), COALESCE(v_existant, 0)) + 1;

    UPDATE commercial_sequences
       SET derniere_sequence = v_seq,
           updated_at = NOW()
     WHERE societe_id = p_societe_id
       AND exercice = p_exercice
       AND type_doc = p_type_doc;

    v_seq_txt := v_seq::TEXT;
    IF LENGTH(v_seq_txt) < 3 THEN
        v_seq_txt := LPAD(v_seq_txt, 3, '0');
    END IF;
    RETURN v_prefixe || '-' || p_exercice::TEXT || '-' || v_seq_txt;
END;
$$;

GRANT SELECT, INSERT, UPDATE ON commercial_sequences TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_reserver_numero_commercial(INTEGER, INTEGER, VARCHAR, VARCHAR) TO hisabpro;

COMMIT;
