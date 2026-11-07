-- Simulations sociales pédagogiques immuables ; aucune paie définitive.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_branche_sociale_versions') IS NULL OR to_regclass('public.paie_simulations_brut') IS NULL THEN
  RAISE EXCEPTION 'Installer115 et116 avant117' USING ERRCODE='23514';
 END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS uq_paie_simulation_brut_societe ON public.paie_simulations_brut(id,societe_id);
CREATE TABLE IF NOT EXISTS public.paie_simulations_sociales (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL,
 brut_id bigint NOT NULL,
 regime varchar(80) NOT NULL CHECK(regime ~ '^[A-Z][A-Z0-9_]{1,79}$'),
 numero integer NOT NULL CHECK(numero>0),
 cle_idempotence uuid NOT NULL,
 demande_sha256 varchar(64) NOT NULL CHECK(demande_sha256 ~ '^[a-f0-9]{64}$'),
 contenu jsonb NOT NULL CHECK((jsonb_typeof(contenu)='object' AND contenu->>'mode'='SIMULATION_SOCIALE_NON_VALIDEE' AND contenu->>'paie_definitive_autorisee'='false' AND contenu->>'statut_reglementaire'='NON_VALIDE_JURIDIQUEMENT') IS TRUE),
 empreinte varchar(64) NOT NULL CHECK(empreinte ~ '^[a-f0-9]{64}$'),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(brut_id,societe_id) REFERENCES public.paie_simulations_brut(id,societe_id),
 UNIQUE(societe_id,cle_idempotence),UNIQUE(brut_id,regime,numero),UNIQUE(id,societe_id)
);
DROP TRIGGER IF EXISTS trg_paie_social_snapshot ON public.paie_simulations_sociales;
CREATE TRIGGER trg_paie_social_snapshot BEFORE INSERT OR UPDATE OR DELETE ON public.paie_simulations_sociales FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable();
DROP TRIGGER IF EXISTS trg_paie_social_snapshot_truncate ON public.paie_simulations_sociales;
CREATE TRIGGER trg_paie_social_snapshot_truncate BEFORE TRUNCATE ON public.paie_simulations_sociales FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable();
REVOKE ALL ON public.paie_simulations_sociales FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.paie_simulations_sociales TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.paie_simulations_sociales_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
