-- Patch 090 : élargit la source de compte des retraitements fiscaux.
--
-- Le moteur fiscal peut proposer plusieurs comptes ou un libellé descriptif
-- (ex. "Comptes de charges concernés"). La limite historique VARCHAR(20)
-- provoquait un HTTP 422 côté API avant même l'insertion en base.
-- Migration idempotente / rejouable.

ALTER TABLE fiscal_retraitements
    ALTER COLUMN compte_source TYPE VARCHAR(120);
