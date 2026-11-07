-- Garde-fous complémentaires après 038, sans modification des données historiques.
-- Avis CNC n°24, §2.3 (irréversibilité) et §2.5 (équilibre par écriture).
-- Annonce officielle : https://www.finances.gov.ma/fr/pages/detail-actualite.aspx?fiche=6558
-- Document signé : https://oecrsk.ma/docs/finance-compta/avis%2024%20CNC%20traitement%20informatique.pdf
BEGIN;

CREATE OR REPLACE FUNCTION hisabpro_proteger_lignes_ecriture_definitive()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_ancienne INTEGER;
    v_nouvelle INTEGER;
    v_parent RECORD;
BEGIN
    IF TG_OP <> 'INSERT' THEN v_ancienne := OLD.ecriture_id; END IF;
    IF TG_OP <> 'DELETE' THEN v_nouvelle := NEW.ecriture_id; END IF;

    -- Contrôler les deux parents lors d'un déplacement. Le verrou sérialise une
    -- modification du brouillon avec sa validation concurrente ; l'ordre des
    -- identifiants évite des verrous croisés lors de déplacements opposés.
    FOR v_parent IN
        SELECT id, numero_ecriture, est_validee
          FROM ecritures
         WHERE id IN (v_ancienne, v_nouvelle)
         ORDER BY id
         FOR UPDATE
    LOOP
        IF v_parent.numero_ecriture IS NOT NULL OR v_parent.est_validee THEN
            RAISE EXCEPTION
                'Lignes de l''écriture définitive % : % interdit. Utilisez une contrepassation.',
                v_parent.id, TG_OP
                USING ERRCODE = '23514';
        END IF;
    END LOOP;

    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION hisabpro_verifier_equilibre_definitif()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_definitive BOOLEAN;
    v_debit NUMERIC;
    v_credit NUMERIC;
    v_non_finies INTEGER;
BEGIN
    SELECT est_validee OR numero_ecriture IS NOT NULL
      INTO v_definitive
      FROM ecritures WHERE id = NEW.id;
    IF NOT COALESCE(v_definitive, FALSE) THEN RETURN NULL; END IF;

    SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0),
           COUNT(*) FILTER (WHERE debit::TEXT IN ('NaN', 'Infinity', '-Infinity')
                               OR credit::TEXT IN ('NaN', 'Infinity', '-Infinity'))
      INTO v_debit, v_credit, v_non_finies
      FROM lignes_ecriture WHERE ecriture_id = NEW.id;

    IF v_non_finies > 0 OR v_debit <= 0 OR v_credit <= 0 OR v_debit <> v_credit THEN
        RAISE EXCEPTION 'Écriture % : débit et crédit positifs, finis et équilibrés requis (% / %).',
            NEW.id, v_debit, v_credit
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

-- Différé jusqu'à la fin de transaction : toutes les lignes du brouillon sont
-- disponibles, et une validation refusée annule aussi sa numérotation.
DROP TRIGGER IF EXISTS trg_hisabpro_equilibre_definitif ON ecritures;
CREATE CONSTRAINT TRIGGER trg_hisabpro_equilibre_definitif
AFTER INSERT OR UPDATE ON ecritures
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION hisabpro_verifier_equilibre_definitif();

COMMIT;
