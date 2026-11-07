-- Rejet tracé possible après désactivation du préparateur.
-- Aucune approbation de sa préparation inactive, aucun transfert d’auteur.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.personnel_demandes_details') IS NULL THEN
  RAISE EXCEPTION 'Installer107 avant108' USING ERRCODE='23514';
 END IF;
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
     (NOT (TG_OP='UPDATE' AND NEW.statut='REJETE') AND NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.prepare_par,false)) OR
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
COMMIT;
