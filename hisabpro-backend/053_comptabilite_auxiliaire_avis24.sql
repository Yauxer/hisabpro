-- Patch 053 — Comptabilité auxiliaire native + FEC Avis n°24
-- Objectif : chaque ligne de compte collectif client/fournisseur porte une
-- identité auxiliaire explicite et historique, sans déduction depuis le libellé.

BEGIN;

-- 1) Référentiel tiers : codes auxiliaires stables, propres au rôle.
ALTER TABLE tiers ADD COLUMN IF NOT EXISTS code_aux_client VARCHAR(20);
ALTER TABLE tiers ADD COLUMN IF NOT EXISTS code_aux_fournisseur VARCHAR(20);

UPDATE tiers
   SET code_aux_client = 'C' || LPAD(id::text, 8, '0')
 WHERE type IN ('client','les_deux')
   AND NULLIF(BTRIM(code_aux_client), '') IS NULL;

UPDATE tiers
   SET code_aux_fournisseur = 'F' || LPAD(id::text, 8, '0')
 WHERE type IN ('fournisseur','les_deux')
   AND NULLIF(BTRIM(code_aux_fournisseur), '') IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_tiers_code_aux_client_societe
    ON tiers (societe_id, code_aux_client)
    WHERE code_aux_client IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_tiers_code_aux_fournisseur_societe
    ON tiers (societe_id, code_aux_fournisseur)
    WHERE code_aux_fournisseur IS NOT NULL;

-- 2) Les règlements gardent désormais le lien natif vers le tiers.
ALTER TABLE reglements ADD COLUMN IF NOT EXISTS tiers_id INTEGER;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_reglements_tiers_aux053') THEN
        ALTER TABLE reglements
          ADD CONSTRAINT fk_reglements_tiers_aux053
          FOREIGN KEY (tiers_id) REFERENCES tiers(id) ON DELETE SET NULL;
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS ix_reglements_tiers_id ON reglements(tiers_id);

UPDATE reglements r
   SET tiers_id = f.tiers_id
  FROM factures f
 WHERE r.tiers_id IS NULL
   AND r.facture_id = f.id
   AND f.societe_id = r.societe_id
   AND f.tiers_id IS NOT NULL;

-- Fallback historique uniquement si le nom correspond exactement à un seul tiers.
WITH uniques AS (
    SELECT r.id AS reglement_id, MIN(t.id) AS tiers_id
      FROM reglements r
      JOIN tiers t ON t.societe_id=r.societe_id
                  AND LOWER(BTRIM(t.nom))=LOWER(BTRIM(r.tiers))
     WHERE r.tiers_id IS NULL
     GROUP BY r.id
    HAVING COUNT(*)=1
)
UPDATE reglements r SET tiers_id=u.tiers_id FROM uniques u WHERE r.id=u.reglement_id;

-- 3) Identité auxiliaire figée sur la ligne comptable définitive.
ALTER TABLE lignes_ecriture ADD COLUMN IF NOT EXISTS tiers_id INTEGER;
ALTER TABLE lignes_ecriture ADD COLUMN IF NOT EXISTS nature_auxiliaire VARCHAR(20);
ALTER TABLE lignes_ecriture ADD COLUMN IF NOT EXISTS compte_auxiliaire_snapshot VARCHAR(20);
ALTER TABLE lignes_ecriture ADD COLUMN IF NOT EXISTS libelle_auxiliaire_snapshot VARCHAR(200);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_lignes_ecriture_tiers_aux053') THEN
        ALTER TABLE lignes_ecriture
          ADD CONSTRAINT fk_lignes_ecriture_tiers_aux053
          FOREIGN KEY (tiers_id) REFERENCES tiers(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_lignes_ecriture_nature_aux053') THEN
        ALTER TABLE lignes_ecriture
          ADD CONSTRAINT ck_lignes_ecriture_nature_aux053
          CHECK (nature_auxiliaire IS NULL OR nature_auxiliaire IN ('client','fournisseur'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_lignes_ecriture_tiers_id ON lignes_ecriture(tiers_id);
CREATE INDEX IF NOT EXISTS ix_lignes_ecriture_aux_reporting
    ON lignes_ecriture(compte, tiers_id, ecriture_id);

-- Les enrichissements ci-dessous concernent uniquement la migration de données.
-- On neutralise temporairement les gardes d'immutabilité/audit puis on les réactive.
ALTER TABLE lignes_ecriture DISABLE TRIGGER trg_hisabpro_proteger_lignes_definitives;
ALTER TABLE lignes_ecriture DISABLE TRIGGER trg_hisabpro_audit_lignes_ecriture;

-- Factures : rattachement sûr lorsqu'une seule pièce métier correspond à l'écriture.
WITH candidats AS (
    SELECT l.id AS ligne_id, MIN(f.tiers_id) AS tiers_id,
           CASE WHEN MIN(f.type::text)='vente' THEN 'client' ELSE 'fournisseur' END AS nature
      FROM lignes_ecriture l
      JOIN ecritures e ON e.id=l.ecriture_id AND e.source='facture'
      JOIN factures f ON f.societe_id=e.societe_id
                     AND f.exercice=e.exercice
                     AND f.date=e.date
                     AND (e.reference=f.numero OR (f.reference IS NOT NULL AND e.reference=f.reference))
     WHERE l.tiers_id IS NULL
       AND f.tiers_id IS NOT NULL
       AND ((f.type::text='vente' AND l.compte LIKE '3421%')
         OR (f.type::text='achat' AND l.compte LIKE '4411%'))
     GROUP BY l.id
    HAVING COUNT(DISTINCT f.id)=1
)
UPDATE lignes_ecriture l
   SET tiers_id=c.tiers_id, nature_auxiliaire=c.nature
  FROM candidats c WHERE l.id=c.ligne_id;

-- Avoirs : numéro d'avoir + facture source donnent le tiers sans ambiguïté.
UPDATE lignes_ecriture l
   SET tiers_id=f.tiers_id,
       nature_auxiliaire=CASE WHEN a.type::text='vente' THEN 'client' ELSE 'fournisseur' END
  FROM ecritures e
  JOIN avoirs a ON a.societe_id=e.societe_id AND a.numero=e.reference
  JOIN factures f ON f.id=a.facture_id AND f.societe_id=a.societe_id
 WHERE l.ecriture_id=e.id
   AND e.source='avoir'
   AND l.tiers_id IS NULL
   AND f.tiers_id IS NOT NULL
   AND ((a.type::text='vente' AND l.compte LIKE '3421%')
     OR (a.type::text='achat' AND l.compte LIKE '4411%'));

-- Règlements : lien explicite règlement -> écriture -> tiers.
UPDATE lignes_ecriture l
   SET tiers_id=r.tiers_id,
       nature_auxiliaire=CASE
         WHEN l.compte LIKE '3421%' OR l.compte LIKE '3425%' THEN 'client'
         WHEN l.compte LIKE '4411%' OR l.compte LIKE '4415%' THEN 'fournisseur'
         ELSE nature_auxiliaire END
  FROM reglements r
 WHERE r.ecriture_id=l.ecriture_id
   AND r.tiers_id IS NOT NULL
   AND l.tiers_id IS NULL
   AND (l.compte LIKE '3421%' OR l.compte LIKE '3425%' OR l.compte LIKE '4411%' OR l.compte LIKE '4415%');

-- Acomptes : la référence métier est stable et le tiers est déjà natif.
UPDATE lignes_ecriture l
   SET tiers_id=a.tiers_id,
       nature_auxiliaire=CASE WHEN a.type='client' THEN 'client' ELSE 'fournisseur' END
  FROM ecritures e
  JOIN acomptes a ON a.societe_id=e.societe_id AND a.numero=e.reference
 WHERE l.ecriture_id=e.id
   AND e.source='acompte'
   AND a.tiers_id IS NOT NULL
   AND l.tiers_id IS NULL
   AND (l.compte LIKE '3421%' OR l.compte LIKE '4421%' OR l.compte LIKE '4411%' OR l.compte LIKE '3411%');

-- Immobilisations : dette d'acquisition identifiée par ACQ-<année>-<id>.
UPDATE lignes_ecriture l
   SET tiers_id=i.fournisseur_tiers_id,
       nature_auxiliaire='fournisseur'
  FROM ecritures e
  JOIN immobilisations i
    ON i.societe_id=e.societe_id
   AND e.reference=('ACQ-' || EXTRACT(YEAR FROM i.date_acquisition)::int || '-' || i.id)
 WHERE l.ecriture_id=e.id
   AND i.fournisseur_tiers_id IS NOT NULL
   AND l.tiers_id IS NULL
   AND (l.compte LIKE '4411%' OR l.compte LIKE '4481%');

-- Fallback legacy strict : pour une ligne collective historique encore anonyme,
-- on accepte uniquement un nom de ligne égal au nom d'un UNIQUE tiers compatible
-- de la même société. Aucun rapprochement approximatif n'est effectué.
WITH uniques AS (
    SELECT l.id AS ligne_id, MIN(t.id) AS tiers_id,
           CASE WHEN l.compte LIKE '3421%' THEN 'client' ELSE 'fournisseur' END AS nature
      FROM lignes_ecriture l
      JOIN ecritures e ON e.id=l.ecriture_id
      JOIN tiers t ON t.societe_id=e.societe_id
                  AND LOWER(BTRIM(t.nom))=LOWER(BTRIM(COALESCE(l.libelle,'')))
                  AND (
                       (l.compte LIKE '3421%' AND t.type IN ('client','les_deux'))
                    OR (l.compte LIKE '4411%' AND t.type IN ('fournisseur','les_deux'))
                  )
     WHERE l.tiers_id IS NULL
       AND (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
     GROUP BY l.id, l.compte
    HAVING COUNT(*)=1
)
UPDATE lignes_ecriture l
   SET tiers_id=u.tiers_id, nature_auxiliaire=u.nature
  FROM uniques u
 WHERE l.id=u.ligne_id;

-- Snapshot historique : jamais recalculé lors d'un export futur.
UPDATE lignes_ecriture l
   SET compte_auxiliaire_snapshot = CASE
           WHEN l.nature_auxiliaire='client' THEN t.code_aux_client
           WHEN l.nature_auxiliaire='fournisseur' THEN t.code_aux_fournisseur
       END,
       libelle_auxiliaire_snapshot = t.nom
  FROM tiers t
 WHERE l.tiers_id=t.id
   AND (NULLIF(BTRIM(l.compte_auxiliaire_snapshot),'') IS NULL
        OR NULLIF(BTRIM(l.libelle_auxiliaire_snapshot),'') IS NULL);

ALTER TABLE lignes_ecriture ENABLE TRIGGER trg_hisabpro_audit_lignes_ecriture;
ALTER TABLE lignes_ecriture ENABLE TRIGGER trg_hisabpro_proteger_lignes_definitives;

-- 4) Garde DB : une écriture collective 3421/4411 ne devient jamais définitive
-- sans Num_Compte_Aux + Libelle_Compte_Aux figés.
CREATE OR REPLACE FUNCTION hisabpro_guard_auxiliaire_validation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF COALESCE(NEW.est_validee,FALSE)=TRUE
       AND COALESCE(OLD.est_validee,FALSE)=FALSE THEN
        IF EXISTS (
            SELECT 1 FROM lignes_ecriture l
             WHERE l.ecriture_id=NEW.id
               AND (l.compte LIKE '3421%' OR l.compte LIKE '4411%')
               AND (l.tiers_id IS NULL
                    OR NULLIF(BTRIM(l.compte_auxiliaire_snapshot),'') IS NULL
                    OR NULLIF(BTRIM(l.libelle_auxiliaire_snapshot),'') IS NULL)
        ) THEN
            RAISE EXCEPTION
                'Auxiliaire obligatoire : les lignes 3421/4411 doivent porter un client/fournisseur et son compte auxiliaire avant validation.'
                USING ERRCODE='23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_auxiliaire_validation ON ecritures;
CREATE TRIGGER trg_hisabpro_auxiliaire_validation
BEFORE UPDATE OF est_validee ON ecritures
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_auxiliaire_validation();

-- Défense en profondeur : si une intégration externe insère exceptionnellement
-- des lignes après avoir créé une écriture déjà définitive, la ligne elle-même
-- reste contrôlée. Le flux HisabPro normal insère les lignes sur un brouillon,
-- puis valide l'écriture, mais la base ne dépend pas de cette seule convention.
CREATE OR REPLACE FUNCTION hisabpro_guard_ligne_auxiliaire_definitive()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_validee BOOLEAN;
BEGIN
    IF NEW.compte LIKE '3421%' OR NEW.compte LIKE '4411%' THEN
        SELECT COALESCE(est_validee,FALSE) INTO v_validee
          FROM ecritures WHERE id=NEW.ecriture_id;
        IF COALESCE(v_validee,FALSE)=TRUE
           AND (NEW.tiers_id IS NULL
                OR NULLIF(BTRIM(NEW.compte_auxiliaire_snapshot),'') IS NULL
                OR NULLIF(BTRIM(NEW.libelle_auxiliaire_snapshot),'') IS NULL) THEN
            RAISE EXCEPTION
                'Auxiliaire obligatoire : une ligne 3421/4411 d''une écriture définitive doit porter son auxiliaire.'
                USING ERRCODE='23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_ligne_auxiliaire_definitive ON lignes_ecriture;
CREATE TRIGGER trg_hisabpro_ligne_auxiliaire_definitive
BEFORE INSERT OR UPDATE OF compte, tiers_id, compte_auxiliaire_snapshot, libelle_auxiliaire_snapshot
ON lignes_ecriture
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_ligne_auxiliaire_definitive();

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        GRANT EXECUTE ON FUNCTION hisabpro_guard_auxiliaire_validation() TO hisabpro;
        GRANT EXECUTE ON FUNCTION hisabpro_guard_ligne_auxiliaire_definitive() TO hisabpro;
    END IF;
END $$;

COMMIT;
