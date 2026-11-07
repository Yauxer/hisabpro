-- PATCH FACT.4B — Durcissement du cycle commercial
-- - numérotation atomique des BC / BL / BR / avoirs créés automatiquement
-- - unicité forte des numéros de documents au niveau PostgreSQL
-- - unicité forte du numéro de facture fournisseur validée

BEGIN;

CREATE TABLE IF NOT EXISTS commercial_sequences (
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice INTEGER NOT NULL,
    type_doc VARCHAR(20) NOT NULL,
    derniere_sequence BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (societe_id, exercice, type_doc),
    CONSTRAINT ck_commercial_sequences_type CHECK (type_doc IN ('devis', 'bc', 'bl', 'br', 'avoir')),
    CONSTRAINT ck_commercial_sequences_positive CHECK (derniere_sequence >= 0)
);

-- Initialise le compteur à partir des documents déjà présents. On retient le
-- suffixe numérique final, indépendamment du préfixe historique/configuré.
WITH historique AS (
    SELECT societe_id, exercice, 'devis'::VARCHAR AS type_doc, numero FROM devis
    UNION ALL
    SELECT societe_id, exercice, 'bc'::VARCHAR AS type_doc, numero FROM bons_commande
    UNION ALL
    SELECT societe_id, exercice,
           CASE WHEN type = 'achat' THEN 'br'::VARCHAR ELSE 'bl'::VARCHAR END AS type_doc,
           numero
      FROM bons_livraison
    UNION ALL
    SELECT societe_id, exercice, 'avoir'::VARCHAR AS type_doc, numero FROM avoirs
), maxima AS (
    SELECT societe_id, exercice, type_doc,
           MAX(CASE
               WHEN numero ~ '[0-9]+$' THEN substring(numero FROM '([0-9]+)$')::BIGINT
               ELSE 0
           END) AS derniere_sequence
      FROM historique
     GROUP BY societe_id, exercice, type_doc
)
INSERT INTO commercial_sequences (societe_id, exercice, type_doc, derniere_sequence)
SELECT societe_id, exercice, type_doc, derniere_sequence
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
    IF p_type_doc NOT IN ('devis', 'bc', 'bl', 'br', 'avoir') THEN
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
        END;
    END IF;

    -- La ligne de compteur est le verrou transactionnel du couple société /
    -- exercice / type de document. Deux validations simultanées ne peuvent donc
    -- pas réserver la même séquence.
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

    -- Re-synchronisation avec l'historique réel : elle protège aussi le cas où
    -- un utilisateur a saisi manuellement un numéro après la migration.
    IF p_type_doc = 'devis' THEN
        SELECT COALESCE(MAX(CASE WHEN numero ~ '[0-9]+$'
                                 THEN substring(numero FROM '([0-9]+)$')::BIGINT ELSE 0 END), 0)
          INTO v_existant
          FROM devis
         WHERE societe_id = p_societe_id AND exercice = p_exercice;
    ELSIF p_type_doc = 'bc' THEN
        SELECT COALESCE(MAX(CASE WHEN numero ~ '[0-9]+$'
                                 THEN substring(numero FROM '([0-9]+)$')::BIGINT ELSE 0 END), 0)
          INTO v_existant
          FROM bons_commande
         WHERE societe_id = p_societe_id AND exercice = p_exercice;
    ELSIF p_type_doc IN ('bl', 'br') THEN
        SELECT COALESCE(MAX(CASE WHEN numero ~ '[0-9]+$'
                                 THEN substring(numero FROM '([0-9]+)$')::BIGINT ELSE 0 END), 0)
          INTO v_existant
          FROM bons_livraison
         WHERE societe_id = p_societe_id
           AND exercice = p_exercice
           AND ((p_type_doc = 'br' AND type = 'achat') OR (p_type_doc = 'bl' AND type <> 'achat'));
    ELSIF p_type_doc = 'avoir' THEN
        SELECT COALESCE(MAX(CASE WHEN numero ~ '[0-9]+$'
                                 THEN substring(numero FROM '([0-9]+)$')::BIGINT ELSE 0 END), 0)
          INTO v_existant
          FROM avoirs
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

-- Les contrôles applicatifs donnent des messages lisibles ; ces index sont la
-- barrière de dernier recours contre les courses concurrentes.
CREATE UNIQUE INDEX IF NOT EXISTS uq_factures_societe_numero
    ON factures (societe_id, numero)
    WHERE numero IS NOT NULL AND BTRIM(numero) <> '';

CREATE UNIQUE INDEX IF NOT EXISTS uq_devis_societe_numero
    ON devis (societe_id, numero);

CREATE UNIQUE INDEX IF NOT EXISTS uq_bons_commande_societe_numero
    ON bons_commande (societe_id, numero);

CREATE UNIQUE INDEX IF NOT EXISTS uq_bons_livraison_societe_numero
    ON bons_livraison (societe_id, numero);

CREATE UNIQUE INDEX IF NOT EXISTS uq_avoirs_societe_numero
    ON avoirs (societe_id, numero);

-- Un fournisseur ne peut avoir deux factures validées portant le même numéro
-- sur le même exercice, même si casse/espaces diffèrent.
CREATE UNIQUE INDEX IF NOT EXISTS uq_factures_fournisseur_reference_validee
    ON factures (societe_id, tiers_id, exercice, LOWER(BTRIM(reference)))
    WHERE type = 'achat'
      AND COALESCE(est_proforma, FALSE) = FALSE
      AND COALESCE(est_validee, FALSE) = TRUE
      AND tiers_id IS NOT NULL
      AND reference IS NOT NULL
      AND BTRIM(reference) <> '';

GRANT SELECT, INSERT, UPDATE ON commercial_sequences TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_reserver_numero_commercial(INTEGER, INTEGER, VARCHAR, VARCHAR) TO hisabpro;

COMMIT;
