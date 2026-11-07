-- Qualifications IR séparées des assiettes sociales ; aucune ancienne ligne réécrite.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_rubrique_versions') IS NULL OR to_regclass('public.paie_branche_sociale_versions') IS NULL THEN
  RAISE EXCEPTION 'Installer113 et116 avant119' USING ERRCODE='23514';
 END IF;
END $$;
CREATE OR REPLACE FUNCTION public.hisabpro_paie_qualification_ir119() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE cle text;q jsonb;consultation date;trts text[];champ text;
BEGIN
 cle:=CASE WHEN TG_TABLE_NAME='paie_rubrique_versions' THEN 'frais_professionnels' ELSE 'deductibilite_ir' END;
 trts:=CASE WHEN TG_TABLE_NAME='paie_rubrique_versions' THEN ARRAY['A_VERIFIER','INCLUS','EXCLUS'] ELSE ARRAY['A_VERIFIER','DEDUCTIBLE','NON_DEDUCTIBLE'] END;
 q:=NEW.contenu->cle;
 IF q IS NULL OR q='null'::jsonb THEN RETURN NEW;END IF;
 IF NOT (jsonb_typeof(q)='object' AND jsonb_typeof(q->'traitement')='string' AND jsonb_typeof(q->'statut_reglementaire')='string'
   AND jsonb_typeof(q->'conditions')='string' AND q->>'traitement'=ANY(trts) AND q->>'statut_reglementaire' IN ('A_VERIFIER','VALIDE','OBSOLETE')
   AND length(btrim(q->>'conditions')) BETWEEN 1 AND 2000
   AND q-ARRAY['traitement','statut_reglementaire','conditions','source_reference','texte_reference','article','url_source','empreinte_preuve','date_consultation']='{}'::jsonb) IS TRUE THEN
  RAISE EXCEPTION 'Qualification fiscale invalide' USING ERRCODE='23514';
 END IF;
 FOREACH champ IN ARRAY ARRAY['source_reference','texte_reference','article','url_source','empreinte_preuve','date_consultation'] LOOP
  IF q->champ IS NOT NULL AND q->champ<>'null'::jsonb AND jsonb_typeof(q->champ)<>'string' THEN
   RAISE EXCEPTION 'Qualification fiscale invalide' USING ERRCODE='23514';
  END IF;
 END LOOP;
 IF q->>'date_consultation' IS NOT NULL THEN
  BEGIN
   IF (q->>'date_consultation') !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN RAISE EXCEPTION 'Consultation invalide' USING ERRCODE='23514';END IF;
   consultation:=(q->>'date_consultation')::date;
   IF NOT isfinite(consultation) OR consultation>current_date THEN RAISE EXCEPTION 'Consultation invalide' USING ERRCODE='23514';END IF;
  EXCEPTION WHEN datetime_field_overflow OR invalid_datetime_format THEN RAISE EXCEPTION 'Date de consultation invalide' USING ERRCODE='23514';END;
 END IF;
 IF q->>'statut_reglementaire'='VALIDE' THEN
  IF NOT (q->>'traitement'<>'A_VERIFIER' AND length(btrim(q->>'source_reference')) BETWEEN 1 AND 300
    AND length(btrim(q->>'texte_reference')) BETWEEN 1 AND 300 AND length(btrim(q->>'article')) BETWEEN 1 AND 150
    AND (q->>'url_source') ~* '^https://([a-zA-Z0-9-]+\.)*(finances\.gov\.ma|tax\.gov\.ma|cnss\.ma|sgg\.gov\.ma|justice\.gov\.ma|acaps\.ma)(:443)?([/?#]|$)'
    AND (q->>'url_source') !~ '[[:space:]]' AND (q->>'empreinte_preuve') ~ '^[a-f0-9]{64}$' AND consultation IS NOT NULL) IS TRUE THEN
   RAISE EXCEPTION 'Preuves de qualification fiscale incomplètes' USING ERRCODE='23514';
  END IF;
  IF NEW.statut='APPROUVEE' AND (NOT NEW.verification_reglementaire_confirmee OR NOT EXISTS(
   SELECT 1 FROM public.personnel_habilitations h WHERE h.societe_id=NEW.societe_id AND h.utilisateur_id=NEW.decision_par
   AND h.capacite='personnel.valider_regles_paie' AND h.revoquee_at IS NULL AND h.liaison_id_snapshot IS NOT DISTINCT FROM (
    SELECT a.id FROM public.utilisateurs u LEFT JOIN public.utilisateurs_societes a ON a.utilisateur_id=u.id AND a.societe_id=NEW.societe_id AND a.actif AND u.societe_id<>NEW.societe_id WHERE u.id=NEW.decision_par))) THEN
   RAISE EXCEPTION 'Qualification fiscale : habilitation dédiée et contrôle confirmé requis' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END $$;
DO $$ DECLARE t text;BEGIN
 FOREACH t IN ARRAY ARRAY['paie_rubrique_versions','paie_branche_sociale_versions'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS trg_paie_ir_qualification119 ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_paie_ir_qualification119 BEFORE INSERT OR UPDATE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_qualification_ir119()',t);
 END LOOP;
END $$;
COMMIT;
