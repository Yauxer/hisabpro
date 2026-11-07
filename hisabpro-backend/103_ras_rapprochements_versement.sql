-- Application manuelle explicite. Rapprochement documentaire, aucun DML comptable.
BEGIN;
CREATE TABLE IF NOT EXISTS public.ras_tva_rapprochements (
 id serial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 capture_id integer NOT NULL REFERENCES public.ras_reglement_captures(id),
 ecriture_id integer NOT NULL REFERENCES public.ecritures(id),
 montant numeric NOT NULL CHECK (montant>0 AND montant=round(montant,2)
   AND montant NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)),
 cle uuid NOT NULL UNIQUE,
 faits jsonb NOT NULL,
 empreinte_sha256 varchar(64) NOT NULL CHECK (empreinte_sha256 ~ '^[a-f0-9]{64}$'),
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ras_rapprochements_capture ON public.ras_tva_rapprochements(societe_id,capture_id);
CREATE INDEX IF NOT EXISTS ix_ras_rapprochements_piece ON public.ras_tva_rapprochements(societe_id,ecriture_id);
CREATE TABLE IF NOT EXISTS public.ras_tva_rapprochement_retraits (
 id serial PRIMARY KEY,
 rapprochement_id integer NOT NULL UNIQUE REFERENCES public.ras_tva_rapprochements(id),
 societe_id integer NOT NULL REFERENCES public.societes(id),
 motif varchar(500) NOT NULL CHECK (length(btrim(motif))>0),
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION public.hisabpro_ras_rapprochement_immuable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Rapprochement RAS immuable : utiliser un retrait motivé' USING ERRCODE='23514'; END;
$$;
-- Fonction de contrôle seulement ; propriétaire réservé au rôle migrateur.
CREATE OR REPLACE FUNCTION public.hisabpro_ras_rapprochement_liens() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE c record; e record; utilise numeric; capacite numeric; attendu jsonb;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtext('hisabpro_ras_rapprochement'),NEW.societe_id);
 IF NOT EXISTS(SELECT 1 FROM public.utilisateurs u WHERE u.id=NEW.created_by AND u.actif
   AND ((u.societe_id=NEW.societe_id AND u.role IN ('admin','comptable')) OR EXISTS(
     SELECT 1 FROM public.utilisateurs_societes us WHERE us.utilisateur_id=u.id
       AND us.societe_id=NEW.societe_id AND us.actif AND us.role IN ('admin','comptable')))) THEN
  RAISE EXCEPTION 'Acteur de rapprochement non autorisé' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME='ras_tva_rapprochement_retraits' THEN
  IF NOT EXISTS(SELECT 1 FROM public.ras_tva_rapprochements r
    WHERE r.id=NEW.rapprochement_id AND r.societe_id=NEW.societe_id) THEN
   RAISE EXCEPTION 'Rapprochement absent de cette société' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
 END IF;
 SELECT r.* INTO c FROM public.ras_reglement_captures r
 JOIN public.ras_tva_reglement_details d ON d.capture_id=r.id AND d.societe_id=r.societe_id
 JOIN public.factures f ON f.id=r.facture_id AND f.societe_id=r.societe_id
 JOIN public.societes s ON s.id=r.societe_id AND s.devise='MAD'
 JOIN public.ecritures od ON od.id=r.ecriture_id AND od.societe_id=r.societe_id
 WHERE r.id=NEW.capture_id AND r.societe_id=NEW.societe_id AND f.type='achat' AND od.est_validee
 AND NOT EXISTS(SELECT 1 FROM public.ras_reglement_annulations a WHERE a.capture_id=r.id);
 IF NOT FOUND THEN
  RAISE EXCEPTION 'Capture TVA opérée active avec OD validée requise' USING ERRCODE='23514';
 END IF;
 SELECT * INTO e FROM public.ecritures WHERE id=NEW.ecriture_id AND societe_id=NEW.societe_id
   AND est_validee AND id<>c.ecriture_id;
 IF NOT FOUND OR EXISTS(SELECT 1 FROM public.ecritures i WHERE i.contrepassation_de_id=NEW.ecriture_id)
   OR EXISTS(SELECT 1 FROM public.ras_reglement_captures r WHERE r.ecriture_id=NEW.ecriture_id)
   OR EXISTS(SELECT 1 FROM public.ras_reglement_annulations a WHERE a.ecriture_id=NEW.ecriture_id) THEN
  RAISE EXCEPTION 'Pièce validée distincte, non contrepassée, requise' USING ERRCODE='23514';
 END IF;
 IF EXISTS(SELECT 1 FROM public.lignes_ecriture l WHERE l.ecriture_id=e.id
    AND (l.debit IS NULL OR l.credit IS NULL OR l.debit<0 OR l.credit<0
      OR l.debit<>round(l.debit,2) OR l.credit<>round(l.credit,2)
      OR l.debit IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
      OR l.credit IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)))
 OR (SELECT count(*) FROM public.lignes_ecriture WHERE ecriture_id=e.id)<2
 OR (SELECT sum(debit-credit) FROM public.lignes_ecriture WHERE ecriture_id=e.id)<>0
 OR NOT EXISTS(SELECT 1 FROM public.lignes_ecriture WHERE ecriture_id=e.id AND compte LIKE '5%' AND credit>debit) THEN
  RAISE EXCEPTION 'Pièce équilibrée au centime avec crédit de trésorerie requise' USING ERRCODE='23514';
 END IF;
 SELECT jsonb_build_object('id',e.id,'date',to_char(e.date,'YYYY-MM-DD'),
   'journal',e.journal,'reference',e.reference,'numero_ecriture',e.numero_ecriture,
   'est_validee',e.est_validee,'source',e.source,
   'lignes',(SELECT jsonb_agg(jsonb_build_object('id',l.id,'compte',l.compte,
     'debit',to_char(l.debit,'FM999999999999999990.00'),
     'credit',to_char(l.credit,'FM999999999999999990.00')) ORDER BY l.id)
     FROM public.lignes_ecriture l WHERE l.ecriture_id=e.id)) INTO attendu;
 IF NEW.faits->'piece' IS DISTINCT FROM attendu
 OR NEW.faits->'capture' IS DISTINCT FROM jsonb_build_object('id',c.id,
     'montant',to_char(c.montant,'FM999999999999999990.00'),
     'compte_destination',c.compte_destination,'ecriture_id',c.ecriture_id)
 OR NEW.faits->'montant' IS DISTINCT FROM to_jsonb(to_char(NEW.montant,'FM999999999999999990.00'))
 OR NEW.faits->'schema_version' IS DISTINCT FROM '1'::jsonb
 OR NEW.faits->'rapprochement_verifie' IS DISTINCT FROM 'true'::jsonb THEN
  RAISE EXCEPTION 'Faits du rapprochement différents des sources comptables' USING ERRCODE='23514';
 END IF;
 SELECT coalesce(sum(r.montant),0) INTO utilise FROM public.ras_tva_rapprochements r
 WHERE r.capture_id=c.id AND NOT EXISTS(SELECT 1 FROM public.ras_tva_rapprochement_retraits x WHERE x.rapprochement_id=r.id);
 IF utilise+NEW.montant>c.montant THEN
  RAISE EXCEPTION 'Capacité de la capture dépassée' USING ERRCODE='23514';
 END IF;
 SELECT coalesce(sum(debit-credit),0) INTO capacite FROM public.lignes_ecriture
 WHERE ecriture_id=e.id AND compte=c.compte_destination;
 SELECT coalesce(sum(r.montant),0) INTO utilise FROM public.ras_tva_rapprochements r
 JOIN public.ras_reglement_captures sc ON sc.id=r.capture_id
 WHERE r.ecriture_id=e.id AND sc.compte_destination=c.compte_destination
 AND NOT EXISTS(SELECT 1 FROM public.ras_tva_rapprochement_retraits x WHERE x.rapprochement_id=r.id);
 IF utilise+NEW.montant>capacite THEN
  RAISE EXCEPTION 'Débit disponible du compte de capture dépassé' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_ras_rapprochement_liens ON public.ras_tva_rapprochements;
CREATE TRIGGER trg_ras_rapprochement_liens BEFORE INSERT ON public.ras_tva_rapprochements
 FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_rapprochement_liens();
DROP TRIGGER IF EXISTS trg_ras_rapprochement_retrait_liens ON public.ras_tva_rapprochement_retraits;
CREATE TRIGGER trg_ras_rapprochement_retrait_liens BEFORE INSERT ON public.ras_tva_rapprochement_retraits
 FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_rapprochement_liens();
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['ras_tva_rapprochements','ras_tva_rapprochement_retraits'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS trg_ras_rapprochement_immuable ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_ras_rapprochement_immuable BEFORE UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_rapprochement_immuable()',t);
  EXECUTE format('DROP TRIGGER IF EXISTS trg_ras_rapprochement_truncate ON public.%I',t);
  EXECUTE format('CREATE TRIGGER trg_ras_rapprochement_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_ras_rapprochement_immuable()',t);
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC',t);
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
   EXECUTE format('GRANT SELECT,INSERT ON public.%I TO hisabpro',t);
   EXECUTE format('REVOKE UPDATE,DELETE,TRUNCATE ON public.%I FROM hisabpro',t);
  END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT USAGE,SELECT ON SEQUENCE public.ras_tva_rapprochements_id_seq,public.ras_tva_rapprochement_retraits_id_seq TO hisabpro;
  REVOKE UPDATE ON SEQUENCE public.ras_tva_rapprochements_id_seq,public.ras_tva_rapprochement_retraits_id_seq FROM hisabpro;
 END IF;
END $$;
REVOKE ALL ON FUNCTION public.hisabpro_ras_rapprochement_liens(),public.hisabpro_ras_rapprochement_immuable() FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT EXECUTE ON FUNCTION public.hisabpro_ras_rapprochement_liens(),public.hisabpro_ras_rapprochement_immuable() TO hisabpro;
 END IF;
END $$;
COMMIT;
