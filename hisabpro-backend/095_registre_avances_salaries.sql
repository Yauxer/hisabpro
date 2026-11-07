-- Registre facultatif : affectation explicite de lignes 3431 définitives.
-- Aucune écriture ni fiche existante modifiée. Après 094, rôle propriétaire.
BEGIN;
CREATE TABLE IF NOT EXISTS public.grh_avances_affectations (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES public.societes(id),
    employe_id INTEGER NOT NULL,
    ligne_id INTEGER NOT NULL REFERENCES public.lignes_ecriture(id) ON DELETE RESTRICT,
    created_by INTEGER NOT NULL REFERENCES public.utilisateurs(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motif VARCHAR(500) NOT NULL CHECK (length(btrim(motif)) > 0),
    annule_par INTEGER REFERENCES public.utilisateurs(id),
    annule_at TIMESTAMP,
    motif_annulation VARCHAR(500),
    CONSTRAINT fk_avances_employe_societe FOREIGN KEY(employe_id,societe_id)
        REFERENCES public.employes(id,societe_id),
    CONSTRAINT ck_avances_annulation CHECK (
        (annule_par IS NULL AND annule_at IS NULL AND motif_annulation IS NULL) OR
        (annule_par IS NOT NULL AND annule_at IS NOT NULL AND motif_annulation IS NOT NULL AND length(btrim(motif_annulation)) > 0))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_avances_ligne_active
    ON public.grh_avances_affectations(ligne_id) WHERE annule_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_avances_employe ON public.grh_avances_affectations(societe_id,employe_id);

CREATE OR REPLACE FUNCTION public.hisabpro_proteger_affectation_avance()
RETURNS TRIGGER LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE source RECORD;
BEGIN
    IF TG_OP IN ('DELETE','TRUNCATE') THEN
        RAISE EXCEPTION 'Historique des avances conservé' USING ERRCODE='23514';
    END IF;
    IF TG_OP='UPDATE' AND (OLD.annule_at IS NOT NULL OR NEW.annule_at IS NULL OR
       ROW(NEW.id,NEW.societe_id,NEW.employe_id,NEW.ligne_id,NEW.created_by,NEW.created_at,NEW.motif)
       IS DISTINCT FROM ROW(OLD.id,OLD.societe_id,OLD.employe_id,OLD.ligne_id,OLD.created_by,OLD.created_at,OLD.motif)) THEN
        RAISE EXCEPTION 'Seule une annulation traçable est permise' USING ERRCODE='23514';
    END IF;
    IF TG_OP='INSERT' AND NEW.annule_at IS NOT NULL THEN
        RAISE EXCEPTION 'Une nouvelle affectation doit être active' USING ERRCODE='23514';
    END IF;
    -- Même verrou que l'API : sérialise les affectations d'un salarié.
    PERFORM 1 FROM public.employes WHERE id=NEW.employe_id AND societe_id=NEW.societe_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Salarié de la société introuvable' USING ERRCODE='23514';
    END IF;
    SELECT e.societe_id,e.est_validee,e.exercice,l.compte,l.debit,l.credit INTO source
    FROM public.lignes_ecriture l JOIN public.ecritures e ON e.id=l.ecriture_id WHERE l.id=NEW.ligne_id;
    IF NOT FOUND OR source.societe_id<>NEW.societe_id OR source.est_validee IS DISTINCT FROM TRUE OR source.compte<>'3431'
       OR source.debit::text IN ('NaN','Infinity','-Infinity') OR source.credit::text IN ('NaN','Infinity','-Infinity')
       OR source.debit+source.credit<=0 THEN
        RAISE EXCEPTION 'Une ligne 3431 définitive de cette société est requise' USING ERRCODE='23514';
    END IF;
    IF public.hisabpro_tva_exercice_clos(NEW.societe_id,source.exercice) THEN
        RAISE EXCEPTION 'Exercice clôturé : affectation conservée en lecture' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE OR REPLACE FUNCTION public.hisabpro_verifier_solde_avance()
RETURNS TRIGGER LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM (
            SELECT sum(l.debit-l.credit) OVER (ORDER BY e.date,e.id,l.id) AS solde
            FROM public.grh_avances_affectations a
            JOIN public.lignes_ecriture l ON l.id=a.ligne_id
            JOIN public.ecritures e ON e.id=l.ecriture_id
            WHERE a.societe_id=NEW.societe_id AND a.employe_id=NEW.employe_id AND a.annule_at IS NULL
        ) mouvements WHERE solde<0
    ) THEN
        RAISE EXCEPTION 'La récupération dépasse les avances affectées à cette date' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_avances_protection ON public.grh_avances_affectations;
CREATE TRIGGER trg_avances_protection BEFORE INSERT OR UPDATE OR DELETE ON public.grh_avances_affectations
    FOR EACH ROW EXECUTE FUNCTION public.hisabpro_proteger_affectation_avance();
DROP TRIGGER IF EXISTS trg_avances_truncate ON public.grh_avances_affectations;
CREATE TRIGGER trg_avances_truncate BEFORE TRUNCATE ON public.grh_avances_affectations
    FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_proteger_affectation_avance();
DROP TRIGGER IF EXISTS trg_avances_solde ON public.grh_avances_affectations;
CREATE TRIGGER trg_avances_solde AFTER INSERT OR UPDATE ON public.grh_avances_affectations
    FOR EACH ROW EXECUTE FUNCTION public.hisabpro_verifier_solde_avance();
DO $$ BEGIN
    IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        REVOKE ALL ON public.grh_avances_affectations FROM hisabpro;
        GRANT SELECT,INSERT ON public.grh_avances_affectations TO hisabpro;
        GRANT UPDATE(annule_par,annule_at,motif_annulation) ON public.grh_avances_affectations TO hisabpro;
        REVOKE ALL ON SEQUENCE public.grh_avances_affectations_id_seq FROM hisabpro;
        GRANT USAGE,SELECT ON SEQUENCE public.grh_avances_affectations_id_seq TO hisabpro;
        GRANT EXECUTE ON FUNCTION public.hisabpro_proteger_affectation_avance(),public.hisabpro_verifier_solde_avance() TO hisabpro;
    END IF;
END $$;
COMMIT;
