-- HisabPro094, après093, par le propriétaire des tables.
-- Aucun montant ni historique modifié. Protection des paramètres d'un exercice
-- dont la clôture est déjà visible ; le verrou de concurrence API reste distinct.
BEGIN;

CREATE OR REPLACE FUNCTION public.hisabpro_tva_exercice_clos(p_societe INTEGER, p_exercice INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SET search_path = pg_catalog, public, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.exercices_comptables e
        WHERE e.societe_id=p_societe AND e.annee=p_exercice AND e.statut='cloture'
    ) OR EXISTS (
        SELECT 1 FROM public.clotures_exercice c
        WHERE c.societe_id=p_societe AND c.exercice=p_exercice
    );
$$;

CREATE OR REPLACE FUNCTION public.hisabpro_proteger_parametres_tva_clotures()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp
AS $$
BEGIN
    IF TG_OP IN ('UPDATE','DELETE') THEN
        IF public.hisabpro_tva_exercice_clos(OLD.societe_id,OLD.exercice) THEN
            RAISE EXCEPTION 'Exercice % clôturé : paramètres TVA verrouillés.', OLD.exercice
                USING ERRCODE='23514', CONSTRAINT='ck_tva_parametres_exercice_ouvert';
        END IF;
    END IF;
    IF TG_OP IN ('INSERT','UPDATE') THEN
        IF public.hisabpro_tva_exercice_clos(NEW.societe_id,NEW.exercice) THEN
            RAISE EXCEPTION 'Exercice % clôturé : paramètres TVA verrouillés.', NEW.exercice
                USING ERRCODE='23514', CONSTRAINT='ck_tva_parametres_exercice_ouvert';
        END IF;
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_parametres_tva_clotures ON public.tva_parametres_exercice;
CREATE TRIGGER trg_hisabpro_parametres_tva_clotures
BEFORE INSERT OR UPDATE OR DELETE ON public.tva_parametres_exercice
FOR EACH ROW EXECUTE FUNCTION public.hisabpro_proteger_parametres_tva_clotures();

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        GRANT EXECUTE ON FUNCTION public.hisabpro_tva_exercice_clos(INTEGER,INTEGER),
            public.hisabpro_proteger_parametres_tva_clotures() TO hisabpro;
    END IF;
END;
$$;

COMMIT;
