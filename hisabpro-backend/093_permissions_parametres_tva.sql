-- HisabPro093 : paramètres TVA, après092, sous le propriétaire des tables.
-- Aucun taux, formule, donnée ni paramètre existant modifié.
BEGIN;
DO $$
DECLARE sequence_id text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        RETURN;
    END IF;
    GRANT SELECT, INSERT ON public.tva_parametres_exercice TO hisabpro;
    GRANT UPDATE (credit_ouverture,prorata_deduction_pct,updated_at)
        ON public.tva_parametres_exercice TO hisabpro;
    sequence_id := pg_get_serial_sequence('public.tva_parametres_exercice','id');
    IF sequence_id IS NOT NULL THEN
        -- Les anciennes005/008 accordaient UPDATE sur toutes les séquences.
        -- nextval suffit au flux ; retirer ce SETVAL hérité sur la seule TVA.
        EXECUTE format('REVOKE UPDATE ON SEQUENCE %s FROM hisabpro',sequence_id::regclass);
        EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO hisabpro',sequence_id::regclass);
    END IF;
    -- Aucun UPDATE global, DELETE, TRUNCATE, CREATE, SETVAL ou droit d'identité.
END $$;
COMMIT;
