-- LETTRAGE FINAL — sécurisation métier, exercice clôturé et audit
-- À exécuter APRÈS 048_rapprochement_bancaire_final.sql.
BEGIN;

-- Un code est un groupe de lettrage. Au sein d'une société, toutes les lignes
-- d'un même code doivent appartenir au même exercice et au même auxiliaire.
-- Pour le compte collectif 3421/4411, le libellé de ligne joue le rôle de tiers ;
-- pour un sous-compte (3421xxxx / 4411xxxx), le sous-compte identifie le tiers.
CREATE OR REPLACE FUNCTION hisabpro_guard_lettrage_comptable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_societe_id INTEGER;
    v_validee BOOLEAN;
    v_numero VARCHAR(80);
    v_compte VARCHAR(20);
    v_libelle TEXT;
    v_exercice INTEGER;
    v_cle_tiers TEXT;
    v_autre RECORD;
BEGIN
    SELECT e.societe_id,
           e.est_validee,
           e.numero_ecriture,
           l.compte,
           l.libelle,
           e.exercice
      INTO v_societe_id, v_validee, v_numero, v_compte, v_libelle, v_exercice
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

    -- Après clôture, le code/date de lettrage font partie de l'archive comptable
    -- et ne sont plus modifiables, y compris par une requête SQL directe.
    IF EXISTS (
        SELECT 1
          FROM exercices_comptables ex
         WHERE ex.societe_id = NEW.societe_id
           AND ex.annee = v_exercice
           AND ex.statut = 'cloture'
    ) OR EXISTS (
        SELECT 1
          FROM clotures_exercice c
         WHERE c.societe_id = NEW.societe_id
           AND c.exercice = v_exercice
    ) THEN
        RAISE EXCEPTION 'Exercice % clôturé : le lettrage est en lecture seule', v_exercice USING ERRCODE='23514';
    END IF;

    IF TG_OP = 'INSERT' THEN
        IF COALESCE(NEW.actif, FALSE) = FALSE
           OR NEW.date_delettrage IS NOT NULL
           OR NEW.delettre_par IS NOT NULL THEN
            RAISE EXCEPTION 'Un nouveau lettrage doit être créé actif et non délettré' USING ERRCODE='23514';
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        -- L'identité et la trace de création sont immuables. Le seul changement
        -- permis est actif TRUE -> FALSE avec la trace de délettrage.
        IF NEW.societe_id IS DISTINCT FROM OLD.societe_id
           OR NEW.ligne_ecriture_id IS DISTINCT FROM OLD.ligne_ecriture_id
           OR NEW.code IS DISTINCT FROM OLD.code
           OR NEW.date_lettrage IS DISTINCT FROM OLD.date_lettrage
           OR NEW.created_by IS DISTINCT FROM OLD.created_by
           OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'Historique de lettrage immuable : identité/code/date de création non modifiables' USING ERRCODE='23514';
        END IF;
        IF COALESCE(OLD.actif, FALSE) = FALSE AND NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION 'Un lettrage délettré est historique et ne peut plus être modifié' USING ERRCODE='23514';
        END IF;
        IF COALESCE(OLD.actif, FALSE) = TRUE AND COALESCE(NEW.actif, FALSE) = TRUE AND NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION 'Utilisez le délettrage explicite au lieu de modifier un lettrage actif' USING ERRCODE='23514';
        END IF;
        IF COALESCE(OLD.actif, FALSE) = TRUE AND COALESCE(NEW.actif, FALSE) = FALSE THEN
            IF NEW.date_delettrage IS NULL THEN
                RAISE EXCEPTION 'La date de délettrage est obligatoire' USING ERRCODE='23514';
            END IF;
            IF NEW.date_delettrage < NEW.date_lettrage THEN
                RAISE EXCEPTION 'La date de délettrage ne peut pas précéder le lettrage' USING ERRCODE='23514';
            END IF;
            -- Un ancien groupe éventuellement créé avant 049 doit toujours
            -- pouvoir être délettré proprement, même si son libellé auxiliaire
            -- historique n'était pas assez précis pour les nouvelles règles.
            RETURN NEW;
        END IF;
    END IF;

    v_cle_tiers := CASE
        WHEN v_compte IN ('3421','4411')
            THEN 'tiers:' || lower(regexp_replace(btrim(COALESCE(v_libelle,'')), '[[:space:]]+', ' ', 'g'))
        ELSE 'compte:' || v_compte
    END;
    IF v_cle_tiers IN ('tiers:', '') THEN
        RAISE EXCEPTION 'Tiers non identifié sur le compte collectif %', v_compte USING ERRCODE='23514';
    END IF;

    -- Un code existant ne peut pas être réutilisé pour un autre exercice,
    -- compte ou tiers. On examine également les lignes historiques inactives.
    SELECT e.exercice AS exercice,
           l.compte AS compte,
           CASE
               WHEN l.compte IN ('3421','4411')
                   THEN 'tiers:' || lower(regexp_replace(btrim(COALESCE(l.libelle,'')), '[[:space:]]+', ' ', 'g'))
               ELSE 'compte:' || l.compte
           END AS cle_tiers
      INTO v_autre
      FROM lettrages_comptables lc
      JOIN lignes_ecriture l ON l.id = lc.ligne_ecriture_id
      JOIN ecritures e ON e.id = l.ecriture_id
     WHERE lc.societe_id = NEW.societe_id
       AND lc.code = NEW.code
       AND lc.id <> COALESCE(NEW.id, -1)
     ORDER BY lc.id
     LIMIT 1;

    IF FOUND AND (
        v_autre.exercice <> v_exercice
        OR v_autre.compte <> v_compte
        OR v_autre.cle_tiers <> v_cle_tiers
    ) THEN
        RAISE EXCEPTION 'Le code % appartient déjà à un autre compte/tiers/exercice', NEW.code USING ERRCODE='23514';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_guard_lettrage_comptable ON lettrages_comptables;
CREATE TRIGGER trg_hisabpro_guard_lettrage_comptable
BEFORE INSERT OR UPDATE ON lettrages_comptables
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_lettrage_comptable();

-- Contrôle différé du groupe complet : un code actif ne peut être validé qu'avec
-- au moins deux lignes et un total débit = crédit au centime. Le contrôle est
-- différé à COMMIT pour permettre l'insertion des lignes du groupe une à une.
CREATE OR REPLACE FUNCTION hisabpro_check_lettrage_equilibre()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_sid INTEGER;
    v_code VARCHAR(10);
    v_nb INTEGER;
    v_debit NUMERIC(24,2);
    v_credit NUMERIC(24,2);
BEGIN
    v_sid := NEW.societe_id;
    v_code := NEW.code;

    SELECT COUNT(*),
           COALESCE(SUM(l.debit), 0)::NUMERIC(24,2),
           COALESCE(SUM(l.credit), 0)::NUMERIC(24,2)
      INTO v_nb, v_debit, v_credit
      FROM lettrages_comptables lc
      JOIN lignes_ecriture l ON l.id = lc.ligne_ecriture_id
     WHERE lc.societe_id = v_sid
       AND lc.code = v_code
       AND lc.actif = TRUE;

    -- 0 ligne active = groupe entièrement délettré : état valide.
    IF v_nb = 0 THEN
        RETURN NEW;
    END IF;
    IF v_nb < 2 THEN
        RAISE EXCEPTION 'Le code % doit contenir au moins deux lignes actives', v_code USING ERRCODE='23514';
    END IF;
    IF v_debit <> v_credit THEN
        RAISE EXCEPTION 'Lettrage % déséquilibré : débit % / crédit %', v_code, v_debit, v_credit USING ERRCODE='23514';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_check_lettrage_equilibre ON lettrages_comptables;
CREATE CONSTRAINT TRIGGER trg_hisabpro_check_lettrage_equilibre
AFTER INSERT OR UPDATE ON lettrages_comptables
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION hisabpro_check_lettrage_equilibre();

-- Le backend ne supprime jamais une trace de lettrage : il la désactive. On
-- retire donc le DELETE au rôle applicatif tout en laissant les cascades FK
-- fonctionner lors d'une suppression administrative de société.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        REVOKE DELETE ON lettrages_comptables FROM hisabpro;
        GRANT SELECT, INSERT, UPDATE ON lettrages_comptables TO hisabpro;
        GRANT EXECUTE ON FUNCTION hisabpro_guard_lettrage_comptable() TO hisabpro;
        GRANT EXECUTE ON FUNCTION hisabpro_check_lettrage_equilibre() TO hisabpro;
    END IF;
END $$;

COMMIT;
