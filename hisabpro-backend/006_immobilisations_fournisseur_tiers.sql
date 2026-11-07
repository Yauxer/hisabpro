-- Patch 03B — rattachement des immobilisations au référentiel fournisseurs
-- PostgreSQL

BEGIN;

ALTER TABLE immobilisations
    ADD COLUMN IF NOT EXISTS fournisseur_tiers_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_immobilisations_fournisseur_tiers'
    ) THEN
        ALTER TABLE immobilisations
            ADD CONSTRAINT fk_immobilisations_fournisseur_tiers
            FOREIGN KEY (fournisseur_tiers_id)
            REFERENCES tiers(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_immobilisations_fournisseur_tiers_id
    ON immobilisations(fournisseur_tiers_id);

-- Rattachement opportuniste des anciennes immobilisations lorsqu'un tiers portant
-- exactement le même nom existe déjà dans la même société.
UPDATE immobilisations i
SET fournisseur_tiers_id = (
    SELECT t.id
    FROM tiers t
    WHERE t.societe_id = i.societe_id
      AND t.actif = TRUE
      AND lower(trim(t.nom)) = lower(trim(i.fournisseur))
    ORDER BY t.id
    LIMIT 1
)
WHERE i.fournisseur_tiers_id IS NULL
  AND i.fournisseur IS NOT NULL
  AND trim(i.fournisseur) <> ''
  AND EXISTS (
      SELECT 1
      FROM tiers t
      WHERE t.societe_id = i.societe_id
        AND t.actif = TRUE
        AND lower(trim(t.nom)) = lower(trim(i.fournisseur))
  );

COMMIT;
