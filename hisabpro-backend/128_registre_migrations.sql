-- Registre des migrations appliquées à une base HisabPro. Additive et rejouable.
-- « executee » : script lancé par ops/migrations_hisabpro.py ;
-- « constatee » : présence déclarée par l'administrateur sur une base existante.
-- À exécuter avec le rôle de migration, après sauvegarde.
BEGIN;
CREATE TABLE IF NOT EXISTS public.hisabpro_migrations (
    fichier      text PRIMARY KEY,
    sha256       char(64) NOT NULL,
    mode         text NOT NULL CHECK (mode IN ('executee', 'constatee')),
    appliquee_le timestamptz NOT NULL DEFAULT now(),
    operateur    text NOT NULL DEFAULT current_user,
    note         text
);
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') AND current_user <> 'hisabpro' THEN
  REVOKE ALL ON public.hisabpro_migrations FROM hisabpro;
  GRANT SELECT ON public.hisabpro_migrations TO hisabpro;
 END IF;
END $$;
COMMIT;
