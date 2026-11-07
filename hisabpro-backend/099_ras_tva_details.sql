-- Application manuelle explicite. Aucun bootstrap ou historique réécrit.
BEGIN;
CREATE TABLE IF NOT EXISTS public.ras_tva_reglement_details (
 capture_id integer PRIMARY KEY REFERENCES public.ras_reglement_captures(id) ON DELETE RESTRICT,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 dossier jsonb NOT NULL CHECK(jsonb_typeof(dossier)='object'),
 created_at timestamp NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION public.hisabpro_ras_tva_details_liens() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE c record; d jsonb:=NEW.dossier; BEGIN
 SELECT cap.*,r.date AS date_paiement,r.montant AS cash,r.ecriture_id AS cash_eid
 INTO c FROM public.ras_reglement_captures cap
 JOIN public.reglements r ON r.id=cap.reglement_id AND r.societe_id=cap.societe_id
 WHERE cap.id=NEW.capture_id AND cap.societe_id=NEW.societe_id;
 IF NOT FOUND OR (d->>'version_regle') IS DISTINCT FROM 'CGI2026-117Vb-listeB-559'
 OR (d->'simulation'->>'statut') IS DISTINCT FROM 'calcule'
 OR (d->'simulation'->>'version_regle') IS DISTINCT FROM (d->>'version_regle')
 OR (d->'faits'->>'date_paiement') IS DISTINCT FROM c.date_paiement::text
 OR (d->'source'->>'societe_id') IS DISTINCT FROM c.societe_id::text
 OR (d->'source'->>'facture_id') IS DISTINCT FROM c.facture_id::text
 OR (d->'source'->>'reglement_id') IS DISTINCT FROM c.reglement_id::text
 OR (d->'source'->>'ecriture_reglement_id') IS DISTINCT FROM c.cash_eid::text
 OR (d->'simulation'->>'retenue_tva')::numeric IS DISTINCT FROM c.montant
 OR (d->'simulation'->>'net_apres_cette_ras_tva')::numeric IS DISTINCT FROM round(c.cash::numeric,2)
 OR (d->'faits'->>'montant_paiement_ttc')::numeric IS DISTINCT FROM round(c.cash::numeric,2)+c.montant
 OR (d->'faits'->>'tva_paiement') IS NULL
 OR (d->'simulation'->>'base_tva') IS NULL
 OR (d->'simulation'->>'base_tva')::numeric IS DISTINCT FROM (d->'faits'->>'tva_paiement')::numeric
 OR (d->'faits'->>'tva_paiement')::numeric IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
 OR (d->'faits'->>'tva_paiement')::numeric < c.montant
 OR (d->'faits'->>'tva_paiement')::numeric > (d->'faits'->>'montant_paiement_ttc')::numeric
 OR (d->'pieces_verifiees') IS DISTINCT FROM 'true'::jsonb
 OR length(coalesce(d->>'empreinte_apercu',''))<>64
 OR NULLIF(btrim(d->>'justification_quote_part'),'') IS NULL THEN
  RAISE EXCEPTION 'Dossier RAS TVA incohérent avec sa capture et son règlement' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION public.hisabpro_ras_tva_details_liens() FROM PUBLIC;
DROP TRIGGER IF EXISTS trg_ras_tva_liens ON public.ras_tva_reglement_details;
CREATE TRIGGER trg_ras_tva_liens BEFORE INSERT ON public.ras_tva_reglement_details
 FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_tva_details_liens();
DROP TRIGGER IF EXISTS trg_ras_tva_immutable ON public.ras_tva_reglement_details;
CREATE TRIGGER trg_ras_tva_immutable BEFORE UPDATE OR DELETE ON public.ras_tva_reglement_details
 FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_trace_immutable();
DROP TRIGGER IF EXISTS trg_ras_tva_truncate ON public.ras_tva_reglement_details;
CREATE TRIGGER trg_ras_tva_truncate BEFORE TRUNCATE ON public.ras_tva_reglement_details
 FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_ras_trace_immutable();
REVOKE ALL ON public.ras_tva_reglement_details FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.ras_tva_reglement_details TO hisabpro;
  GRANT EXECUTE ON FUNCTION public.hisabpro_ras_tva_details_liens() TO hisabpro;
  REVOKE UPDATE,DELETE,TRUNCATE ON public.ras_tva_reglement_details FROM hisabpro;
 END IF;
END $$;
COMMIT;
