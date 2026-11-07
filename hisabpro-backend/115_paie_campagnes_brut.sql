-- Campagnes et simulations du brut uniquement ;aucune validation de paie.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_variables_evenements') IS NULL THEN RAISE EXCEPTION 'Installer114 avant115' USING ERRCODE='23514';END IF;
END $$;
CREATE TABLE IF NOT EXISTS public.paie_campagnes (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 periode date NOT NULL CHECK(isfinite(periode) AND extract(day FROM periode)=1),
 type_campagne varchar(15) NOT NULL CHECK(type_campagne='NORMALE'),
 cree_par integer NOT NULL REFERENCES public.utilisateurs(id),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(societe_id,periode,type_campagne),UNIQUE(id,societe_id)
);
CREATE TABLE IF NOT EXISTS public.paie_simulations_brut (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL,
 campagne_id bigint NOT NULL,
 numero integer NOT NULL CHECK(numero>0),
 cle_idempotence uuid NOT NULL,
 demande_sha256 varchar(64) NOT NULL CHECK(demande_sha256 ~ '^[a-f0-9]{64}$'),
 contenu jsonb NOT NULL CHECK(jsonb_typeof(contenu)='object' AND contenu->>'mode'='SIMULATION_BRUT_NON_VALIDEE' AND contenu->>'paie_definitive_autorisee'='false'),
 empreinte varchar(64) NOT NULL CHECK(empreinte ~ '^[a-f0-9]{64}$'),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(campagne_id,societe_id) REFERENCES public.paie_campagnes(id,societe_id),
 UNIQUE(societe_id,cle_idempotence),UNIQUE(campagne_id,numero)
);
CREATE OR REPLACE FUNCTION public.hisabpro_paie_simulation_immuable() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Conserver campagnes et snapshots ;créer une nouvelle simulation' USING ERRCODE='23514';END IF;
 IF TG_TABLE_NAME='paie_campagnes' THEN
  IF NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.cree_par,false) THEN RAISE EXCEPTION 'Créateur actif de la société requis' USING ERRCODE='23514';END IF;
 ELSE
  IF NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.auteur_id,false) THEN RAISE EXCEPTION 'Auteur actif de la société requis' USING ERRCODE='23514';END IF;
 END IF;
 RETURN NEW;
END $$;
DO $$ DECLARE t text;BEGIN
 FOREACH t IN ARRAY ARRAY['paie_campagnes','paie_simulations_brut'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS trg_paie_simulation ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_paie_simulation BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable()',t);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_paie_simulation_truncate ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_paie_simulation_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_simulation_immuable()',t);
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC',t);
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.paie_campagnes,public.paie_simulations_brut TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.paie_campagnes_id_seq,public.paie_simulations_brut_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
