-- Lot1A.3, après105/106. Aucune activation, reprise ou habilitation implicite.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.personnel_evenements') IS NULL OR to_regclass('public.personnel_habilitations') IS NULL THEN
  RAISE EXCEPTION 'Installer105 et106 avant107' USING ERRCODE='23514';
 END IF;
END $$;

-- Un brouillon sans rémunération connue ne reçoit pas un faux salaire zéro.
ALTER TABLE public.employes ALTER COLUMN salaire_brut DROP NOT NULL;
ALTER TABLE public.personnel_dossiers ADD COLUMN IF NOT EXISTS beneficiaire_sans_compte_confirme boolean NOT NULL DEFAULT false;
ALTER TABLE public.personnel_dossiers ADD COLUMN IF NOT EXISTS reference_beneficiaire varchar(200);
ALTER TABLE public.personnel_dossiers ADD COLUMN IF NOT EXISTS date_sortie_approuvee date;
ALTER TABLE public.personnel_demandes ADD COLUMN IF NOT EXISTS independance_confirmee boolean NOT NULL DEFAULT false;
ALTER TABLE public.personnel_demandes ADD COLUMN IF NOT EXISTS reference_independance varchar(200);

DO $$ DECLARE c record; BEGIN
 FOR c IN SELECT conname FROM pg_constraint WHERE conrelid='public.personnel_habilitations'::regclass
  AND contype='c' AND conname IN ('personnel_habilitations_capacite_check','ck_personnel_capacites107') LOOP
  EXECUTE format('ALTER TABLE public.personnel_habilitations DROP CONSTRAINT %I',c.conname);
 END LOOP;
 ALTER TABLE public.personnel_habilitations ADD CONSTRAINT ck_personnel_capacites107 CHECK(capacite IN (
  'personnel.lire_identite','personnel.lire_remuneration','personnel.lire_identifiants_sensibles','personnel.audit_lire',
  'personnel.proposer','personnel.soumettre','personnel.approuver'));
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='public.personnel_dossiers'::regclass AND conname='ck_personnel_sortie107') THEN
  ALTER TABLE public.personnel_dossiers ADD CONSTRAINT ck_personnel_sortie107 CHECK(date_sortie_approuvee IS NULL OR isfinite(date_sortie_approuvee));
 END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.personnel_demandes_details (
 demande_id integer PRIMARY KEY,
 societe_id integer NOT NULL,
 employe_id integer NOT NULL,
 contenu jsonb NOT NULL CHECK(jsonb_typeof(contenu)='object'),
 FOREIGN KEY(demande_id,societe_id,employe_id) REFERENCES public.personnel_demandes(id,societe_id,employe_id)
);

CREATE OR REPLACE FUNCTION public.hisabpro_personnel_workflow_integrite()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE etat text; rev integer;
BEGIN
 IF TG_TABLE_NAME='personnel_demandes_details' THEN
  IF TG_OP<>'INSERT' THEN
   RAISE EXCEPTION 'Proposition conservée :créer une nouvelle demande' USING ERRCODE='23514';
  END IF;
  SELECT statut INTO etat FROM public.personnel_demandes WHERE id=NEW.demande_id AND societe_id=NEW.societe_id AND employe_id=NEW.employe_id;
  IF etat IS DISTINCT FROM 'BROUILLON' THEN
   RAISE EXCEPTION 'Contenu requis avant soumission' USING ERRCODE='23514';
  END IF;
 ELSE
  IF TG_OP='INSERT' THEN
   IF NEW.statut<>'BROUILLON' THEN
    RAISE EXCEPTION 'Créer une demande brouillon avant toute décision' USING ERRCODE='23514';
   END IF;
  ELSE
   IF NOT ((OLD.statut='BROUILLON' AND NEW.statut='SOUMIS') OR
           (OLD.statut='SOUMIS' AND NEW.statut IN ('APPROUVE','REJETE'))) THEN
    RAISE EXCEPTION 'Transition Personnel interdite' USING ERRCODE='23514';
   END IF;
   IF NOT EXISTS(SELECT 1 FROM public.personnel_demandes_details WHERE demande_id=NEW.id AND societe_id=NEW.societe_id AND employe_id=NEW.employe_id) THEN
    RAISE EXCEPTION 'Proposition typée manquante' USING ERRCODE='23514';
   END IF;
   SELECT revision INTO rev FROM public.personnel_dossiers WHERE employe_id=NEW.employe_id AND societe_id=NEW.societe_id FOR UPDATE;
   IF NEW.statut<>'REJETE' AND NEW.revision_attendue<>rev THEN
    RAISE EXCEPTION 'Révision Personnel périmée' USING ERRCODE='23514';
   END IF;
   IF NEW.statut IN ('APPROUVE','REJETE') AND (NOT NEW.independance_confirmee OR NEW.reference_independance IS NULL OR length(btrim(NEW.reference_independance)) NOT BETWEEN 1 AND 200) THEN
    RAISE EXCEPTION 'Confirmation indépendante et référence requises' USING ERRCODE='23514';
   END IF;
  END IF;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_personnel_workflow107 ON public.personnel_demandes;
CREATE TRIGGER trg_personnel_workflow107 BEFORE INSERT OR UPDATE ON public.personnel_demandes FOR EACH ROW
 EXECUTE FUNCTION public.hisabpro_personnel_workflow_integrite();
DROP TRIGGER IF EXISTS trg_personnel_details107 ON public.personnel_demandes_details;
CREATE TRIGGER trg_personnel_details107 BEFORE INSERT OR UPDATE OR DELETE ON public.personnel_demandes_details FOR EACH ROW
 EXECUTE FUNCTION public.hisabpro_personnel_workflow_integrite();
DROP TRIGGER IF EXISTS trg_personnel_details_truncate107 ON public.personnel_demandes_details;
CREATE TRIGGER trg_personnel_details_truncate107 BEFORE TRUNCATE ON public.personnel_demandes_details FOR EACH STATEMENT
 EXECUTE FUNCTION public.hisabpro_personnel_workflow_integrite();

REVOKE ALL ON public.personnel_demandes_details FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.personnel_dossiers,public.personnel_demandes,public.personnel_contrats_versions,
   public.personnel_remunerations_versions,public.personnel_evenements,public.personnel_demandes_details TO hisabpro;
  GRANT UPDATE(statut,revision,date_sortie_approuvee) ON public.personnel_dossiers TO hisabpro;
  GRANT UPDATE(statut,soumis_at,decision_par,decision_at,motif_decision,independance_confirmee,reference_independance) ON public.personnel_demandes TO hisabpro;
  GRANT UPDATE(approuvee_par,approuvee_at) ON public.personnel_contrats_versions,public.personnel_remunerations_versions TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.personnel_demandes_id_seq,public.personnel_contrats_versions_id_seq,
   public.personnel_remunerations_versions_id_seq,public.personnel_evenements_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
