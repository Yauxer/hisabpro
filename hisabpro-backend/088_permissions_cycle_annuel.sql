-- Application manuelle par le rôle migrateur après le schéma annuel,
-- protections038/052 et référentiels existants. Aucune donnée ni taux modifié.
BEGIN;
DO $$
DECLARE
    sequence_id text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        RETURN;
    END IF;
    -- Trace définitive : insertion par le flux de clôture, jamais UPDATE/DELETE.
    GRANT SELECT, INSERT ON public.clotures_exercice TO hisabpro;
    sequence_id := pg_get_serial_sequence('public.clotures_exercice','id');
    IF sequence_id IS NOT NULL THEN
        EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO hisabpro',sequence_id::regclass);
    END IF;
    -- Lectures nécessaires à la provenance paie et aux contrôles annuels.
    -- N'accorde aucune édition des référentiels sociaux globaux.
    GRANT SELECT ON public.bareme_ir, public.taux_cotisations, public.deductions_ir TO hisabpro;
    -- Aucun TRUNCATE, CREATE, nouveau UPDATE/SETVAL de séquence ou rôle créé.
END $$;
COMMIT;
