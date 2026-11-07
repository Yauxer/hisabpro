-- Provenance annuelle par société ; aucun taux ni paramètre historique modifié.
BEGIN;
CREATE TABLE IF NOT EXISTS public.paie_referentiel_versions (
 id serial PRIMARY KEY,
 societe_id integer NOT NULL REFERENCES public.societes(id),
 annee integer NOT NULL,
 version integer NOT NULL,
 empreinte varchar(64) NOT NULL,
 parametres json NOT NULL,
 sources json NOT NULL,
 regime varchar(200),
 commentaire varchar(2000),
 qualification varchar(30) NOT NULL,
 created_by integer NOT NULL REFERENCES public.utilisateurs(id),
 created_at timestamp NOT NULL DEFAULT now(),
 CONSTRAINT uq_paie_referentiel_version UNIQUE(societe_id,annee,version),
 CONSTRAINT ck_paie_referentiel_version CHECK(version>0),
 CONSTRAINT ck_paie_referentiel_annee CHECK(annee BETWEEN 2025 AND 2100),
 CONSTRAINT ck_paie_referentiel_qualification CHECK(qualification IN ('non_verifie','preuves_partielles'))
);
CREATE INDEX IF NOT EXISTS ix_paie_referentiel_versions_societe_id ON public.paie_referentiel_versions(societe_id);
CREATE OR REPLACE FUNCTION public.hisabpro_proteger_referentiel_paie()
RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 RAISE EXCEPTION 'Versions du référentiel paie conservées : modification ou suppression interdite' USING ERRCODE='23514';
END $$;
DROP TRIGGER IF EXISTS trg_paie_referentiel_immutable ON public.paie_referentiel_versions;
CREATE TRIGGER trg_paie_referentiel_immutable BEFORE UPDATE OR DELETE ON public.paie_referentiel_versions
FOR EACH ROW EXECUTE FUNCTION public.hisabpro_proteger_referentiel_paie();
DROP TRIGGER IF EXISTS trg_paie_referentiel_truncate ON public.paie_referentiel_versions;
CREATE TRIGGER trg_paie_referentiel_truncate BEFORE TRUNCATE ON public.paie_referentiel_versions
FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_proteger_referentiel_paie();
REVOKE UPDATE, DELETE, TRUNCATE ON public.paie_referentiel_versions FROM PUBLIC;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT, INSERT ON public.paie_referentiel_versions TO hisabpro;
  REVOKE UPDATE, DELETE, TRUNCATE ON public.paie_referentiel_versions FROM hisabpro;
  GRANT USAGE, SELECT ON SEQUENCE public.paie_referentiel_versions_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
