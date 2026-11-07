-- Dates comptables d'annulation et de rejet d'un règlement, pour la TVA sur encaissements.
-- Additive et rejouable. Aucun historique n'est daté : les anciennes annulations
-- restent NULL et sont lues via la date de leur écriture de contrepassation.
-- À exécuter avec le rôle de migration, après sauvegarde et recette sur copie isolée.
BEGIN;
ALTER TABLE public.reglements
 ADD COLUMN IF NOT EXISTS date_annulation_effective date,
 ADD COLUMN IF NOT EXISTS date_rejet_effective date;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint
                WHERE conrelid='public.reglements'::regclass
                  AND conname='ck_reglements_annulation_effective127') THEN
  ALTER TABLE public.reglements ADD CONSTRAINT ck_reglements_annulation_effective127
   CHECK (date_annulation_effective IS NULL OR statut='annule');
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint
                WHERE conrelid='public.reglements'::regclass
                  AND conname='ck_reglements_rejet_effectif127') THEN
  ALTER TABLE public.reglements ADD CONSTRAINT ck_reglements_rejet_effectif127
   CHECK (date_rejet_effective IS NULL OR statut='rejete');
 END IF;
END $$;
COMMIT;
