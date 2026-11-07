-- HisabPro — FACT.1
-- Fondations du cycle commercial : liens tiers/articles, traçabilité des lignes
-- et conservation des conditions commerciales jusqu'à la facture.
-- Compatible avec les documents historiques : tous les nouveaux liens sont nullable.

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1) Lien technique vers le tiers
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE factures       ADD COLUMN IF NOT EXISTS tiers_id INTEGER;
ALTER TABLE devis          ADD COLUMN IF NOT EXISTS tiers_id INTEGER;
ALTER TABLE bons_commande  ADD COLUMN IF NOT EXISTS tiers_id INTEGER;
ALTER TABLE bons_livraison ADD COLUMN IF NOT EXISTS tiers_id INTEGER;

-- Snapshot légal du tiers sur la facture : l'historique ne dépend plus des
-- modifications futures de la fiche client/fournisseur.
ALTER TABLE factures ADD COLUMN IF NOT EXISTS tiers_ice_snapshot VARCHAR(20);
ALTER TABLE factures ADD COLUMN IF NOT EXISTS tiers_if_snapshot VARCHAR(50);
ALTER TABLE factures ADD COLUMN IF NOT EXISTS tiers_rc_snapshot VARCHAR(50);
ALTER TABLE factures ADD COLUMN IF NOT EXISTS tiers_adresse_snapshot TEXT;
ALTER TABLE factures ADD COLUMN IF NOT EXISTS tiers_ville_snapshot VARCHAR(100);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2) Lien article + filiation des lignes
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE lignes_devis ADD COLUMN IF NOT EXISTS article_id INTEGER;

ALTER TABLE lignes_bon_commande ADD COLUMN IF NOT EXISTS article_id INTEGER;
ALTER TABLE lignes_bon_commande ADD COLUMN IF NOT EXISTS source_ligne_devis_id INTEGER;
ALTER TABLE lignes_bon_commande ADD COLUMN IF NOT EXISTS tva DOUBLE PRECISION DEFAULT 20;
ALTER TABLE lignes_bon_commande ADD COLUMN IF NOT EXISTS remise DOUBLE PRECISION DEFAULT 0;
ALTER TABLE lignes_bon_commande ADD COLUMN IF NOT EXISTS remise2 DOUBLE PRECISION DEFAULT 0;
ALTER TABLE lignes_bon_commande ADD COLUMN IF NOT EXISTS rabais DOUBLE PRECISION DEFAULT 0;

ALTER TABLE lignes_bon_livraison ADD COLUMN IF NOT EXISTS article_id INTEGER;
ALTER TABLE lignes_bon_livraison ADD COLUMN IF NOT EXISTS source_ligne_bc_id INTEGER;
ALTER TABLE lignes_bon_livraison ADD COLUMN IF NOT EXISTS prix_unitaire DOUBLE PRECISION DEFAULT 0;
ALTER TABLE lignes_bon_livraison ADD COLUMN IF NOT EXISTS tva DOUBLE PRECISION DEFAULT 20;
ALTER TABLE lignes_bon_livraison ADD COLUMN IF NOT EXISTS remise DOUBLE PRECISION DEFAULT 0;
ALTER TABLE lignes_bon_livraison ADD COLUMN IF NOT EXISTS remise2 DOUBLE PRECISION DEFAULT 0;
ALTER TABLE lignes_bon_livraison ADD COLUMN IF NOT EXISTS rabais DOUBLE PRECISION DEFAULT 0;

ALTER TABLE lignes_facture ADD COLUMN IF NOT EXISTS article_id INTEGER;
ALTER TABLE lignes_facture ADD COLUMN IF NOT EXISTS source_ligne_devis_id INTEGER;
ALTER TABLE lignes_facture ADD COLUMN IF NOT EXISTS source_ligne_bc_id INTEGER;
ALTER TABLE lignes_facture ADD COLUMN IF NOT EXISTS source_ligne_bl_id INTEGER;

-- Normalise les nouvelles colonnes financières avant NOT NULL.
UPDATE lignes_bon_commande
SET tva = COALESCE(tva, 20), remise = COALESCE(remise, 0),
    remise2 = COALESCE(remise2, 0), rabais = COALESCE(rabais, 0);
UPDATE lignes_bon_livraison
SET prix_unitaire = COALESCE(prix_unitaire, 0), tva = COALESCE(tva, 20),
    remise = COALESCE(remise, 0), remise2 = COALESCE(remise2, 0), rabais = COALESCE(rabais, 0);

ALTER TABLE lignes_bon_commande ALTER COLUMN tva SET DEFAULT 20;
ALTER TABLE lignes_bon_commande ALTER COLUMN remise SET DEFAULT 0;
ALTER TABLE lignes_bon_commande ALTER COLUMN remise2 SET DEFAULT 0;
ALTER TABLE lignes_bon_commande ALTER COLUMN rabais SET DEFAULT 0;
ALTER TABLE lignes_bon_commande ALTER COLUMN tva SET NOT NULL;
ALTER TABLE lignes_bon_commande ALTER COLUMN remise SET NOT NULL;
ALTER TABLE lignes_bon_commande ALTER COLUMN remise2 SET NOT NULL;
ALTER TABLE lignes_bon_commande ALTER COLUMN rabais SET NOT NULL;

ALTER TABLE lignes_bon_livraison ALTER COLUMN prix_unitaire SET DEFAULT 0;
ALTER TABLE lignes_bon_livraison ALTER COLUMN tva SET DEFAULT 20;
ALTER TABLE lignes_bon_livraison ALTER COLUMN remise SET DEFAULT 0;
ALTER TABLE lignes_bon_livraison ALTER COLUMN remise2 SET DEFAULT 0;
ALTER TABLE lignes_bon_livraison ALTER COLUMN rabais SET DEFAULT 0;
ALTER TABLE lignes_bon_livraison ALTER COLUMN prix_unitaire SET NOT NULL;
ALTER TABLE lignes_bon_livraison ALTER COLUMN tva SET NOT NULL;
ALTER TABLE lignes_bon_livraison ALTER COLUMN remise SET NOT NULL;
ALTER TABLE lignes_bon_livraison ALTER COLUMN remise2 SET NOT NULL;
ALTER TABLE lignes_bon_livraison ALTER COLUMN rabais SET NOT NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3) Contraintes FK, ajoutées de façon idempotente
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_factures_tiers_fact1') THEN
    ALTER TABLE factures ADD CONSTRAINT fk_factures_tiers_fact1 FOREIGN KEY (tiers_id) REFERENCES tiers(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_devis_tiers_fact1') THEN
    ALTER TABLE devis ADD CONSTRAINT fk_devis_tiers_fact1 FOREIGN KEY (tiers_id) REFERENCES tiers(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_bc_tiers_fact1') THEN
    ALTER TABLE bons_commande ADD CONSTRAINT fk_bc_tiers_fact1 FOREIGN KEY (tiers_id) REFERENCES tiers(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_bl_tiers_fact1') THEN
    ALTER TABLE bons_livraison ADD CONSTRAINT fk_bl_tiers_fact1 FOREIGN KEY (tiers_id) REFERENCES tiers(id) ON DELETE SET NULL;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_ligne_devis_article_fact1') THEN
    ALTER TABLE lignes_devis ADD CONSTRAINT fk_ligne_devis_article_fact1 FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_ligne_bc_article_fact1') THEN
    ALTER TABLE lignes_bon_commande ADD CONSTRAINT fk_ligne_bc_article_fact1 FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_ligne_bc_devis_fact1') THEN
    ALTER TABLE lignes_bon_commande ADD CONSTRAINT fk_ligne_bc_devis_fact1 FOREIGN KEY (source_ligne_devis_id) REFERENCES lignes_devis(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_ligne_bl_article_fact1') THEN
    ALTER TABLE lignes_bon_livraison ADD CONSTRAINT fk_ligne_bl_article_fact1 FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_ligne_bl_bc_fact1') THEN
    ALTER TABLE lignes_bon_livraison ADD CONSTRAINT fk_ligne_bl_bc_fact1 FOREIGN KEY (source_ligne_bc_id) REFERENCES lignes_bon_commande(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_ligne_facture_article_fact1') THEN
    ALTER TABLE lignes_facture ADD CONSTRAINT fk_ligne_facture_article_fact1 FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_ligne_facture_devis_fact1') THEN
    ALTER TABLE lignes_facture ADD CONSTRAINT fk_ligne_facture_devis_fact1 FOREIGN KEY (source_ligne_devis_id) REFERENCES lignes_devis(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_ligne_facture_bc_fact1') THEN
    ALTER TABLE lignes_facture ADD CONSTRAINT fk_ligne_facture_bc_fact1 FOREIGN KEY (source_ligne_bc_id) REFERENCES lignes_bon_commande(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_ligne_facture_bl_fact1') THEN
    ALTER TABLE lignes_facture ADD CONSTRAINT fk_ligne_facture_bl_fact1 FOREIGN KEY (source_ligne_bl_id) REFERENCES lignes_bon_livraison(id) ON DELETE SET NULL;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_factures_tiers_id_fact1 ON factures(tiers_id);
CREATE INDEX IF NOT EXISTS ix_devis_tiers_id_fact1 ON devis(tiers_id);
CREATE INDEX IF NOT EXISTS ix_bc_tiers_id_fact1 ON bons_commande(tiers_id);
CREATE INDEX IF NOT EXISTS ix_bl_tiers_id_fact1 ON bons_livraison(tiers_id);
CREATE INDEX IF NOT EXISTS ix_ligne_devis_article_fact1 ON lignes_devis(article_id);
CREATE INDEX IF NOT EXISTS ix_ligne_bc_article_fact1 ON lignes_bon_commande(article_id);
CREATE INDEX IF NOT EXISTS ix_ligne_bl_article_fact1 ON lignes_bon_livraison(article_id);
CREATE INDEX IF NOT EXISTS ix_ligne_facture_article_fact1 ON lignes_facture(article_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- 4) Backfill conservateur des documents historiques
--    On ne lie que lorsque le nom/désignation correspond à UNE fiche unique.
-- ─────────────────────────────────────────────────────────────────────────────
WITH uniques AS (
  SELECT societe_id, lower(trim(nom)) AS cle, MIN(id) AS id
  FROM tiers GROUP BY societe_id, lower(trim(nom)) HAVING COUNT(*) = 1
)
UPDATE factures f SET tiers_id=u.id FROM uniques u
WHERE f.tiers_id IS NULL AND u.societe_id=f.societe_id AND u.cle=lower(trim(f.tiers));
WITH uniques AS (
  SELECT societe_id, lower(trim(nom)) AS cle, MIN(id) AS id
  FROM tiers GROUP BY societe_id, lower(trim(nom)) HAVING COUNT(*) = 1
)
UPDATE devis d SET tiers_id=u.id FROM uniques u
WHERE d.tiers_id IS NULL AND u.societe_id=d.societe_id AND u.cle=lower(trim(d.tiers));
WITH uniques AS (
  SELECT societe_id, lower(trim(nom)) AS cle, MIN(id) AS id
  FROM tiers GROUP BY societe_id, lower(trim(nom)) HAVING COUNT(*) = 1
)
UPDATE bons_commande b SET tiers_id=u.id FROM uniques u
WHERE b.tiers_id IS NULL AND u.societe_id=b.societe_id AND u.cle=lower(trim(b.tiers));
WITH uniques AS (
  SELECT societe_id, lower(trim(nom)) AS cle, MIN(id) AS id
  FROM tiers GROUP BY societe_id, lower(trim(nom)) HAVING COUNT(*) = 1
)
UPDATE bons_livraison b SET tiers_id=u.id FROM uniques u
WHERE b.tiers_id IS NULL AND u.societe_id=b.societe_id AND u.cle=lower(trim(b.tiers));

-- Snapshot facture depuis la fiche tiers retrouvée.
UPDATE factures f SET
  tiers_ice_snapshot = COALESCE(f.tiers_ice_snapshot, t.ice),
  tiers_if_snapshot = COALESCE(f.tiers_if_snapshot, t.identifiant_fiscal),
  tiers_rc_snapshot = COALESCE(f.tiers_rc_snapshot, t.rc),
  tiers_adresse_snapshot = COALESCE(f.tiers_adresse_snapshot, t.adresse),
  tiers_ville_snapshot = COALESCE(f.tiers_ville_snapshot, t.ville)
FROM tiers t WHERE f.tiers_id=t.id;

-- Articles : même politique conservatrice (désignation unique par société).
WITH uniques AS (
  SELECT societe_id, lower(trim(designation)) AS cle, MIN(id) AS id
  FROM articles GROUP BY societe_id, lower(trim(designation)) HAVING COUNT(*) = 1
)
UPDATE lignes_devis l SET article_id=u.id
FROM devis d, uniques u
WHERE l.devis_id=d.id AND l.article_id IS NULL AND u.societe_id=d.societe_id AND u.cle=lower(trim(l.description));

WITH uniques AS (
  SELECT societe_id, lower(trim(designation)) AS cle, MIN(id) AS id
  FROM articles GROUP BY societe_id, lower(trim(designation)) HAVING COUNT(*) = 1
)
UPDATE lignes_bon_commande l SET article_id=u.id
FROM bons_commande b, uniques u
WHERE l.bon_commande_id=b.id AND l.article_id IS NULL AND u.societe_id=b.societe_id AND u.cle=lower(trim(l.description));

WITH uniques AS (
  SELECT societe_id, lower(trim(designation)) AS cle, MIN(id) AS id
  FROM articles GROUP BY societe_id, lower(trim(designation)) HAVING COUNT(*) = 1
)
UPDATE lignes_bon_livraison l SET article_id=u.id
FROM bons_livraison b, uniques u
WHERE l.bon_livraison_id=b.id AND l.article_id IS NULL AND u.societe_id=b.societe_id AND u.cle=lower(trim(l.description));

WITH uniques AS (
  SELECT societe_id, lower(trim(designation)) AS cle, MIN(id) AS id
  FROM articles GROUP BY societe_id, lower(trim(designation)) HAVING COUNT(*) = 1
)
UPDATE lignes_facture l SET article_id=u.id
FROM factures f, uniques u
WHERE l.facture_id=f.id AND l.article_id IS NULL AND u.societe_id=f.societe_id AND u.cle=lower(trim(l.description));

-- Filiation Devis -> BC, seulement si la désignation est unique dans le devis.
UPDATE lignes_bon_commande lb SET
  source_ligne_devis_id = ld.id,
  article_id = COALESCE(lb.article_id, ld.article_id),
  tva = COALESCE(ld.tva, lb.tva)
FROM bons_commande bc, lignes_devis ld
WHERE lb.bon_commande_id=bc.id
  AND bc.devis_id=ld.devis_id
  AND lower(trim(lb.description))=lower(trim(ld.description))
  AND lb.source_ligne_devis_id IS NULL
  AND 1 = (SELECT COUNT(*) FROM lignes_devis x
           WHERE x.devis_id=bc.devis_id AND lower(trim(x.description))=lower(trim(lb.description)));

-- Filiation BC -> BL/BR, même règle de prudence.
UPDATE lignes_bon_livraison ll SET
  source_ligne_bc_id = lb.id,
  article_id = COALESCE(ll.article_id, lb.article_id),
  prix_unitaire = CASE WHEN COALESCE(ll.prix_unitaire,0)=0 THEN lb.prix_unitaire ELSE ll.prix_unitaire END,
  tva = COALESCE(lb.tva, ll.tva),
  remise = COALESCE(lb.remise, ll.remise),
  remise2 = COALESCE(lb.remise2, ll.remise2),
  rabais = COALESCE(lb.rabais, ll.rabais)
FROM bons_livraison bl, lignes_bon_commande lb
WHERE ll.bon_livraison_id=bl.id
  AND bl.bon_commande_id=lb.bon_commande_id
  AND lower(trim(ll.description))=lower(trim(lb.description))
  AND ll.source_ligne_bc_id IS NULL
  AND 1 = (SELECT COUNT(*) FROM lignes_bon_commande x
           WHERE x.bon_commande_id=bl.bon_commande_id AND lower(trim(x.description))=lower(trim(ll.description)));

COMMIT;
