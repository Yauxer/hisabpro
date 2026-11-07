BEGIN;

-- Patch 06A — inventaire physique figé + rapprochement comptable du stock final.

ALTER TABLE familles_articles
    ADD COLUMN IF NOT EXISTS compte_stock VARCHAR(10) DEFAULT '3111';
ALTER TABLE familles_articles
    ADD COLUMN IF NOT EXISTS compte_variation_stock VARCHAR(10) DEFAULT '6114';

UPDATE familles_articles SET compte_stock = '3111'
WHERE compte_stock IS NULL OR btrim(compte_stock) = '';
UPDATE familles_articles SET compte_variation_stock = '6114'
WHERE compte_variation_stock IS NULL OR btrim(compte_variation_stock) = '';

CREATE TABLE IF NOT EXISTS inventaires_stock (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    exercice INTEGER NOT NULL,
    date_inventaire DATE NOT NULL,
    reference VARCHAR(100) NOT NULL,
    note VARCHAR(500),
    total_valeur NUMERIC(18,2) NOT NULL DEFAULT 0,
    total_perte NUMERIC(18,2) NOT NULL DEFAULT 0,
    total_excedent NUMERIC(18,2) NOT NULL DEFAULT 0,
    ecriture_stock_id INTEGER REFERENCES ecritures(id) ON DELETE SET NULL,
    cree_par INTEGER REFERENCES utilisateurs(id),
    validee_le TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_inventaire_stock_societe_reference UNIQUE (societe_id, reference)
);

CREATE INDEX IF NOT EXISTS ix_inventaires_stock_societe_exercice
    ON inventaires_stock (societe_id, exercice, date_inventaire);

CREATE TABLE IF NOT EXISTS inventaires_stock_lignes (
    id SERIAL PRIMARY KEY,
    inventaire_id INTEGER NOT NULL REFERENCES inventaires_stock(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES articles(id),
    code VARCHAR(50) NOT NULL,
    designation VARCHAR(300) NOT NULL,
    quantite_theorique NUMERIC(18,4) NOT NULL DEFAULT 0,
    quantite_reelle NUMERIC(18,4) NOT NULL DEFAULT 0,
    ecart_quantite NUMERIC(18,4) NOT NULL DEFAULT 0,
    cmup NUMERIC(18,4) NOT NULL DEFAULT 0,
    valeur_stock NUMERIC(18,2) NOT NULL DEFAULT 0,
    valeur_ecart NUMERIC(18,2) NOT NULL DEFAULT 0,
    compte_stock VARCHAR(10) NOT NULL DEFAULT '3111',
    compte_variation VARCHAR(10) NOT NULL DEFAULT '6114',
    CONSTRAINT uq_inventaire_stock_ligne_article UNIQUE (inventaire_id, article_id),
    CONSTRAINT ck_inventaire_stock_qte_reelle_non_negative CHECK (quantite_reelle >= 0)
);

CREATE INDEX IF NOT EXISTS ix_inventaires_stock_lignes_inventaire
    ON inventaires_stock_lignes (inventaire_id);

-- Le rôle applicatif doit pouvoir exploiter les nouvelles tables même si la
-- migration est exécutée depuis pgAdmin avec un propriétaire différent.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE inventaires_stock TO hisabpro;
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE inventaires_stock_lignes TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE inventaires_stock_id_seq TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE inventaires_stock_lignes_id_seq TO hisabpro;
    END IF;
END $$;

COMMIT;
