-- PATCH FACT.4 — Facturation robuste
-- - brouillons sans numéro définitif
-- - numérotation atomique à la validation
-- - échéance contractuelle figée
-- - immutabilité des factures validées
-- - contrôle des doublons de factures fournisseurs

BEGIN;

-- Migration rejouable : si FACT.4 a déjà été installée, les triggers
-- d'immutabilité peuvent déjà exister. Ils doivent être retirés AVANT les
-- backfills historiques ci-dessous, sinon l'ancienne version du trigger peut
-- refuser la mise à jour d'une facture déjà validée et mettre toute la
-- transaction en état aborted (25P02). Ils sont recréés plus bas dans la même
-- transaction.
DROP TRIGGER IF EXISTS trg_hisabpro_guard_facture_validee ON factures;
DROP TRIGGER IF EXISTS trg_hisabpro_guard_ligne_facture_validee ON lignes_facture;

ALTER TABLE factures
    ALTER COLUMN numero DROP NOT NULL;

ALTER TABLE factures
    ADD COLUMN IF NOT EXISTS est_validee BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS date_validation TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS validee_par INTEGER NULL REFERENCES utilisateurs(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS date_echeance DATE NULL;

-- Les pièces déjà présentes avant FACT.4 sont considérées comme historiques/définitives.
-- Les proformas restent modifiables jusqu'à leur conversion.
UPDATE factures
SET est_validee = TRUE,
    date_validation = COALESCE(date_validation, created_at, NOW()),
    date_echeance = COALESCE(date_echeance, date + COALESCE(delai_paiement, 60))
WHERE COALESCE(est_proforma, FALSE) = FALSE;

UPDATE factures
SET est_validee = FALSE,
    date_validation = NULL,
    validee_par = NULL,
    date_echeance = COALESCE(date_echeance, date + COALESCE(delai_paiement, 60))
WHERE COALESCE(est_proforma, FALSE) = TRUE;

CREATE TABLE IF NOT EXISTS facturation_sequences (
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice INTEGER NOT NULL,
    type_doc VARCHAR(20) NOT NULL,
    derniere_sequence BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (societe_id, exercice, type_doc),
    CONSTRAINT ck_facturation_sequences_type CHECK (type_doc IN ('facture', 'proforma')),
    CONSTRAINT ck_facturation_sequences_positive CHECK (derniere_sequence >= 0)
);

-- Initialisation à partir de l'historique existant. Le suffixe numérique final est utilisé,
-- quel que soit le préfixe configuré à l'époque.
INSERT INTO facturation_sequences (societe_id, exercice, type_doc, derniere_sequence)
SELECT
    societe_id,
    exercice,
    CASE WHEN COALESCE(est_proforma, FALSE) THEN 'proforma' ELSE 'facture' END AS type_doc,
    MAX(CASE
        WHEN numero ~ '[0-9]+$' THEN substring(numero FROM '([0-9]+)$')::BIGINT
        ELSE 0
    END) AS derniere_sequence
FROM factures
GROUP BY societe_id, exercice, CASE WHEN COALESCE(est_proforma, FALSE) THEN 'proforma' ELSE 'facture' END
ON CONFLICT (societe_id, exercice, type_doc)
DO UPDATE SET
    derniere_sequence = GREATEST(facturation_sequences.derniere_sequence, EXCLUDED.derniere_sequence),
    updated_at = NOW();

CREATE OR REPLACE FUNCTION hisabpro_reserver_numero_facture(
    p_societe_id INTEGER,
    p_exercice INTEGER,
    p_type_doc VARCHAR,
    p_prefixe VARCHAR
) RETURNS VARCHAR
LANGUAGE plpgsql
AS $$
DECLARE
    v_seq BIGINT;
    v_prefixe VARCHAR;
    v_seq_txt VARCHAR;
BEGIN
    IF p_type_doc NOT IN ('facture', 'proforma') THEN
        RAISE EXCEPTION 'Type de document de facturation invalide : %', p_type_doc;
    END IF;
    v_prefixe := NULLIF(BTRIM(p_prefixe), '');
    IF v_prefixe IS NULL THEN
        v_prefixe := CASE WHEN p_type_doc = 'proforma' THEN 'PF' ELSE 'FA' END;
    END IF;

    INSERT INTO facturation_sequences (societe_id, exercice, type_doc, derniere_sequence, updated_at)
    VALUES (p_societe_id, p_exercice, p_type_doc, 1, NOW())
    ON CONFLICT (societe_id, exercice, type_doc)
    DO UPDATE SET
        derniere_sequence = facturation_sequences.derniere_sequence + 1,
        updated_at = NOW()
    RETURNING derniere_sequence INTO v_seq;

    v_seq_txt := v_seq::TEXT;
    IF LENGTH(v_seq_txt) < 3 THEN
        v_seq_txt := LPAD(v_seq_txt, 3, '0');
    END IF;
    RETURN v_prefixe || '-' || p_exercice::TEXT || '-' || v_seq_txt;
END;
$$;

CREATE INDEX IF NOT EXISTS ix_factures_fournisseur_reference
ON factures (societe_id, tiers_id, exercice, reference)
WHERE type = 'achat' AND COALESCE(est_proforma, FALSE) = FALSE;

CREATE OR REPLACE FUNCTION hisabpro_guard_facture_validee()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_dup INTEGER;
    v_devient_validee BOOLEAN := FALSE;
BEGIN
    -- Les contrôles de complétude (échéance, fournisseur, référence externe)
    -- s'appliquent uniquement au passage brouillon -> définitif. Une mise à jour
    -- technique autorisée d'une facture historique déjà validée (snapshot,
    -- statut de paiement, etc.) ne doit pas être bloquée par des données legacy.
    IF TG_OP = 'INSERT' THEN
        v_devient_validee := COALESCE(NEW.est_proforma, FALSE) = FALSE
                              AND COALESCE(NEW.est_validee, FALSE) = TRUE;
    ELSE
        v_devient_validee := COALESCE(NEW.est_proforma, FALSE) = FALSE
                              AND COALESCE(NEW.est_validee, FALSE) = TRUE
                              AND (
                                  COALESCE(OLD.est_validee, FALSE) = FALSE
                                  OR COALESCE(OLD.est_proforma, FALSE) = TRUE
                              );
    END IF;
    -- Un numéro interne définitif ne doit jamais être réutilisé.
    IF NEW.numero IS NOT NULL THEN
        SELECT f.id INTO v_dup
        FROM factures f
        WHERE f.societe_id = NEW.societe_id
          AND f.numero = NEW.numero
          AND f.id <> COALESCE(NEW.id, -1)
        LIMIT 1;
        IF v_dup IS NOT NULL THEN
            RAISE EXCEPTION 'Numéro de facture interne déjà utilisé : %', NEW.numero;
        END IF;
    END IF;

    IF v_devient_validee THEN
        IF NEW.numero IS NULL OR BTRIM(NEW.numero) = '' THEN
            RAISE EXCEPTION 'Une facture validée doit avoir un numéro interne définitif';
        END IF;
        IF NEW.date_echeance IS NULL THEN
            RAISE EXCEPTION 'Une facture validée doit avoir une date d''échéance';
        END IF;

        -- Pour un achat, la référence est le numéro porté par la facture du fournisseur.
        IF NEW.type::TEXT = 'achat' THEN
            IF NEW.tiers_id IS NULL THEN
                RAISE EXCEPTION 'Une facture fournisseur validée doit être rattachée à un fournisseur';
            END IF;
            IF NEW.reference IS NULL OR BTRIM(NEW.reference) = '' THEN
                RAISE EXCEPTION 'Le numéro de facture fournisseur est obligatoire avant validation';
            END IF;
            SELECT f.id INTO v_dup
            FROM factures f
            WHERE f.societe_id = NEW.societe_id
              AND f.type::TEXT = 'achat'
              AND COALESCE(f.est_proforma, FALSE) = FALSE
              AND COALESCE(f.est_validee, FALSE) = TRUE
              AND f.tiers_id = NEW.tiers_id
              AND f.exercice = NEW.exercice
              AND LOWER(BTRIM(COALESCE(f.reference, ''))) = LOWER(BTRIM(NEW.reference))
              AND f.id <> COALESCE(NEW.id, -1)
            LIMIT 1;
            IF v_dup IS NOT NULL THEN
                RAISE EXCEPTION 'Facture fournisseur en doublon : ce numéro existe déjà pour ce fournisseur sur l''exercice %', NEW.exercice;
            END IF;
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' AND COALESCE(OLD.est_proforma, FALSE) = FALSE AND COALESCE(OLD.est_validee, FALSE) = TRUE THEN
        IF COALESCE(NEW.est_validee, FALSE) = FALSE THEN
            RAISE EXCEPTION 'Une facture validée ne peut pas être repassée en brouillon';
        END IF;
        IF NEW.numero IS DISTINCT FROM OLD.numero
           OR NEW.date IS DISTINCT FROM OLD.date
           OR NEW.exercice IS DISTINCT FROM OLD.exercice
           OR NEW.type IS DISTINCT FROM OLD.type
           OR NEW.tiers_id IS DISTINCT FROM OLD.tiers_id
           OR NEW.tiers IS DISTINCT FROM OLD.tiers
           OR NEW.reference IS DISTINCT FROM OLD.reference
           OR NEW.date_echeance IS DISTINCT FROM OLD.date_echeance
           OR NEW.delai_paiement IS DISTINCT FROM OLD.delai_paiement
           OR NEW.remise_globale IS DISTINCT FROM OLD.remise_globale
           OR NEW.ristourne IS DISTINCT FROM OLD.ristourne
           OR NEW.escompte IS DISTINCT FROM OLD.escompte
           OR NEW.frais_transport_ht IS DISTINCT FROM OLD.frais_transport_ht
           OR NEW.frais_transport_tva IS DISTINCT FROM OLD.frais_transport_tva
           OR NEW.frais_emballage_ht IS DISTINCT FROM OLD.frais_emballage_ht
           OR NEW.frais_emballage_tva IS DISTINCT FROM OLD.frais_emballage_tva
           OR NEW.ras_taux IS DISTINCT FROM OLD.ras_taux
           OR NEW.nature_tva_achat IS DISTINCT FROM OLD.nature_tva_achat
           OR NEW.tva_deductible_pct IS DISTINCT FROM OLD.tva_deductible_pct
        THEN
            RAISE EXCEPTION 'Facture validée : les données de facturation sont immuables. Utilisez un avoir ou un document correctif.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_guard_facture_validee ON factures;
CREATE TRIGGER trg_hisabpro_guard_facture_validee
BEFORE INSERT OR UPDATE ON factures
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_facture_validee();

CREATE OR REPLACE FUNCTION hisabpro_guard_ligne_facture_validee()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_facture_id INTEGER;
    v_validee BOOLEAN;
    v_proforma BOOLEAN;
BEGIN
    v_facture_id := COALESCE(NEW.facture_id, OLD.facture_id);
    SELECT est_validee, COALESCE(est_proforma, FALSE)
      INTO v_validee, v_proforma
    FROM factures WHERE id = v_facture_id;

    IF COALESCE(v_validee, FALSE) = TRUE AND COALESCE(v_proforma, FALSE) = FALSE THEN
        RAISE EXCEPTION 'Facture validée : ses lignes sont immuables. Utilisez un avoir ou un document correctif.';
    END IF;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_guard_ligne_facture_validee ON lignes_facture;
CREATE TRIGGER trg_hisabpro_guard_ligne_facture_validee
BEFORE INSERT OR UPDATE OR DELETE ON lignes_facture
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_ligne_facture_validee();

GRANT SELECT, INSERT, UPDATE ON facturation_sequences TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_reserver_numero_facture(INTEGER, INTEGER, VARCHAR, VARCHAR) TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_guard_facture_validee() TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_guard_ligne_facture_validee() TO hisabpro;

COMMIT;
