-- Patch 02C — intégrité des dates effectives chèques/effets
-- PostgreSQL. À exécuter avec un compte propriétaire/admin.
--
-- IMPORTANT : on n'invente PAS de date pour les anciennes lignes incohérentes.
-- La contrainte NOT VALID protège immédiatement les nouvelles écritures/modifications
-- sans échouer à cause d'un historique éventuel à régulariser manuellement.

BEGIN;

ALTER TABLE reglements
    DROP CONSTRAINT IF EXISTS ck_reglements_statut_date_effective;

ALTER TABLE reglements
    ADD CONSTRAINT ck_reglements_statut_date_effective
    CHECK (statut NOT IN ('encaisse', 'paye') OR date_encaissement IS NOT NULL)
    NOT VALID;

-- Droits applicatifs (utile lorsque la migration est exécutée avec postgres/pgAdmin).
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE reglements TO hisabpro;
    END IF;
END $$;

COMMIT;

-- Diagnostic à exécuter après migration :
-- SELECT id, facture_id, date, mode, statut, date_echeance, date_encaissement, montant
-- FROM reglements
-- WHERE statut IN ('encaisse', 'paye') AND date_encaissement IS NULL
-- ORDER BY id;
--
-- Quand toutes les anciennes lignes ont été corrigées avec leur VRAIE date :
-- ALTER TABLE reglements VALIDATE CONSTRAINT ck_reglements_statut_date_effective;
