-- Compléments documentaires hors contenu071 ; additif/rejouable et manuel.
BEGIN;
CREATE TABLE IF NOT EXISTS public.liasse_balance_documents (
 id SERIAL PRIMARY KEY,
 societe_id INTEGER NOT NULL REFERENCES public.societes(id),
 preparation_id INTEGER NOT NULL REFERENCES public.liasse_balances_preparation(id),
 empreinte_preparation VARCHAR(64) NOT NULL CHECK (empreinte_preparation ~ '^[a-f0-9]{64}$'),
 cle UUID NOT NULL,
 nom_original VARCHAR(255) NOT NULL CHECK (length(trim(nom_original)) > 0),
 nom_stockage VARCHAR(50) NOT NULL CHECK (nom_stockage ~ '^[a-f0-9]{32}\.(pdf|jpg|jpeg|png|xlsx|xls|doc|docx)$'),
 reference VARCHAR(500) NOT NULL CHECK (length(trim(reference)) > 0),
 taille INTEGER NOT NULL CHECK (taille BETWEEN 1 AND 10485760),
 sha256 VARCHAR(64) NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
 created_by INTEGER NOT NULL REFERENCES public.utilisateurs(id),
 acteur_nom VARCHAR(200),
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT uq_balance_document_cle UNIQUE(societe_id,cle),
 CONSTRAINT uq_balance_document_nom UNIQUE(societe_id,preparation_id,nom_stockage)
);
CREATE INDEX IF NOT EXISTS ix_balance_documents_preparation ON public.liasse_balance_documents(societe_id,preparation_id,id);
CREATE OR REPLACE FUNCTION public.hisabpro_balance_document_liens() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 PERFORM pg_advisory_xact_lock(hashtext('hisabpro_balance_documents'),NEW.societe_id);
 IF NOT EXISTS(SELECT 1 FROM public.liasse_balances_preparation p
   WHERE p.id=NEW.preparation_id AND p.societe_id=NEW.societe_id
   AND p.empreinte_sha256=NEW.empreinte_preparation) THEN
  RAISE EXCEPTION 'Preparation source absente ou empreinte differente' USING ERRCODE='23514';
 END IF;
 SELECT u.nom INTO NEW.acteur_nom FROM public.utilisateurs u WHERE u.id=NEW.created_by AND u.actif
   AND ((u.societe_id=NEW.societe_id AND u.role IN ('admin','comptable')) OR EXISTS(
    SELECT 1 FROM public.utilisateurs_societes us WHERE us.utilisateur_id=u.id
     AND us.societe_id=NEW.societe_id AND us.actif AND us.role IN ('admin','comptable')));
 IF NOT FOUND THEN
  RAISE EXCEPTION 'Acteur documentaire non autorise' USING ERRCODE='23514';
 END IF;
 IF coalesce((SELECT sum(taille) FROM public.liasse_balance_documents
     WHERE societe_id=NEW.societe_id AND preparation_id=NEW.preparation_id),0)+NEW.taille>52428800 THEN
  RAISE EXCEPTION 'Capacite documentaire de cinquante Mo depassee' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END;
$$;
CREATE OR REPLACE FUNCTION public.hisabpro_balance_document_immuable() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
BEGIN
 RAISE EXCEPTION 'Document de preparation immuable : conserver son historique';
END;
$$;
DROP TRIGGER IF EXISTS trg_balance_document_liens ON public.liasse_balance_documents;
CREATE TRIGGER trg_balance_document_liens BEFORE INSERT ON public.liasse_balance_documents
 FOR EACH ROW EXECUTE FUNCTION public.hisabpro_balance_document_liens();
DROP TRIGGER IF EXISTS trg_balance_document_immuable ON public.liasse_balance_documents;
CREATE TRIGGER trg_balance_document_immuable BEFORE UPDATE OR DELETE ON public.liasse_balance_documents
 FOR EACH ROW EXECUTE FUNCTION public.hisabpro_balance_document_immuable();
DROP TRIGGER IF EXISTS trg_balance_document_truncate ON public.liasse_balance_documents;
CREATE TRIGGER trg_balance_document_truncate BEFORE TRUNCATE ON public.liasse_balance_documents
 FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_balance_document_immuable();
REVOKE ALL ON FUNCTION public.hisabpro_balance_document_liens() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.hisabpro_balance_document_immuable() FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.liasse_balance_documents TO hisabpro;
  REVOKE UPDATE,DELETE,TRUNCATE ON public.liasse_balance_documents FROM hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.liasse_balance_documents_id_seq TO hisabpro;
  REVOKE UPDATE ON SEQUENCE public.liasse_balance_documents_id_seq FROM hisabpro;
 END IF;
END $$;
COMMIT;
