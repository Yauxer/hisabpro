-- Profil Personnel seul : aucun compte ni droit attribué automatiquement.
-- Déployer d'abord le code qui confine ce rôle sur toutes les instances.
BEGIN;
DO $$ BEGIN
 IF to_regclass('public.personnel_demandes_details') IS NULL THEN
  RAISE EXCEPTION 'Installer105 à108 avant109' USING ERRCODE='23514';
 END IF;
END $$;
ALTER TABLE public.utilisateurs DROP CONSTRAINT IF EXISTS ck_utilisateurs_role_hisabpro;
ALTER TABLE public.utilisateurs ADD CONSTRAINT ck_utilisateurs_role_hisabpro
 CHECK (role IN ('admin','comptable','lecture','personnel'));
ALTER TABLE public.utilisateurs_societes DROP CONSTRAINT IF EXISTS ck_utilisateurs_societes_role_hisabpro;
ALTER TABLE public.utilisateurs_societes ADD CONSTRAINT ck_utilisateurs_societes_role_hisabpro
 CHECK (role IN ('admin','comptable','lecture','personnel'));
COMMIT;
