-- FACT.6 — Avoirs, retours et annulations robustes
-- À exécuter après 030_facturation_durcissement.sql.

ALTER TABLE avoirs
    ADD COLUMN IF NOT EXISTS retour_stock BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS remise_globale_snapshot DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS ristourne_snapshot DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS escompte_snapshot DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS nature_tva_achat_snapshot VARCHAR(30),
    ADD COLUMN IF NOT EXISTS tva_deductible_pct_snapshot NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS date_annulation TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS annulee_par INTEGER NULL REFERENCES utilisateurs(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS ecriture_annulation_id INTEGER NULL REFERENCES ecritures(id) ON DELETE SET NULL;

ALTER TABLE lignes_avoir
    ADD COLUMN IF NOT EXISTS facture_ligne_id INTEGER NULL REFERENCES lignes_facture(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS article_id INTEGER NULL REFERENCES articles(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS remise2 DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS rabais DOUBLE PRECISION NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS ix_lignes_avoir_facture_ligne
    ON lignes_avoir(facture_ligne_id);
CREATE INDEX IF NOT EXISTS ix_lignes_avoir_article
    ON lignes_avoir(article_id);

-- Une même ligne de facture ne peut apparaître qu'une fois dans un même avoir.
CREATE UNIQUE INDEX IF NOT EXISTS ux_lignes_avoir_source_par_avoir
    ON lignes_avoir(avoir_id, facture_ligne_id)
    WHERE facture_ligne_id IS NOT NULL;

-- Quantités strictement positives pour les nouvelles lignes.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_lignes_avoir_quantite_positive'
    ) THEN
        ALTER TABLE lignes_avoir
            ADD CONSTRAINT ck_lignes_avoir_quantite_positive CHECK (quantite > 0) NOT VALID;
    END IF;
END $$;
