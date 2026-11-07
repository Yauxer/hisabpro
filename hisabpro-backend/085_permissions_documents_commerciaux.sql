-- Application manuelle explicite par un rôle migrateur distinct.
-- Complément fermé de077/079 :devis,commandes etlivraisons/réceptions.
-- Schéma commercial existant requis ;aucune table,donnée ou rôle créé.
-- Aucune permission supplémentaire sur audit,archive ou objet des autres modules.
BEGIN;
DO $$
DECLARE
    nom_table text;
    sequence_id text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        RETURN;
    END IF;
    GRANT SELECT, INSERT, UPDATE, DELETE ON public.devis, public.lignes_devis,
        public.bons_commande, public.lignes_bon_commande,
        public.bons_livraison, public.lignes_bon_livraison TO hisabpro;
    FOREACH nom_table IN ARRAY ARRAY[
        'devis','lignes_devis','bons_commande','lignes_bon_commande',
        'bons_livraison','lignes_bon_livraison'
    ] LOOP
        sequence_id := pg_get_serial_sequence(format('public.%I',nom_table),'id');
        IF sequence_id IS NOT NULL THEN
            EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO hisabpro',sequence_id::regclass);
        END IF;
    END LOOP;
    -- Ni TRUNCATE ni SETVAL/UPDATE de séquence ajouté. Droits hérités conservés.
    -- Les contrôles API/RBAC,multi-société etles déclencheurs métier restent requis.
END $$;
COMMIT;
