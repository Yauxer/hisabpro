-- Application manuelle explicite par le rôle migrateur, après le schéma
-- facturation et les permissions077/079. Aucun bootstrap ni rôle créé.
-- Les droits des traces035/045 sont déjà présents : ils restent inchangés.
BEGIN;
DO $$
DECLARE
    nom_table text;
    sequence_id text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        RETURN;
    END IF;
    GRANT SELECT, INSERT, UPDATE ON public.acomptes, public.avoirs TO hisabpro;
    -- Une ligne d'avoir conserve la source figée ; aucun UPDATE ou DELETE ajouté.
    GRANT SELECT, INSERT ON public.lignes_avoir TO hisabpro;
    FOREACH nom_table IN ARRAY ARRAY['acomptes','avoirs','lignes_avoir'] LOOP
        sequence_id := pg_get_serial_sequence(format('public.%I',nom_table),'id');
        IF sequence_id IS NOT NULL THEN
            EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO hisabpro',sequence_id::regclass);
        END IF;
    END LOOP;
    -- Aucun DELETE, TRUNCATE, CREATE ou nouveau SETVAL/UPDATE de séquence.
    -- Annulations par les flux métier existants, sans effacer les documents.
END $$;
COMMIT;
