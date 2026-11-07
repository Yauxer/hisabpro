-- Patch 02A — TVA : régime figé sur facture + date fiscale d'encaissement
-- PostgreSQL. À exécuter APRÈS sauvegarde de la base.

BEGIN;

ALTER TABLE factures
    ADD COLUMN IF NOT EXISTS regime_tva VARCHAR(30);

ALTER TABLE factures
    ALTER COLUMN regime_tva SET DEFAULT 'encaissement';

-- Fige le régime actuellement paramétré sur les factures historiques qui n'en ont pas.
UPDATE factures f
SET regime_tva = COALESCE(s.regime_tva, 'encaissement')
FROM societes s
WHERE f.societe_id = s.id
  AND (f.regime_tva IS NULL OR f.regime_tva = '');

ALTER TABLE reglements
    ADD COLUMN IF NOT EXISTS date_encaissement DATE;

CREATE INDEX IF NOT EXISTS ix_reglements_date_encaissement
    ON reglements(date_encaissement);

-- Backfill uniquement les moyens dont la date du règlement est exploitable sans
-- inventer une date d'encaissement bancaire. Les chèques/effets historiques restent
-- volontairement NULL et seront signalés dans l'écran TVA.
UPDATE reglements r
SET date_encaissement = r.date
FROM factures f
WHERE r.facture_id = f.id
  AND r.date_encaissement IS NULL
  AND r.statut <> 'rejete'
  AND (
        r.mode NOT IN ('cheque', 'effet')
        OR (f.type = 'achat' AND r.mode = 'cheque')
      );

COMMIT;
