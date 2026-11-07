-- Coffre RH :politiques explicites et pièces chiffrées ;aucune donnée créée.
BEGIN;
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='personnel_contrats_versions' AND column_name='regime_amo') THEN
  RAISE EXCEPTION 'Installer105 à110 avant111' USING ERRCODE='23514';
 END IF;
END $$;
CREATE TABLE IF NOT EXISTS public.personnel_coffre_politiques (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 reference_garde_cles varchar(200) NOT NULL CHECK(length(btrim(reference_garde_cles))>0),
 reference_conservation varchar(200) NOT NULL CHECK(length(btrim(reference_conservation))>0),
 reference_rotation_sauvegarde varchar(200) NOT NULL CHECK(length(btrim(reference_rotation_sauvegarde))>0),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 declaree_par integer NOT NULL REFERENCES public.utilisateurs(id),
 declaree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(id,societe_id)
);
CREATE TABLE IF NOT EXISTS public.personnel_coffre_pieces (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL,
 employe_id integer NOT NULL,
 politique_id bigint NOT NULL,
 categorie varchar(15) NOT NULL CHECK(categorie IN ('contrat','banque','autre')),
 mime varchar(30) NOT NULL CHECK(mime IN ('application/pdf','image/png','image/jpeg')),
 octets integer NOT NULL CHECK(octets>0 AND octets<=4194304),
 cle_id varchar(64) NOT NULL CHECK(length(btrim(cle_id))>0),
 contenu_chiffre text NOT NULL CHECK(length(contenu_chiffre)>80),
 deposee_par integer NOT NULL REFERENCES public.utilisateurs(id),
 deposee_at timestamp NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(id,societe_id,employe_id),
 FOREIGN KEY(employe_id,societe_id) REFERENCES public.personnel_dossiers(employe_id,societe_id),
 FOREIGN KEY(politique_id,societe_id) REFERENCES public.personnel_coffre_politiques(id,societe_id)
);
CREATE INDEX IF NOT EXISTS ix_personnel_coffre_pieces_dossier ON public.personnel_coffre_pieces(societe_id,employe_id,id);
CREATE OR REPLACE FUNCTION public.hisabpro_personnel_coffre_immuable()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP<>'INSERT' THEN
  RAISE EXCEPTION 'Conserver les politiques et pièces du coffre RH' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME='personnel_coffre_politiques' THEN
  IF NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.declaree_par,true) THEN
   RAISE EXCEPTION 'Administrateur actif de la société requis' USING ERRCODE='23514';
  END IF;
 ELSE
  IF NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.deposee_par,false) THEN
   RAISE EXCEPTION 'Déposant actif de la société requis' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END $$;
DO $$ DECLARE t text;BEGIN
 FOREACH t IN ARRAY ARRAY['personnel_coffre_politiques','personnel_coffre_pieces'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS trg_personnel_coffre_immuable ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_personnel_coffre_immuable BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_personnel_coffre_immuable()',t);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_personnel_coffre_truncate ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_personnel_coffre_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_personnel_coffre_immuable()',t);
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC',t);
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.personnel_coffre_politiques,public.personnel_coffre_pieces TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.personnel_coffre_politiques_id_seq,public.personnel_coffre_pieces_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
