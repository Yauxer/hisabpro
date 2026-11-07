-- Complement ferme de077 : seules colonnes de detachement des sources.
-- Aucune modification de donnees ; aucune permission UPDATE sur table entiere.
BEGIN;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        GRANT UPDATE (facture_id, statut) ON public.bons_commande TO hisabpro;
        GRANT UPDATE (facture_id) ON public.bons_livraison TO hisabpro;
        GRANT UPDATE (facture_id, statut) ON public.devis TO hisabpro;
        GRANT UPDATE (facture_id) ON public.mouvements_stock TO hisabpro;
    END IF;
END $$;
COMMIT;
