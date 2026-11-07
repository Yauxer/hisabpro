-- Catalogue vide ;aucun taux,barème ou exonération présumé. Migration additive.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.personnel_banque_versions') IS NULL OR to_regprocedure('public.hisabpro_personnel_membre(integer,integer,boolean)') IS NULL THEN
  RAISE EXCEPTION 'Installer le socle Personnel105 à112 avant113' USING ERRCODE='23514';
 END IF;
END $$;
-- Capacité dédiée à l'expert réglementaire ;aucune attribution automatique.
ALTER TABLE public.personnel_habilitations DROP CONSTRAINT IF EXISTS ck_personnel_capacites107;
ALTER TABLE public.personnel_habilitations ADD CONSTRAINT ck_personnel_capacites107 CHECK(capacite IN (
 'personnel.lire_identite','personnel.lire_remuneration','personnel.lire_identifiants_sensibles','personnel.audit_lire',
 'personnel.proposer','personnel.soumettre','personnel.approuver','personnel.valider_regles_paie'));
CREATE TABLE IF NOT EXISTS public.paie_rubriques (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 code varchar(40) NOT NULL CHECK(code ~ '^[A-Z][A-Z0-9_]{1,39}$'),
 cree_par integer NOT NULL REFERENCES public.utilisateurs(id),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(societe_id,code),UNIQUE(id,societe_id)
);
CREATE TABLE IF NOT EXISTS public.paie_rubrique_versions (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL,
 rubrique_id bigint NOT NULL,
 numero integer NOT NULL CHECK(numero>0),
 contenu jsonb NOT NULL CHECK(jsonb_typeof(contenu)='object' AND contenu ? 'regles' AND (contenu->'regles') ?& ARRAY['IR','CNSS','AMO']),
 date_debut date NOT NULL CHECK(isfinite(date_debut)),
 date_fin date CHECK(isfinite(date_fin) AND date_fin>=date_debut),
 statut varchar(12) NOT NULL DEFAULT 'PROPOSEE' CHECK(statut IN ('PROPOSEE','APPROUVEE','REJETEE')),
 prepare_par integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 decision_par integer REFERENCES public.utilisateurs(id),
 decision_at timestamp,
 motif_decision varchar(500),
 reference_controle varchar(200),
 verification_reglementaire_confirmee boolean NOT NULL DEFAULT false,
 FOREIGN KEY(rubrique_id,societe_id) REFERENCES public.paie_rubriques(id,societe_id),
 UNIQUE(rubrique_id,numero),UNIQUE(id,societe_id),
 CHECK((statut='PROPOSEE' AND decision_par IS NULL AND decision_at IS NULL AND motif_decision IS NULL AND reference_controle IS NULL AND NOT verification_reglementaire_confirmee)
 OR (statut<>'PROPOSEE' AND decision_par IS NOT NULL AND decision_at IS NOT NULL AND length(btrim(motif_decision))>0 AND length(btrim(reference_controle))>0)),
 CHECK(statut<>'APPROUVEE' OR decision_par<>prepare_par)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_paie_rubrique_effet ON public.paie_rubrique_versions(rubrique_id,date_debut) WHERE statut='APPROUVEE';
CREATE OR REPLACE FUNCTION public.hisabpro_paie_catalogue_immuable() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP IN ('DELETE','TRUNCATE') THEN RAISE EXCEPTION 'Conserver le catalogue et ses versions' USING ERRCODE='23514';END IF;
 IF TG_TABLE_NAME='paie_rubriques' THEN
  IF TG_OP<>'INSERT' OR NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.cree_par,false) THEN RAISE EXCEPTION 'Rubrique immuable,acteur de la société requis' USING ERRCODE='23514';END IF;
 ELSE
  IF TG_OP='INSERT' THEN
   IF NEW.statut<>'PROPOSEE' OR NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.prepare_par,false) THEN RAISE EXCEPTION 'Proposition par acteur actif requise' USING ERRCODE='23514';END IF;
  ELSE
   IF OLD.statut<>'PROPOSEE' OR NEW.statut='PROPOSEE' OR
    (to_jsonb(NEW)-ARRAY['statut','decision_par','decision_at','motif_decision','reference_controle','verification_reglementaire_confirmee']) IS DISTINCT FROM
    (to_jsonb(OLD)-ARRAY['statut','decision_par','decision_at','motif_decision','reference_controle','verification_reglementaire_confirmee']) THEN
     RAISE EXCEPTION 'Version de rubrique immuable' USING ERRCODE='23514';
   END IF;
   IF NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.decision_par,false) OR
    (NEW.statut='APPROUVEE' AND NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.prepare_par,false)) THEN
     RAISE EXCEPTION 'Acteur actif de la société requis' USING ERRCODE='23514';
   END IF;
   IF NEW.statut='APPROUVEE' AND EXISTS(
    SELECT 1 FROM jsonb_each(NEW.contenu->'regles') r WHERE r.value->>'statut_reglementaire'='VALIDE') THEN
    IF NOT NEW.verification_reglementaire_confirmee OR NOT EXISTS(
     SELECT 1 FROM public.personnel_habilitations h WHERE h.societe_id=NEW.societe_id AND h.utilisateur_id=NEW.decision_par
     AND h.capacite='personnel.valider_regles_paie' AND h.revoquee_at IS NULL AND h.liaison_id_snapshot IS NOT DISTINCT FROM (
      SELECT a.id FROM public.utilisateurs u LEFT JOIN public.utilisateurs_societes a ON a.utilisateur_id=u.id AND a.societe_id=NEW.societe_id AND a.actif AND u.societe_id<>NEW.societe_id WHERE u.id=NEW.decision_par)) THEN
      RAISE EXCEPTION 'Vérification réglementaire et habilitation dédiée requises' USING ERRCODE='23514';
    END IF;
   END IF;
  END IF;
 END IF;
 RETURN NEW;
END $$;
DO $$ DECLARE t text;BEGIN
 FOREACH t IN ARRAY ARRAY['paie_rubriques','paie_rubrique_versions'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS trg_paie_catalogue ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_paie_catalogue BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_catalogue_immuable()',t);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_paie_catalogue_truncate ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_paie_catalogue_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_catalogue_immuable()',t);
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC',t);
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.paie_rubriques,public.paie_rubrique_versions TO hisabpro;
  GRANT UPDATE(statut,decision_par,decision_at,motif_decision,reference_controle,verification_reglementaire_confirmee) ON public.paie_rubrique_versions TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.paie_rubriques_id_seq,public.paie_rubrique_versions_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
