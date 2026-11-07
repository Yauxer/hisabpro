-- Métadonnées documentaires facultatives ; aucune affectation fiscale automatique.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_variables') IS NULL THEN RAISE EXCEPTION 'Installer114 avant123' USING ERRCODE='23514';END IF;
END $$;
CREATE OR REPLACE FUNCTION public.hisabpro_paie_reference123() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE r jsonb;k text;v jsonb;d date;
BEGIN
 r=NEW.donnees->'rattachement_revenus';
 IF r IS NULL OR r='null'::jsonb THEN RETURN NEW;END IF;
 IF jsonb_typeof(r)<>'object' THEN RAISE EXCEPTION 'Rattachement documentaire : objet requis' USING ERRCODE='23514';END IF;
 FOR k,v IN SELECT key,value FROM jsonb_each(r) LOOP
  IF k NOT IN ('reference_debut','reference_fin','reference_justification','versement_date','versement_reference') THEN RAISE EXCEPTION 'Rattachement documentaire : champ inconnu' USING ERRCODE='23514';END IF;
  IF v='null'::jsonb THEN CONTINUE;END IF;
  IF jsonb_typeof(v)<>'string' THEN RAISE EXCEPTION 'Rattachement documentaire : texte requis' USING ERRCODE='23514';END IF;
  IF k IN ('reference_debut','reference_fin','versement_date') THEN
   IF (r->>k)!~'^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN RAISE EXCEPTION 'Rattachement documentaire : date ISO requise' USING ERRCODE='23514';END IF;
   BEGIN
    d=(r->>k)::date;
    IF NOT isfinite(d) OR to_char(d,'YYYY-MM-DD')<>(r->>k) THEN RAISE EXCEPTION 'Date invalide';END IF;
   EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'Rattachement documentaire : date invalide' USING ERRCODE='23514';END;
  ELSE
   IF length(btrim(r->>k)) NOT BETWEEN 1 AND 200 THEN RAISE EXCEPTION 'Rattachement documentaire : référence requise,200caractères maximum' USING ERRCODE='23514';END IF;
  END IF;
 END LOOP;
 IF (r->>'reference_debut' IS NULL)<>(r->>'reference_fin' IS NULL)
 OR (r->>'reference_debut' IS NULL)<>(r->>'reference_justification' IS NULL)
 OR (r->>'versement_date' IS NULL)<>(r->>'versement_reference' IS NULL)
 OR (r->>'reference_debut' IS NULL AND r->>'versement_date' IS NULL) THEN
  RAISE EXCEPTION 'Rattachement documentaire : dates et preuves à renseigner ensemble' USING ERRCODE='23514';
 END IF;
 IF (r->>'reference_fin')::date<(r->>'reference_debut')::date THEN RAISE EXCEPTION 'Rattachement documentaire : période inversée' USING ERRCODE='23514';END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS aaa_paie_reference123 ON public.paie_variables;
CREATE TRIGGER aaa_paie_reference123 BEFORE INSERT OR UPDATE ON public.paie_variables FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_reference123();
COMMIT;
