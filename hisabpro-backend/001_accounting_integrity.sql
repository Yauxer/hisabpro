-- HisabPro PATCH 01 — Intégrité du grand livre
-- À exécuter UNE FOIS sur une base existante, après sauvegarde.
-- PostgreSQL.

BEGIN;

-- 1) Refuser la migration si des données déjà présentes sont comptablement invalides.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM lignes_ecriture
        WHERE COALESCE(debit, 0) < 0
           OR COALESCE(credit, 0) < 0
           OR (COALESCE(debit, 0) > 0 AND COALESCE(credit, 0) > 0)
    ) THEN
        RAISE EXCEPTION
            'Migration interrompue : lignes_ecriture contient des montants négatifs ou des lignes simultanément débit/crédit. Corrigez ces lignes avant de relancer.';
    END IF;
END $$;

-- 2) Normaliser les NULL existants avant de rendre les colonnes NOT NULL.
UPDATE lignes_ecriture SET debit = 0 WHERE debit IS NULL;
UPDATE lignes_ecriture SET credit = 0 WHERE credit IS NULL;

-- 3) FLOAT -> NUMERIC(18,2) : source de vérité monétaire exacte.
ALTER TABLE lignes_ecriture
    ALTER COLUMN debit TYPE NUMERIC(18,2)
        USING ROUND(COALESCE(debit, 0)::numeric, 2),
    ALTER COLUMN credit TYPE NUMERIC(18,2)
        USING ROUND(COALESCE(credit, 0)::numeric, 2),
    ALTER COLUMN debit SET DEFAULT 0.00,
    ALTER COLUMN credit SET DEFAULT 0.00,
    ALTER COLUMN debit SET NOT NULL,
    ALTER COLUMN credit SET NOT NULL;

-- 4) Après arrondi monétaire, aucune écriture existante ne doit devenir déséquilibrée.
DO $$
BEGIN
    IF EXISTS (
        SELECT ecriture_id
        FROM lignes_ecriture
        GROUP BY ecriture_id
        HAVING ROUND(SUM(debit), 2) <> ROUND(SUM(credit), 2)
    ) THEN
        RAISE EXCEPTION
            'Migration interrompue : au moins une écriture devient déséquilibrée après passage en NUMERIC(18,2). Vérifiez les écritures concernées.';
    END IF;
END $$;

-- 5) Contraintes SQL : même un import/script externe ne peut plus injecter
--    un débit/crédit négatif ou les deux sens sur la même ligne.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_ligne_ecriture_debit_non_negatif') THEN
        ALTER TABLE lignes_ecriture
            ADD CONSTRAINT ck_ligne_ecriture_debit_non_negatif CHECK (debit >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_ligne_ecriture_credit_non_negatif') THEN
        ALTER TABLE lignes_ecriture
            ADD CONSTRAINT ck_ligne_ecriture_credit_non_negatif CHECK (credit >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_ligne_ecriture_un_seul_sens') THEN
        ALTER TABLE lignes_ecriture
            ADD CONSTRAINT ck_ligne_ecriture_un_seul_sens CHECK (NOT (debit > 0 AND credit > 0));
    END IF;
END $$;

COMMIT;

-- Contrôles de sortie : doivent retourner 0 anomalie.
SELECT COUNT(*) AS lignes_invalides
FROM lignes_ecriture
WHERE debit < 0 OR credit < 0 OR (debit > 0 AND credit > 0);

SELECT COUNT(*) AS ecritures_desequilibrees
FROM (
    SELECT ecriture_id
    FROM lignes_ecriture
    GROUP BY ecriture_id
    HAVING SUM(debit) <> SUM(credit)
) x;
