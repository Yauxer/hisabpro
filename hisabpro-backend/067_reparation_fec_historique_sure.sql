-- Patch 096 / migration 067 — Enrichissement FEC historique sûr
--
-- Objectif : réparer uniquement les métadonnées FEC que HisabPro peut relier
-- sans ambiguïté à une pièce métier déjà existante. Les montants, dates,
-- numéros et journaux des écritures définitives ne sont jamais réécrits.
--
-- Cette migration :
--   * complète les liens tiers historiques par égalité exacte lorsque le tiers
--     correspondant est unique dans la société ;
--   * complète les snapshots auxiliaires 3421/4411 depuis une facture ou un
--     règlement relié de manière déterministe ;
--   * ajoute une référence documentaire via ecriture_justificatifs (append-only)
--     lorsque la facture/le règlement porte déjà une référence exploitable ;
--   * laisse volontairement intactes les anomalies qui exigent une vraie pièce
--     utilisateur ou une décision comptable (aucune référence n'est inventée).
--
-- À exécuter après 066_liquidation_is_snapshot_detail.sql.

BEGIN;

-- Le motif est repris par le trigger d'audit des lignes. L'acteur reste système,
-- ce qui distingue clairement cette migration d'une modification utilisateur.
SELECT set_config(
    'hisabpro.audit_motif',
    'Patch 096 / migration 067 : enrichissement FEC historique déterministe, sans modification des montants ni des numéros comptables',
    true
);

-- 1) Référentiel tiers : défense en profondeur si une ancienne base n'avait pas
-- reçu tous les codes auxiliaires du patch 053.
UPDATE tiers
   SET code_aux_client = 'C' || LPAD(id::text, 8, '0')
 WHERE type IN ('client','les_deux')
   AND NULLIF(BTRIM(code_aux_client), '') IS NULL;

UPDATE tiers
   SET code_aux_fournisseur = 'F' || LPAD(id::text, 8, '0')
 WHERE type IN ('fournisseur','les_deux')
   AND NULLIF(BTRIM(code_aux_fournisseur), '') IS NULL;

-- 2) Anciennes factures/règlements : rattachement au tiers uniquement lorsque le
-- nom historique correspond exactement à un tiers unique et compatible.
WITH candidats AS (
    SELECT f.id AS facture_id, MIN(t.id) AS tiers_id
      FROM factures f
      JOIN tiers t
        ON t.societe_id = f.societe_id
       AND LOWER(BTRIM(t.nom)) = LOWER(BTRIM(f.tiers))
       AND (
            (f.type::text = 'vente' AND t.type IN ('client','les_deux'))
         OR (f.type::text = 'achat' AND t.type IN ('fournisseur','les_deux'))
       )
     WHERE f.tiers_id IS NULL
     GROUP BY f.id
    HAVING COUNT(*) = 1
)
UPDATE factures f
   SET tiers_id = c.tiers_id
  FROM candidats c
 WHERE f.id = c.facture_id;

UPDATE reglements r
   SET tiers_id = f.tiers_id
  FROM factures f
 WHERE r.tiers_id IS NULL
   AND r.facture_id = f.id
   AND f.societe_id = r.societe_id
   AND f.tiers_id IS NOT NULL;

WITH candidats AS (
    SELECT r.id AS reglement_id, MIN(t.id) AS tiers_id
      FROM reglements r
      JOIN tiers t
        ON t.societe_id = r.societe_id
       AND LOWER(BTRIM(t.nom)) = LOWER(BTRIM(r.tiers))
     WHERE r.tiers_id IS NULL
     GROUP BY r.id
    HAVING COUNT(*) = 1
)
UPDATE reglements r
   SET tiers_id = c.tiers_id
  FROM candidats c
 WHERE r.id = c.reglement_id;

-- 3) Correspondances facture -> écriture. On privilégie la référence portée par
-- l'écriture ; à défaut, on accepte le numéro/référence explicitement présent
-- dans le libellé. Une ambiguïté laisse l'écriture intacte.
CREATE TEMP TABLE _fec067_facture_match ON COMMIT DROP AS
WITH candidats AS (
    SELECT e.id AS ecriture_id, f.id AS facture_id, f.tiers_id,
           f.tiers AS libelle_aux,
           CASE WHEN f.type::text = 'vente' THEN 'client' ELSE 'fournisseur' END AS nature,
           CASE WHEN f.type::text = 'vente'
                THEN NULLIF(BTRIM(f.numero), '')
                ELSE COALESCE(NULLIF(BTRIM(f.reference), ''), NULLIF(BTRIM(f.numero), ''))
           END AS reference_piece,
           1 AS priorite
      FROM ecritures e
      JOIN factures f
        ON f.societe_id = e.societe_id
       AND f.exercice = e.exercice
       AND f.date = e.date
       AND f.tiers_id IS NOT NULL
       AND ((f.type::text = 'vente' AND e.journal::text = 'VT')
         OR (f.type::text = 'achat' AND e.journal::text = 'AC'))
     WHERE e.source = 'facture'
       AND NULLIF(BTRIM(e.reference), '') IS NOT NULL
       AND (
            e.reference = f.numero
         OR (NULLIF(BTRIM(f.reference), '') IS NOT NULL AND e.reference = f.reference)
       )

    UNION

    SELECT e.id, f.id, f.tiers_id, f.tiers,
           CASE WHEN f.type::text = 'vente' THEN 'client' ELSE 'fournisseur' END,
           CASE WHEN f.type::text = 'vente'
                THEN NULLIF(BTRIM(f.numero), '')
                ELSE COALESCE(NULLIF(BTRIM(f.reference), ''), NULLIF(BTRIM(f.numero), ''))
           END,
           2
      FROM ecritures e
      JOIN factures f
        ON f.societe_id = e.societe_id
       AND f.exercice = e.exercice
       AND f.date = e.date
       AND f.tiers_id IS NOT NULL
       AND ((f.type::text = 'vente' AND e.journal::text = 'VT')
         OR (f.type::text = 'achat' AND e.journal::text = 'AC'))
     WHERE e.source = 'facture'
       AND (
            (NULLIF(BTRIM(f.numero), '') IS NOT NULL
             AND STRPOS(LOWER(e.libelle), LOWER(BTRIM(f.numero))) > 0)
         OR (NULLIF(BTRIM(f.reference), '') IS NOT NULL
             AND STRPOS(LOWER(e.libelle), LOWER(BTRIM(f.reference))) > 0)
       )
),
meilleure_priorite AS (
    SELECT ecriture_id, MIN(priorite) AS priorite
      FROM candidats
     GROUP BY ecriture_id
),
uniques AS (
    SELECT c.ecriture_id,
           MIN(c.facture_id) AS facture_id,
           MIN(c.tiers_id) AS tiers_id,
           MIN(c.libelle_aux) AS libelle_aux,
           MIN(c.nature) AS nature,
           MIN(c.reference_piece) AS reference_piece
      FROM candidats c
      JOIN meilleure_priorite p
        ON p.ecriture_id = c.ecriture_id
       AND p.priorite = c.priorite
     GROUP BY c.ecriture_id
    HAVING COUNT(DISTINCT c.facture_id) = 1
)
SELECT * FROM uniques;

-- 4) Correspondances règlement -> écriture. Trois niveaux : lien technique
-- explicite, référence métier exacte, puis signature historique stricte
-- (tiers en fin de libellé + mode + montant + chronologie). Si plusieurs
-- règlements conviennent, aucun enrichissement n'est réalisé.
CREATE TEMP TABLE _fec067_reglement_match ON COMMIT DROP AS
WITH candidats AS (
    SELECT e.id AS ecriture_id, r.id AS reglement_id, r.tiers_id,
           r.tiers AS libelle_aux,
           CASE WHEN l_collectif.compte LIKE '4411%' THEN 'fournisseur' ELSE 'client' END AS nature,
           COALESCE(NULLIF(BTRIM(r.reference), ''), NULLIF(BTRIM(r.numero), '')) AS reference_piece,
           1 AS priorite
      FROM ecritures e
      JOIN reglements r
        ON r.societe_id = e.societe_id
       AND r.ecriture_id = e.id
       AND r.tiers_id IS NOT NULL
      LEFT JOIN LATERAL (
          SELECT l.compte
            FROM lignes_ecriture l
           WHERE l.ecriture_id = e.id
             AND (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
           ORDER BY l.id
           LIMIT 1
      ) l_collectif ON TRUE
     WHERE e.source = 'reglement'

    UNION

    SELECT e.id, r.id, r.tiers_id, r.tiers,
           CASE WHEN l_collectif.compte LIKE '4411%' THEN 'fournisseur' ELSE 'client' END,
           COALESCE(NULLIF(BTRIM(r.reference), ''), NULLIF(BTRIM(r.numero), '')),
           2
      FROM ecritures e
      JOIN reglements r
        ON r.societe_id = e.societe_id
       AND r.tiers_id IS NOT NULL
       AND NULLIF(BTRIM(e.reference), '') IS NOT NULL
       AND (e.reference = r.reference OR e.reference = r.numero)
      LEFT JOIN LATERAL (
          SELECT l.compte
            FROM lignes_ecriture l
           WHERE l.ecriture_id = e.id
             AND (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
           ORDER BY l.id
           LIMIT 1
      ) l_collectif ON TRUE
     WHERE e.source = 'reglement'

    UNION

    SELECT e.id, r.id, r.tiers_id, r.tiers,
           CASE WHEN l_collectif.compte LIKE '4411%' THEN 'fournisseur' ELSE 'client' END,
           COALESCE(NULLIF(BTRIM(r.reference), ''), NULLIF(BTRIM(r.numero), '')),
           3
      FROM ecritures e
      JOIN reglements r
        ON r.societe_id = e.societe_id
       AND r.tiers_id IS NOT NULL
       AND r.date <= e.date
       AND EXTRACT(YEAR FROM r.date)::int <= e.exercice
       AND RIGHT(LOWER(BTRIM(e.libelle)), CHAR_LENGTH(LOWER(BTRIM(r.tiers)))) = LOWER(BTRIM(r.tiers))
       AND (
            (LOWER(e.libelle) LIKE '%effet%' AND r.mode = 'effet')
         OR ((LOWER(e.libelle) LIKE '%chèque%' OR LOWER(e.libelle) LIKE '%cheque%') AND r.mode = 'cheque')
         OR (LOWER(e.libelle) NOT LIKE '%effet%'
             AND LOWER(e.libelle) NOT LIKE '%chèque%'
             AND LOWER(e.libelle) NOT LIKE '%cheque%')
       )
       AND EXISTS (
           SELECT 1
             FROM lignes_ecriture lx
            WHERE lx.ecriture_id = e.id
              AND (
                  ABS(COALESCE(lx.debit, 0)::numeric - COALESCE(r.montant, 0)::numeric) <= 0.01
               OR ABS(COALESCE(lx.credit, 0)::numeric - COALESCE(r.montant, 0)::numeric) <= 0.01
              )
       )
      LEFT JOIN LATERAL (
          SELECT l.compte
            FROM lignes_ecriture l
           WHERE l.ecriture_id = e.id
             AND (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
           ORDER BY l.id
           LIMIT 1
      ) l_collectif ON TRUE
     WHERE e.source = 'reglement'
),
meilleure_priorite AS (
    SELECT ecriture_id, MIN(priorite) AS priorite
      FROM candidats
     GROUP BY ecriture_id
),
uniques AS (
    SELECT c.ecriture_id,
           MIN(c.reglement_id) AS reglement_id,
           MIN(c.tiers_id) AS tiers_id,
           MIN(c.libelle_aux) AS libelle_aux,
           MIN(c.nature) AS nature,
           MIN(c.reference_piece) AS reference_piece
      FROM candidats c
      JOIN meilleure_priorite p
        ON p.ecriture_id = c.ecriture_id
       AND p.priorite = c.priorite
     GROUP BY c.ecriture_id
    HAVING COUNT(DISTINCT c.reglement_id) = 1
)
SELECT * FROM uniques;

-- 5) Enrichissement des lignes collectives. On n'autorise temporairement que
-- cette mise à jour de métadonnées historiques ; le trigger d'audit reste actif.
ALTER TABLE lignes_ecriture DISABLE TRIGGER trg_hisabpro_proteger_lignes_definitives;

UPDATE lignes_ecriture l
   SET tiers_id = COALESCE(l.tiers_id, m.tiers_id),
       nature_auxiliaire = COALESCE(NULLIF(BTRIM(l.nature_auxiliaire), ''), m.nature),
       compte_auxiliaire_snapshot = COALESCE(
           NULLIF(BTRIM(l.compte_auxiliaire_snapshot), ''),
           CASE WHEN m.nature = 'client' THEN t.code_aux_client ELSE t.code_aux_fournisseur END
       ),
       libelle_auxiliaire_snapshot = COALESCE(
           NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), ''),
           NULLIF(BTRIM(m.libelle_aux), ''),
           t.nom
       )
  FROM _fec067_facture_match m
  JOIN tiers t ON t.id = m.tiers_id
 WHERE l.ecriture_id = m.ecriture_id
   AND ((m.nature = 'client' AND l.compte LIKE '3421%')
     OR (m.nature = 'fournisseur' AND l.compte LIKE '4411%'))
   AND (
       l.tiers_id IS NULL
       OR NULLIF(BTRIM(l.compte_auxiliaire_snapshot), '') IS NULL
       OR NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), '') IS NULL
   );

UPDATE lignes_ecriture l
   SET tiers_id = COALESCE(l.tiers_id, m.tiers_id),
       nature_auxiliaire = COALESCE(
           NULLIF(BTRIM(l.nature_auxiliaire), ''),
           CASE WHEN l.compte LIKE '4411%' THEN 'fournisseur' ELSE 'client' END
       ),
       compte_auxiliaire_snapshot = COALESCE(
           NULLIF(BTRIM(l.compte_auxiliaire_snapshot), ''),
           CASE WHEN l.compte LIKE '4411%' THEN t.code_aux_fournisseur ELSE t.code_aux_client END
       ),
       libelle_auxiliaire_snapshot = COALESCE(
           NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), ''),
           NULLIF(BTRIM(m.libelle_aux), ''),
           t.nom
       )
  FROM _fec067_reglement_match m
  JOIN tiers t ON t.id = m.tiers_id
 WHERE l.ecriture_id = m.ecriture_id
   AND (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
   AND (
       l.tiers_id IS NULL
       OR NULLIF(BTRIM(l.compte_auxiliaire_snapshot), '') IS NULL
       OR NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), '') IS NULL
   );

-- Cas où le tiers était déjà présent mais où l'ancien snapshot était incomplet.
UPDATE lignes_ecriture l
   SET nature_auxiliaire = COALESCE(
           NULLIF(BTRIM(l.nature_auxiliaire), ''),
           CASE WHEN l.compte LIKE '4411%' THEN 'fournisseur' ELSE 'client' END
       ),
       compte_auxiliaire_snapshot = COALESCE(
           NULLIF(BTRIM(l.compte_auxiliaire_snapshot), ''),
           CASE WHEN l.compte LIKE '4411%' THEN t.code_aux_fournisseur ELSE t.code_aux_client END
       ),
       libelle_auxiliaire_snapshot = COALESCE(
           NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), ''),
           t.nom
       )
  FROM tiers t
 WHERE l.tiers_id = t.id
   AND (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
   AND (
       NULLIF(BTRIM(l.nature_auxiliaire), '') IS NULL
       OR NULLIF(BTRIM(l.compte_auxiliaire_snapshot), '') IS NULL
       OR NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), '') IS NULL
   );

ALTER TABLE lignes_ecriture ENABLE TRIGGER trg_hisabpro_proteger_lignes_definitives;

-- 6) Les écritures définitives restent intactes : on ajoute la référence dans
-- la table append-only prévue à cet effet. Aucune référence synthétique n'est
-- générée si la pièce métier n'en porte pas déjà une.
INSERT INTO ecriture_justificatifs (
    societe_id, ecriture_id, reference, date_piece,
    source_type, source_id, prioritaire, motif
)
SELECT e.societe_id, e.id, m.reference_piece, COALESCE(e.date_piece, e.date),
       'reparation_fec', m.facture_id, TRUE,
       'Patch 096 : référence de facture existante rattachée à une écriture historique sans modifier l''écriture définitive.'
  FROM _fec067_facture_match m
  JOIN ecritures e ON e.id = m.ecriture_id
 WHERE NULLIF(BTRIM(m.reference_piece), '') IS NOT NULL
   AND NULLIF(BTRIM(e.reference), '') IS NULL
   AND NOT EXISTS (
       SELECT 1 FROM ecriture_justificatifs j
        WHERE j.ecriture_id = e.id
          AND NULLIF(BTRIM(j.reference), '') IS NOT NULL
   );

INSERT INTO ecriture_justificatifs (
    societe_id, ecriture_id, reference, date_piece,
    source_type, source_id, prioritaire, motif
)
SELECT e.societe_id, e.id, m.reference_piece, COALESCE(e.date_piece, e.date),
       'reparation_fec', m.reglement_id, TRUE,
       'Patch 096 : référence de règlement existante rattachée à une écriture historique sans modifier l''écriture définitive.'
  FROM _fec067_reglement_match m
  JOIN ecritures e ON e.id = m.ecriture_id
 WHERE NULLIF(BTRIM(m.reference_piece), '') IS NOT NULL
   AND NULLIF(BTRIM(e.reference), '') IS NULL
   AND NOT EXISTS (
       SELECT 1 FROM ecriture_justificatifs j
        WHERE j.ecriture_id = e.id
          AND NULLIF(BTRIM(j.reference), '') IS NOT NULL
   );

COMMIT;
