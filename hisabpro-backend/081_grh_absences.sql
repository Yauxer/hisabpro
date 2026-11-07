-- Gestion administrative des demandes ; aucun solde legal ni retenue de paie.
BEGIN;
-- Un contrat historique inconnu ne doit pas etre deduit. Les valeurs deja
-- saisies ou produites par une ancienne080 restent intactes car ambigues.
ALTER TABLE public.employes ALTER COLUMN type_contrat DROP DEFAULT;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_employes_id_societe' AND conrelid='public.employes'::regclass) THEN
  ALTER TABLE public.employes ADD CONSTRAINT uq_employes_id_societe UNIQUE (id,societe_id);
 END IF;
END $$;
CREATE TABLE IF NOT EXISTS public.grh_absences (
 id serial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 employe_id integer NOT NULL,
 type_absence varchar(20) NOT NULL,
 date_debut date NOT NULL,
 date_fin date NOT NULL,
 motif varchar(1000),
 statut varchar(20) NOT NULL DEFAULT 'demande',
 commentaire_decision varchar(1000),
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 decided_by integer REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now(),
 decided_at timestamp,
 CONSTRAINT uq_grh_absences_id_societe UNIQUE(id,societe_id),
 CONSTRAINT fk_grh_absences_employe_societe FOREIGN KEY(employe_id,societe_id) REFERENCES public.employes(id,societe_id),
 CONSTRAINT ck_grh_absences_dates CHECK(date_fin>=date_debut),
 CONSTRAINT ck_grh_absences_type CHECK(type_absence IN ('conge','absence','autre')),
 CONSTRAINT ck_grh_absences_statut CHECK(statut IN ('demande','approuve','refuse','annule'))
);
CREATE INDEX IF NOT EXISTS ix_grh_absences_societe_id ON public.grh_absences(societe_id);
CREATE INDEX IF NOT EXISTS ix_grh_absences_employe_id ON public.grh_absences(employe_id);
CREATE TABLE IF NOT EXISTS public.grh_absence_evenements (
 id serial PRIMARY KEY,
 absence_id integer NOT NULL,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 acteur_id integer NOT NULL REFERENCES public.utilisateurs(id),
 ancien_statut varchar(20),
 nouveau_statut varchar(20) NOT NULL,
 commentaire varchar(1000),
 created_at timestamp NOT NULL DEFAULT now(),
 CONSTRAINT fk_grh_absence_evenements_absence_societe FOREIGN KEY(absence_id,societe_id) REFERENCES public.grh_absences(id,societe_id),
 CONSTRAINT ck_grh_absence_evenements_statut CHECK(nouveau_statut IN ('demande','approuve','refuse','annule'))
);
CREATE INDEX IF NOT EXISTS ix_grh_absence_evenements_absence_id ON public.grh_absence_evenements(absence_id);
CREATE INDEX IF NOT EXISTS ix_grh_absence_evenements_societe_id ON public.grh_absence_evenements(societe_id);
CREATE OR REPLACE FUNCTION public.hisabpro_proteger_historique_grh()
RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 RAISE EXCEPTION 'L historique GRH est conserve : modification ou suppression interdite' USING ERRCODE='23514';
END $$;
DROP TRIGGER IF EXISTS trg_grh_historique_immutable ON public.grh_absence_evenements;
CREATE TRIGGER trg_grh_historique_immutable BEFORE UPDATE OR DELETE ON public.grh_absence_evenements
FOR EACH ROW EXECUTE FUNCTION public.hisabpro_proteger_historique_grh();
DROP TRIGGER IF EXISTS trg_grh_historique_truncate ON public.grh_absence_evenements;
CREATE TRIGGER trg_grh_historique_truncate BEFORE TRUNCATE ON public.grh_absence_evenements
FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_proteger_historique_grh();
REVOKE UPDATE, DELETE, TRUNCATE ON public.grh_absence_evenements FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT, INSERT ON public.grh_absences,public.grh_absence_evenements TO hisabpro;
  GRANT UPDATE (statut,commentaire_decision,decided_by,decided_at) ON public.grh_absences TO hisabpro;
  REVOKE UPDATE, DELETE, TRUNCATE ON public.grh_absence_evenements FROM hisabpro;
  GRANT USAGE, SELECT ON SEQUENCE public.grh_absences_id_seq,public.grh_absence_evenements_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
