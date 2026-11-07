-- Application manuelle après052 et les protections comptables existantes.
-- Lecture de l'état post-clôture et insertion d'une décision par le flux métier.
BEGIN;
DO $$
DECLARE
    sequence_id text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        RETURN;
    END IF;
    GRANT SELECT, INSERT ON public.decisions_affectation_resultat TO hisabpro;
    sequence_id := pg_get_serial_sequence('public.decisions_affectation_resultat','id');
    IF sequence_id IS NOT NULL THEN
        EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO hisabpro',sequence_id::regclass);
    END IF;
    -- Trace définitive052 :aucun UPDATE,DELETE,TRUNCATE,CREATE ou nouveau SETVAL.
    -- Aucune décision,écriture ou donnée historique modifiée par ce script.
END $$;
COMMIT;
