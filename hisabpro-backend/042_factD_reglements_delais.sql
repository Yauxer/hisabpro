-- FACT-D — règlements, encours client et délais de paiement
-- Migration idempotente et rejouable.
BEGIN;

ALTER TABLE factures
    ADD COLUMN IF NOT EXISTS mode_reglement_prevu VARCHAR(20),
    ADD COLUMN IF NOT EXISTS reference_reglement_prevue VARCHAR(100);

-- Les contrôles NOT VALID protègent toutes les nouvelles écritures sans rendre
-- la migration impossible à cause d'une éventuelle donnée legacy à nettoyer.
ALTER TABLE reglements DROP CONSTRAINT IF EXISTS ck_reglements_mode_factd;
ALTER TABLE reglements
    ADD CONSTRAINT ck_reglements_mode_factd
    CHECK (mode IN ('virement','cheque','especes','effet','carte','prelevement','autre')) NOT VALID;

ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_factures_mode_reglement_prevu_factd;
ALTER TABLE factures
    ADD CONSTRAINT ck_factures_mode_reglement_prevu_factd
    CHECK (mode_reglement_prevu IS NULL OR mode_reglement_prevu IN ('virement','cheque','especes','effet','carte','prelevement','autre')) NOT VALID;

ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_factures_delai_paiement_factd;
ALTER TABLE factures
    ADD CONSTRAINT ck_factures_delai_paiement_factd
    CHECK (delai_paiement IS NULL OR (delai_paiement >= 0 AND delai_paiement <= 365)) NOT VALID;

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
           OR NEW.mode_reglement_prevu IS DISTINCT FROM OLD.mode_reglement_prevu
           OR NEW.reference_reglement_prevue IS DISTINCT FROM OLD.reference_reglement_prevue
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

COMMIT;
