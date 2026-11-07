-- Additif : aucun changement de facture ou d'historique de migration029.
-- Une suppression du parent pouvait contourner la garde de ses lignes.
BEGIN;

CREATE OR REPLACE FUNCTION public.hisabpro_guard_suppression_facture_definitive()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF COALESCE(OLD.est_validee, FALSE) AND NOT COALESCE(OLD.est_proforma, FALSE) THEN
        RAISE EXCEPTION 'Une facture definitive ne peut pas etre supprimee. Utilisez un avoir ou un document correctif.'
            USING ERRCODE = '23514';
    END IF;
    RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS trg_facture_definitive_no_delete ON public.factures;
CREATE TRIGGER trg_facture_definitive_no_delete
    BEFORE DELETE ON public.factures
    FOR EACH ROW EXECUTE FUNCTION public.hisabpro_guard_suppression_facture_definitive();

COMMIT;
