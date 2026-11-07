-- Pont documentaire explicite ; validation/comptabilisation ordinaires conservées.
BEGIN;
CREATE TABLE IF NOT EXISTS public.factures_correspondantes (
 id serial PRIMARY KEY,
 liaison_id integer NOT NULL REFERENCES public.societes_liees(id),
 facture_vente_id integer NOT NULL UNIQUE REFERENCES public.factures(id) ON DELETE RESTRICT,
 facture_achat_id integer NOT NULL UNIQUE REFERENCES public.factures(id) ON DELETE RESTRICT,
 cle uuid NOT NULL UNIQUE,
 faits jsonb NOT NULL CHECK(jsonb_typeof(faits)='object'),
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now(),
 CHECK(facture_vente_id<>facture_achat_id)
);
CREATE OR REPLACE FUNCTION public.hisabpro_factures_correspondantes_controle()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE l record; v record; a record; n integer;
BEGIN
 SELECT * INTO l FROM public.societes_liees WHERE id=NEW.liaison_id;
 IF NOT FOUND OR EXISTS(SELECT 1 FROM public.societes_liees_retraits WHERE liaison_id=l.id)
 THEN RAISE EXCEPTION 'Liaison absente ou retirée' USING ERRCODE='23514'; END IF;
 SELECT * INTO v FROM public.factures WHERE id=NEW.facture_vente_id FOR UPDATE;
 SELECT * INTO a FROM public.factures WHERE id=NEW.facture_achat_id;
 IF v.id IS NULL OR a.id IS NULL OR v.societe_id<>l.vendeur_id OR a.societe_id<>l.acheteur_id
 OR v.type::text<>'vente' OR a.type::text<>'achat' OR NOT v.est_validee OR v.est_proforma
 OR v.statut::text='annulee' OR a.est_validee OR a.est_comptabilisee OR a.est_proforma
 OR v.tiers_id IS DISTINCT FROM l.client_id OR a.tiers_id IS DISTINCT FROM l.fournisseur_id
 OR a.reference IS DISTINCT FROM v.numero OR v.ras_taux IS DISTINCT FROM 0::double precision
 OR ROW(v.date,v.date_echeance,v.delai_paiement,v.remise_globale,v.ristourne,v.escompte,
        v.frais_transport_ht,v.frais_transport_tva,v.frais_transport_mode,v.frais_transport_qualification_tva,
        v.frais_emballage_ht,v.frais_emballage_tva,v.frais_emballage_mode,v.frais_emballage_qualification_tva)
 IS DISTINCT FROM ROW(a.date,a.date_echeance,a.delai_paiement,a.remise_globale,a.ristourne,a.escompte,
        a.frais_transport_ht,a.frais_transport_tva,a.frais_transport_mode,a.frais_transport_qualification_tva,
        a.frais_emballage_ht,a.frais_emballage_tva,a.frais_emballage_mode,a.frais_emballage_qualification_tva)
 THEN RAISE EXCEPTION 'Factures correspondantes incohérentes' USING ERRCODE='23514'; END IF;
 n:=jsonb_array_length(NEW.faits->'lignes');
 IF n IS NULL OR n=0 OR n<>(SELECT count(*) FROM public.lignes_facture WHERE facture_id=v.id)
 OR n<>(SELECT count(*) FROM public.lignes_facture WHERE facture_id=a.id)
 OR n<>(SELECT count(DISTINCT x.source_id) FROM jsonb_to_recordset(NEW.faits->'lignes') AS x(source_id int))
 OR n<>(SELECT count(DISTINCT x.achat_id) FROM jsonb_to_recordset(NEW.faits->'lignes') AS x(achat_id int))
 OR n<>(SELECT count(*) FROM jsonb_to_recordset(NEW.faits->'lignes') AS x(source_id int,achat_id int,article_id int)
 JOIN public.lignes_facture lv ON lv.id=x.source_id AND lv.facture_id=v.id
 JOIN public.lignes_facture la ON la.id=x.achat_id AND la.facture_id=a.id AND la.article_id=x.article_id
 JOIN public.articles ar ON ar.id=la.article_id AND ar.societe_id=l.acheteur_id AND ar.actif
 WHERE ROW(lv.description,lv.quantite,lv.prix_unitaire,lv.tva,lv.qualification_tva,lv.remise,lv.remise2,lv.rabais)
 IS NOT DISTINCT FROM ROW(la.description,la.quantite,la.prix_unitaire,la.tva,la.qualification_tva,la.remise,la.remise2,la.rabais))
 THEN RAISE EXCEPTION 'Lignes correspondantes incohérentes' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION public.hisabpro_factures_correspondantes_controle() FROM PUBLIC;
DROP TRIGGER IF EXISTS trg_factures_correspondantes_insert ON public.factures_correspondantes;
CREATE TRIGGER trg_factures_correspondantes_insert BEFORE INSERT ON public.factures_correspondantes FOR EACH ROW EXECUTE FUNCTION public.hisabpro_factures_correspondantes_controle();
DROP TRIGGER IF EXISTS trg_factures_correspondantes_immutable ON public.factures_correspondantes;
CREATE TRIGGER trg_factures_correspondantes_immutable BEFORE UPDATE OR DELETE ON public.factures_correspondantes FOR EACH ROW EXECUTE FUNCTION public.hisabpro_ras_trace_immutable();
DROP TRIGGER IF EXISTS trg_factures_correspondantes_truncate ON public.factures_correspondantes;
CREATE TRIGGER trg_factures_correspondantes_truncate BEFORE TRUNCATE ON public.factures_correspondantes FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_ras_trace_immutable();
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT,INSERT ON public.factures_correspondantes TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.factures_correspondantes_id_seq TO hisabpro;
  REVOKE UPDATE,DELETE,TRUNCATE ON public.factures_correspondantes FROM hisabpro;
  GRANT EXECUTE ON FUNCTION public.hisabpro_factures_correspondantes_controle() TO hisabpro;
 END IF;
END $$;
COMMIT;
