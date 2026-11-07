-- Après097. Sérialisation du Journal avec la clôture488 ; aucun DML historique.
BEGIN;
CREATE OR REPLACE FUNCTION public.hisabpro_verifier_journal_ouvert(p_societe INTEGER,p_exercice INTEGER)
RETURNS void LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    -- Même clé que l'API de clôture, verrou transactionnel partagé sans attente.
    -- La clôture peut créer ses propres écritures sous son verrou exclusif.
    PERFORM public.hisabpro_verrou_tva_cloture(p_societe,p_exercice,FALSE);
    IF public.hisabpro_tva_exercice_clos(p_societe,p_exercice) THEN
        RAISE EXCEPTION 'Exercice clôturé : Journal verrouillé.'
            USING ERRCODE='23514',CONSTRAINT='ck_journal_exercice_ouvert';
    END IF;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_verrou_entete_journal()
RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE ancien_societe INTEGER; ancien_exercice INTEGER;
        nouveau_societe INTEGER; nouveau_exercice INTEGER; perimetre RECORD;
BEGIN
    IF TG_OP IN ('UPDATE','DELETE') THEN
        ancien_societe:=OLD.societe_id; ancien_exercice:=OLD.exercice;
    END IF;
    IF TG_OP IN ('INSERT','UPDATE') THEN
        nouveau_societe:=NEW.societe_id; nouveau_exercice:=NEW.exercice;
    END IF;
    FOR perimetre IN
        SELECT DISTINCT v.societe,v.exercice
        FROM (VALUES(ancien_societe,ancien_exercice),(nouveau_societe,nouveau_exercice)) v(societe,exercice)
        WHERE v.societe IS NOT NULL ORDER BY v.societe,v.exercice
    LOOP
        PERFORM public.hisabpro_verifier_journal_ouvert(perimetre.societe,perimetre.exercice);
    END LOOP;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_verrou_lignes_journal()
RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE ancien_parent INTEGER; nouveau_parent INTEGER; parent RECORD;
BEGIN
    IF TG_OP IN ('UPDATE','DELETE') THEN ancien_parent:=OLD.ecriture_id; END IF;
    IF TG_OP IN ('INSERT','UPDATE') THEN nouveau_parent:=NEW.ecriture_id; END IF;
    -- Même ordre de parents que072. Le verrou interdit qu'un déplacement du
    -- parent change son périmètre après cette lecture. Lors d'un DELETE CASCADE,
    -- le parent disparu a déjà été protégé par le trigger d'en-tête.
    FOR parent IN
        SELECT e.id,e.societe_id,e.exercice FROM public.ecritures e
        WHERE e.id IN (ancien_parent,nouveau_parent) ORDER BY e.id FOR UPDATE
    LOOP
        PERFORM public.hisabpro_verifier_journal_ouvert(parent.societe_id,parent.exercice);
    END LOOP;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;

-- Avant les contrôles existants, qui restent tous installés et inchangés.
DROP TRIGGER IF EXISTS trg_00_hisabpro_journal_cloture ON public.ecritures;
CREATE TRIGGER trg_00_hisabpro_journal_cloture BEFORE INSERT OR UPDATE OR DELETE ON public.ecritures
    FOR EACH ROW EXECUTE FUNCTION public.hisabpro_verrou_entete_journal();
DROP TRIGGER IF EXISTS trg_00_hisabpro_lignes_cloture ON public.lignes_ecriture;
CREATE TRIGGER trg_00_hisabpro_lignes_cloture BEFORE INSERT OR UPDATE OR DELETE ON public.lignes_ecriture
    FOR EACH ROW EXECUTE FUNCTION public.hisabpro_verrou_lignes_journal();
DO $$ BEGIN
    IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        GRANT EXECUTE ON FUNCTION public.hisabpro_verifier_journal_ouvert(INTEGER,INTEGER),
            public.hisabpro_verrou_entete_journal(),public.hisabpro_verrou_lignes_journal() TO hisabpro;
    END IF;
END $$;
COMMIT;
