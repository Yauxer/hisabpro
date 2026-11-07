-- Lien natif du contrôle IR à son RNI annuel constitué ; aucune ligne ancienne réécrite.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_controles_frais_annuels') IS NULL THEN RAISE EXCEPTION 'Installer 121 avant 122' USING ERRCODE='23514';END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS uq_paie_frais_annuels_societe ON public.paie_controles_frais_annuels(id,societe_id);
CREATE TABLE IF NOT EXISTS public.paie_ir_sources_annuelles (
 ir_id bigint PRIMARY KEY,
 societe_id integer NOT NULL,
 frais_annuels_id bigint NOT NULL,
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 FOREIGN KEY(ir_id,societe_id) REFERENCES public.paie_controles_ir_annuels(id,societe_id),
 FOREIGN KEY(frais_annuels_id,societe_id) REFERENCES public.paie_controles_frais_annuels(id,societe_id)
);
CREATE OR REPLACE FUNCTION public.hisabpro_paie_ir_source122() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE c jsonb;h text;
BEGIN
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Conserver le lien du RNI annuel au contrôle IR' USING ERRCODE='23514';END IF;
 SELECT contenu->'source_frais_annuels' INTO c FROM public.paie_controles_ir_annuels WHERE id=NEW.ir_id AND societe_id=NEW.societe_id AND auteur_id=NEW.auteur_id;
 SELECT empreinte INTO h FROM public.paie_controles_frais_annuels WHERE id=NEW.frais_annuels_id AND societe_id=NEW.societe_id;
 IF (c->>'id'=NEW.frais_annuels_id::text AND c->>'empreinte'=h AND h IS NOT NULL) IS NOT TRUE THEN
  RAISE EXCEPTION 'Lien IR et source annuelle incohérents' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_paie_ir_source_annuelle ON public.paie_ir_sources_annuelles;
CREATE TRIGGER trg_paie_ir_source_annuelle BEFORE INSERT OR UPDATE OR DELETE ON public.paie_ir_sources_annuelles FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_ir_source122();
DROP TRIGGER IF EXISTS trg_paie_ir_source_annuelle_truncate ON public.paie_ir_sources_annuelles;
CREATE TRIGGER trg_paie_ir_source_annuelle_truncate BEFORE TRUNCATE ON public.paie_ir_sources_annuelles FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_ir_source122();
REVOKE ALL ON public.paie_ir_sources_annuelles FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN GRANT SELECT,INSERT ON public.paie_ir_sources_annuelles TO hisabpro;END IF;
END $$;
COMMIT;
