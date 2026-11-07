-- Régimes déclarés :aucune affiliation,exonération ou formule déduite.
BEGIN;
ALTER TABLE public.personnel_contrats_versions ADD COLUMN IF NOT EXISTS regime_amo varchar(120);
ALTER TABLE public.personnel_contrats_versions ADD COLUMN IF NOT EXISTS regime_retraite varchar(120);
ALTER TABLE public.personnel_contrats_versions ADD COLUMN IF NOT EXISTS regime_mutuelle varchar(120);
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='public.personnel_contrats_versions'::regclass AND conname='ck_personnel_regimes110') THEN
  ALTER TABLE public.personnel_contrats_versions ADD CONSTRAINT ck_personnel_regimes110 CHECK (
    (regime_amo IS NULL OR length(btrim(regime_amo))>0) AND
    (regime_retraite IS NULL OR length(btrim(regime_retraite))>0) AND
    (regime_mutuelle IS NULL OR length(btrim(regime_mutuelle))>0));
 END IF;
END $$;
COMMIT;
