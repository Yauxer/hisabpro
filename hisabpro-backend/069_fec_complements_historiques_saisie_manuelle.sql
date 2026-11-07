-- Patch 098 / migration 069 — Saisie manuelle contrôlée des compléments FEC historiques
--
-- La table ligne_auxiliaire_complements reste append-only. Cette migration
-- n'altère aucune écriture comptable et n'autorise ni UPDATE ni DELETE.
-- Elle permet simplement à l'utilisateur applicatif d'ajouter, via l'API
-- contrôlée HisabPro, le tiers exact d'une ancienne ligne 3421/4411 lorsque
-- ce rattachement ne pouvait pas être déduit automatiquement.

BEGIN;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        GRANT SELECT, INSERT ON TABLE ligne_auxiliaire_complements TO hisabpro;
        GRANT USAGE, SELECT ON SEQUENCE ligne_auxiliaire_complements_id_seq TO hisabpro;
    END IF;
END $$;

COMMIT;
