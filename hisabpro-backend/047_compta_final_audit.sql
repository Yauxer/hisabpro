-- COMPTA-FINAL — corrections issues de l'audit final Comptabilité
-- À exécuter APRÈS 046_factH_audit_final_facturation.sql.
--
-- 1) lettrage persistant sans modifier les lignes comptables définitives ;
-- 2) rapprochement bancaire persistant ligne relevé <-> ligne comptable ;
-- 3) état/solde de relevé persistant par compte et période ;
-- 4) garde-fous PostgreSQL tenant / compte / sens / montant / écriture définitive.
BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Lettrage comptable : métadonnée séparée de lignes_ecriture.
--    On ne rajoute volontairement PAS code_lettrage sur lignes_ecriture :
--    COMPTA.3 rend les lignes définitives immuables, ce qui doit rester vrai.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lettrages_comptables (
    id                SERIAL PRIMARY KEY,
    societe_id        INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    ligne_ecriture_id INTEGER NOT NULL REFERENCES lignes_ecriture(id) ON DELETE CASCADE,
    code              VARCHAR(10) NOT NULL,
    date_lettrage     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by        INTEGER NULL REFERENCES utilisateurs(id) ON DELETE SET NULL,
    actif             BOOLEAN NOT NULL DEFAULT TRUE,
    date_delettrage   TIMESTAMP NULL,
    delettre_par      INTEGER NULL REFERENCES utilisateurs(id) ON DELETE SET NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_lettrage_code CHECK (code ~ '^[A-Z]{1,10}$')
);

CREATE INDEX IF NOT EXISTS ix_lettrages_comptables_societe_code
    ON lettrages_comptables (societe_id, code);
CREATE INDEX IF NOT EXISTS ix_lettrages_comptables_ligne
    ON lettrages_comptables (ligne_ecriture_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_lettrage_comptable_ligne_actif
    ON lettrages_comptables (ligne_ecriture_id)
    WHERE actif = TRUE;

CREATE OR REPLACE FUNCTION hisabpro_guard_lettrage_comptable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_societe_id INTEGER;
    v_validee BOOLEAN;
    v_numero VARCHAR(80);
    v_compte VARCHAR(20);
BEGIN
    SELECT e.societe_id, e.est_validee, e.numero_ecriture, l.compte
      INTO v_societe_id, v_validee, v_numero, v_compte
      FROM lignes_ecriture l
      JOIN ecritures e ON e.id = l.ecriture_id
     WHERE l.id = NEW.ligne_ecriture_id;

    IF v_societe_id IS NULL THEN
        RAISE EXCEPTION 'Ligne comptable de lettrage introuvable' USING ERRCODE='23503';
    END IF;
    IF NEW.societe_id <> v_societe_id THEN
        RAISE EXCEPTION 'Lettrage inter-sociétés interdit' USING ERRCODE='23514';
    END IF;
    IF COALESCE(v_validee, FALSE) = FALSE OR v_numero IS NULL THEN
        RAISE EXCEPTION 'Le lettrage est réservé aux écritures comptables définitives' USING ERRCODE='23514';
    END IF;
    IF LEFT(v_compte, 4) NOT IN ('3421','4411') THEN
        RAISE EXCEPTION 'Compte % non lettrable : seuls 3421/4411 sont autorisés', v_compte USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_guard_lettrage_comptable ON lettrages_comptables;
CREATE TRIGGER trg_hisabpro_guard_lettrage_comptable
BEFORE INSERT OR UPDATE OF ligne_ecriture_id, societe_id, actif ON lettrages_comptables
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_lettrage_comptable();

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Rapprochement bancaire réellement lié à la ligne comptable.
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE rapprochement_lignes
    ADD COLUMN IF NOT EXISTS ecriture_ligne_id INTEGER NULL,
    ADD COLUMN IF NOT EXISTS date_rapprochement TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS rapproche_par INTEGER NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_rapprochement_ecriture_ligne') THEN
        ALTER TABLE rapprochement_lignes
            ADD CONSTRAINT fk_rapprochement_ecriture_ligne
            FOREIGN KEY (ecriture_ligne_id) REFERENCES lignes_ecriture(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_rapprochement_rapproche_par') THEN
        ALTER TABLE rapprochement_lignes
            ADD CONSTRAINT fk_rapprochement_rapproche_par
            FOREIGN KEY (rapproche_par) REFERENCES utilisateurs(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_rapprochement_lignes_ecriture_ligne
    ON rapprochement_lignes (ecriture_ligne_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_rapprochement_ecriture_ligne_active
    ON rapprochement_lignes (ecriture_ligne_id)
    WHERE ecriture_ligne_id IS NOT NULL AND rapprochee = TRUE;

CREATE OR REPLACE FUNCTION hisabpro_guard_rapprochement_comptable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_societe_id INTEGER;
    v_compte VARCHAR(20);
    v_debit NUMERIC(18,2);
    v_credit NUMERIC(18,2);
    v_validee BOOLEAN;
    v_numero VARCHAR(80);
    v_montant_compta NUMERIC(18,2);
BEGIN
    IF NEW.ecriture_ligne_id IS NULL THEN
        IF COALESCE(NEW.rapprochee, FALSE) THEN
            RAISE EXCEPTION 'Une ligne rapprochée doit référencer une ligne comptable' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
    END IF;

    SELECT e.societe_id, l.compte, l.debit, l.credit, e.est_validee, e.numero_ecriture
      INTO v_societe_id, v_compte, v_debit, v_credit, v_validee, v_numero
      FROM lignes_ecriture l
      JOIN ecritures e ON e.id = l.ecriture_id
     WHERE l.id = NEW.ecriture_ligne_id;

    IF v_societe_id IS NULL THEN
        RAISE EXCEPTION 'Ligne comptable de rapprochement introuvable' USING ERRCODE='23503';
    END IF;
    IF NEW.societe_id <> v_societe_id THEN
        RAISE EXCEPTION 'Rapprochement inter-sociétés interdit' USING ERRCODE='23514';
    END IF;
    IF COALESCE(v_validee, FALSE) = FALSE OR v_numero IS NULL THEN
        RAISE EXCEPTION 'Rapprochement réservé aux écritures définitives' USING ERRCODE='23514';
    END IF;
    IF NEW.compte <> v_compte THEN
        RAISE EXCEPTION 'Compte relevé % différent du compte comptable %', NEW.compte, v_compte USING ERRCODE='23514';
    END IF;

    -- Convention bancaire : crédit relevé = débit banque en comptabilité,
    -- débit relevé = crédit banque en comptabilité.
    IF NEW.sens = 'credit' THEN
        v_montant_compta := COALESCE(v_debit, 0);
    ELSIF NEW.sens = 'debit' THEN
        v_montant_compta := COALESCE(v_credit, 0);
    ELSE
        RAISE EXCEPTION 'Sens de relevé invalide : %', NEW.sens USING ERRCODE='23514';
    END IF;

    IF ABS(COALESCE(NEW.montant,0)::NUMERIC - v_montant_compta) > 0.01 THEN
        RAISE EXCEPTION 'Montant du relevé (%) incompatible avec la ligne comptable (%)', NEW.montant, v_montant_compta USING ERRCODE='23514';
    END IF;

    NEW.rapprochee := TRUE;
    NEW.date_rapprochement := COALESCE(NEW.date_rapprochement, CURRENT_TIMESTAMP);
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_guard_rapprochement_comptable ON rapprochement_lignes;
CREATE TRIGGER trg_hisabpro_guard_rapprochement_comptable
BEFORE INSERT OR UPDATE OF ecriture_ligne_id, rapprochee, compte, sens, montant, societe_id
ON rapprochement_lignes
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_rapprochement_comptable();

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Solde de relevé persistant par compte/période.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rapprochement_etats (
    id           SERIAL PRIMARY KEY,
    societe_id   INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    compte       VARCHAR(10) NOT NULL,
    date_debut   DATE NOT NULL,
    date_fin     DATE NOT NULL,
    solde_releve NUMERIC(18,2) NULL,
    updated_by   INTEGER NULL REFERENCES utilisateurs(id) ON DELETE SET NULL,
    updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_rapprochement_etat_dates CHECK (date_fin >= date_debut),
    CONSTRAINT uq_rapprochement_etat_periode UNIQUE (societe_id, compte, date_debut, date_fin)
);

CREATE INDEX IF NOT EXISTS ix_rapprochement_etats_societe_compte
    ON rapprochement_etats (societe_id, compte, date_debut, date_fin);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON lettrages_comptables, rapprochement_etats TO hisabpro;
        GRANT USAGE, SELECT ON SEQUENCE lettrages_comptables_id_seq, rapprochement_etats_id_seq TO hisabpro;
        GRANT EXECUTE ON FUNCTION hisabpro_guard_lettrage_comptable() TO hisabpro;
        GRANT EXECUTE ON FUNCTION hisabpro_guard_rapprochement_comptable() TO hisabpro;
    END IF;
END $$;

COMMIT;
