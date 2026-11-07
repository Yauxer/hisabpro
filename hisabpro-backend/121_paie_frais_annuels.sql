-- Contrôles annuels sourcés, sans actualisation des périodes historiques.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_preparations_fiscales') IS NULL THEN RAISE EXCEPTION 'Installer 120 avant 121' USING ERRCODE='23514';END IF;
END $$;
CREATE TABLE IF NOT EXISTS public.paie_controles_frais_annuels (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL,
 employe_id integer NOT NULL,
 annee integer NOT NULL CHECK(annee=2026),
 cle_idempotence uuid NOT NULL,
 demande_sha256 varchar(64) NOT NULL CHECK(demande_sha256 ~ '^[a-f0-9]{64}$'),
 contenu jsonb NOT NULL CHECK((jsonb_typeof(contenu)='object' AND contenu->>'mode'='CONTROLE_FRAIS_ANNUELS_NON_VALIDE' AND contenu->>'paie_definitive_autorisee'='false' AND contenu->>'statut_reglementaire'='NON_VALIDE_JURIDIQUEMENT' AND contenu->>'annee'=annee::text AND contenu->>'employe_id'=employe_id::text AND jsonb_typeof(contenu->'sources')='array' AND jsonb_array_length(contenu->'sources') BETWEEN 1 AND 12) IS TRUE),
 empreinte varchar(64) NOT NULL CHECK(empreinte ~ '^[a-f0-9]{64}$'),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(employe_id,societe_id) REFERENCES public.personnel_dossiers(employe_id,societe_id),
 UNIQUE(societe_id,cle_idempotence),UNIQUE(id,societe_id,auteur_id)
);
CREATE TABLE IF NOT EXISTS public.paie_controle_frais_sources (
 controle_id bigint NOT NULL,
 societe_id integer NOT NULL,
 preparation_id bigint NOT NULL,
 periode date NOT NULL CHECK(isfinite(periode) AND periode BETWEEN DATE '2026-01-01' AND DATE '2026-12-01' AND extract(day FROM periode)=1),
 auteur_id integer NOT NULL,
 PRIMARY KEY(controle_id,preparation_id),UNIQUE(controle_id,periode),
 FOREIGN KEY(controle_id,societe_id,auteur_id) REFERENCES public.paie_controles_frais_annuels(id,societe_id,auteur_id),
 FOREIGN KEY(preparation_id,societe_id) REFERENCES public.paie_preparations_fiscales(id,societe_id)
);
CREATE OR REPLACE FUNCTION public.hisabpro_paie_frais_source121() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE c jsonb;h text;
BEGIN
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Conserver les sources du contrôle annuel' USING ERRCODE='23514';END IF;
 SELECT contenu INTO c FROM public.paie_controles_frais_annuels WHERE id=NEW.controle_id AND societe_id=NEW.societe_id AND auteur_id=NEW.auteur_id;
 SELECT empreinte INTO h FROM public.paie_preparations_fiscales WHERE id=NEW.preparation_id AND societe_id=NEW.societe_id;
 IF c IS NULL OR h IS NULL OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(c->'sources') x WHERE x->>'preparation_id'=NEW.preparation_id::text AND x->>'periode'=NEW.periode::text AND x->>'empreinte'=h) THEN
  RAISE EXCEPTION 'Source annuelle non prévue ou incohérente' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_paie_frais_annuels ON public.paie_controles_frais_annuels;
CREATE TRIGGER trg_paie_frais_annuels BEFORE INSERT OR UPDATE OR DELETE ON public.paie_controles_frais_annuels FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable();
DROP TRIGGER IF EXISTS trg_paie_frais_annuels_truncate ON public.paie_controles_frais_annuels;
CREATE TRIGGER trg_paie_frais_annuels_truncate BEFORE TRUNCATE ON public.paie_controles_frais_annuels FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable();
DROP TRIGGER IF EXISTS trg_paie_frais_source ON public.paie_controle_frais_sources;
CREATE TRIGGER trg_paie_frais_source BEFORE INSERT OR UPDATE OR DELETE ON public.paie_controle_frais_sources FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_frais_source121();
DROP TRIGGER IF EXISTS trg_paie_frais_source_truncate ON public.paie_controle_frais_sources;
CREATE TRIGGER trg_paie_frais_source_truncate BEFORE TRUNCATE ON public.paie_controle_frais_sources FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_frais_source121();
REVOKE ALL ON public.paie_controles_frais_annuels,public.paie_controle_frais_sources FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.paie_controles_frais_annuels,public.paie_controle_frais_sources TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.paie_controles_frais_annuels_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
