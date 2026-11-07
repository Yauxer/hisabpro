-- Patch 09.2 — ETIC (Etat des Informations Complémentaires)
-- A exécuter après 025_css_credits_is.sql.
-- Le patch 020 reste volontairement indépendant / non requis.
BEGIN;

CREATE TABLE IF NOT EXISTS etic_sections_exercice (
    id BIGSERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice INTEGER NOT NULL,
    code VARCHAR(10) NOT NULL,
    contenu JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_by INTEGER REFERENCES utilisateurs(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_etic_section_societe_exercice_code UNIQUE (societe_id, exercice, code),
    CONSTRAINT ck_etic_section_code CHECK (
        code IN (
            'A1','A2','A3',
            'B1','B2','B2bis','B3','B4','B5','B6','B7','B8','B9','B10','B11','B12','B13','B14',
            'C1','C2','C3','C4','C5'
        )
    )
);

CREATE INDEX IF NOT EXISTS ix_etic_sections_societe_exercice
    ON etic_sections_exercice (societe_id, exercice);

-- Mise à jour automatique de la date de modification.
CREATE OR REPLACE FUNCTION hisabpro_touch_etic_section()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_hisabpro_touch_etic_section ON etic_sections_exercice;
CREATE TRIGGER trg_hisabpro_touch_etic_section
BEFORE UPDATE ON etic_sections_exercice
FOR EACH ROW EXECUTE FUNCTION hisabpro_touch_etic_section();

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE etic_sections_exercice TO hisabpro;
GRANT USAGE, SELECT ON SEQUENCE etic_sections_exercice_id_seq TO hisabpro;

COMMIT;
