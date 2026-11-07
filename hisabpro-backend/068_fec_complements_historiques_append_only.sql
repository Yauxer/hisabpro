-- Patch 097 / migration 068 — Compléments FEC historiques append-only
--
-- Le patch 096 tentait d'enrichir directement les lignes définitives historiques.
-- Ce patch adopte une stratégie plus sûre : aucune ligne comptable validée n'est
-- réécrite. Les auxiliaires déterminés sans ambiguïté sont stockés dans une table
-- append-only dédiée et les références de pièces dans ecriture_justificatifs.
--
-- Les règles ci-dessous n'inventent jamais un tiers. Elles n'acceptent qu'un
-- rapprochement exact et unique (tiers, facture ou règlement existant).
-- Pour un règlement existant sans référence externe, REG-<id> est l'identifiant
-- interne stable déjà utilisé par HisabPro lors des nouveaux flux comptables.
--
-- À exécuter après 067_reparation_fec_historique_sure.sql. Idempotent.

BEGIN;

CREATE TABLE IF NOT EXISTS ligne_auxiliaire_complements (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    ligne_ecriture_id INTEGER NOT NULL REFERENCES lignes_ecriture(id) ON DELETE RESTRICT,
    tiers_id INTEGER NOT NULL REFERENCES tiers(id) ON DELETE RESTRICT,
    nature_auxiliaire VARCHAR(20) NOT NULL,
    compte_auxiliaire_snapshot VARCHAR(20) NOT NULL,
    libelle_auxiliaire_snapshot VARCHAR(200) NOT NULL,
    source_type VARCHAR(30) NOT NULL DEFAULT 'reparation_historique',
    source_id INTEGER NULL,
    motif VARCHAR(500) NULL,
    created_by INTEGER NULL REFERENCES utilisateurs(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_ligne_aux_complement_nature
        CHECK (nature_auxiliaire IN ('client','fournisseur')),
    CONSTRAINT ck_ligne_aux_complement_compte_non_vide
        CHECK (length(trim(compte_auxiliaire_snapshot)) > 0),
    CONSTRAINT ck_ligne_aux_complement_libelle_non_vide
        CHECK (length(trim(libelle_auxiliaire_snapshot)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_ligne_aux_complements_ligne
    ON ligne_auxiliaire_complements(ligne_ecriture_id, id);
CREATE INDEX IF NOT EXISTS ix_ligne_aux_complements_societe
    ON ligne_auxiliaire_complements(societe_id);

CREATE OR REPLACE FUNCTION hisabpro_guard_ligne_aux_complement_append_only()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'Les compléments auxiliaires historiques sont append-only : % interdit.', TG_OP
        USING ERRCODE='23514';
END;
$$;

DROP TRIGGER IF EXISTS trg_ligne_aux_complements_append_only ON ligne_auxiliaire_complements;
CREATE TRIGGER trg_ligne_aux_complements_append_only
BEFORE UPDATE OR DELETE ON ligne_auxiliaire_complements
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_ligne_aux_complement_append_only();

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        GRANT SELECT ON TABLE ligne_auxiliaire_complements TO hisabpro;
    END IF;
END $$;

-- Codes auxiliaires stables pour les tiers historiques qui en seraient encore dépourvus.
UPDATE tiers
   SET code_aux_client = 'C' || LPAD(id::text, 8, '0')
 WHERE type::text IN ('client','les_deux')
   AND NULLIF(BTRIM(code_aux_client), '') IS NULL;

UPDATE tiers
   SET code_aux_fournisseur = 'F' || LPAD(id::text, 8, '0')
 WHERE type::text IN ('fournisseur','les_deux')
   AND NULLIF(BTRIM(code_aux_fournisseur), '') IS NULL;

-- ---------------------------------------------------------------------------
-- 1) Auxiliaires historiques : candidats exacts et déterministes
-- ---------------------------------------------------------------------------
CREATE TEMP TABLE _fec068_aux_candidates (
    ligne_id INTEGER,
    societe_id INTEGER,
    tiers_id INTEGER,
    priorite INTEGER,
    source_type VARCHAR(30),
    source_id INTEGER
) ON COMMIT DROP;

-- P1 : la ligne possède déjà un tiers_id mais l'ancien snapshot est incomplet.
INSERT INTO _fec068_aux_candidates
SELECT l.id, e.societe_id, t.id, 1, 'tiers_ligne', t.id
  FROM lignes_ecriture l
  JOIN ecritures e ON e.id=l.ecriture_id
  JOIN tiers t ON t.id=l.tiers_id AND t.societe_id=e.societe_id
 WHERE (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
   AND (
       NULLIF(BTRIM(l.compte_auxiliaire_snapshot), '') IS NULL
       OR NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), '') IS NULL
   )
   AND ((l.compte LIKE '3421%' AND t.type::text IN ('client','les_deux'))
     OR (l.compte LIKE '4411%' AND t.type::text IN ('fournisseur','les_deux')));

-- P2 : libellé de la ligne = nom exact d'un tiers unique et compatible.
INSERT INTO _fec068_aux_candidates
SELECT l.id, e.societe_id, MIN(t.id), 2, 'libelle_ligne', MIN(t.id)
  FROM lignes_ecriture l
  JOIN ecritures e ON e.id=l.ecriture_id
  JOIN tiers t
    ON t.societe_id=e.societe_id
   AND LOWER(BTRIM(t.nom))=LOWER(BTRIM(COALESCE(l.libelle,'')))
   AND ((l.compte LIKE '3421%' AND t.type::text IN ('client','les_deux'))
     OR (l.compte LIKE '4411%' AND t.type::text IN ('fournisseur','les_deux')))
 WHERE (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
   AND (l.tiers_id IS NULL
        OR NULLIF(BTRIM(l.compte_auxiliaire_snapshot), '') IS NULL
        OR NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), '') IS NULL)
 GROUP BY l.id, e.societe_id
HAVING COUNT(DISTINCT t.id)=1;

-- P3 : flux chèque/effet historiques générés par HisabPro : le nom du tiers est
-- figé après le séparateur « — ». On exige un tiers unique et compatible.
INSERT INTO _fec068_aux_candidates
SELECT l.id, e.societe_id, MIN(t.id), 3, 'libelle_ecriture', MIN(t.id)
  FROM lignes_ecriture l
  JOIN ecritures e ON e.id=l.ecriture_id
  JOIN tiers t
    ON t.societe_id=e.societe_id
   AND STRPOS(e.libelle, '—') > 0
   AND LOWER(BTRIM(t.nom))=LOWER(BTRIM(SPLIT_PART(e.libelle, '—', 2)))
   AND ((l.compte LIKE '3421%' AND t.type::text IN ('client','les_deux'))
     OR (l.compte LIKE '4411%' AND t.type::text IN ('fournisseur','les_deux')))
 WHERE (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
   AND (l.tiers_id IS NULL
        OR NULLIF(BTRIM(l.compte_auxiliaire_snapshot), '') IS NULL
        OR NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), '') IS NULL)
 GROUP BY l.id, e.societe_id
HAVING COUNT(DISTINCT t.id)=1;

-- P4 : facture unique dont le numéro/référence est déjà porté explicitement par
-- la référence ou le libellé de l'écriture. Aucun rapprochement approximatif.
INSERT INTO _fec068_aux_candidates
SELECT l.id, e.societe_id, MIN(f.tiers_id), 4, 'facture', MIN(f.id)
  FROM lignes_ecriture l
  JOIN ecritures e ON e.id=l.ecriture_id
  JOIN factures f
    ON f.societe_id=e.societe_id
   AND f.tiers_id IS NOT NULL
   AND ((l.compte LIKE '3421%' AND f.type::text='vente')
     OR (l.compte LIKE '4411%' AND f.type::text='achat'))
   AND (
        (NULLIF(BTRIM(e.reference),'') IS NOT NULL
         AND (e.reference=f.numero OR e.reference=f.reference))
     OR (NULLIF(BTRIM(f.numero),'') IS NOT NULL
         AND STRPOS(LOWER(e.libelle), LOWER(BTRIM(f.numero))) > 0)
     OR (NULLIF(BTRIM(f.reference),'') IS NOT NULL
         AND STRPOS(LOWER(e.libelle), LOWER(BTRIM(f.reference))) > 0)
   )
 WHERE (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
   AND (l.tiers_id IS NULL
        OR NULLIF(BTRIM(l.compte_auxiliaire_snapshot), '') IS NULL
        OR NULLIF(BTRIM(l.libelle_auxiliaire_snapshot), '') IS NULL)
 GROUP BY l.id, e.societe_id
HAVING COUNT(DISTINCT f.tiers_id)=1;

-- P5 : ancien règlement relié techniquement à l'écriture.
INSERT INTO _fec068_aux_candidates
SELECT l.id, e.societe_id, MIN(r.tiers_id), 5, 'reglement', MIN(r.id)
  FROM lignes_ecriture l
  JOIN ecritures e ON e.id=l.ecriture_id
  JOIN reglements r
    ON r.societe_id=e.societe_id
   AND r.ecriture_id=e.id
   AND r.tiers_id IS NOT NULL
  JOIN tiers t ON t.id=r.tiers_id AND t.societe_id=e.societe_id
 WHERE (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
   AND ((l.compte LIKE '3421%' AND t.type::text IN ('client','les_deux'))
     OR (l.compte LIKE '4411%' AND t.type::text IN ('fournisseur','les_deux')))
 GROUP BY l.id, e.societe_id
HAVING COUNT(DISTINCT r.tiers_id)=1;

-- Choix : priorité la plus forte puis un seul tiers. Une ambiguïté laisse la
-- ligne intacte et donc visible dans le contrôle FEC.
CREATE TEMP TABLE _fec068_aux_match ON COMMIT DROP AS
WITH p AS (
    SELECT ligne_id, MIN(priorite) AS priorite
      FROM _fec068_aux_candidates
     GROUP BY ligne_id
), u AS (
    SELECT c.ligne_id, c.societe_id,
           MIN(c.tiers_id) AS tiers_id,
           MIN(c.source_type) AS source_type,
           MIN(c.source_id) AS source_id
      FROM _fec068_aux_candidates c
      JOIN p ON p.ligne_id=c.ligne_id AND p.priorite=c.priorite
     GROUP BY c.ligne_id, c.societe_id
    HAVING COUNT(DISTINCT c.tiers_id)=1
)
SELECT * FROM u;

INSERT INTO ligne_auxiliaire_complements (
    societe_id, ligne_ecriture_id, tiers_id, nature_auxiliaire,
    compte_auxiliaire_snapshot, libelle_auxiliaire_snapshot,
    source_type, source_id, motif
)
SELECT m.societe_id, l.id, t.id,
       CASE WHEN l.compte LIKE '3421%' THEN 'client' ELSE 'fournisseur' END,
       CASE WHEN l.compte LIKE '3421%' THEN t.code_aux_client ELSE t.code_aux_fournisseur END,
       t.nom,
       m.source_type, m.source_id,
       'Patch 097 : complément auxiliaire FEC historique append-only ; écriture définitive inchangée.'
  FROM _fec068_aux_match m
  JOIN lignes_ecriture l ON l.id=m.ligne_id
  JOIN tiers t ON t.id=m.tiers_id AND t.societe_id=m.societe_id
 WHERE NULLIF(BTRIM(CASE WHEN l.compte LIKE '3421%' THEN t.code_aux_client ELSE t.code_aux_fournisseur END), '') IS NOT NULL
   AND NOT EXISTS (
       SELECT 1
         FROM ligne_auxiliaire_complements c
        WHERE c.ligne_ecriture_id=l.id
          AND c.tiers_id=t.id
          AND c.compte_auxiliaire_snapshot=(CASE WHEN l.compte LIKE '3421%' THEN t.code_aux_client ELSE t.code_aux_fournisseur END)
   );

-- ---------------------------------------------------------------------------
-- 2) Références documentaires historiques
-- ---------------------------------------------------------------------------
-- 2.a Factures : référence/numéro explicite ; à défaut, facture unique du bon
-- type le même jour lorsque le libellé indique bien FA°/FN°.
CREATE TEMP TABLE _fec068_facture_candidates (
    ecriture_id INTEGER,
    facture_id INTEGER,
    reference_piece VARCHAR(100),
    priorite INTEGER
) ON COMMIT DROP;

INSERT INTO _fec068_facture_candidates
SELECT e.id, f.id,
       CASE WHEN f.type::text='vente'
            THEN NULLIF(BTRIM(f.numero),'')
            ELSE COALESCE(NULLIF(BTRIM(f.reference),''), NULLIF(BTRIM(f.numero),'')) END,
       1
  FROM ecritures e
  JOIN factures f
    ON f.societe_id=e.societe_id
   AND ((e.journal::text='VT' AND f.type::text='vente')
     OR (e.journal::text='AC' AND f.type::text='achat'))
 WHERE NULLIF(BTRIM(COALESCE(e.reference,'')), '') IS NULL
   AND (
        (NULLIF(BTRIM(f.numero),'') IS NOT NULL
         AND STRPOS(LOWER(e.libelle), LOWER(BTRIM(f.numero))) > 0)
     OR (NULLIF(BTRIM(f.reference),'') IS NOT NULL
         AND STRPOS(LOWER(e.libelle), LOWER(BTRIM(f.reference))) > 0)
   );

INSERT INTO _fec068_facture_candidates
SELECT e.id, f.id,
       CASE WHEN f.type::text='vente'
            THEN NULLIF(BTRIM(f.numero),'')
            ELSE COALESCE(NULLIF(BTRIM(f.reference),''), NULLIF(BTRIM(f.numero),'')) END,
       2
  FROM ecritures e
  JOIN factures f
    ON f.societe_id=e.societe_id
   AND f.date=e.date
   AND ((e.journal::text='VT' AND f.type::text='vente' AND LOWER(e.libelle) LIKE 'fa%')
     OR (e.journal::text='AC' AND f.type::text='achat' AND LOWER(e.libelle) LIKE 'fn%'))
 WHERE NULLIF(BTRIM(COALESCE(e.reference,'')), '') IS NULL;

CREATE TEMP TABLE _fec068_facture_match ON COMMIT DROP AS
WITH p AS (
    SELECT ecriture_id, MIN(priorite) AS priorite
      FROM _fec068_facture_candidates
     WHERE NULLIF(BTRIM(reference_piece),'') IS NOT NULL
     GROUP BY ecriture_id
), u AS (
    SELECT c.ecriture_id, MIN(c.facture_id) AS facture_id,
           MIN(c.reference_piece) AS reference_piece
      FROM _fec068_facture_candidates c
      JOIN p ON p.ecriture_id=c.ecriture_id AND p.priorite=c.priorite
     GROUP BY c.ecriture_id
    HAVING COUNT(DISTINCT c.facture_id)=1
)
SELECT * FROM u;

INSERT INTO ecriture_justificatifs (
    societe_id, ecriture_id, reference, date_piece,
    source_type, source_id, prioritaire, motif
)
SELECT e.societe_id, e.id, m.reference_piece, COALESCE(e.date_piece,e.date),
       'reparation_fec_facture', m.facture_id, TRUE,
       'Patch 097 : référence de facture existante ajoutée en complément append-only.'
  FROM _fec068_facture_match m
  JOIN ecritures e ON e.id=m.ecriture_id
 WHERE NULLIF(BTRIM(m.reference_piece),'') IS NOT NULL
   AND NOT EXISTS (
       SELECT 1 FROM ecriture_justificatifs j
        WHERE j.ecriture_id=e.id
          AND NULLIF(BTRIM(j.reference),'') IS NOT NULL
   );

-- 2.b Règlements : lien technique, référence exacte, ou signature stricte d'un
-- flux généré HisabPro (tiers exact après « — », mode et montant présents).
CREATE TEMP TABLE _fec068_reglement_candidates (
    ecriture_id INTEGER,
    reglement_id INTEGER,
    reference_piece VARCHAR(100),
    priorite INTEGER
) ON COMMIT DROP;

INSERT INTO _fec068_reglement_candidates
SELECT e.id, r.id,
       COALESCE(NULLIF(BTRIM(r.reference),''), NULLIF(BTRIM(r.numero),''), 'REG-'||r.id::text),
       1
  FROM ecritures e
  JOIN reglements r ON r.societe_id=e.societe_id AND r.ecriture_id=e.id
 WHERE NULLIF(BTRIM(COALESCE(e.reference,'')), '') IS NULL;

INSERT INTO _fec068_reglement_candidates
SELECT e.id, r.id,
       COALESCE(NULLIF(BTRIM(r.reference),''), NULLIF(BTRIM(r.numero),''), 'REG-'||r.id::text),
       2
  FROM ecritures e
  JOIN reglements r
    ON r.societe_id=e.societe_id
   AND NULLIF(BTRIM(e.reference),'') IS NOT NULL
   AND (e.reference=r.reference OR e.reference=r.numero)
 WHERE NOT EXISTS (
       SELECT 1 FROM ecriture_justificatifs j
        WHERE j.ecriture_id=e.id AND NULLIF(BTRIM(j.reference),'') IS NOT NULL
   );

INSERT INTO _fec068_reglement_candidates
SELECT e.id, r.id,
       COALESCE(NULLIF(BTRIM(r.reference),''), NULLIF(BTRIM(r.numero),''), 'REG-'||r.id::text),
       3
  FROM ecritures e
  JOIN reglements r
    ON r.societe_id=e.societe_id
   AND STRPOS(e.libelle, '—') > 0
   AND LOWER(BTRIM(r.tiers))=LOWER(BTRIM(SPLIT_PART(e.libelle, '—', 2)))
   AND r.date <= e.date
   AND (
       (LOWER(e.libelle) LIKE '%effet%' AND r.mode='effet')
       OR ((LOWER(e.libelle) LIKE '%chèque%' OR LOWER(e.libelle) LIKE '%cheque%') AND r.mode='cheque')
       OR (LOWER(e.libelle) LIKE 'encaissement%' AND r.mode IN ('cheque','effet'))
   )
   AND EXISTS (
       SELECT 1 FROM lignes_ecriture lx
        WHERE lx.ecriture_id=e.id
          AND (
              ABS(COALESCE(lx.debit,0)::numeric - COALESCE(r.montant,0)::numeric) <= 0.01
           OR ABS(COALESCE(lx.credit,0)::numeric - COALESCE(r.montant,0)::numeric) <= 0.01
          )
   )
 WHERE NULLIF(BTRIM(COALESCE(e.reference,'')), '') IS NULL
   AND NOT EXISTS (
       SELECT 1 FROM ecriture_justificatifs j
        WHERE j.ecriture_id=e.id AND NULLIF(BTRIM(j.reference),'') IS NOT NULL
   );

CREATE TEMP TABLE _fec068_reglement_match ON COMMIT DROP AS
WITH p AS (
    SELECT ecriture_id, MIN(priorite) AS priorite
      FROM _fec068_reglement_candidates
     GROUP BY ecriture_id
), u AS (
    SELECT c.ecriture_id, MIN(c.reglement_id) AS reglement_id,
           MIN(c.reference_piece) AS reference_piece
      FROM _fec068_reglement_candidates c
      JOIN p ON p.ecriture_id=c.ecriture_id AND p.priorite=c.priorite
     GROUP BY c.ecriture_id
    HAVING COUNT(DISTINCT c.reglement_id)=1
)
SELECT * FROM u;

INSERT INTO ecriture_justificatifs (
    societe_id, ecriture_id, reference, date_piece,
    source_type, source_id, prioritaire, motif
)
SELECT e.societe_id, e.id, m.reference_piece, COALESCE(e.date_piece,e.date),
       'reparation_fec_reglement', m.reglement_id, TRUE,
       'Patch 097 : référence du règlement source ajoutée en complément append-only.'
  FROM _fec068_reglement_match m
  JOIN ecritures e ON e.id=m.ecriture_id
 WHERE NULLIF(BTRIM(m.reference_piece),'') IS NOT NULL
   AND NOT EXISTS (
       SELECT 1 FROM ecriture_justificatifs j
        WHERE j.ecriture_id=e.id
          AND NULLIF(BTRIM(j.reference),'') IS NOT NULL
   );

COMMIT;

-- Diagnostic non destructif affiché par pgAdmin/psql après migration.
SELECT
    (SELECT COUNT(*) FROM ligne_auxiliaire_complements) AS complements_auxiliaires_total,
    (SELECT COUNT(*) FROM ecriture_justificatifs
      WHERE source_type IN ('reparation_fec_facture','reparation_fec_reglement')) AS references_fec_reparees_total;
