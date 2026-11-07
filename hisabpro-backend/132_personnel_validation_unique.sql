-- Validation par une seule personne pour les petites entreprises (lot 974). Additive et rejouable.
-- Par défaut rien ne change : préparateur et décideur doivent être distincts.
-- Si l'administrateur active le mode pour sa société (motif conservé), le même compte
-- peut préparer puis décider ; son identité reste enregistrée à chaque étape.
-- Un salarié ne peut jamais décider sur ses propres données (règles 106/114 inchangées).
-- À exécuter avec le rôle de migration, après sauvegarde, après 113, 114 et 116.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_rubrique_versions') IS NULL OR to_regclass('public.paie_variables') IS NULL OR to_regclass('public.personnel_demandes') IS NULL
    OR to_regclass('public.paie_branche_sociale_versions') IS NULL THEN
  RAISE EXCEPTION 'Installer 113, 114 et 116 avant 132' USING ERRCODE='23514';
 END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.personnel_validation_unique (
 societe_id integer PRIMARY KEY REFERENCES public.societes(id),
 active boolean NOT NULL DEFAULT true,
 activee_par integer NOT NULL REFERENCES public.utilisateurs(id),
 activee_at timestamp NOT NULL DEFAULT clock_timestamp(),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 desactivee_par integer REFERENCES public.utilisateurs(id),
 desactivee_at timestamp,
 CHECK(active OR (desactivee_par IS NOT NULL AND desactivee_at IS NOT NULL))
);

CREATE OR REPLACE FUNCTION public.hisabpro_validation_unique(s integer) RETURNS boolean
LANGUAGE sql STABLE SET search_path=pg_catalog,public,pg_temp AS $$
 SELECT EXISTS(SELECT 1 FROM public.personnel_validation_unique WHERE societe_id=s AND active)
$$;

CREATE OR REPLACE FUNCTION public.hisabpro_validation_unique132() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP IN ('DELETE','TRUNCATE') THEN RAISE EXCEPTION 'Conserver la trace du mode de validation' USING ERRCODE='23514';END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_validation_unique132 ON public.personnel_validation_unique;
CREATE TRIGGER trg_validation_unique132 BEFORE DELETE ON public.personnel_validation_unique FOR EACH ROW EXECUTE FUNCTION public.hisabpro_validation_unique132();
DROP TRIGGER IF EXISTS trg_validation_unique132_truncate ON public.personnel_validation_unique;
CREATE TRIGGER trg_validation_unique132_truncate BEFORE TRUNCATE ON public.personnel_validation_unique FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_validation_unique132();

-- Les contrôles « décideur différent du préparateur » deviennent conditionnels : la clause est
-- retirée des contraintes existantes (le reste de chaque contrainte est conservé à l'identique),
-- puis réimposée par le déclencheur ci-dessous sauf validation unique activée.
DO $$ DECLARE c record; def text; reste text; BEGIN
 FOR c IN SELECT oid, conrelid::regclass AS t, conname FROM pg_constraint
   WHERE contype='c' AND conrelid IN ('public.paie_rubrique_versions'::regclass,'public.paie_branche_sociale_versions'::regclass,
                                      'public.paie_variables'::regclass,'public.personnel_demandes'::regclass)
     AND pg_get_constraintdef(oid) LIKE '%decision_par <> prepare_par%'
 LOOP
  def := pg_get_constraintdef(c.oid);
  reste := replace(def, '(decision_par <> prepare_par) AND ', '');
  IF c.t::text IN ('personnel_demandes','paie_variables','public.personnel_demandes','public.paie_variables')
     AND (reste = def OR reste LIKE '%decision_par <> prepare_par%') THEN
   RAISE EXCEPTION 'Contrainte % inattendue : migration 132 arrêtée sans modification', c.conname USING ERRCODE='23514';
  END IF;
  EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', c.t, c.conname);
  IF reste <> def AND reste NOT LIKE '%decision_par <> prepare_par%' THEN
   EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I %s', c.t, left(c.conname, 50) || '_132', reste);
  END IF;
 END LOOP;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_decideur132() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF NEW.statut IN ('APPROUVEE','APPROUVE') OR (TG_TABLE_NAME='personnel_demandes' AND NEW.statut='REJETE') THEN NULL; ELSE RETURN NEW; END IF;
 IF NEW.decision_par=NEW.prepare_par
    AND NOT public.hisabpro_validation_unique(NEW.societe_id) THEN
  RAISE EXCEPTION 'Décideur différent du préparateur requis (validation unique non activée)' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_decideur132 ON public.paie_rubrique_versions;
CREATE TRIGGER trg_decideur132 BEFORE INSERT OR UPDATE ON public.paie_rubrique_versions FOR EACH ROW EXECUTE FUNCTION public.hisabpro_decideur132();
DROP TRIGGER IF EXISTS trg_decideur132 ON public.paie_branche_sociale_versions;
CREATE TRIGGER trg_decideur132 BEFORE INSERT OR UPDATE ON public.paie_branche_sociale_versions FOR EACH ROW EXECUTE FUNCTION public.hisabpro_decideur132();
DROP TRIGGER IF EXISTS trg_decideur132 ON public.paie_variables;
CREATE TRIGGER trg_decideur132 BEFORE INSERT OR UPDATE ON public.paie_variables FOR EACH ROW EXECUTE FUNCTION public.hisabpro_decideur132();
DROP TRIGGER IF EXISTS trg_decideur132 ON public.personnel_demandes;
CREATE TRIGGER trg_decideur132 BEFORE INSERT OR UPDATE ON public.personnel_demandes FOR EACH ROW EXECUTE FUNCTION public.hisabpro_decideur132();

REVOKE ALL ON public.personnel_validation_unique FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT,UPDATE ON public.personnel_validation_unique TO hisabpro;
 END IF;
END $$;
COMMIT;
