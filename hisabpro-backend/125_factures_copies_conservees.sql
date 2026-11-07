-- Copie interne du PDF émis ; aucun statut de facture ou écriture modifié.
BEGIN;
CREATE TABLE IF NOT EXISTS public.factures_copies_conservees (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 facture_id integer NOT NULL REFERENCES public.factures(id),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 document_pdf bytea NOT NULL CHECK(octet_length(document_pdf) BETWEEN 5 AND 10485760 AND substring(document_pdf FROM 1 FOR 5)=decode('255044462d','hex')),
 pdf_sha256 varchar(64) NOT NULL CHECK(pdf_sha256=encode(sha256(document_pdf),'hex')),
 source jsonb NOT NULL CHECK((jsonb_typeof(source)='object' AND source->>'version'='COPIE_FACTURE_923' AND source->>'facture_id'=facture_id::text) IS TRUE),
 source_sha256 varchar(64) NOT NULL CHECK(source_sha256 ~ '^[a-f0-9]{64}$'),
 UNIQUE(societe_id,facture_id),UNIQUE(id,societe_id)
);
CREATE OR REPLACE FUNCTION public.hisabpro_facture_copie125() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Une copie conservée ne peut être remplacée ou supprimée' USING ERRCODE='23514';END IF;
 IF NOT EXISTS(SELECT 1 FROM public.factures f WHERE f.id=NEW.facture_id AND f.societe_id=NEW.societe_id AND f.est_validee AND NOT coalesce(f.est_proforma,false) AND f.type::text='vente' AND f.numero=NEW.source->>'numero' AND f.date::text=NEW.source->>'date') THEN
  RAISE EXCEPTION 'La copie doit provenir d’une facture de vente validée de cette société' USING ERRCODE='23514';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM public.utilisateurs u WHERE u.id=NEW.auteur_id AND u.actif AND
  ((u.societe_id=NEW.societe_id AND u.role IN ('admin','comptable')) OR EXISTS(
   SELECT 1 FROM public.utilisateurs_societes m WHERE m.utilisateur_id=u.id AND m.societe_id=NEW.societe_id AND m.actif AND m.role IN ('admin','comptable')))) THEN
  RAISE EXCEPTION 'Auteur non habilité dans la société' USING ERRCODE='23514';
 END IF;
 NEW.cree_at:=clock_timestamp();
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_facture_copie125 ON public.factures_copies_conservees;
CREATE TRIGGER trg_facture_copie125 BEFORE INSERT OR UPDATE OR DELETE ON public.factures_copies_conservees FOR EACH ROW EXECUTE FUNCTION public.hisabpro_facture_copie125();
DROP TRIGGER IF EXISTS trg_facture_copie125_truncate ON public.factures_copies_conservees;
CREATE TRIGGER trg_facture_copie125_truncate BEFORE TRUNCATE ON public.factures_copies_conservees FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_facture_copie125();
REVOKE ALL ON public.factures_copies_conservees FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.factures_copies_conservees TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.factures_copies_conservees_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
