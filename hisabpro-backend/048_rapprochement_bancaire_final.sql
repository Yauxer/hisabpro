-- RAPPROCHEMENT BANCAIRE FINAL — ergonomie + soldes explicites
-- À exécuter APRÈS 047_compta_final_audit.sql.
BEGIN;

ALTER TABLE rapprochement_etats
    ADD COLUMN IF NOT EXISTS solde_initial NUMERIC(18,2) NULL,
    ADD COLUMN IF NOT EXISTS solde_final   NUMERIC(18,2) NULL;

-- Reprise transparente de l'ancien champ unique : il représentait le solde
-- figurant sur le relevé, donc le solde final de la période.
UPDATE rapprochement_etats
   SET solde_final = solde_releve
 WHERE solde_final IS NULL
   AND solde_releve IS NOT NULL;

-- Une fois l'exercice clôturé, le rapprochement fait partie de l'archive
-- comptable : même une requête SQL directe ne doit plus pouvoir l'altérer.
CREATE OR REPLACE FUNCTION hisabpro_guard_rapprochement_exercice_cloture()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_sid INTEGER;
    v_date DATE;
    v_annee INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_sid := OLD.societe_id;
        v_date := OLD.date;
    ELSE
        v_sid := NEW.societe_id;
        v_date := NEW.date;
    END IF;

    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        IF EXISTS (
            SELECT 1 FROM exercices_comptables e
             WHERE e.societe_id = OLD.societe_id
               AND OLD.date BETWEEN e.date_debut AND e.date_fin
               AND e.statut = 'cloture'
        ) OR EXISTS (
            SELECT 1 FROM clotures_exercice c
             WHERE c.societe_id = OLD.societe_id
               AND c.exercice = EXTRACT(YEAR FROM OLD.date)::INTEGER
        ) THEN
            RAISE EXCEPTION 'Exercice clôturé : rapprochement bancaire en lecture seule' USING ERRCODE='23514';
        END IF;
    END IF;

    SELECT e.annee INTO v_annee
      FROM exercices_comptables e
     WHERE e.societe_id = v_sid
       AND v_date BETWEEN e.date_debut AND e.date_fin
     ORDER BY e.date_debut DESC
     LIMIT 1;
    v_annee := COALESCE(v_annee, EXTRACT(YEAR FROM v_date)::INTEGER);

    IF EXISTS (
        SELECT 1 FROM exercices_comptables e
         WHERE e.societe_id = v_sid
           AND v_date BETWEEN e.date_debut AND e.date_fin
           AND e.statut = 'cloture'
    ) OR EXISTS (
        SELECT 1 FROM clotures_exercice c
         WHERE c.societe_id = v_sid
           AND c.exercice = v_annee
    ) THEN
        RAISE EXCEPTION 'Exercice % clôturé : rapprochement bancaire en lecture seule', v_annee USING ERRCODE='23514';
    END IF;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_rapprochement_exercice_cloture ON rapprochement_lignes;
CREATE TRIGGER trg_hisabpro_rapprochement_exercice_cloture
BEFORE INSERT OR UPDATE OR DELETE ON rapprochement_lignes
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_rapprochement_exercice_cloture();

CREATE OR REPLACE FUNCTION hisabpro_guard_rapprochement_etat_cloture()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_sid INTEGER;
    v_debut DATE;
    v_fin DATE;
    v_annee INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_sid := OLD.societe_id;
        v_debut := OLD.date_debut;
        v_fin := OLD.date_fin;
    ELSE
        v_sid := NEW.societe_id;
        v_debut := NEW.date_debut;
        v_fin := NEW.date_fin;
    END IF;

    IF TG_OP IN ('UPDATE', 'DELETE') AND (
        EXISTS (
            SELECT 1 FROM exercices_comptables e
             WHERE e.societe_id = OLD.societe_id
               AND e.date_debut <= OLD.date_fin
               AND e.date_fin >= OLD.date_debut
               AND e.statut = 'cloture'
        ) OR EXISTS (
            SELECT 1 FROM clotures_exercice c
             WHERE c.societe_id = OLD.societe_id
               AND c.exercice BETWEEN EXTRACT(YEAR FROM OLD.date_debut)::INTEGER
                                   AND EXTRACT(YEAR FROM OLD.date_fin)::INTEGER
        )
    ) THEN
        RAISE EXCEPTION 'Exercice clôturé : état de rapprochement en lecture seule' USING ERRCODE='23514';
    END IF;

    IF EXISTS (
        SELECT 1 FROM exercices_comptables e
         WHERE e.societe_id = v_sid
           AND e.date_debut <= v_fin
           AND e.date_fin >= v_debut
           AND e.statut = 'cloture'
    ) OR EXISTS (
        SELECT 1 FROM clotures_exercice c
         WHERE c.societe_id = v_sid
           AND c.exercice BETWEEN EXTRACT(YEAR FROM v_debut)::INTEGER
                               AND EXTRACT(YEAR FROM v_fin)::INTEGER
    ) THEN
        v_annee := EXTRACT(YEAR FROM v_debut)::INTEGER;
        RAISE EXCEPTION 'Exercice % clôturé : état de rapprochement en lecture seule', v_annee USING ERRCODE='23514';
    END IF;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_rapprochement_etat_cloture ON rapprochement_etats;
CREATE TRIGGER trg_hisabpro_rapprochement_etat_cloture
BEFORE INSERT OR UPDATE OR DELETE ON rapprochement_etats
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_rapprochement_etat_cloture();

-- On conserve solde_releve pendant la phase de compatibilité avec les versions
-- antérieures du front. L'API 048 le synchronise désormais avec solde_final.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON rapprochement_etats TO hisabpro;
        GRANT EXECUTE ON FUNCTION hisabpro_guard_rapprochement_exercice_cloture() TO hisabpro;
        GRANT EXECUTE ON FUNCTION hisabpro_guard_rapprochement_etat_cloture() TO hisabpro;
    END IF;
END $$;

COMMIT;
