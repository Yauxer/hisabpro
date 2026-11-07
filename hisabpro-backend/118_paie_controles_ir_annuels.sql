-- Contrôle annuel pédagogique, ni retenue mensuelle ni liquidation définitive.
BEGIN;
DO $$ BEGIN
 IF to_regprocedure('public.hisabpro_paie_simulation_immuable()') IS NULL THEN RAISE EXCEPTION 'Installer le socle paie avant118' USING ERRCODE='23514';END IF;
END $$;
CREATE TABLE IF NOT EXISTS public.paie_controles_ir_annuels (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 annee integer NOT NULL CHECK(annee=2026),
 cle_idempotence uuid NOT NULL,
 demande_sha256 varchar(64) NOT NULL CHECK(demande_sha256 ~ '^[a-f0-9]{64}$'),
 contenu jsonb NOT NULL CHECK((jsonb_typeof(contenu)='object' AND contenu->>'mode'='CONTROLE_IR_ANNUEL_NON_VALIDE' AND contenu->>'paie_definitive_autorisee'='false' AND contenu->>'statut_reglementaire'='NON_VALIDE_JURIDIQUEMENT' AND contenu->>'annee'=annee::text) IS TRUE),
 empreinte varchar(64) NOT NULL CHECK(empreinte ~ '^[a-f0-9]{64}$'),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(societe_id,cle_idempotence),UNIQUE(id,societe_id)
);
DROP TRIGGER IF EXISTS trg_paie_ir_annuel ON public.paie_controles_ir_annuels;
CREATE TRIGGER trg_paie_ir_annuel BEFORE INSERT OR UPDATE OR DELETE ON public.paie_controles_ir_annuels FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable();
DROP TRIGGER IF EXISTS trg_paie_ir_annuel_truncate ON public.paie_controles_ir_annuels;
CREATE TRIGGER trg_paie_ir_annuel_truncate BEFORE TRUNCATE ON public.paie_controles_ir_annuels FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable();
REVOKE ALL ON public.paie_controles_ir_annuels FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.paie_controles_ir_annuels TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.paie_controles_ir_annuels_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
