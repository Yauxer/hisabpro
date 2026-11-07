-- APPLICATION MANUELLE EXPLICITE UNIQUEMENT. Aucun bootstrap ni modèle Base.
BEGIN;
CREATE TABLE IF NOT EXISTS public.ras_reglement_captures (
 id serial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 reglement_id integer NOT NULL UNIQUE REFERENCES public.reglements(id),
 facture_id integer NOT NULL REFERENCES public.factures(id),
 ecriture_id integer NOT NULL UNIQUE REFERENCES public.ecritures(id),
 montant numeric NOT NULL CHECK(montant>0 AND montant=round(montant,2) AND montant NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)),
 date_operation date NOT NULL,
 reference varchar(100) NOT NULL CHECK(length(btrim(reference))>0),
 compte_destination varchar(10) NOT NULL,
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.ras_reglement_annulations (
 id serial PRIMARY KEY,
 capture_id integer NOT NULL UNIQUE REFERENCES public.ras_reglement_captures(id),
 societe_id integer NOT NULL REFERENCES public.societes(id),
 ecriture_id integer NOT NULL UNIQUE REFERENCES public.ecritures(id),
 date_operation date NOT NULL,
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION public.hisabpro_ras_trace_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Capture RAS et annulation conservées : modification/suppression interdite' USING ERRCODE='23514'; END $$;
-- Le propriétaire de cette fonction doit rester le rôle administrateur de migration.
-- Lecture de contrôle uniquement ; aucun droit global sur les appartenances n'est ajouté.
CREATE OR REPLACE FUNCTION public.hisabpro_ras_trace_liens() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM public.utilisateurs u WHERE u.id=NEW.created_by AND u.actif
   AND ((u.societe_id=NEW.societe_id AND u.role IN ('admin','comptable')) OR EXISTS(
     SELECT 1 FROM public.utilisateurs_societes us WHERE us.utilisateur_id=u.id
       AND us.societe_id=NEW.societe_id AND us.actif AND us.role IN ('admin','comptable')))) THEN
  RAISE EXCEPTION 'Acteur capture RAS non autorisé pour cette société' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME='ras_reglement_captures' THEN
  IF NOT EXISTS(SELECT 1 FROM public.reglements r JOIN public.factures f ON f.id=r.facture_id
    JOIN public.ecritures e ON e.id=NEW.ecriture_id
    WHERE r.id=NEW.reglement_id AND f.id=NEW.facture_id AND r.societe_id=NEW.societe_id
      AND f.societe_id=NEW.societe_id AND e.societe_id=NEW.societe_id
      AND NOT coalesce(f.ras_comptabilisee,false) AND r.mode IN ('virement','especes')
      AND r.statut='complet' AND r.est_comptabilisee AND e.journal='OD'
      AND e.source='ras_reglement' AND e.date=NEW.date_operation AND e.reference=NEW.reference
      AND EXISTS(SELECT 1 FROM public.ecritures cash WHERE cash.id=r.ecriture_id AND cash.societe_id=NEW.societe_id)
      AND (SELECT count(*) FROM public.lignes_ecriture l WHERE l.ecriture_id=e.id)=2
      AND EXISTS(SELECT 1 FROM public.lignes_ecriture l WHERE l.ecriture_id=e.id AND l.compte=NEW.compte_destination
        AND l.debit=CASE WHEN f.type='vente' THEN NEW.montant ELSE 0 END
        AND l.credit=CASE WHEN f.type='vente' THEN 0 ELSE NEW.montant END)
      AND EXISTS(SELECT 1 FROM public.lignes_ecriture l WHERE l.ecriture_id=e.id AND l.compte<>NEW.compte_destination
        AND l.tiers_id=f.tiers_id AND l.compte_auxiliaire_snapshot IS NOT NULL
        AND l.debit=CASE WHEN f.type='vente' THEN 0 ELSE NEW.montant END
        AND l.credit=CASE WHEN f.type='vente' THEN NEW.montant ELSE 0 END)) THEN
   RAISE EXCEPTION 'Liens capture RAS incohérents' USING ERRCODE='23514';
  END IF;
 ELSE
  IF NOT EXISTS(SELECT 1 FROM public.ras_reglement_captures c JOIN public.ecritures e ON e.id=NEW.ecriture_id
    JOIN public.reglements r ON r.id=c.reglement_id AND r.societe_id=c.societe_id
    WHERE c.id=NEW.capture_id AND c.societe_id=NEW.societe_id AND e.societe_id=NEW.societe_id
      AND e.contrepassation_de_id=c.ecriture_id AND e.journal='OD' AND e.source='ras_reglement'
      AND e.date=NEW.date_operation AND e.date_piece=NEW.date_operation
      AND r.statut='annule' AND NEW.date_operation>=c.date_operation
      AND e.reference='ANN-RAS-'||c.id::text
      AND (SELECT count(*) FROM public.lignes_ecriture WHERE ecriture_id=e.id)=2
      AND NOT EXISTS(SELECT 1 FROM public.lignes_ecriture original
        WHERE original.ecriture_id=c.ecriture_id AND NOT EXISTS(
          SELECT 1 FROM public.lignes_ecriture inverse WHERE inverse.ecriture_id=e.id
          AND inverse.compte=original.compte AND inverse.debit=original.credit AND inverse.credit=original.debit
          AND inverse.tiers_id IS NOT DISTINCT FROM original.tiers_id
          AND inverse.nature_auxiliaire IS NOT DISTINCT FROM original.nature_auxiliaire
          AND inverse.compte_auxiliaire_snapshot IS NOT DISTINCT FROM original.compte_auxiliaire_snapshot
          AND inverse.libelle_auxiliaire_snapshot IS NOT DISTINCT FROM original.libelle_auxiliaire_snapshot))) THEN
   RAISE EXCEPTION 'Liens annulation RAS incohérents' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE OR REPLACE FUNCTION public.hisabpro_ras_ledger_lie() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE eid integer; lie boolean; BEGIN
 IF TG_OP='INSERT' THEN eid := NEW.ecriture_id;
 ELSIF TG_TABLE_NAME='ecritures' THEN eid := OLD.id; ELSE eid := OLD.ecriture_id; END IF;
 SELECT EXISTS(SELECT 1 FROM public.ras_reglement_captures WHERE ecriture_id=eid
   UNION ALL SELECT 1 FROM public.ras_reglement_annulations WHERE ecriture_id=eid) INTO lie;
 IF TG_TABLE_NAME='lignes_ecriture' AND TG_OP='UPDATE' THEN
  SELECT lie OR EXISTS(SELECT 1 FROM public.ras_reglement_captures WHERE ecriture_id=NEW.ecriture_id
    UNION ALL SELECT 1 FROM public.ras_reglement_annulations WHERE ecriture_id=NEW.ecriture_id) INTO lie;
 END IF;
 IF lie AND (TG_OP IN ('INSERT','DELETE') OR (TG_TABLE_NAME='lignes_ecriture' AND to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD))
    OR (TG_TABLE_NAME='ecritures' AND (to_jsonb(NEW)-ARRAY['est_validee','date_validation','validee_par','numero_ecriture'])
      IS DISTINCT FROM (to_jsonb(OLD)-ARRAY['est_validee','date_validation','validee_par','numero_ecriture']))) THEN
  RAISE EXCEPTION 'Écriture liée à une capture RAS conservée : utiliser le règlement' USING ERRCODE='23514';
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END $$;
DROP TRIGGER IF EXISTS trg_ras_ledger_lie ON public.ecritures;
CREATE TRIGGER trg_ras_ledger_lie BEFORE UPDATE OR DELETE ON public.ecritures FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_ledger_lie();
DROP TRIGGER IF EXISTS trg_ras_ligne_liee ON public.lignes_ecriture;
CREATE TRIGGER trg_ras_ligne_liee BEFORE INSERT OR UPDATE OR DELETE ON public.lignes_ecriture FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_ledger_lie();
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['ras_reglement_captures','ras_reglement_annulations'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS trg_ras_immutable ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_ras_immutable BEFORE UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_trace_immutable()',t);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_ras_truncate ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_ras_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_ras_trace_immutable()',t);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_ras_liens ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_ras_liens BEFORE INSERT ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_trace_liens()',t);
  EXECUTE format('REVOKE UPDATE,DELETE,TRUNCATE ON public.%I FROM PUBLIC',t);
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
   EXECUTE format('GRANT SELECT,INSERT ON public.%I TO hisabpro',t);
   EXECUTE format('REVOKE UPDATE,DELETE,TRUNCATE ON public.%I FROM hisabpro',t);
   EXECUTE format('GRANT USAGE,SELECT ON SEQUENCE public.%I TO hisabpro',t||'_id_seq');
  END IF;
 END LOOP;
END $$;
COMMIT;
