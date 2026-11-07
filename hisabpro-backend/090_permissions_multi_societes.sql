-- Application manuelle après le schéma multi-société et ses contraintes.
-- Aucun utilisateur, accès, rôle global ou donnée comptable créé/modifié.
BEGIN;
DO $$
DECLARE
    sequence_id text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        RETURN;
    END IF;
    -- Création/invitation et suppression d'un accès secondaire par les routes
    -- existantes ;le compte personnel reste dans utilisateurs,non supprimable ici.
    GRANT SELECT, INSERT, DELETE ON public.utilisateurs_societes TO hisabpro;
    -- Le flux ne modifie que rôle/activation :identités et création protégées.
    GRANT UPDATE (role,actif) ON public.utilisateurs_societes TO hisabpro;
    sequence_id := pg_get_serial_sequence('public.utilisateurs_societes','id');
    IF sequence_id IS NOT NULL THEN
        EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO hisabpro',sequence_id::regclass);
    END IF;
    -- Aucun UPDATE global de table,TRUNCATE,CREATE ou nouveau SETVAL.
END $$;
COMMIT;
