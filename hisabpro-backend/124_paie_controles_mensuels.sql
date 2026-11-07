-- Contrôle préparatoire ; aucune retenue, dette, paie définitive ou écriture.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_preparations_fiscales') IS NULL OR to_regprocedure('public.hisabpro_paie_reference123()') IS NULL THEN RAISE EXCEPTION 'Installer120 et123 avant124' USING ERRCODE='23514';END IF;
END $$;
CREATE TABLE IF NOT EXISTS public.paie_controles_mensuels (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL,
 employe_id integer NOT NULL,
 preparation_id bigint NOT NULL,
 periode date NOT NULL CHECK(isfinite(periode) AND periode BETWEEN DATE '2026-01-01' AND DATE '2026-12-01' AND extract(day FROM periode)=1),
 cle_idempotence uuid NOT NULL,
 demande_sha256 varchar(64) NOT NULL CHECK(demande_sha256 ~ '^[a-f0-9]{64}$'),
 contenu jsonb NOT NULL CHECK((jsonb_typeof(contenu)='object' AND contenu->>'mode'='CONTROLE_MENSUEL_PREPARATOIRE' AND contenu->>'paie_definitive_autorisee'='false' AND contenu->>'statut_reglementaire'='NON_VALIDE_JURIDIQUEMENT' AND contenu->>'employe_id'=employe_id::text AND contenu->>'periode'=periode::text) IS TRUE),
 empreinte varchar(64) NOT NULL CHECK(empreinte ~ '^[a-f0-9]{64}$'),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(preparation_id,societe_id) REFERENCES public.paie_preparations_fiscales(id,societe_id),
 FOREIGN KEY(employe_id,societe_id) REFERENCES public.personnel_dossiers(employe_id,societe_id),
 UNIQUE(societe_id,cle_idempotence),UNIQUE(id,societe_id)
);
CREATE OR REPLACE FUNCTION public.hisabpro_paie_mensuel124() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Conserver les contrôles mensuels et leur provenance' USING ERRCODE='23514';END IF;
 IF NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.auteur_id,false) OR NOT EXISTS(
  SELECT 1 FROM public.paie_preparations_fiscales p CROSS JOIN LATERAL jsonb_array_elements(p.contenu->'employes') e
  WHERE p.id=NEW.preparation_id AND p.societe_id=NEW.societe_id AND e->>'employe_id'=NEW.employe_id::text
  AND p.contenu->>'periode'=NEW.periode::text AND p.empreinte=NEW.contenu#>>'{source_preparation,empreinte}'
  AND NEW.contenu#>>'{source_preparation,id}'=NEW.preparation_id::text) THEN
  RAISE EXCEPTION 'Provenance du contrôle mensuel incohérente' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_paie_mensuel124 ON public.paie_controles_mensuels;
CREATE TRIGGER trg_paie_mensuel124 BEFORE INSERT OR UPDATE OR DELETE ON public.paie_controles_mensuels FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_mensuel124();
DROP TRIGGER IF EXISTS trg_paie_mensuel124_truncate ON public.paie_controles_mensuels;
CREATE TRIGGER trg_paie_mensuel124_truncate BEFORE TRUNCATE ON public.paie_controles_mensuels FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_mensuel124();
REVOKE ALL ON public.paie_controles_mensuels FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN GRANT SELECT,INSERT ON public.paie_controles_mensuels TO hisabpro;GRANT USAGE,SELECT ON SEQUENCE public.paie_controles_mensuels_id_seq TO hisabpro;END IF;
END $$;
COMMIT;
