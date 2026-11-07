-- Personnel 1A.1 : installation sans activation ni habilitation implicite.
-- Appliquer après sauvegarde avec le rôle migrateur, jamais au démarrage.
BEGIN;
CREATE TABLE IF NOT EXISTS public.personnel_acces_societes (
    societe_id integer PRIMARY KEY REFERENCES public.societes(id),
    activee_par integer NOT NULL REFERENCES public.utilisateurs(id),
    activee_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motif varchar(500) NOT NULL CHECK (length(btrim(motif)) BETWEEN 1 AND 500)
);
CREATE TABLE IF NOT EXISTS public.personnel_habilitations (
    id serial PRIMARY KEY,
    societe_id integer NOT NULL REFERENCES public.societes(id),
    utilisateur_id integer NOT NULL REFERENCES public.utilisateurs(id),
    -- Identité historique de l'invitation, pas une FK bloquant sa révocation.
    liaison_id_snapshot integer CHECK (liaison_id_snapshot IS NULL OR liaison_id_snapshot>0),
    capacite varchar(80) NOT NULL CHECK (capacite IN (
        'personnel.lire_identite', 'personnel.lire_remuneration',
        'personnel.lire_identifiants_sensibles', 'personnel.audit_lire')),
    accordee_par integer NOT NULL REFERENCES public.utilisateurs(id),
    accordee_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motif varchar(500) NOT NULL CHECK (length(btrim(motif)) BETWEEN 1 AND 500),
    revoquee_par integer REFERENCES public.utilisateurs(id),
    revoquee_at timestamp,
    motif_revocation varchar(500),
    CONSTRAINT ck_personnel_habilitation_revocation CHECK (
        (revoquee_par IS NULL AND revoquee_at IS NULL AND motif_revocation IS NULL) OR
        (revoquee_par IS NOT NULL AND revoquee_at IS NOT NULL
         AND motif_revocation IS NOT NULL AND length(btrim(motif_revocation)) BETWEEN 1 AND 500))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_personnel_habilitation_active
    ON public.personnel_habilitations(societe_id,utilisateur_id,capacite) WHERE revoquee_at IS NULL;

CREATE OR REPLACE FUNCTION public.hisabpro_personnel_membre(s integer,u integer,admin_requis boolean)
RETURNS boolean LANGUAGE sql STABLE SET search_path=pg_catalog,public,pg_temp AS $$
 SELECT EXISTS (
  SELECT 1 FROM public.utilisateurs p WHERE p.id=u AND p.actif AND (
   (p.societe_id=s AND (NOT admin_requis OR p.role='admin')) OR
   (p.societe_id<>s AND EXISTS (SELECT 1 FROM public.utilisateurs_societes a WHERE a.utilisateur_id=p.id
    AND a.societe_id=s AND a.actif AND (NOT admin_requis OR a.role='admin')))))
$$;
CREATE OR REPLACE FUNCTION public.hisabpro_personnel_proteger_acces()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP IN ('DELETE','TRUNCATE') THEN
  RAISE EXCEPTION 'Historique des accès Personnel conservé' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME='personnel_acces_societes' THEN
  IF TG_OP<>'INSERT' THEN
   RAISE EXCEPTION 'La protection Personnel ne peut pas être désactivée silencieusement' USING ERRCODE='23514';
  END IF;
  IF NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.activee_par,true) THEN
   RAISE EXCEPTION 'Administrateur actif de la société requis' USING ERRCODE='23514';
  END IF;
 ELSE
  IF TG_OP='INSERT' THEN
   IF NEW.revoquee_at IS NOT NULL OR NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.accordee_par,true)
      OR NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.utilisateur_id,false) THEN
    RAISE EXCEPTION 'Habilitation Personnel hors périmètre ou déjà révoquée' USING ERRCODE='23514';
   END IF;
   IF NEW.liaison_id_snapshot IS DISTINCT FROM (
    SELECT a.id FROM public.utilisateurs u LEFT JOIN public.utilisateurs_societes a
     ON a.utilisateur_id=u.id AND a.societe_id=NEW.societe_id AND a.actif AND u.societe_id<>NEW.societe_id
     WHERE u.id=NEW.utilisateur_id) THEN
    RAISE EXCEPTION 'Invitation active différente de la source de l’habilitation' USING ERRCODE='23514';
   END IF;
  ELSE
   IF OLD.revoquee_at IS NOT NULL OR NEW.revoquee_at IS NULL OR
      ROW(NEW.id,NEW.societe_id,NEW.utilisateur_id,NEW.liaison_id_snapshot,NEW.capacite,NEW.accordee_par,NEW.accordee_at,NEW.motif)
      IS DISTINCT FROM ROW(OLD.id,OLD.societe_id,OLD.utilisateur_id,OLD.liaison_id_snapshot,OLD.capacite,OLD.accordee_par,OLD.accordee_at,OLD.motif)
      OR NOT public.hisabpro_personnel_membre(NEW.societe_id,NEW.revoquee_par,true) THEN
    RAISE EXCEPTION 'Seule une révocation tracée par un administrateur est permise' USING ERRCODE='23514';
   END IF;
  END IF;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_personnel_activation_protegee ON public.personnel_acces_societes;
CREATE TRIGGER trg_personnel_activation_protegee BEFORE INSERT OR UPDATE OR DELETE ON public.personnel_acces_societes
 FOR EACH ROW EXECUTE FUNCTION public.hisabpro_personnel_proteger_acces();
DROP TRIGGER IF EXISTS trg_personnel_activation_truncate ON public.personnel_acces_societes;
CREATE TRIGGER trg_personnel_activation_truncate BEFORE TRUNCATE ON public.personnel_acces_societes
 FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_personnel_proteger_acces();
DROP TRIGGER IF EXISTS trg_personnel_habilitation_protegee ON public.personnel_habilitations;
CREATE TRIGGER trg_personnel_habilitation_protegee BEFORE INSERT OR UPDATE OR DELETE ON public.personnel_habilitations
 FOR EACH ROW EXECUTE FUNCTION public.hisabpro_personnel_proteger_acces();
DROP TRIGGER IF EXISTS trg_personnel_habilitation_truncate ON public.personnel_habilitations;
CREATE TRIGGER trg_personnel_habilitation_truncate BEFORE TRUNCATE ON public.personnel_habilitations
 FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_personnel_proteger_acces();
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  REVOKE ALL ON public.personnel_acces_societes,public.personnel_habilitations FROM hisabpro;
  GRANT SELECT,INSERT ON public.personnel_acces_societes,public.personnel_habilitations TO hisabpro;
  GRANT UPDATE(revoquee_par,revoquee_at,motif_revocation) ON public.personnel_habilitations TO hisabpro;
  GRANT USAGE,SELECT ON SEQUENCE public.personnel_habilitations_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
