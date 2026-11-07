BEGIN;

-- Patch 06C — moteur unique des mouvements de stock.
-- Les lignes historiques restent intactes ; on ajoute uniquement les métadonnées
-- nécessaires à la traçabilité, l'idempotence et aux annulations compensatoires.

ALTER TABLE mouvements_stock
    ADD COLUMN IF NOT EXISTS date_mouvement date,
    ADD COLUMN IF NOT EXISTS cmup_avant double precision,
    ADD COLUMN IF NOT EXISTS source_type varchar(40),
    ADD COLUMN IF NOT EXISTS source_id integer,
    ADD COLUMN IF NOT EXISTS source_ligne_id integer,
    ADD COLUMN IF NOT EXISTS cle_idempotence varchar(180),
    ADD COLUMN IF NOT EXISTS cree_par integer,
    ADD COLUMN IF NOT EXISTS annule_mouvement_id integer;

-- La date technique historique constitue le meilleur repère disponible pour les
-- anciens mouvements. Les nouvelles lignes utilisent la vraie date métier.
UPDATE mouvements_stock
SET date_mouvement = COALESCE(date_mouvement, created_at::date, CURRENT_DATE)
WHERE date_mouvement IS NULL;

ALTER TABLE mouvements_stock
    ALTER COLUMN date_mouvement SET DEFAULT CURRENT_DATE,
    ALTER COLUMN date_mouvement SET NOT NULL;

DO $$
BEGIN
    ALTER TABLE mouvements_stock
        ADD CONSTRAINT fk_mouvements_stock_cree_par
        FOREIGN KEY (cree_par) REFERENCES utilisateurs(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE mouvements_stock
        ADD CONSTRAINT fk_mouvements_stock_annule_mouvement
        FOREIGN KEY (annule_mouvement_id) REFERENCES mouvements_stock(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- NOT VALID : les éventuelles données legacy non conformes restent consultables,
-- mais toute nouvelle ligne doit respecter ces garde-fous.
DO $$
BEGIN
    ALTER TABLE mouvements_stock
        ADD CONSTRAINT ck_mouvements_stock_type_06c
        CHECK (type IN ('entree', 'sortie', 'correction')) NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE mouvements_stock
        ADD CONSTRAINT ck_mouvements_stock_quantite_positive_06c
        CHECK (quantite > 0) NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS ix_mouvements_stock_date_06c
    ON mouvements_stock (societe_id, article_id, date_mouvement, id);

CREATE INDEX IF NOT EXISTS ix_mouvements_stock_source_06c
    ON mouvements_stock (societe_id, source_type, source_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_mouvements_stock_idempotence_06c
    ON mouvements_stock (societe_id, cle_idempotence)
    WHERE cle_idempotence IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mouvements_stock_annulation_06c
    ON mouvements_stock (annule_mouvement_id)
    WHERE annule_mouvement_id IS NOT NULL;

-- Même précaution que pour les migrations TVA : l'application se connecte avec
-- le rôle hisabpro alors que pgAdmin est souvent lancé avec postgres.
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE mouvements_stock TO hisabpro;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE mouvements_stock_id_seq TO hisabpro;

COMMIT;
