-- FACT.8 — Échéanciers de paiement & acomptes avancés
BEGIN;

CREATE TABLE IF NOT EXISTS echeances_facture (
    id BIGSERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    facture_id INTEGER NOT NULL REFERENCES factures(id) ON DELETE CASCADE,
    ordre SMALLINT NOT NULL,
    date_echeance DATE NOT NULL,
    montant NUMERIC(18,2) NOT NULL,
    libelle VARCHAR(120),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_echeance_facture_ordre CHECK (ordre > 0),
    CONSTRAINT ck_echeance_facture_montant CHECK (montant > 0),
    CONSTRAINT uq_echeance_facture_ordre UNIQUE (facture_id, ordre)
);

CREATE INDEX IF NOT EXISTS ix_echeances_facture_societe_date
    ON echeances_facture(societe_id, date_echeance, facture_id);
CREATE INDEX IF NOT EXISTS ix_echeances_facture_facture
    ON echeances_facture(facture_id, ordre);

CREATE TABLE IF NOT EXISTS imputations_acomptes (
    id BIGSERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    acompte_id INTEGER NOT NULL REFERENCES acomptes(id) ON DELETE RESTRICT,
    facture_id INTEGER NOT NULL REFERENCES factures(id) ON DELETE RESTRICT,
    date_imputation DATE NOT NULL DEFAULT CURRENT_DATE,
    montant NUMERIC(18,2) NOT NULL,
    est_comptabilisee BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_imputation_acompte_montant CHECK (montant > 0)
);

CREATE INDEX IF NOT EXISTS ix_imputations_acomptes_acompte
    ON imputations_acomptes(societe_id, acompte_id, date_imputation);
CREATE INDEX IF NOT EXISTS ix_imputations_acomptes_facture
    ON imputations_acomptes(societe_id, facture_id, date_imputation);

-- Backfill des anciennes imputations 1 acompte -> 1 facture.
INSERT INTO imputations_acomptes (
    societe_id, acompte_id, facture_id, date_imputation, montant, est_comptabilisee
)
SELECT
    a.societe_id,
    a.id,
    a.facture_id,
    COALESCE(a.date_imputation, a.date),
    a.montant,
    COALESCE(a.est_imputee_compta, FALSE)
FROM acomptes a
WHERE a.facture_id IS NOT NULL
  AND a.statut = 'impute'
  AND a.montant > 0
  AND NOT EXISTS (
      SELECT 1 FROM imputations_acomptes ia WHERE ia.acompte_id = a.id
  );

-- Le rôle applicatif doit pouvoir utiliser les nouvelles tables même si la
-- migration a été exécutée par un rôle administrateur PostgreSQL.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE echeances_facture TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE echeances_facture_id_seq TO hisabpro;
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE imputations_acomptes TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE imputations_acomptes_id_seq TO hisabpro;
    END IF;
END $$;

COMMIT;
