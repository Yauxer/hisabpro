-- Banque RH :réutilise le circuit indépendant,aucun virement ni écriture.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.personnel_coffre_politiques') IS NULL THEN
  RAISE EXCEPTION 'Installer111 avant112' USING ERRCODE='23514';
 END IF;
END $$;
ALTER TABLE public.personnel_demandes DROP CONSTRAINT IF EXISTS personnel_demandes_nature_check;
ALTER TABLE public.personnel_demandes DROP CONSTRAINT IF EXISTS ck_personnel_nature112;
ALTER TABLE public.personnel_demandes ADD CONSTRAINT ck_personnel_nature112 CHECK(nature IN ('DOSSIER','CONTRAT','REMUNERATION','SORTIE','BANQUE'));
CREATE TABLE IF NOT EXISTS public.personnel_banque_versions (
 demande_id integer PRIMARY KEY,
 societe_id integer NOT NULL,
 employe_id integer NOT NULL,
 politique_id bigint NOT NULL,
 piece_id bigint,
 version integer NOT NULL CHECK(version>0),
 date_effet date NOT NULL CHECK(isfinite(date_effet)),
 cle_id varchar(64) NOT NULL CHECK(length(btrim(cle_id))>0),
 contenu_chiffre text NOT NULL CHECK(length(contenu_chiffre)>80),
 masque varchar(20) NOT NULL CHECK(length(masque)>4),
 verification_confirmee boolean NOT NULL DEFAULT false,
 approuvee_par integer REFERENCES public.utilisateurs(id),
 approuvee_at timestamp,
 UNIQUE(societe_id,employe_id,version),
 FOREIGN KEY(demande_id,societe_id,employe_id) REFERENCES public.personnel_demandes(id,societe_id,employe_id),
 FOREIGN KEY(politique_id,societe_id) REFERENCES public.personnel_coffre_politiques(id,societe_id),
 FOREIGN KEY(piece_id,societe_id,employe_id) REFERENCES public.personnel_coffre_pieces(id,societe_id,employe_id),
 CHECK((approuvee_par IS NULL AND approuvee_at IS NULL AND NOT verification_confirmee) OR (approuvee_par IS NOT NULL AND approuvee_at IS NOT NULL AND verification_confirmee))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_personnel_banque_effet ON public.personnel_banque_versions(societe_id,employe_id,date_effet) WHERE approuvee_at IS NOT NULL;
CREATE OR REPLACE FUNCTION public.hisabpro_personnel_banque_immuable()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE d public.personnel_demandes;
BEGIN
 IF TG_OP IN ('DELETE','TRUNCATE') THEN RAISE EXCEPTION 'Conserver les coordonnées bancaires et leur historique' USING ERRCODE='23514';END IF;
 SELECT * INTO d FROM public.personnel_demandes WHERE id=NEW.demande_id AND societe_id=NEW.societe_id AND employe_id=NEW.employe_id;
 IF d.id IS NULL OR d.nature<>'BANQUE' THEN RAISE EXCEPTION 'Demande bancaire correspondante requise' USING ERRCODE='23514';END IF;
 IF TG_OP='INSERT' AND (d.statut<>'BROUILLON' OR NEW.approuvee_at IS NOT NULL) THEN RAISE EXCEPTION 'Créer une proposition bancaire avant validation' USING ERRCODE='23514';END IF;
 IF TG_OP='UPDATE' AND (OLD.approuvee_at IS NOT NULL OR d.statut='REJETE' OR
    (to_jsonb(NEW)-'verification_confirmee'-'approuvee_par'-'approuvee_at') IS DISTINCT FROM (to_jsonb(OLD)-'verification_confirmee'-'approuvee_par'-'approuvee_at')) THEN
  RAISE EXCEPTION 'Proposition bancaire immuable' USING ERRCODE='23514';
 END IF;
 IF NEW.approuvee_at IS NOT NULL AND (d.statut<>'APPROUVE' OR NEW.approuvee_par IS DISTINCT FROM d.decision_par OR NEW.approuvee_at IS DISTINCT FROM d.decision_at OR NOT NEW.verification_confirmee) THEN
  RAISE EXCEPTION 'Contrôle bancaire indépendant requis' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_personnel_banque_immuable ON public.personnel_banque_versions;
CREATE TRIGGER trg_personnel_banque_immuable BEFORE INSERT OR UPDATE OR DELETE ON public.personnel_banque_versions FOR EACH ROW EXECUTE FUNCTION public.hisabpro_personnel_banque_immuable();
DROP TRIGGER IF EXISTS trg_personnel_banque_truncate ON public.personnel_banque_versions;
CREATE TRIGGER trg_personnel_banque_truncate BEFORE TRUNCATE ON public.personnel_banque_versions FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_personnel_banque_immuable();
REVOKE ALL ON public.personnel_banque_versions FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.personnel_banque_versions TO hisabpro;
  GRANT UPDATE(verification_confirmee,approuvee_par,approuvee_at) ON public.personnel_banque_versions TO hisabpro;
 END IF;
END $$;
COMMIT;
