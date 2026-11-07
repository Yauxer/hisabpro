-- Bulletins de paie figés et registre des avances/prêts (lot 968). Additive et rejouable, après 124.
-- Le contenu d'un bulletin est figé (empreinte) ; seuls le rattachement
-- comptable, le paiement et une annulation motivée sont ajoutés, une seule fois.
-- À exécuter avec le rôle de migration, après sauvegarde.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.paie_controles_mensuels') IS NULL THEN RAISE EXCEPTION 'Installer124 avant131' USING ERRCODE='23514';END IF;
END $$;
CREATE TABLE IF NOT EXISTS public.paie_bulletins (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 employe_id integer NOT NULL,
 periode date NOT NULL CHECK(isfinite(periode) AND extract(day FROM periode)=1),
 controle_id bigint NOT NULL,
 cle_idempotence uuid NOT NULL,
 contenu jsonb NOT NULL CHECK((jsonb_typeof(contenu)='object' AND contenu->>'mode'='BULLETIN_968' AND contenu->>'employe_id'=employe_id::text AND contenu->>'periode'=periode::text) IS TRUE),
 empreinte varchar(64) NOT NULL CHECK(empreinte ~ '^[a-f0-9]{64}$'),
 net_a_payer numeric(15,2) NOT NULL CHECK(net_a_payer>=0),
 statut varchar(10) NOT NULL DEFAULT 'VALIDE' CHECK(statut IN ('VALIDE','ANNULE')),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 ecriture_id integer REFERENCES public.ecritures(id) ON DELETE SET NULL,
 paiement_ecriture_id integer REFERENCES public.ecritures(id) ON DELETE SET NULL,
 paiement_date date,
 paiement_mode varchar(20) CHECK(paiement_mode IS NULL OR paiement_mode IN ('virement','cheque','especes')),
 annule_par integer REFERENCES public.utilisateurs(id),
 annule_at timestamp,
 motif_annulation varchar(500),
 FOREIGN KEY(controle_id,societe_id) REFERENCES public.paie_controles_mensuels(id,societe_id),
 FOREIGN KEY(employe_id,societe_id) REFERENCES public.employes(id,societe_id),
 UNIQUE(societe_id,cle_idempotence),
 CHECK((statut='VALIDE' AND annule_at IS NULL AND annule_par IS NULL AND motif_annulation IS NULL) OR
       (statut='ANNULE' AND annule_at IS NOT NULL AND annule_par IS NOT NULL AND length(btrim(coalesce(motif_annulation,'')))>0)),
 CHECK((paiement_date IS NULL)=(paiement_mode IS NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_paie_bulletins_valide ON public.paie_bulletins(societe_id,employe_id,periode) WHERE statut='VALIDE';
CREATE INDEX IF NOT EXISTS ix_paie_bulletins_periode ON public.paie_bulletins(societe_id,periode);
CREATE OR REPLACE FUNCTION public.hisabpro_paie_bulletins131() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP IN ('DELETE','TRUNCATE') THEN RAISE EXCEPTION 'Conserver les bulletins de paie ; annuler avec un motif' USING ERRCODE='23514';END IF;
 IF TG_OP='UPDATE' THEN
  IF (NEW.societe_id,NEW.employe_id,NEW.periode,NEW.controle_id,NEW.cle_idempotence,NEW.contenu,NEW.empreinte,NEW.net_a_payer,NEW.auteur_id,NEW.motif,NEW.cree_at)
     IS DISTINCT FROM (OLD.societe_id,OLD.employe_id,OLD.periode,OLD.controle_id,OLD.cle_idempotence,OLD.contenu,OLD.empreinte,OLD.net_a_payer,OLD.auteur_id,OLD.motif,OLD.cree_at) THEN
   RAISE EXCEPTION 'Contenu du bulletin figé' USING ERRCODE='23514';END IF;
  IF OLD.statut='ANNULE' THEN RAISE EXCEPTION 'Bulletin annulé : aucune modification' USING ERRCODE='23514';END IF;
  IF OLD.ecriture_id IS NOT NULL AND NEW.ecriture_id IS DISTINCT FROM OLD.ecriture_id AND NEW.ecriture_id IS NOT NULL THEN
   RAISE EXCEPTION 'Bulletin déjà comptabilisé' USING ERRCODE='23514';END IF;
  -- Suppression du brouillon de paiement : le bulletin redevient à payer.
  IF OLD.paiement_ecriture_id IS NOT NULL AND NEW.paiement_ecriture_id IS NULL THEN NEW.paiement_date:=NULL;NEW.paiement_mode:=NULL;
  ELSIF OLD.paiement_date IS NOT NULL AND (NEW.paiement_date,NEW.paiement_mode,NEW.paiement_ecriture_id) IS DISTINCT FROM (OLD.paiement_date,OLD.paiement_mode,OLD.paiement_ecriture_id) THEN
   RAISE EXCEPTION 'Paiement du bulletin déjà enregistré' USING ERRCODE='23514';
  END IF;
  IF NEW.statut='ANNULE' AND (OLD.paiement_date IS NOT NULL OR EXISTS(SELECT 1 FROM public.ecritures e WHERE e.id=OLD.ecriture_id AND e.est_validee)) THEN
   RAISE EXCEPTION 'Bulletin payé ou comptabilisé définitivement : contrepasser avant annulation' USING ERRCODE='23514';END IF;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_paie_bulletins131 ON public.paie_bulletins;
CREATE TRIGGER trg_paie_bulletins131 BEFORE UPDATE OR DELETE ON public.paie_bulletins FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_bulletins131();
DROP TRIGGER IF EXISTS trg_paie_bulletins131_truncate ON public.paie_bulletins;
CREATE TRIGGER trg_paie_bulletins131_truncate BEFORE TRUNCATE ON public.paie_bulletins FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_bulletins131();
REVOKE ALL ON public.paie_bulletins FROM PUBLIC;
CREATE TABLE IF NOT EXISTS public.paie_avances (
 id bigserial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 employe_id integer NOT NULL,
 nature varchar(10) NOT NULL CHECK(nature IN ('AVANCE','PRET')),
 date_octroi date NOT NULL CHECK(isfinite(date_octroi)),
 montant numeric(15,2) NOT NULL CHECK(montant>0),
 retenue_mensuelle numeric(15,2) CHECK(retenue_mensuelle IS NULL OR retenue_mensuelle>0),
 mode_versement varchar(20) NOT NULL CHECK(mode_versement IN ('virement','cheque','especes')),
 motif varchar(500) NOT NULL CHECK(length(btrim(motif))>0),
 auteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 cree_at timestamp NOT NULL DEFAULT clock_timestamp(),
 ecriture_id integer REFERENCES public.ecritures(id) ON DELETE SET NULL,
 statut varchar(10) NOT NULL DEFAULT 'ACTIVE' CHECK(statut IN ('ACTIVE','ANNULEE')),
 annule_par integer REFERENCES public.utilisateurs(id),
 annule_at timestamp,
 motif_annulation varchar(500),
 FOREIGN KEY(employe_id,societe_id) REFERENCES public.employes(id,societe_id),
 CHECK((statut='ACTIVE' AND annule_at IS NULL AND annule_par IS NULL AND motif_annulation IS NULL) OR
       (statut='ANNULEE' AND annule_at IS NOT NULL AND annule_par IS NOT NULL AND length(btrim(coalesce(motif_annulation,'')))>0))
);
CREATE INDEX IF NOT EXISTS ix_paie_avances_employe ON public.paie_avances(societe_id,employe_id);
CREATE OR REPLACE FUNCTION public.hisabpro_paie_avances131() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP IN ('DELETE','TRUNCATE') THEN RAISE EXCEPTION 'Conserver les avances ; annuler avec un motif' USING ERRCODE='23514';END IF;
 IF (NEW.societe_id,NEW.employe_id,NEW.nature,NEW.date_octroi,NEW.montant,NEW.retenue_mensuelle,NEW.mode_versement,NEW.motif,NEW.auteur_id,NEW.cree_at)
    IS DISTINCT FROM (OLD.societe_id,OLD.employe_id,OLD.nature,OLD.date_octroi,OLD.montant,OLD.retenue_mensuelle,OLD.mode_versement,OLD.motif,OLD.auteur_id,OLD.cree_at) THEN
  RAISE EXCEPTION 'Avance figée : annuler et ressaisir' USING ERRCODE='23514';END IF;
 IF OLD.statut='ANNULEE' THEN RAISE EXCEPTION 'Avance annulée : aucune modification' USING ERRCODE='23514';END IF;
 IF OLD.ecriture_id IS NOT NULL AND NEW.ecriture_id IS NOT NULL AND NEW.ecriture_id<>OLD.ecriture_id THEN RAISE EXCEPTION 'Avance déjà comptabilisée' USING ERRCODE='23514';END IF;
 IF NEW.statut='ANNULEE' AND (EXISTS(SELECT 1 FROM public.ecritures e WHERE e.id=OLD.ecriture_id AND e.est_validee) OR EXISTS(
   SELECT 1 FROM public.paie_bulletins b CROSS JOIN LATERAL jsonb_array_elements(b.contenu->'retenues_avances') r
   WHERE b.societe_id=OLD.societe_id AND b.statut='VALIDE' AND r->>'avance_id'=OLD.id::text)) THEN
  RAISE EXCEPTION 'Avance comptabilisée ou déjà retenue sur un bulletin : annulation impossible' USING ERRCODE='23514';END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_paie_avances131 ON public.paie_avances;
CREATE TRIGGER trg_paie_avances131 BEFORE UPDATE OR DELETE ON public.paie_avances FOR EACH ROW EXECUTE FUNCTION public.hisabpro_paie_avances131();
DROP TRIGGER IF EXISTS trg_paie_avances131_truncate ON public.paie_avances;
CREATE TRIGGER trg_paie_avances131_truncate BEFORE TRUNCATE ON public.paie_avances FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_paie_avances131();
REVOKE ALL ON public.paie_avances FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN GRANT SELECT,INSERT,UPDATE ON public.paie_bulletins TO hisabpro;GRANT USAGE,SELECT ON SEQUENCE public.paie_bulletins_id_seq TO hisabpro;
  GRANT SELECT,INSERT,UPDATE ON public.paie_avances TO hisabpro;GRANT USAGE,SELECT ON SEQUENCE public.paie_avances_id_seq TO hisabpro;END IF;
END $$;
COMMIT;
