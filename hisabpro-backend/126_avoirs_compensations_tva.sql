-- Qualification explicite des compensations. Aucun historique n'est présumé signé.
-- À exécuter avec le rôle de migration, après sauvegarde et recette sur copie isolée.
BEGIN;
ALTER TABLE public.utilisations_avoirs
 ADD COLUMN IF NOT EXISTS date_acceptation_compensation date,
 ADD COLUMN IF NOT EXISTS date_annulation_effective date;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint
                WHERE conrelid='public.utilisations_avoirs'::regclass
                  AND conname='ck_utilisations_compensation126') THEN
  ALTER TABLE public.utilisations_avoirs ADD CONSTRAINT ck_utilisations_compensation126
   CHECK (date_acceptation_compensation IS NULL OR
          (type_utilisation='imputation' AND date_acceptation_compensation=date_utilisation
           AND reference IS NOT NULL AND length(btrim(reference))>0));
 END IF;
END $$;
COMMIT;
