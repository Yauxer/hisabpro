-- COMPTA.1 — Chaîne comptable automatique des formulaires
-- À appliquer après 031_avoirs_retours.sql

BEGIN;

-- Les comptes saisis dans la fiche Article existaient déjà dans l'UI mais
-- n'étaient pas persistés côté backend. Ils deviennent de vraies surcharges
-- du compte de la famille.
ALTER TABLE articles ADD COLUMN IF NOT EXISTS compte_vente VARCHAR(10);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS compte_achat VARCHAR(10);

-- Snapshots comptables figés à la validation de la facture : une modification
-- ultérieure du tiers, de l'article ou de sa famille ne doit jamais modifier la
-- logique comptable d'une pièce déjà validée.
ALTER TABLE factures ADD COLUMN IF NOT EXISTS compte_tiers_snapshot VARCHAR(10);
ALTER TABLE lignes_facture ADD COLUMN IF NOT EXISTS compte_vente_snapshot VARCHAR(10);
ALTER TABLE lignes_facture ADD COLUMN IF NOT EXISTS compte_achat_snapshot VARCHAR(10);

-- Les acomptes sont rattachés techniquement au tiers et conservent également
-- le compte qui était applicable lors de leur création.
ALTER TABLE acomptes ADD COLUMN IF NOT EXISTS tiers_id INTEGER REFERENCES tiers(id) ON DELETE SET NULL;
ALTER TABLE acomptes ADD COLUMN IF NOT EXISTS compte_tiers_snapshot VARCHAR(10);
ALTER TABLE acomptes ADD COLUMN IF NOT EXISTS banque VARCHAR(100);
CREATE INDEX IF NOT EXISTS ix_acomptes_tiers_id ON acomptes(tiers_id);

-- Les backfills ci-dessous ne modifient aucune donnée métier de la facture :
-- ils remplissent uniquement les nouveaux snapshots comptables. Les guards FACT.4
-- bloquent volontairement toute UPDATE d'une facture/ligne validée, y compris une
-- UPDATE purement technique. On les neutralise donc uniquement dans cette
-- transaction de migration, puis on les réactive avant COMMIT. En cas d'erreur,
-- le ROLLBACK de la transaction restaure aussi l'état des triggers.
ALTER TABLE factures DISABLE TRIGGER trg_hisabpro_guard_facture_validee;
ALTER TABLE lignes_facture DISABLE TRIGGER trg_hisabpro_guard_ligne_facture_validee;

-- Backfill prudent pour les factures historiques déjà validées.
UPDATE factures f
SET compte_tiers_snapshot = CASE
    WHEN f.type::text = 'vente' THEN COALESCE(NULLIF(BTRIM(t.compte_client), ''), '3421')
    ELSE COALESCE(NULLIF(BTRIM(t.compte_fournisseur), ''), '4411')
END
FROM tiers t
WHERE f.tiers_id = t.id
  AND f.societe_id = t.societe_id
  AND f.est_validee = TRUE
  AND (f.compte_tiers_snapshot IS NULL OR BTRIM(f.compte_tiers_snapshot) = '');

UPDATE factures
SET compte_tiers_snapshot = CASE WHEN type::text = 'vente' THEN '3421' ELSE '4411' END
WHERE est_validee = TRUE
  AND (compte_tiers_snapshot IS NULL OR BTRIM(compte_tiers_snapshot) = '');

UPDATE lignes_facture lf
SET compte_vente_snapshot = COALESCE(
        (SELECT COALESCE(NULLIF(BTRIM(a.compte_vente), ''), NULLIF(BTRIM(fa.compte_vente), ''))
           FROM articles a
           LEFT JOIN familles_articles fa ON fa.id = a.famille_id AND fa.societe_id = a.societe_id
           JOIN factures f2 ON f2.id = lf.facture_id AND f2.societe_id = a.societe_id
          WHERE a.id = lf.article_id
          LIMIT 1),
        '7111'
    ),
    compte_achat_snapshot = COALESCE(
        (SELECT COALESCE(NULLIF(BTRIM(a.compte_achat), ''), NULLIF(BTRIM(fa.compte_achat), ''))
           FROM articles a
           LEFT JOIN familles_articles fa ON fa.id = a.famille_id AND fa.societe_id = a.societe_id
           JOIN factures f2 ON f2.id = lf.facture_id AND f2.societe_id = a.societe_id
          WHERE a.id = lf.article_id
          LIMIT 1),
        '6111'
    )
WHERE EXISTS (
    SELECT 1 FROM factures f
    WHERE f.id = lf.facture_id AND f.est_validee = TRUE
)
  AND (
      lf.compte_vente_snapshot IS NULL OR BTRIM(lf.compte_vente_snapshot) = ''
      OR lf.compte_achat_snapshot IS NULL OR BTRIM(lf.compte_achat_snapshot) = ''
  );

-- Réactivation impérative des protections métier FACT.4.
ALTER TABLE lignes_facture ENABLE TRIGGER trg_hisabpro_guard_ligne_facture_validee;
ALTER TABLE factures ENABLE TRIGGER trg_hisabpro_guard_facture_validee;

COMMIT;
