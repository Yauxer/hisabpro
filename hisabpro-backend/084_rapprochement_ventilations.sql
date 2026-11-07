-- Additif : aucune reprise arbitraire d'anciens règlements ou relevés.
-- À appliquer après 048 et 083. Aucun montant ou écriture comptable modifié.
BEGIN;
CREATE TABLE IF NOT EXISTS rapprochement_ventilations (
    releve_id INTEGER NOT NULL REFERENCES rapprochement_lignes(id) ON DELETE RESTRICT,
    ecriture_ligne_id INTEGER NOT NULL REFERENCES lignes_ecriture(id) ON DELETE RESTRICT,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    operation_id UUID NOT NULL,
    PRIMARY KEY (releve_id, ecriture_ligne_id),
    CONSTRAINT uq_rapprochement_ventilation_ligne UNIQUE (ecriture_ligne_id)
);
CREATE INDEX IF NOT EXISTS ix_rapprochement_ventilation_societe
    ON rapprochement_ventilations(societe_id, releve_id);

CREATE OR REPLACE FUNCTION hisabpro_guard_rapprochement_ventilation()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v RECORD; r RECORD; e RECORD;
BEGIN
    IF TG_OP='UPDATE' THEN
        RAISE EXCEPTION 'Dérapprocher puis rapprocher explicitement la ventilation' USING ERRCODE='23514';
    END IF;
    IF TG_OP='DELETE' THEN v:=OLD; ELSE v:=NEW; END IF;
    PERFORM pg_advisory_xact_lock(726883, v.societe_id);
    SELECT * INTO r FROM rapprochement_lignes WHERE id=v.releve_id FOR UPDATE;
    SELECT ec.*, l.compte AS compte_ligne INTO e FROM lignes_ecriture l
        JOIN ecritures ec ON ec.id=l.ecriture_id WHERE l.id=v.ecriture_ligne_id;
    IF r.societe_id IS DISTINCT FROM v.societe_id OR e.societe_id IS DISTINCT FROM v.societe_id
       OR r.compte IS DISTINCT FROM e.compte_ligne THEN
        RAISE EXCEPTION 'Société ou compte bancaire incompatible' USING ERRCODE='23514';
    END IF;
    IF EXISTS(SELECT 1 FROM exercices_comptables x WHERE x.societe_id=v.societe_id
        AND x.statut='cloture' AND (r.date BETWEEN x.date_debut AND x.date_fin OR e.date BETWEEN x.date_debut AND x.date_fin))
       OR EXISTS(SELECT 1 FROM clotures_exercice x WHERE x.societe_id=v.societe_id
        AND x.exercice IN (EXTRACT(YEAR FROM r.date)::INTEGER, e.exercice)) THEN
        RAISE EXCEPTION 'Exercice clôturé : rapprochement bancaire en lecture seule' USING ERRCODE='23514';
    END IF;
    IF TG_OP='INSERT' THEN
        IF e.est_validee IS DISTINCT FROM TRUE OR e.numero_ecriture IS NULL
           OR r.ecriture_ligne_id IS NOT NULL
           OR NOT EXISTS(SELECT 1 FROM reglements g WHERE g.societe_id=v.societe_id
                AND g.ecriture_id=e.id AND g.numero LIKE 'VT-'||REPLACE(v.operation_id::TEXT,'-','')||'-%') THEN
            RAISE EXCEPTION 'Lien définitif natif de ventilation requis' USING ERRCODE='23514';
        END IF;
        IF EXISTS(SELECT 1 FROM rapprochement_lignes x WHERE x.societe_id=v.societe_id
            AND x.rapprochee AND x.ecriture_ligne_id=v.ecriture_ligne_id AND x.id<>v.releve_id)
           OR EXISTS(SELECT 1 FROM rapprochement_ventilations x WHERE x.releve_id=v.releve_id
            AND x.operation_id<>v.operation_id) THEN
            RAISE EXCEPTION 'Ligne déjà rapprochée ou lot incompatible' USING ERRCODE='23505';
        END IF;
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END $$;
DROP TRIGGER IF EXISTS trg_hisabpro_rapprochement_ventilation ON rapprochement_ventilations;
CREATE TRIGGER trg_hisabpro_rapprochement_ventilation BEFORE INSERT OR UPDATE OR DELETE
    ON rapprochement_ventilations FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_rapprochement_ventilation();

CREATE OR REPLACE FUNCTION hisabpro_guard_releve_ventilation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(726883,NEW.societe_id);
    IF TG_OP='UPDATE' AND EXISTS(SELECT 1 FROM rapprochement_ventilations x WHERE x.releve_id=NEW.id) AND
       (NEW.societe_id IS DISTINCT FROM OLD.societe_id OR NEW.compte IS DISTINCT FROM OLD.compte
        OR NEW.date IS DISTINCT FROM OLD.date OR NEW.montant IS DISTINCT FROM OLD.montant
        OR NEW.sens IS DISTINCT FROM OLD.sens OR NEW.libelle IS DISTINCT FROM OLD.libelle
        OR NEW.rapprochee IS DISTINCT FROM TRUE OR NEW.ecriture_ligne_id IS NOT NULL) THEN
        RAISE EXCEPTION 'Dérapprochez la ventilation avant de modifier le relevé' USING ERRCODE='23514';
    END IF;
    IF NEW.rapprochee AND NEW.ecriture_ligne_id IS NOT NULL AND
       EXISTS(SELECT 1 FROM rapprochement_ventilations x WHERE x.ecriture_ligne_id=NEW.ecriture_ligne_id) THEN
        RAISE EXCEPTION 'Cette ligne comptable est déjà rapprochée avec une ventilation' USING ERRCODE='23505';
    END IF;
    RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_hisabpro_releve_ventilation ON rapprochement_lignes;
CREATE TRIGGER trg_hisabpro_releve_ventilation BEFORE INSERT OR UPDATE
    ON rapprochement_lignes FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_releve_ventilation();

DO $$ BEGIN
    IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro') THEN
        GRANT SELECT,INSERT,DELETE ON rapprochement_ventilations TO hisabpro;
        GRANT SELECT,UPDATE ON rapprochement_lignes TO hisabpro;
        GRANT SELECT ON reglements,factures,ecritures,lignes_ecriture,
            exercices_comptables,clotures_exercice TO hisabpro;
        REVOKE UPDATE,TRUNCATE ON rapprochement_ventilations FROM hisabpro;
    END IF;
END $$;

-- Le garde 047 des liens simples reste identique. Seule sa branche sans lien
-- accepte les nouvelles affectations intégrales, contrôlées au centime.
CREATE OR REPLACE FUNCTION hisabpro_check_rapprochement_ventilation(p rapprochement_lignes)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE n INTEGER; total NUMERIC; op UUID; nb_nat INTEGER;
BEGIN
    SELECT COUNT(*), MIN(operation_id::TEXT)::UUID INTO n,op
        FROM rapprochement_ventilations WHERE releve_id=p.id;
    IF p.rapprochee IS DISTINCT FROM TRUE OR p.ecriture_ligne_id IS NOT NULL OR n<2 OR n>50
       OR EXISTS(SELECT 1 FROM rapprochement_ventilations a WHERE a.releve_id=p.id
            AND (a.societe_id<>p.societe_id OR a.operation_id<>op)) THEN
        RAISE EXCEPTION 'Une ligne rapprochée doit référencer une ligne comptable ou une ventilation entière' USING ERRCODE='23514';
    END IF;
    IF EXISTS(SELECT 1 FROM rapprochement_ventilations a
        JOIN lignes_ecriture l ON l.id=a.ecriture_ligne_id JOIN ecritures e ON e.id=l.ecriture_id
        WHERE a.releve_id=p.id AND (e.societe_id<>p.societe_id OR l.compte<>p.compte
            OR e.est_validee IS DISTINCT FROM TRUE OR e.numero_ecriture IS NULL
            OR (p.sens='credit' AND (l.debit<=0 OR COALESCE(l.credit,0)<>0))
            OR (p.sens='debit' AND (l.credit<=0 OR COALESCE(l.debit,0)<>0)))) THEN
        RAISE EXCEPTION 'Lignes bancaires définitives incompatibles avec la ventilation' USING ERRCODE='23514';
    END IF;
    SELECT COUNT(*) INTO nb_nat FROM reglements g WHERE g.societe_id=p.societe_id
        AND g.numero LIKE 'VT-'||REPLACE(op::TEXT,'-','')||'-%';
    IF nb_nat<>n OR EXISTS(SELECT 1 FROM reglements g WHERE g.societe_id=p.societe_id
        AND g.numero LIKE 'VT-'||REPLACE(op::TEXT,'-','')||'-%'
        AND NOT EXISTS(SELECT 1 FROM rapprochement_ventilations a JOIN lignes_ecriture l
            ON l.id=a.ecriture_ligne_id WHERE a.releve_id=p.id AND l.ecriture_id=g.ecriture_id)) THEN
        RAISE EXCEPTION 'Le lot natif doit être rapproché intégralement' USING ERRCODE='23514';
    END IF;
    SELECT SUM(CASE WHEN p.sens='credit' THEN l.debit ELSE l.credit END) INTO total
        FROM rapprochement_ventilations a JOIN lignes_ecriture l ON l.id=a.ecriture_ligne_id WHERE a.releve_id=p.id;
    IF p.sens NOT IN ('credit','debit') OR total IS NULL OR total::TEXT IN ('NaN','Infinity','-Infinity')
       OR p.montant::TEXT IN ('NaN','Infinity','-Infinity') OR p.montant::NUMERIC<>total THEN
        RAISE EXCEPTION 'Le total de la ventilation doit égaler exactement le relevé' USING ERRCODE='23514';
    END IF;
END $$;
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
            PERFORM hisabpro_check_rapprochement_ventilation(NEW);
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


CREATE OR REPLACE FUNCTION hisabpro_guard_ventilation_commit()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE r rapprochement_lignes; rid INTEGER;
BEGIN
    IF TG_OP='DELETE' THEN rid:=OLD.releve_id; ELSE rid:=NEW.releve_id; END IF;
    SELECT * INTO r FROM rapprochement_lignes WHERE id=rid;
    IF r.rapprochee OR EXISTS(SELECT 1 FROM rapprochement_ventilations WHERE releve_id=rid) THEN
        PERFORM hisabpro_check_rapprochement_ventilation(r);
    END IF;
    RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS trg_hisabpro_ventilation_commit ON rapprochement_ventilations;
CREATE CONSTRAINT TRIGGER trg_hisabpro_ventilation_commit
    AFTER INSERT OR DELETE ON rapprochement_ventilations DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_ventilation_commit();
CREATE OR REPLACE FUNCTION hisabpro_no_truncate_ventilation()
RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
    RAISE EXCEPTION 'TRUNCATE rapprochement interdit : dérapprocher explicitement' USING ERRCODE='23514';
END $$;
DROP TRIGGER IF EXISTS trg_hisabpro_no_truncate_ventilation ON rapprochement_ventilations;
CREATE TRIGGER trg_hisabpro_no_truncate_ventilation BEFORE TRUNCATE ON rapprochement_ventilations
    FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_no_truncate_ventilation();
COMMIT;
