-- Personnel 1A.2 : structures uniquement, aucune reprise/activation automatique.
-- Dépend de105 et des clés composites employes (bootstrap/081).
-- Les mutations applicatives seront ouvertes avec le circuit1A.3, pas ici.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.personnel_habilitations') IS NULL OR
    to_regclass('public.personnel_acces_societes') IS NULL THEN
  RAISE EXCEPTION 'Installer105 avant106' USING ERRCODE='23514';
 END IF;
END $$;

-- Espaces de bord ASCII seulement ;casse,espaces internes et zéros conservés.
CREATE OR REPLACE FUNCTION public.hisabpro_personnel_matricule(v text)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog,public,pg_temp AS $$
 SELECT nullif(btrim(v,E' \t\n\r\f\013'),'')
$$;

CREATE TABLE IF NOT EXISTS public.personnel_dossiers (
 employe_id integer PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 matricule_cle varchar(50) NOT NULL CHECK (matricule_cle=public.hisabpro_personnel_matricule(matricule_cle)
                                          AND public.hisabpro_personnel_matricule(matricule_cle) IS NOT NULL),
 origine varchar(24) NOT NULL CHECK (origine IN ('nouveau','historique_a_confirmer')),
 statut varchar(20) NOT NULL DEFAULT 'BROUILLON' CHECK (statut IN ('BROUILLON','A_VALIDER','ACTIF','SUSPENDU','SORTI')),
 revision integer NOT NULL DEFAULT 0 CHECK (revision>=0),
 utilisateur_beneficiaire_id integer REFERENCES public.utilisateurs(id),
 cree_par integer NOT NULL REFERENCES public.utilisateurs(id),
 cree_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT uq_personnel_dossier_societe UNIQUE(employe_id,societe_id),
 CONSTRAINT uq_personnel_matricule_societe UNIQUE(societe_id,matricule_cle),
 FOREIGN KEY(employe_id,societe_id) REFERENCES public.employes(id,societe_id)
);

CREATE TABLE IF NOT EXISTS public.personnel_demandes (
 id serial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 employe_id integer NOT NULL,
 nature varchar(20) NOT NULL CHECK (nature IN ('DOSSIER','CONTRAT','REMUNERATION','SORTIE')),
 revision_attendue integer NOT NULL CHECK (revision_attendue>=0),
 prepare_par integer NOT NULL REFERENCES public.utilisateurs(id),
 beneficiaire_snapshot integer REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK (length(btrim(motif)) BETWEEN 1 AND 500),
 statut varchar(20) NOT NULL DEFAULT 'BROUILLON' CHECK (statut IN ('BROUILLON','SOUMIS','APPROUVE','REJETE')),
 cree_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
 soumis_at timestamp,
 decision_par integer REFERENCES public.utilisateurs(id),
 decision_at timestamp,
 motif_decision varchar(500),
 CONSTRAINT uq_personnel_demande_societe UNIQUE(id,societe_id,employe_id),
 FOREIGN KEY(employe_id,societe_id) REFERENCES public.personnel_dossiers(employe_id,societe_id),
 CHECK ((statut='BROUILLON' AND soumis_at IS NULL AND decision_par IS NULL AND decision_at IS NULL AND motif_decision IS NULL)
 OR (statut='SOUMIS' AND soumis_at IS NOT NULL AND decision_par IS NULL AND decision_at IS NULL AND motif_decision IS NULL)
 OR (statut IN ('APPROUVE','REJETE') AND soumis_at IS NOT NULL AND decision_par IS NOT NULL AND decision_at IS NOT NULL AND decision_at>=soumis_at
     AND decision_par<>prepare_par AND (beneficiaire_snapshot IS NULL OR decision_par<>beneficiaire_snapshot)
     AND motif_decision IS NOT NULL AND length(btrim(motif_decision)) BETWEEN 1 AND 500)),
 CHECK (soumis_at IS NULL OR soumis_at>=cree_at)
);

-- Une version approuvée s'applique de sa date d'effet (incluse) jusqu'à la
-- prochaine version approuvée (exclue). Aucun ancien montant/date réécrit.
-- Les dates de contrat sont des données déclarées, distinctes des bornes de version.
CREATE TABLE IF NOT EXISTS public.personnel_contrats_versions (
 id serial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 employe_id integer NOT NULL,
 demande_id integer NOT NULL,
 version integer NOT NULL CHECK (version>0),
 date_effet date NOT NULL CHECK (isfinite(date_effet)),
 type_contrat varchar(40) NOT NULL CHECK (length(btrim(type_contrat))>0),
 date_debut date NOT NULL CHECK (isfinite(date_debut)),
 date_fin date CHECK (isfinite(date_fin)),
 reference_justificatif varchar(200) NOT NULL CHECK (length(btrim(reference_justificatif))>0),
 approuvee_par integer REFERENCES public.utilisateurs(id),
 approuvee_at timestamp,
 UNIQUE(id,societe_id,employe_id),
 UNIQUE(societe_id,employe_id,version),
 UNIQUE(demande_id),
 FOREIGN KEY(demande_id,societe_id,employe_id) REFERENCES public.personnel_demandes(id,societe_id,employe_id),
 CHECK (date_fin IS NULL OR date_fin>=date_debut),
 CHECK (date_effet>=date_debut AND (date_fin IS NULL OR date_effet<=date_fin)),
 CHECK ((approuvee_par IS NULL)=(approuvee_at IS NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_personnel_contrat_effet
 ON public.personnel_contrats_versions(societe_id,employe_id,date_effet) WHERE approuvee_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.personnel_remunerations_versions (
 id serial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 employe_id integer NOT NULL,
 demande_id integer NOT NULL,
 contrat_version_id integer NOT NULL,
 version integer NOT NULL CHECK (version>0),
 composant varchar(30) NOT NULL DEFAULT 'SALAIRE_BASE' CHECK (composant='SALAIRE_BASE'),
 date_effet date NOT NULL CHECK (isfinite(date_effet)),
 montant numeric(18,2) NOT NULL CHECK (montant>=0 AND montant<'Infinity'::numeric AND montant<>'NaN'::numeric),
 periodicite varchar(15) NOT NULL CHECK (periodicite IN ('mensuelle','journaliere','horaire')),
 devise varchar(3) NOT NULL DEFAULT 'MAD' CHECK (devise='MAD'),
 reference_justificatif varchar(200) NOT NULL CHECK (length(btrim(reference_justificatif))>0),
 approuvee_par integer REFERENCES public.utilisateurs(id),
 approuvee_at timestamp,
 UNIQUE(societe_id,employe_id,composant,version),
 UNIQUE(demande_id),
 FOREIGN KEY(demande_id,societe_id,employe_id) REFERENCES public.personnel_demandes(id,societe_id,employe_id),
 FOREIGN KEY(contrat_version_id,societe_id,employe_id) REFERENCES public.personnel_contrats_versions(id,societe_id,employe_id),
 CHECK ((approuvee_par IS NULL)=(approuvee_at IS NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_personnel_remuneration_effet
 ON public.personnel_remunerations_versions(societe_id,employe_id,composant,date_effet) WHERE approuvee_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.personnel_evenements (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 employe_id integer NOT NULL,
 demande_id integer,
 revision integer NOT NULL CHECK (revision>=0),
 nature varchar(60) NOT NULL CHECK (length(btrim(nature))>0),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK (length(btrim(motif)) BETWEEN 1 AND 500),
 cree_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(employe_id,societe_id) REFERENCES public.personnel_dossiers(employe_id,societe_id),
 FOREIGN KEY(demande_id,societe_id,employe_id) REFERENCES public.personnel_demandes(id,societe_id,employe_id)
);

CREATE OR REPLACE FUNCTION public.hisabpro_personnel_integrite_dossier()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE cle text; s integer; e integer;
BEGIN
 IF TG_OP IN ('DELETE','TRUNCATE') THEN
  RAISE EXCEPTION 'Conserver le dossier et son historique Personnel' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME='employes' THEN
  cle:=public.hisabpro_personnel_matricule(NEW.matricule);s:=NEW.societe_id;e:=NEW.id;
 ELSE
  cle:=NEW.matricule_cle;s:=NEW.societe_id;e:=NEW.employe_id;
 END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('hisabpro:personnel:matricule:'||s||':'||coalesce(cle,''),0));
 IF TG_TABLE_NAME='employes' THEN
  IF EXISTS(SELECT 1 FROM public.personnel_dossiers d WHERE d.societe_id=s AND d.matricule_cle=cle AND d.employe_id<>e)
   OR EXISTS(SELECT 1 FROM public.personnel_dossiers d WHERE d.employe_id=e AND (d.societe_id<>s OR d.matricule_cle IS DISTINCT FROM cle)) THEN
   RAISE EXCEPTION 'Matricule lié à un dossier Personnel :modification contrôlée requise' USING ERRCODE='23514';
  END IF;
 ELSE
  IF TG_OP='UPDATE' AND ROW(NEW.employe_id,NEW.societe_id,NEW.matricule_cle,NEW.origine,NEW.cree_par,NEW.cree_at)
   IS DISTINCT FROM ROW(OLD.employe_id,OLD.societe_id,OLD.matricule_cle,OLD.origine,OLD.cree_par,OLD.cree_at) THEN
   RAISE EXCEPTION 'Origine et identité du dossier conservées' USING ERRCODE='23514';
  END IF;
  IF NOT EXISTS(SELECT 1 FROM public.employes x WHERE x.id=e AND x.societe_id=s
      AND public.hisabpro_personnel_matricule(x.matricule)=cle)
   OR EXISTS(SELECT 1 FROM public.employes x WHERE x.societe_id=s AND x.id<>e
      AND public.hisabpro_personnel_matricule(x.matricule)=cle) THEN
   RAISE EXCEPTION 'Matricule manquant ou ambigu :aucune reprise automatique' USING ERRCODE='23514';
  END IF;
  IF (TG_OP='INSERT' AND NOT public.hisabpro_personnel_membre(s,NEW.cree_par,false))
   OR ((TG_OP='INSERT' OR NEW.utilisateur_beneficiaire_id IS DISTINCT FROM OLD.utilisateur_beneficiaire_id)
       AND NEW.utilisateur_beneficiaire_id IS NOT NULL AND NOT public.hisabpro_personnel_membre(s,NEW.utilisateur_beneficiaire_id,false)) THEN
   RAISE EXCEPTION 'Acteur ou bénéficiaire hors société' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_personnel_conserver_versions()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE d public.personnel_demandes; beneficiaire integer;
BEGIN
 IF TG_OP IN ('DELETE','TRUNCATE') OR TG_TABLE_NAME='personnel_evenements' AND TG_OP='UPDATE' THEN
  RAISE EXCEPTION 'Historique Personnel conservé' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME='personnel_demandes' THEN
  IF TG_OP='UPDATE' AND (OLD.statut IN ('APPROUVE','REJETE') OR
      (OLD.statut='SOUMIS' AND ROW(NEW.id,NEW.societe_id,NEW.employe_id,NEW.nature,NEW.revision_attendue,
       NEW.prepare_par,NEW.beneficiaire_snapshot,NEW.motif,NEW.cree_at,NEW.soumis_at)
       IS DISTINCT FROM ROW(OLD.id,OLD.societe_id,OLD.employe_id,OLD.nature,OLD.revision_attendue,
       OLD.prepare_par,OLD.beneficiaire_snapshot,OLD.motif,OLD.cree_at,OLD.soumis_at))) THEN
   RAISE EXCEPTION 'Demande soumise ou décidée figée' USING ERRCODE='23514';
  END IF;
  SELECT utilisateur_beneficiaire_id INTO beneficiaire FROM public.personnel_dossiers
   WHERE employe_id=NEW.employe_id AND societe_id=NEW.societe_id;
  IF NEW.beneficiaire_snapshot IS DISTINCT FROM beneficiaire OR
     NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.prepare_par,false) OR
     (NEW.decision_par IS NOT NULL AND (NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.decision_par,false)
       OR NEW.decision_par=beneficiaire)) THEN
   RAISE EXCEPTION 'Acteur indépendant de la société requis' USING ERRCODE='23514';
  END IF;
 ELSIF TG_TABLE_NAME='personnel_evenements' THEN
  IF NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.auteur_id,false) THEN
   RAISE EXCEPTION 'Auteur actif de la société requis' USING ERRCODE='23514';
  END IF;
 ELSE
  IF TG_OP='UPDATE' AND OLD.approuvee_at IS NOT NULL THEN
   RAISE EXCEPTION 'Version approuvée immuable' USING ERRCODE='23514';
  END IF;
  SELECT * INTO d FROM public.personnel_demandes WHERE id=NEW.demande_id AND societe_id=NEW.societe_id AND employe_id=NEW.employe_id;
  IF TG_OP='UPDATE' THEN
   IF ROW(NEW.id,NEW.societe_id,NEW.employe_id,NEW.demande_id,NEW.version)
      IS DISTINCT FROM ROW(OLD.id,OLD.societe_id,OLD.employe_id,OLD.demande_id,OLD.version)
    OR d.statut='REJETE' OR (d.statut IN ('SOUMIS','APPROUVE') AND
       (to_jsonb(NEW)-'approuvee_par'-'approuvee_at') IS DISTINCT FROM (to_jsonb(OLD)-'approuvee_par'-'approuvee_at')) THEN
    RAISE EXCEPTION 'Identité de version et contenu soumis conservés' USING ERRCODE='23514';
   END IF;
  END IF;
  IF d.id IS NOT NULL AND (d.nature<>CASE WHEN TG_TABLE_NAME='personnel_contrats_versions' THEN 'CONTRAT' ELSE 'REMUNERATION' END
   OR (NEW.approuvee_at IS NOT NULL AND (d.statut<>'APPROUVE' OR NEW.approuvee_par IS DISTINCT FROM d.decision_par
                                       OR NEW.approuvee_at IS DISTINCT FROM d.decision_at))) THEN
   RAISE EXCEPTION 'Version non liée à la décision correspondante' USING ERRCODE='23514';
  END IF;
  IF TG_TABLE_NAME='personnel_remunerations_versions' THEN
   IF NEW.approuvee_at IS NOT NULL AND NOT EXISTS(
    SELECT 1 FROM public.personnel_contrats_versions c WHERE c.id=NEW.contrat_version_id
     AND c.societe_id=NEW.societe_id AND c.employe_id=NEW.employe_id AND c.approuvee_at IS NOT NULL
     AND c.date_effet<=NEW.date_effet AND (c.date_fin IS NULL OR NEW.date_effet<=c.date_fin)) THEN
    RAISE EXCEPTION 'Contrat approuvé applicable requis' USING ERRCODE='23514';
   END IF;
  END IF;
 END IF;
 RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_personnel_employe_matricule ON public.employes;
CREATE TRIGGER trg_personnel_employe_matricule BEFORE INSERT OR UPDATE OF id,societe_id,matricule ON public.employes
 FOR EACH ROW EXECUTE FUNCTION public.hisabpro_personnel_integrite_dossier();
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['personnel_dossiers','personnel_demandes','personnel_contrats_versions','personnel_remunerations_versions','personnel_evenements'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS trg_personnel_integrite ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_personnel_integrite BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.%I()',
   t,CASE WHEN t='personnel_dossiers' THEN 'hisabpro_personnel_integrite_dossier' ELSE 'hisabpro_personnel_conserver_versions' END);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_personnel_truncate ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_personnel_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.%I()',
   t,CASE WHEN t='personnel_dossiers' THEN 'hisabpro_personnel_integrite_dossier' ELSE 'hisabpro_personnel_conserver_versions' END);
 END LOOP;
END $$;

CREATE OR REPLACE VIEW public.personnel_remunerations_periodes AS
 SELECT r.*,lead(date_effet) OVER(PARTITION BY societe_id,employe_id,composant ORDER BY date_effet) AS date_fin_effet_exclue
 FROM public.personnel_remunerations_versions r WHERE approuvee_at IS NOT NULL;
CREATE OR REPLACE VIEW public.personnel_contrats_periodes AS
 SELECT c.*,lead(date_effet) OVER(PARTITION BY societe_id,employe_id ORDER BY date_effet) AS date_fin_effet_exclue
 FROM public.personnel_contrats_versions c WHERE approuvee_at IS NOT NULL;

DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['personnel_dossiers','personnel_demandes','personnel_contrats_versions','personnel_remunerations_versions','personnel_evenements','personnel_remunerations_periodes','personnel_contrats_periodes'] LOOP
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC',t);
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  FOREACH t IN ARRAY ARRAY['personnel_dossiers','personnel_demandes','personnel_contrats_versions','personnel_remunerations_versions','personnel_evenements','personnel_remunerations_periodes','personnel_contrats_periodes'] LOOP
   EXECUTE format('REVOKE ALL ON public.%I FROM hisabpro',t);
   EXECUTE format('GRANT SELECT ON public.%I TO hisabpro',t);
  END LOOP;
 END IF;
END $$;
COMMIT;
