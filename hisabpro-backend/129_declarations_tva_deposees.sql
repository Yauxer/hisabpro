-- Déclarations TVA déposées figées. Additive et rejouable.
-- Une déclaration déposée n'est jamais modifiée ni supprimée : seule une
-- rectificative peut la marquer « remplacee ». Aucun historique n'est créé ici.
-- À exécuter avec le rôle de migration, après sauvegarde.
BEGIN;
CREATE TABLE IF NOT EXISTS public.declarations_tva_deposees (
    id                  serial PRIMARY KEY,
    societe_id          integer NOT NULL REFERENCES public.societes(id),
    exercice            integer NOT NULL,
    periodicite         varchar(15) NOT NULL,
    date_debut          date NOT NULL,
    date_fin            date NOT NULL,
    collectee           numeric(18,2) NOT NULL,
    recuperable         numeric(18,2) NOT NULL,
    credit_anterieur    numeric(18,2) NOT NULL,
    tva_due             numeric(18,2) NOT NULL,
    credit_tva          numeric(18,2) NOT NULL,
    snapshot            json NOT NULL,
    date_depot          date NOT NULL,
    reference_depot     varchar(100) NOT NULL,
    motif_rectification text,
    remplace_id         integer REFERENCES public.declarations_tva_deposees(id),
    statut              varchar(10) NOT NULL DEFAULT 'active',
    deposee_par         integer REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    created_at          timestamp DEFAULT now(),
    CONSTRAINT ck_decl_tva_periodicite129 CHECK (periodicite IN ('mensuelle','trimestrielle')),
    CONSTRAINT ck_decl_tva_statut129 CHECK (statut IN ('active','remplacee')),
    CONSTRAINT ck_decl_tva_depot_apres_periode129 CHECK (date_depot > date_fin),
    CONSTRAINT ck_decl_tva_reference129 CHECK (length(trim(reference_depot)) > 0),
    CONSTRAINT ck_decl_tva_motif_rectificative129 CHECK (
        remplace_id IS NULL OR length(trim(coalesce(motif_rectification,''))) > 0)
);
CREATE INDEX IF NOT EXISTS ix_declarations_tva_deposees_societe_id ON public.declarations_tva_deposees(societe_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_decl_tva_active129
    ON public.declarations_tva_deposees(societe_id, date_debut, date_fin) WHERE statut = 'active';

CREATE OR REPLACE FUNCTION public.hisabpro_proteger_declaration_tva_deposee()
RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Déclaration TVA déposée % : suppression interdite.', OLD.id USING ERRCODE = '23514';
    END IF;
    -- Seul le passage active -> remplacee est admis, sans autre changement.
    IF OLD.statut = 'active' AND NEW.statut = 'remplacee'
       AND (to_jsonb(NEW) - 'statut') = (to_jsonb(OLD) - 'statut') THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'Déclaration TVA déposée % : modification interdite (déposer une rectificative).', OLD.id
        USING ERRCODE = '23514';
END $$;

DROP TRIGGER IF EXISTS trg_proteger_declaration_tva_deposee129 ON public.declarations_tva_deposees;
CREATE TRIGGER trg_proteger_declaration_tva_deposee129
    BEFORE UPDATE OR DELETE ON public.declarations_tva_deposees
    FOR EACH ROW EXECUTE FUNCTION public.hisabpro_proteger_declaration_tva_deposee();

DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') AND current_user <> 'hisabpro' THEN
  GRANT SELECT, INSERT, UPDATE ON public.declarations_tva_deposees TO hisabpro;
  GRANT USAGE, SELECT ON SEQUENCE public.declarations_tva_deposees_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
