-- Application manuelle par le rôle migrateur, après le schéma bancaire,
-- 048 et 084. Aucun bootstrap, rôle, document ou mouvement comptable créé.
BEGIN;
DO $$
DECLARE
    nom_table text;
    sequence_id text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        RETURN;
    END IF;
    -- La suppression publique d'une banque est une désactivation : pas DELETE.
    GRANT SELECT, INSERT, UPDATE ON public.comptes_bancaires TO hisabpro;
    -- Le flux existant permet de supprimer un relevé non rapproché et non clos.
    GRANT SELECT, INSERT, UPDATE, DELETE ON public.rapprochement_lignes TO hisabpro;
    FOREACH nom_table IN ARRAY ARRAY['comptes_bancaires','rapprochement_lignes'] LOOP
        sequence_id := pg_get_serial_sequence(format('public.%I',nom_table),'id');
        IF sequence_id IS NOT NULL THEN
            EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO hisabpro',sequence_id::regclass);
        END IF;
    END LOOP;
    -- Aucun TRUNCATE, CREATE ou nouveau UPDATE/SETVAL de séquence.
    -- Les droits des états048 et des ventilations084 restent inchangés.
END $$;
COMMIT;
