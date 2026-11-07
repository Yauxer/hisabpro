-- Après096, rôle propriétaire. Aucun DML ni création d'exercice historique.
BEGIN;
CREATE OR REPLACE FUNCTION public.hisabpro_verrou_tva_cloture(p_societe INTEGER,p_exercice INTEGER,p_exclusif BOOLEAN)
RETURNS void LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE cle BIGINT; acquis BOOLEAN;
BEGIN
    cle:=hashtextextended('hisabpro:tva-cloture:'||p_societe::text||':'||p_exercice::text,0);
    IF p_exclusif THEN acquis:=pg_try_advisory_xact_lock(cle);
    ELSE acquis:=pg_try_advisory_xact_lock_shared(cle); END IF;
    IF acquis IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'Opération TVA/clôture concurrente : réessayez la transaction.'
            USING ERRCODE='40001',CONSTRAINT='ck_tva_cloture_concurrence';
    END IF;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_proteger_parametres_tva_clotures()
RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    ancien_societe INTEGER; ancien_exercice INTEGER;
    nouveau_societe INTEGER; nouveau_exercice INTEGER;
    exercice_verrouille RECORD; perimetre RECORD;
BEGIN
    IF TG_OP IN ('UPDATE','DELETE') THEN
        ancien_societe:=OLD.societe_id; ancien_exercice:=OLD.exercice;
    END IF;
    IF TG_OP IN ('INSERT','UPDATE') THEN
        nouveau_societe:=NEW.societe_id; nouveau_exercice:=NEW.exercice;
    END IF;
    -- Conserver le verrou de ligne096 et son ordre pour les exercices présents.
    FOR exercice_verrouille IN
        SELECT e.statut FROM public.exercices_comptables e
        WHERE (e.societe_id=ancien_societe AND e.annee=ancien_exercice)
           OR (e.societe_id=nouveau_societe AND e.annee=nouveau_exercice)
        ORDER BY e.societe_id,e.annee FOR SHARE
    LOOP
        IF exercice_verrouille.statut='cloture' THEN
            RAISE EXCEPTION 'Exercice clôturé : paramètres TVA verrouillés.'
                USING ERRCODE='23514',CONSTRAINT='ck_tva_parametres_exercice_ouvert';
        END IF;
    END LOOP;
    -- Protège aussi un périmètre sans ligne. Ne pas attendre un advisory lock
    -- après des verrous de lignes : le conflit annule la transaction à rejouer.
    FOR perimetre IN
        SELECT DISTINCT v.societe,v.exercice
        FROM (VALUES(ancien_societe,ancien_exercice),(nouveau_societe,nouveau_exercice)) v(societe,exercice)
        WHERE v.societe IS NOT NULL ORDER BY v.societe,v.exercice
    LOOP
        PERFORM public.hisabpro_verrou_tva_cloture(perimetre.societe,perimetre.exercice,FALSE);
    END LOOP;
    IF TG_OP IN ('UPDATE','DELETE') THEN
        IF public.hisabpro_tva_exercice_clos(OLD.societe_id,OLD.exercice) THEN
            RAISE EXCEPTION 'Exercice % clôturé : paramètres TVA verrouillés.',OLD.exercice
                USING ERRCODE='23514',CONSTRAINT='ck_tva_parametres_exercice_ouvert';
        END IF;
    END IF;
    IF TG_OP IN ('INSERT','UPDATE') THEN
        IF public.hisabpro_tva_exercice_clos(NEW.societe_id,NEW.exercice) THEN
            RAISE EXCEPTION 'Exercice % clôturé : paramètres TVA verrouillés.',NEW.exercice
                USING ERRCODE='23514',CONSTRAINT='ck_tva_parametres_exercice_ouvert';
        END IF;
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_verrou_trace_tva()
RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    PERFORM e.id FROM public.exercices_comptables e
        WHERE e.societe_id=NEW.societe_id AND e.annee=NEW.exercice FOR SHARE;
    PERFORM public.hisabpro_verrou_tva_cloture(NEW.societe_id,NEW.exercice,TRUE);
    RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_verrou_statut_tva()
RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE ancien_societe INTEGER; ancien_exercice INTEGER;
        nouveau_societe INTEGER; nouveau_exercice INTEGER; perimetre RECORD;
BEGIN
    IF TG_OP IN ('UPDATE','DELETE') THEN
        ancien_societe:=OLD.societe_id;ancien_exercice:=OLD.annee;
    END IF;
    IF TG_OP IN ('INSERT','UPDATE') THEN
        nouveau_societe:=NEW.societe_id;nouveau_exercice:=NEW.annee;
    END IF;
    FOR perimetre IN
        SELECT DISTINCT v.societe,v.exercice
        FROM (VALUES(ancien_societe,ancien_exercice),(nouveau_societe,nouveau_exercice)) v(societe,exercice)
        WHERE v.societe IS NOT NULL ORDER BY v.societe,v.exercice
    LOOP
        PERFORM public.hisabpro_verrou_tva_cloture(perimetre.societe,perimetre.exercice,TRUE);
    END LOOP;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_hisabpro_trace_tva_concurrence ON public.clotures_exercice;
CREATE TRIGGER trg_hisabpro_trace_tva_concurrence BEFORE INSERT ON public.clotures_exercice
    FOR EACH ROW EXECUTE FUNCTION public.hisabpro_verrou_trace_tva();
DROP TRIGGER IF EXISTS trg_hisabpro_statut_tva_concurrence ON public.exercices_comptables;
CREATE TRIGGER trg_hisabpro_statut_tva_concurrence
    BEFORE INSERT OR DELETE OR UPDATE OF statut,societe_id,annee ON public.exercices_comptables
    FOR EACH ROW EXECUTE FUNCTION public.hisabpro_verrou_statut_tva();
DO $$ BEGIN
    IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        GRANT EXECUTE ON FUNCTION public.hisabpro_verrou_tva_cloture(INTEGER,INTEGER,BOOLEAN),
            public.hisabpro_verrou_trace_tva(),public.hisabpro_verrou_statut_tva() TO hisabpro;
    END IF;
END $$;
COMMIT;
