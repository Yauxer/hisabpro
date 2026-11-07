-- Patch 058 : corrige les permissions manquantes de la migration 055.
-- À exécuter dans la base HisabPro, via pgAdmin avec le propriétaire des objets
-- (ou un superutilisateur PostgreSQL), et NON avec le compte de l'application.
-- Le rôle de connexion applicative attendu ici est « hisabpro » ; si votre
-- DATABASE_URL utilise un autre rôle, adaptez la variable v_role ci-dessous.
-- Migration idempotente ; elle ne modifie aucune donnée comptable.
BEGIN;
DO $hisabpro_permissions$
DECLARE
    v_role name := 'hisabpro';
    v_sequence text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_role) THEN
        RAISE EXCEPTION 'Rôle PostgreSQL % introuvable : vérifiez le rôle de connexion du backend.', v_role;
    END IF;
    IF to_regclass('public.plan_comptable_cgnc_reference') IS NULL
       OR to_regclass('public.comptes_societe') IS NULL THEN
        RAISE EXCEPTION 'Tables du patch 055 manquantes : exécutez d’abord 055_plan_comptable_societe_exercices_decales.sql.';
    END IF;

    -- Le référentiel commun est fourni par les migrations : lecture uniquement.
    EXECUTE format('GRANT USAGE ON SCHEMA public TO %I', v_role);
    EXECUTE format('GRANT SELECT ON TABLE public.plan_comptable_cgnc_reference TO %I', v_role);

    -- Le plan personnalisé appartient à chaque société : accès applicatif.
    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.comptes_societe TO %I', v_role);

    -- INSERT sur comptes_societe nécessite aussi le droit sur son compteur id.
    v_sequence := pg_get_serial_sequence('public.comptes_societe', 'id');
    IF v_sequence IS NULL THEN
        RAISE EXCEPTION 'Séquence d’identifiants comptes_societe.id introuvable.';
    END IF;
    EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO %I', v_sequence::regclass, v_role);
END;
$hisabpro_permissions$;
COMMIT;
