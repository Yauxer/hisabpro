-- Manifeste ferme : inscription et cycle direct facture/reglement uniquement.
-- Executer par un migrateur distinct du role applicatif, apres 074/075/076.
-- Ne cree aucun role et ne change aucune donnee ni protection metier.
BEGIN;
DO $$
DECLARE
    nom_table TEXT;
    sequence_id TEXT;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        RETURN;
    END IF;
    GRANT USAGE ON SCHEMA public TO hisabpro;
    -- Inscription, parametrage et preparation du plan/exercice.
    GRANT SELECT, INSERT, UPDATE ON public.societes, public.utilisateurs,
        public.modules_actifs, public.comptes_societe,
        public.exercices_comptables, public.periodes_comptables TO hisabpro;
    -- CRUD de brouillons et flux metier : triggers de validation conserves.
    GRANT SELECT, INSERT, UPDATE, DELETE ON public.tiers, public.familles_articles,
        public.articles, public.factures, public.lignes_facture, public.reglements,
        public.ecritures, public.lignes_ecriture TO hisabpro;
    GRANT SELECT, INSERT ON public.mouvements_stock TO hisabpro;
    -- Sources optionnelles seulement consultees dans le cycle direct.
    GRANT SELECT ON public.utilisateurs_societes, public.plan_comptable_cgnc_reference,
        public.clotures_exercice, public.facturation_sequences,
        public.devis, public.lignes_devis, public.bons_commande, public.lignes_bon_commande,
        public.bons_livraison, public.lignes_bon_livraison, public.avoirs, public.lignes_avoir,
        public.acomptes, public.imputations_acomptes, public.utilisations_avoirs,
        public.comptes_bancaires, public.tva_parametres_exercice,
        public.modeles_ecritures, public.lignes_modele TO hisabpro;
    -- nextval/currval des seules tables inserees ; aucun SETVAL (UPDATE).
    FOREACH nom_table IN ARRAY ARRAY[
        'societes','utilisateurs','modules_actifs','comptes_societe',
        'exercices_comptables','periodes_comptables','tiers','familles_articles',
        'articles','factures','lignes_facture','reglements','ecritures',
        'lignes_ecriture','mouvements_stock'
    ] LOOP
        sequence_id := pg_get_serial_sequence(format('public.%I', nom_table), 'id');
        IF sequence_id IS NOT NULL THEN
            EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO hisabpro', sequence_id::regclass);
        END IF;
    END LOOP;
END $$;
COMMIT;
