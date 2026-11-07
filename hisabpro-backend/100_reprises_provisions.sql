-- Installation explicite après 098/099. Pas de DML historique ni de create_all.
BEGIN;
CREATE TABLE IF NOT EXISTS public.reprises_provisions (
 id serial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 ajustement_id integer NOT NULL REFERENCES public.ajustements_inventaire(id) ON DELETE RESTRICT,
 ecriture_id integer NOT NULL UNIQUE REFERENCES public.ecritures(id) ON DELETE RESTRICT,
 cle uuid NOT NULL,
 montant numeric(18,2) NOT NULL CHECK(montant>0 AND montant<'10000000000000000'::numeric),
 faits jsonb NOT NULL CHECK(jsonb_typeof(faits)='object'),
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now(),
 UNIQUE(societe_id,cle)
);
CREATE INDEX IF NOT EXISTS ix_reprises_provisions_source ON public.reprises_provisions(societe_id,ajustement_id);
CREATE TABLE IF NOT EXISTS public.reprises_provisions_annulations (
 id serial PRIMARY KEY,
 reprise_id integer NOT NULL UNIQUE REFERENCES public.reprises_provisions(id) ON DELETE RESTRICT,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 ecriture_id integer NOT NULL UNIQUE REFERENCES public.ecritures(id) ON DELETE RESTRICT,
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION public.hisabpro_reprise_piece_protegee(p integer)
RETURNS boolean LANGUAGE sql STABLE SET search_path=pg_catalog,public AS $$
 SELECT EXISTS(SELECT 1 FROM public.reprises_provisions r
 JOIN public.ajustements_inventaire a ON a.id=r.ajustement_id
 WHERE r.ecriture_id=p OR a.ecriture_id=p
 UNION ALL SELECT 1 FROM public.reprises_provisions_annulations WHERE ecriture_id=p)
$$;

CREATE OR REPLACE FUNCTION public.hisabpro_reprise_liens()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE a record; src record; e record; produit text; consomme numeric; montant_source numeric;
BEGIN
 SELECT * INTO a FROM public.ajustements_inventaire WHERE id=NEW.ajustement_id AND societe_id=NEW.societe_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Source de reprise étrangère ou absente' USING ERRCODE='23514'; END IF;
 -- Même verrou source que l'API, pris avant le calcul de capacité.
 SELECT * INTO src FROM public.ecritures WHERE id=a.ecriture_id AND societe_id=NEW.societe_id FOR UPDATE;
 IF NOT FOUND OR NOT src.est_validee OR src.numero_ecriture IS NULL OR src.exercice<>a.exercice
 OR EXISTS(SELECT 1 FROM public.ecritures WHERE contrepassation_de_id=src.id)
 THEN RAISE EXCEPTION 'Dotation source non qualifiée' USING ERRCODE='23514'; END IF;
 montant_source:=a.montant;
 IF a.type='provision_risque' AND (a.compte_contrepartie LIKE '15%' OR a.compte_contrepartie LIKE '45%') THEN
  produit:=CASE WHEN a.compte_activite LIKE '6195%' THEN '7195' WHEN a.compte_activite LIKE '6393%' THEN '7393' WHEN a.compte_activite LIKE '6595%' THEN '7595' END;
 ELSIF a.type='depreciation_client' AND a.compte_contrepartie LIKE '3942%' THEN
  produit:=CASE WHEN a.compte_activite='6196' OR a.compte_activite LIKE '61964%' THEN '7196' WHEN a.compte_activite LIKE '6596%' THEN '7596' END;
 ELSIF a.type='depreciation_stock' AND a.compte_contrepartie LIKE '391%' THEN
  produit:=CASE WHEN a.compte_activite='6196' OR a.compte_activite LIKE '61961%' THEN '7196' END;
 END IF;
 IF produit IS NULL OR (SELECT count(*) FROM public.lignes_ecriture WHERE ecriture_id=src.id)<>2
 OR NOT EXISTS(SELECT 1 FROM public.lignes_ecriture WHERE ecriture_id=src.id AND compte=a.compte_activite AND debit=montant_source AND credit=0)
 OR NOT EXISTS(SELECT 1 FROM public.lignes_ecriture WHERE ecriture_id=src.id AND compte=a.compte_contrepartie AND credit=montant_source AND debit=0)
 THEN RAISE EXCEPTION 'Lignes de dotation incohérentes' USING ERRCODE='23514'; END IF;
 SELECT * INTO e FROM public.ecritures WHERE id=NEW.ecriture_id AND societe_id=NEW.societe_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Pièce de reprise étrangère ou absente' USING ERRCODE='23514'; END IF;
 -- Marge minimale à partir de la nouvelle date, pas seulement le solde final.
 WITH mouvements AS (
  SELECT re.date AS jour,r.montant AS delta FROM public.reprises_provisions r
  JOIN public.ecritures re ON re.id=r.ecriture_id WHERE r.ajustement_id=a.id
  UNION ALL
  SELECT ne.date,-r.montant FROM public.reprises_provisions r
  JOIN public.ecritures re ON re.id=r.ecriture_id
  JOIN public.reprises_provisions_annulations n ON n.reprise_id=r.id
  JOIN public.ecritures ne ON ne.id=n.ecriture_id
  WHERE r.ajustement_id=a.id AND re.est_validee AND ne.est_validee
 ), par_jour AS (SELECT jour,sum(delta) AS delta FROM mouvements GROUP BY jour),
 chronologie AS (SELECT jour,sum(delta) OVER(ORDER BY jour) AS cumul FROM par_jour)
 SELECT greatest(coalesce((SELECT sum(delta) FROM par_jour WHERE jour<=e.date),0),
                 coalesce((SELECT max(cumul) FROM chronologie WHERE jour>e.date),0)) INTO consomme;
 IF e.est_validee OR e.date<src.date OR e.source IS DISTINCT FROM 'reprise_provision'
 OR NEW.montant+consomme>montant_source
 OR NEW.faits->>'version' IS DISTINCT FROM 'CGNC-reprises-615'
 OR NEW.faits->>'source_id' IS DISTINCT FROM a.id::text
 OR NEW.faits->>'source_ecriture_id' IS DISTINCT FROM src.id::text
 OR NEW.faits->>'societe_id' IS DISTINCT FROM NEW.societe_id::text
 OR NEW.faits->>'exercice' IS DISTINCT FROM e.exercice::text
 OR NEW.faits->>'compte_provision' IS DISTINCT FROM a.compte_contrepartie
 OR NEW.faits->>'compte_reprise' IS DISTINCT FROM produit
 OR (NEW.faits->'faits'->>'montant')::numeric IS DISTINCT FROM NEW.montant
 OR NEW.faits->'faits'->>'date' IS DISTINCT FROM e.date::text
 OR NULLIF(btrim(NEW.faits->'faits'->>'justification'),'') IS NULL
 OR (SELECT count(*) FROM public.lignes_ecriture WHERE ecriture_id=e.id)<>2
 OR NOT EXISTS(SELECT 1 FROM public.lignes_ecriture WHERE ecriture_id=e.id AND compte=a.compte_contrepartie AND debit=NEW.montant AND credit=0)
 OR NOT EXISTS(SELECT 1 FROM public.lignes_ecriture WHERE ecriture_id=e.id AND compte=produit AND credit=NEW.montant AND debit=0)
 THEN RAISE EXCEPTION 'Reprise incohérente ou capacité dépassée' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_reprise_annulation_liens()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE r record; e record; original record; source_id integer;
BEGIN
 SELECT * INTO r FROM public.reprises_provisions WHERE id=NEW.reprise_id AND societe_id=NEW.societe_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Reprise étrangère ou absente' USING ERRCODE='23514'; END IF;
 SELECT a.ecriture_id INTO source_id FROM public.ajustements_inventaire a WHERE a.id=r.ajustement_id;
 PERFORM 1 FROM public.ecritures WHERE id=source_id FOR UPDATE;
 SELECT * INTO original FROM public.ecritures WHERE id=r.ecriture_id AND societe_id=NEW.societe_id FOR UPDATE;
 SELECT * INTO e FROM public.ecritures WHERE id=NEW.ecriture_id AND societe_id=NEW.societe_id;
 IF NOT FOUND OR e.est_validee OR e.date<original.date OR e.source IS DISTINCT FROM 'reprise_provision'
 OR (SELECT count(*) FROM public.lignes_ecriture WHERE ecriture_id=e.id)<>2
 OR EXISTS(SELECT 1 FROM public.lignes_ecriture l WHERE l.ecriture_id=original.id
     AND NOT EXISTS(SELECT 1 FROM public.lignes_ecriture i WHERE i.ecriture_id=e.id AND i.compte=l.compte AND i.debit=l.credit AND i.credit=l.debit))
 THEN RAISE EXCEPTION 'Inverse de reprise incohérent' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_reprise_journal_protection()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE parent integer;
BEGIN
 IF TG_TABLE_NAME='ecritures' THEN
  IF TG_OP='INSERT' THEN
   IF NEW.contrepassation_de_id IS NOT NULL AND public.hisabpro_reprise_piece_protegee(NEW.contrepassation_de_id) THEN
    RAISE EXCEPTION 'Utiliser l annulation du registre de reprises' USING ERRCODE='23514';
   END IF;
  ELSIF public.hisabpro_reprise_piece_protegee(OLD.id) THEN
   IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Pièce de reprise protégée' USING ERRCODE='23514'; END IF;
   IF NEW.est_validee AND NOT OLD.est_validee AND EXISTS(
    SELECT 1 FROM public.reprises_provisions_annulations n
    JOIN public.reprises_provisions r ON r.id=n.reprise_id
    JOIN public.ecritures original ON original.id=r.ecriture_id
    WHERE n.ecriture_id=OLD.id AND NOT original.est_validee) THEN
    RAISE EXCEPTION 'Valider la reprise avant son inverse' USING ERRCODE='23514';
   END IF;
   IF (to_jsonb(NEW)-ARRAY['est_validee','date_validation','validee_par','numero_ecriture']) IS DISTINCT FROM
      (to_jsonb(OLD)-ARRAY['est_validee','date_validation','validee_par','numero_ecriture']) THEN
    RAISE EXCEPTION 'Contenu de reprise figé' USING ERRCODE='23514';
   END IF;
  END IF;
 ELSIF TG_TABLE_NAME='lignes_ecriture' THEN
  IF TG_OP IN ('UPDATE','DELETE') THEN
   IF public.hisabpro_reprise_piece_protegee(OLD.ecriture_id) THEN RAISE EXCEPTION 'Ligne liée à une reprise figée' USING ERRCODE='23514'; END IF;
  END IF;
  IF TG_OP IN ('UPDATE','INSERT') THEN
   IF public.hisabpro_reprise_piece_protegee(NEW.ecriture_id) THEN RAISE EXCEPTION 'Ligne liée à une reprise figée' USING ERRCODE='23514'; END IF;
  END IF;
 ELSE
  IF EXISTS(SELECT 1 FROM public.reprises_provisions WHERE ajustement_id=OLD.id) THEN
   RAISE EXCEPTION 'Dotation liée à une reprise figée' USING ERRCODE='23514';
  END IF;
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_reprise_liens ON public.reprises_provisions;
CREATE TRIGGER trg_reprise_liens BEFORE INSERT ON public.reprises_provisions FOR EACH ROW EXECUTE FUNCTION public.hisabpro_reprise_liens();
DROP TRIGGER IF EXISTS trg_reprise_annulation_liens ON public.reprises_provisions_annulations;
CREATE TRIGGER trg_reprise_annulation_liens BEFORE INSERT ON public.reprises_provisions_annulations FOR EACH ROW EXECUTE FUNCTION public.hisabpro_reprise_annulation_liens();
DROP TRIGGER IF EXISTS trg_reprise_immutable ON public.reprises_provisions;
CREATE TRIGGER trg_reprise_immutable BEFORE UPDATE OR DELETE ON public.reprises_provisions FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_trace_immutable();
DROP TRIGGER IF EXISTS trg_reprise_annulation_immutable ON public.reprises_provisions_annulations;
CREATE TRIGGER trg_reprise_annulation_immutable BEFORE UPDATE OR DELETE ON public.reprises_provisions_annulations FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_trace_immutable();
DROP TRIGGER IF EXISTS trg_reprise_truncate ON public.reprises_provisions;
CREATE TRIGGER trg_reprise_truncate BEFORE TRUNCATE ON public.reprises_provisions FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_ras_trace_immutable();
DROP TRIGGER IF EXISTS trg_reprise_annulation_truncate ON public.reprises_provisions_annulations;
CREATE TRIGGER trg_reprise_annulation_truncate BEFORE TRUNCATE ON public.reprises_provisions_annulations FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_ras_trace_immutable();
DROP TRIGGER IF EXISTS trg_reprise_journal ON public.ecritures;
CREATE TRIGGER trg_reprise_journal BEFORE INSERT OR UPDATE OR DELETE ON public.ecritures FOR EACH ROW EXECUTE FUNCTION public.hisabpro_reprise_journal_protection();
DROP TRIGGER IF EXISTS trg_reprise_lignes ON public.lignes_ecriture;
CREATE TRIGGER trg_reprise_lignes BEFORE INSERT OR UPDATE OR DELETE ON public.lignes_ecriture FOR EACH ROW EXECUTE FUNCTION public.hisabpro_reprise_journal_protection();
DROP TRIGGER IF EXISTS trg_reprise_source ON public.ajustements_inventaire;
CREATE TRIGGER trg_reprise_source BEFORE UPDATE OR DELETE ON public.ajustements_inventaire FOR EACH ROW EXECUTE FUNCTION public.hisabpro_reprise_journal_protection();
REVOKE ALL ON public.reprises_provisions,public.reprises_provisions_annulations FROM PUBLIC;
REVOKE ALL ON FUNCTION public.hisabpro_reprise_piece_protegee(integer),public.hisabpro_reprise_liens(),
 public.hisabpro_reprise_annulation_liens(),public.hisabpro_reprise_journal_protection() FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.reprises_provisions,public.reprises_provisions_annulations TO hisabpro;
  GRANT USAGE,SELECT ON public.reprises_provisions_id_seq,public.reprises_provisions_annulations_id_seq TO hisabpro;
  REVOKE UPDATE,DELETE,TRUNCATE ON public.reprises_provisions,public.reprises_provisions_annulations FROM hisabpro;
  GRANT EXECUTE ON FUNCTION public.hisabpro_reprise_piece_protegee(integer),public.hisabpro_reprise_liens(),
   public.hisabpro_reprise_annulation_liens(),public.hisabpro_reprise_journal_protection() TO hisabpro;
 END IF;
END $$;
COMMIT;
