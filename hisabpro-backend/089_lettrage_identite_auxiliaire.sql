-- Après049/053 :aligner la clé de tiers du déclencheur avec les sources natives.
-- Aucun groupe historique, écriture, auxiliaire ou montant modifié.
-- Priorité tiers_id,puis auxiliaire figé ;libellé conservé comme repli historique.
-- Tous les autres contrôles049 et le contrôle différé d'équilibre sont conservés.
BEGIN;
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
    v_tiers_id INTEGER;
    v_auxiliaire TEXT;
    v_exercice INTEGER;
    v_cle_tiers TEXT;
    v_autre RECORD;
BEGIN
    SELECT e.societe_id,
           e.est_validee,
           e.numero_ecriture,
           l.compte,
           l.libelle,
           l.tiers_id,
           l.compte_auxiliaire_snapshot,
           e.exercice
      INTO v_societe_id, v_validee, v_numero, v_compte, v_libelle, v_tiers_id, v_auxiliaire, v_exercice
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
        WHEN v_compte IN ('3421','4411') AND COALESCE(v_tiers_id,0) <> 0
            THEN 'tiers_id:' || v_tiers_id::text
        WHEN v_compte IN ('3421','4411') AND btrim(COALESCE(v_auxiliaire,'')) <> ''
            THEN 'aux:' || lower(regexp_replace(btrim(v_auxiliaire), '[[:space:]]+', ' ', 'g'))
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
               WHEN l.compte IN ('3421','4411') AND COALESCE(l.tiers_id,0) <> 0
                   THEN 'tiers_id:' || l.tiers_id::text
               WHEN l.compte IN ('3421','4411') AND btrim(COALESCE(l.compte_auxiliaire_snapshot,'')) <> ''
                   THEN 'aux:' || lower(regexp_replace(btrim(l.compte_auxiliaire_snapshot), '[[:space:]]+', ' ', 'g'))
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

COMMIT;
