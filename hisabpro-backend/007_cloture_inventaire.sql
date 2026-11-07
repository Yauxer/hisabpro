-- Patch 04 — Clôture & écritures d'inventaire
-- À exécuter avec un compte pouvant modifier le schéma (ex. postgres).

BEGIN;

CREATE TABLE IF NOT EXISTS ajustements_inventaire (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    exercice INTEGER NOT NULL,
    type VARCHAR(30) NOT NULL,
    libelle VARCHAR(300) NOT NULL,
    montant NUMERIC(18,2) NOT NULL,
    compte_activite VARCHAR(10) NOT NULL,
    compte_contrepartie VARCHAR(10) NOT NULL,
    ecriture_id INTEGER NULL REFERENCES ecritures(id) ON DELETE SET NULL,
    contrepassation_id INTEGER NULL REFERENCES ecritures(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT ck_ajustement_inventaire_montant_positif CHECK (montant > 0),
    CONSTRAINT ck_ajustement_inventaire_type CHECK (
        type IN ('cca','pca','fnp','fae','provision_risque','depreciation_client','depreciation_stock')
    )
);

CREATE INDEX IF NOT EXISTS ix_ajustements_inventaire_societe_exercice
    ON ajustements_inventaire (societe_id, exercice);

-- Le résultat de clôture est monétaire : NUMERIC plutôt que FLOAT.
ALTER TABLE clotures_exercice
    ALTER COLUMN resultat_net TYPE NUMERIC(18,2)
    USING ROUND(COALESCE(resultat_net, 0)::numeric, 2);

-- Si les migrations sont exécutées avec postgres alors que l'application utilise
-- le rôle hisabpro, accorder explicitement les droits (évite le problème rencontré
-- sur tva_parametres_exercice).
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE ajustements_inventaire TO hisabpro';
        EXECUTE 'GRANT USAGE, SELECT, UPDATE ON SEQUENCE ajustements_inventaire_id_seq TO hisabpro';
    END IF;
END $$;

COMMIT;
