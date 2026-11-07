-- Patch 092 — réparation ponctuelle des liquidations IS confirmées avant le
-- contrôle de cohérence de la référence des acomptes.
--
-- Le script ne retire QUE les photographies pour lesquelles :
--   1) un exercice comptable antérieur existe ;
--   2) aucune liquidation fiscale N-1 n'est confirmée ;
--   3) aucune référence annuelle d'acomptes n'a été forcée/justifiée.
-- Les véritables premiers exercices ne sont donc pas concernés.
--
-- À exécuter une fois en tant que propriétaire de la base (le trigger
-- d'immutabilité doit être momentanément suspendu pour réparer ces lignes
-- créées par l'ancien comportement applicatif).

BEGIN;

LOCK TABLE fiscal_liquidations_is IN SHARE ROW EXCLUSIVE MODE;

ALTER TABLE fiscal_liquidations_is
    DISABLE TRIGGER trg_hisabpro_fiscal_liquidation_immutable;

WITH invalides AS (
    SELECT l.id
    FROM fiscal_liquidations_is l
    JOIN exercices_comptables courant
      ON courant.societe_id = l.societe_id
     AND courant.annee = l.exercice
    LEFT JOIN fiscal_parametres_exercice p
      ON p.societe_id = l.societe_id
     AND p.exercice = l.exercice
    WHERE EXISTS (
        SELECT 1
        FROM exercices_comptables precedent
        WHERE precedent.societe_id = l.societe_id
          AND precedent.date_fin < courant.date_debut
    )
      AND NOT EXISTS (
        SELECT 1
        FROM fiscal_liquidations_is n_1
        WHERE n_1.societe_id = l.societe_id
          AND n_1.exercice = l.exercice - 1
      )
      AND p.acomptes_reference_forcee IS NULL
)
DELETE FROM fiscal_liquidations_is l
USING invalides i
WHERE l.id = i.id;

ALTER TABLE fiscal_liquidations_is
    ENABLE TRIGGER trg_hisabpro_fiscal_liquidation_immutable;

COMMIT;
