-- Patch 060 : réparer la résolution de la fonction TVA lorsque les taux sont
-- stockés en DOUBLE PRECISION (frais de transport, emballage et lignes de facture).
-- Conserver la validation fiscale existante : NE PAS supprimer les triggers.
-- Exécuter sur la base HisabPro avec le propriétaire des fonctions (ou un admin).
BEGIN;

-- La règle de TVA de la migration 033 est l'unique source de vérité.
-- Si elle manque réellement, ne pas créer de règle fiscale de remplacement.
DO $verification_tva_060$
BEGIN
    IF to_regprocedure('public.hisabpro_tva_combinaison_valide(date,numeric,character varying)') IS NULL THEN
        RAISE EXCEPTION 'Fonction TVA de base absente : vérifier/appliquer d''abord 033_conformite_tva_frais.sql dans la base HisabPro.';
    END IF;
END;
$verification_tva_060$;

-- Surcharge exacte pour les colonnes SQLAlchemy Float / PostgreSQL float8.
-- Elle transmet la même date, qualification et taux (converti en NUMERIC)
-- à la fonction métier existante ; les contrôles restent inchangés.
CREATE OR REPLACE FUNCTION public.hisabpro_tva_combinaison_valide(
    p_date DATE,
    p_taux DOUBLE PRECISION,
    p_qualification VARCHAR
)
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
AS $fonction_tva_float8$
    SELECT public.hisabpro_tva_combinaison_valide(
        p_date, p_taux::NUMERIC, p_qualification
    );
$fonction_tva_float8$;

-- Le compte de l'application est « hisabpro » dans les migrations existantes.
-- Garder la migration compatible avec les instances utilisant un autre rôle.
DO $permissions_tva_060$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT EXECUTE ON FUNCTION public.hisabpro_tva_combinaison_valide(
            DATE, DOUBLE PRECISION, VARCHAR
        ) TO hisabpro;
    END IF;
END;
$permissions_tva_060$;

-- Vérifier les deux signatures et les résultats, sans créer de facture de test.
DO $verification_finale_060$
BEGIN
    IF to_regprocedure('public.hisabpro_tva_combinaison_valide(date,double precision,character varying)') IS NULL THEN
        RAISE EXCEPTION 'La surcharge TVA DOUBLE PRECISION n''a pas été créée.';
    END IF;
    IF public.hisabpro_tva_combinaison_valide(DATE '2025-11-10', 20.0::DOUBLE PRECISION, 'taxable'::VARCHAR) IS DISTINCT FROM TRUE
       OR public.hisabpro_tva_combinaison_valide(DATE '2025-11-10', 0.0::DOUBLE PRECISION, 'taxable'::VARCHAR) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'La surcharge TVA ne délègue pas correctement à la fonction NUMERIC.';
    END IF;
END;
$verification_finale_060$;

COMMIT;
