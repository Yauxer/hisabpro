-- Association déclarée, pas qualification fiscale d'un groupe. Installation explicite.
BEGIN;
CREATE TABLE IF NOT EXISTS public.societes_liees (
 id serial PRIMARY KEY,
 vendeur_id integer NOT NULL REFERENCES public.societes(id),
 acheteur_id integer NOT NULL REFERENCES public.societes(id),
 client_id integer NOT NULL REFERENCES public.tiers(id),
 fournisseur_id integer NOT NULL REFERENCES public.tiers(id),
 cle uuid NOT NULL,
 justification varchar(500) NOT NULL CHECK(length(btrim(justification))>0),
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now(),
 CHECK(vendeur_id<>acheteur_id), UNIQUE(vendeur_id,cle)
);
CREATE TABLE IF NOT EXISTS public.societes_liees_retraits (
 id serial PRIMARY KEY,
 liaison_id integer NOT NULL UNIQUE REFERENCES public.societes_liees(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION public.hisabpro_societes_liees_controle()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE s integer; l record;
BEGIN
 IF TG_TABLE_NAME='societes_liees' THEN
  -- Sérialiser création/retrait d'une même paire, y compris sous LOGIN SQL.
  PERFORM pg_advisory_xact_lock(LEAST(NEW.vendeur_id,NEW.acheteur_id),GREATEST(NEW.vendeur_id,NEW.acheteur_id));
  IF NOT EXISTS(SELECT 1 FROM public.tiers WHERE id=NEW.client_id AND societe_id=NEW.vendeur_id AND type IN ('client','les_deux') AND actif)
   OR NOT EXISTS(SELECT 1 FROM public.tiers WHERE id=NEW.fournisseur_id AND societe_id=NEW.acheteur_id AND type IN ('fournisseur','les_deux') AND actif)
  THEN RAISE EXCEPTION 'Tiers de liaison étrangers, inactifs ou incompatibles' USING ERRCODE='23514'; END IF;
  IF EXISTS(SELECT 1 FROM public.societes_liees x WHERE x.vendeur_id=NEW.vendeur_id AND x.acheteur_id=NEW.acheteur_id
    AND NOT EXISTS(SELECT 1 FROM public.societes_liees_retraits r WHERE r.liaison_id=x.id))
  THEN RAISE EXCEPTION 'Liaison active déjà présente' USING ERRCODE='23505'; END IF;
 ELSE
  SELECT * INTO l FROM public.societes_liees WHERE id=NEW.liaison_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Liaison absente' USING ERRCODE='23514'; END IF;
  PERFORM pg_advisory_xact_lock(LEAST(l.vendeur_id,l.acheteur_id),GREATEST(l.vendeur_id,l.acheteur_id));
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION public.hisabpro_societes_liees_controle() FROM PUBLIC;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['societes_liees','societes_liees_retraits'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS trg_societes_liees_insert ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_societes_liees_insert BEFORE INSERT ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_societes_liees_controle()',t);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_societes_liees_immutable ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_societes_liees_immutable BEFORE UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_trace_immutable()',t);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_societes_liees_truncate ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_societes_liees_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_ras_trace_immutable()',t);
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.societes_liees,public.societes_liees_retraits TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.societes_liees_id_seq,public.societes_liees_retraits_id_seq TO hisabpro;
  REVOKE UPDATE,DELETE,TRUNCATE ON public.societes_liees,public.societes_liees_retraits FROM hisabpro;
  GRANT EXECUTE ON FUNCTION public.hisabpro_societes_liees_controle() TO hisabpro;
 END IF;
END $$;
COMMIT;
