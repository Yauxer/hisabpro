-- BALANCE / GRAND LIVRE FINAL — index de reporting comptable
-- À exécuter APRÈS 049_lettrage_final.sql.
BEGIN;

-- Les états comptables ne lisent que les écritures définitives d'une société,
-- d'un exercice et d'une plage de dates. Cet index partiel évite de parcourir
-- les brouillons lorsque le volume augmente.
CREATE INDEX IF NOT EXISTS ix_ecritures_reporting_definitif
    ON ecritures (societe_id, exercice, date, id)
    WHERE est_validee = TRUE AND numero_ecriture IS NOT NULL;

-- Le grand livre et les balances agrègent ensuite par compte.
CREATE INDEX IF NOT EXISTS ix_lignes_ecriture_reporting_compte
    ON lignes_ecriture (compte, ecriture_id, id);

-- La résolution prudente des auxiliaires utilise les comptes paramétrés sur les
-- fiches tiers, y compris pour les tiers historiques devenus inactifs.
CREATE INDEX IF NOT EXISTS ix_tiers_reporting_compte_client
    ON tiers (societe_id, compte_client, id);
CREATE INDEX IF NOT EXISTS ix_tiers_reporting_compte_fournisseur
    ON tiers (societe_id, compte_fournisseur, id);

COMMIT;
