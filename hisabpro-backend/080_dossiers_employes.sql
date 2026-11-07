-- Dossier GRH optionnel ; aucun taux ni salaire historique modifié.
BEGIN;
ALTER TABLE public.employes ADD COLUMN IF NOT EXISTS matricule varchar(50);
ALTER TABLE public.employes ADD COLUMN IF NOT EXISTS numero_cnss varchar(50);
ALTER TABLE public.employes ADD COLUMN IF NOT EXISTS type_contrat varchar(20);
ALTER TABLE public.employes ADD COLUMN IF NOT EXISTS date_sortie date;
ALTER TABLE public.employes ADD COLUMN IF NOT EXISTS email varchar(254);
ALTER TABLE public.employes ADD COLUMN IF NOT EXISTS telephone varchar(50);
ALTER TABLE public.employes ADD COLUMN IF NOT EXISTS personnes_charge_ir integer;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_employes_personnes_charge_ir' AND conrelid='public.employes'::regclass) THEN
  ALTER TABLE public.employes ADD CONSTRAINT ck_employes_personnes_charge_ir CHECK (personnes_charge_ir IS NULL OR personnes_charge_ir BETWEEN 0 AND 6) NOT VALID;
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_employes_dates' AND conrelid='public.employes'::regclass) THEN
  ALTER TABLE public.employes ADD CONSTRAINT ck_employes_dates CHECK (date_sortie IS NULL OR date_embauche IS NULL OR date_sortie >= date_embauche) NOT VALID;
 END IF;
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
  GRANT SELECT, INSERT ON public.employes TO hisabpro;
  GRANT UPDATE (nom, poste, salaire_brut, situation_familiale, nb_enfants, date_embauche, matricule, numero_cnss, type_contrat, date_sortie, email, telephone, personnes_charge_ir, actif) ON public.employes TO hisabpro;
  GRANT USAGE, SELECT ON SEQUENCE public.employes_id_seq TO hisabpro;
 END IF;
END $$;
COMMIT;
