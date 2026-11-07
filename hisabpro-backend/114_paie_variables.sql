-- Variables exactes et traçables ;aucun bulletin,paiement ni écriture généré.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_rubrique_versions') IS NULL THEN RAISE EXCEPTION 'Installer113 avant114' USING ERRCODE='23514';END IF;
END $$;
CREATE TABLE IF NOT EXISTS public.paie_variables (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL,
 employe_id integer NOT NULL,
 rubrique_id bigint NOT NULL,
 rubrique_version_id bigint NOT NULL,
 contrat_version_id integer NOT NULL,
 remuneration_version_id integer NOT NULL REFERENCES public.personnel_remunerations_versions(id),
 beneficiaire_snapshot integer REFERENCES public.utilisateurs(id),
 periode date NOT NULL CHECK(isfinite(periode) AND extract(day FROM periode)=1),
 annee integer NOT NULL CHECK(annee=extract(year FROM periode)),
 date_effet date NOT NULL CHECK(isfinite(date_effet) AND date_trunc('month',date_effet)::date=periode),
 periodicite varchar(12) NOT NULL CHECK(periodicite IN ('mensuelle','ponctuelle','annuelle')),
 mode varchar(15) NOT NULL CHECK(mode IN ('MONTANT','QUANTITE_TAUX')),
 montant numeric(18,2) NOT NULL CHECK(montant>=0 AND montant<'Infinity'::numeric AND montant<>'NaN'::numeric),
 donnees jsonb NOT NULL CHECK(jsonb_typeof(donnees)='object'),
 instantane jsonb NOT NULL CHECK(jsonb_typeof(instantane)='object'),
 source_reference varchar(200) NOT NULL CHECK(length(btrim(source_reference))>0),
 prepare_par integer NOT NULL REFERENCES public.utilisateurs(id),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 statut varchar(12) NOT NULL DEFAULT 'BROUILLON' CHECK(statut IN ('BROUILLON','SOUMIS','APPROUVE','REJETE','ANNULE')),
 soumise_at timestamp,
 decision_par integer REFERENCES public.utilisateurs(id),
 decision_at timestamp,
 reference_controle varchar(200),
 justificatifs_verifies boolean NOT NULL DEFAULT false,
 FOREIGN KEY(employe_id,societe_id) REFERENCES public.personnel_dossiers(employe_id,societe_id),
 FOREIGN KEY(rubrique_id,societe_id) REFERENCES public.paie_rubriques(id,societe_id),
 FOREIGN KEY(rubrique_version_id,societe_id) REFERENCES public.paie_rubrique_versions(id,societe_id),
 FOREIGN KEY(contrat_version_id,societe_id,employe_id) REFERENCES public.personnel_contrats_versions(id,societe_id,employe_id),
 UNIQUE(id,societe_id),
 CHECK((statut IN ('BROUILLON','SOUMIS') AND decision_par IS NULL AND decision_at IS NULL AND reference_controle IS NULL AND NOT justificatifs_verifies)
  OR(statut IN ('APPROUVE','REJETE','ANNULE') AND decision_par IS NOT NULL AND decision_at IS NOT NULL AND length(btrim(reference_controle))>0)),
 CHECK(statut<>'SOUMIS' OR soumise_at IS NOT NULL),
 CHECK(statut<>'APPROUVE' OR (decision_par<>prepare_par AND decision_par IS DISTINCT FROM beneficiaire_snapshot AND justificatifs_verifies AND soumise_at IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_paie_variable_source ON public.paie_variables(societe_id,employe_id,periode,rubrique_id,source_reference) WHERE statut IN ('BROUILLON','SOUMIS','APPROUVE');
CREATE UNIQUE INDEX IF NOT EXISTS uq_paie_variable_mensuelle ON public.paie_variables(societe_id,employe_id,periode,rubrique_id) WHERE periodicite='mensuelle' AND statut IN ('BROUILLON','SOUMIS','APPROUVE');
CREATE UNIQUE INDEX IF NOT EXISTS uq_paie_variable_annuelle ON public.paie_variables(societe_id,employe_id,annee,rubrique_id) WHERE periodicite='annuelle' AND statut IN ('BROUILLON','SOUMIS','APPROUVE');
CREATE TABLE IF NOT EXISTS public.paie_variables_evenements (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL,
 variable_id bigint NOT NULL,
 statut varchar(12) NOT NULL CHECK(statut IN ('BROUILLON','SOUMIS','APPROUVE','REJETE','ANNULE')),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(variable_id,societe_id) REFERENCES public.paie_variables(id,societe_id)
);
CREATE OR REPLACE FUNCTION public.hisabpro_paie_variable_integrite() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP IN ('DELETE','TRUNCATE') THEN RAISE EXCEPTION 'Conserver variables et historique' USING ERRCODE='23514';END IF;
 IF TG_TABLE_NAME='paie_variables_evenements' THEN
  IF TG_OP<>'INSERT' OR NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.auteur_id,false)
   OR NOT EXISTS(SELECT 1 FROM public.paie_variables v WHERE v.id=NEW.variable_id AND v.societe_id=NEW.societe_id AND v.statut=NEW.statut) THEN
   RAISE EXCEPTION 'Événement de variable append-only et correspondant requis' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
 END IF;
 IF TG_OP='INSERT' THEN
  IF NEW.statut<>'BROUILLON' OR NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.prepare_par,false)
   OR NOT EXISTS(SELECT 1 FROM public.personnel_dossiers d WHERE d.employe_id=NEW.employe_id AND d.societe_id=NEW.societe_id AND NEW.beneficiaire_snapshot IS NOT DISTINCT FROM d.utilisateur_beneficiaire_id)
   OR NOT EXISTS(SELECT 1 FROM public.paie_rubrique_versions r WHERE r.id=NEW.rubrique_version_id AND r.rubrique_id=NEW.rubrique_id AND r.societe_id=NEW.societe_id AND r.statut='APPROUVEE')
   OR NOT EXISTS(SELECT 1 FROM public.personnel_remunerations_versions r WHERE r.id=NEW.remuneration_version_id AND r.employe_id=NEW.employe_id AND r.societe_id=NEW.societe_id AND r.contrat_version_id=NEW.contrat_version_id AND r.approuvee_at IS NOT NULL) THEN
   RAISE EXCEPTION 'Brouillon et sources approuvées de la même société requis' USING ERRCODE='23514';
  END IF;
 ELSE
  IF OLD.statut NOT IN ('BROUILLON','SOUMIS') OR
   (to_jsonb(NEW)-ARRAY['statut','soumise_at','decision_par','decision_at','reference_controle','justificatifs_verifies']) IS DISTINCT FROM
   (to_jsonb(OLD)-ARRAY['statut','soumise_at','decision_par','decision_at','reference_controle','justificatifs_verifies']) THEN
    RAISE EXCEPTION 'Variable immuable,créer une nouvelle proposition traçable' USING ERRCODE='23514';
  END IF;
  IF NOT ((OLD.statut='BROUILLON' AND NEW.statut IN ('SOUMIS','ANNULE')) OR (OLD.statut='SOUMIS' AND NEW.statut IN ('APPROUVE','REJETE'))) THEN
   RAISE EXCEPTION 'Transition de variable interdite' USING ERRCODE='23514';
  END IF;
  IF OLD.statut='SOUMIS' AND NEW.soumise_at IS DISTINCT FROM OLD.soumise_at THEN RAISE EXCEPTION 'Soumission immuable' USING ERRCODE='23514';END IF;
  IF NEW.statut='ANNULE' AND NEW.decision_par<>NEW.prepare_par THEN RAISE EXCEPTION 'Annulation de brouillon réservée au préparateur' USING ERRCODE='23514';END IF;
  IF NEW.decision_par IS NOT NULL AND NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.decision_par,false) THEN RAISE EXCEPTION 'Décideur actif requis' USING ERRCODE='23514';END IF;
  IF NEW.statut='APPROUVE' AND NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.prepare_par,false) THEN RAISE EXCEPTION 'Préparateur actif requis avant approbation' USING ERRCODE='23514';END IF;
 END IF;
 RETURN NEW;
END $$;
DO $$ DECLARE t text;BEGIN
 FOREACH t IN ARRAY ARRAY['paie_variables','paie_variables_evenements'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS trg_paie_variable ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_paie_variable BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_variable_integrite()',t);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_paie_variable_truncate ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_paie_variable_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_variable_integrite()',t);
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC',t);
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.paie_variables,public.paie_variables_evenements TO hisabpro;
  GRANT UPDATE(statut,soumise_at,decision_par,decision_at,reference_controle,justificatifs_verifies) ON public.paie_variables TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.paie_variables_id_seq,public.paie_variables_evenements_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
