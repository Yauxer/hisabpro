-- Préparations fiscales reliées au social ; aucune retenue ni paie définitive.
BEGIN;
DO $$ BEGIN
 IF to_regprocedure('public.hisabpro_paie_qualification_ir119()') IS NULL OR to_regclass('public.paie_simulations_sociales') IS NULL THEN
  RAISE EXCEPTION 'Installer 117 et 119 avant 120' USING ERRCODE='23514';
 END IF;
END $$;
CREATE TABLE IF NOT EXISTS public.paie_preparations_fiscales (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL,
 social_id bigint NOT NULL,
 numero integer NOT NULL CHECK(numero>0),
 cle_idempotence uuid NOT NULL,
 demande_sha256 varchar(64) NOT NULL CHECK(demande_sha256 ~ '^[a-f0-9]{64}$'),
 contenu jsonb NOT NULL CHECK((jsonb_typeof(contenu)='object' AND contenu->>'mode'='PREPARATION_BASES_FISCALES_NON_VALIDEE' AND contenu->>'paie_definitive_autorisee'='false' AND contenu->>'statut_reglementaire'='NON_VALIDE_JURIDIQUEMENT' AND contenu->>'social_id'=social_id::text) IS TRUE),
 empreinte varchar(64) NOT NULL CHECK(empreinte ~ '^[a-f0-9]{64}$'),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(social_id,societe_id) REFERENCES public.paie_simulations_sociales(id,societe_id),
 UNIQUE(societe_id,cle_idempotence),UNIQUE(social_id,numero),UNIQUE(id,societe_id)
);
DROP TRIGGER IF EXISTS trg_paie_bases_fiscales ON public.paie_preparations_fiscales;
CREATE TRIGGER trg_paie_bases_fiscales BEFORE INSERT OR UPDATE OR DELETE ON public.paie_preparations_fiscales FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable();
DROP TRIGGER IF EXISTS trg_paie_bases_fiscales_truncate ON public.paie_preparations_fiscales;
CREATE TRIGGER trg_paie_bases_fiscales_truncate BEFORE TRUNCATE ON public.paie_preparations_fiscales FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable();
REVOKE ALL ON public.paie_preparations_fiscales FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.paie_preparations_fiscales TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.paie_preparations_fiscales_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
