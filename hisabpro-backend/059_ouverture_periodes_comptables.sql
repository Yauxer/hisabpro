-- Patch 059 — Ouverture/reouverture des periodes sur exercice non cloture.
-- Executer APRES 038 et 058 en tant que proprietaire des fonctions/tables.
-- Ne modifie aucune ecriture, aucune periode existante, aucun audit historique.
-- Les periodes des exercices definitivement clotures restent inalterables.
BEGIN;

CREATE OR REPLACE FUNCTION hisabpro_proteger_statut_periode()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_societe_id INTEGER;
    v_annee INTEGER;
    v_statut VARCHAR(20);
BEGIN
    -- Une periode ouverte n'est pas autorisee dans un exercice cloture,
    -- meme si le statut de l'exercice a ete modifie en dehors du parcours API.
    IF NEW.statut = 'ouverte' THEN
        SELECT e.societe_id, e.annee, e.statut
          INTO v_societe_id, v_annee, v_statut
          FROM exercices_comptables e
         WHERE e.id = NEW.exercice_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Exercice % introuvable', NEW.exercice_id
                USING ERRCODE = '23503';
        END IF;
        IF v_statut = 'cloture' OR EXISTS (
            SELECT 1 FROM clotures_exercice ce
             WHERE ce.societe_id = v_societe_id
               AND ce.exercice = v_annee
        ) THEN
            RAISE EXCEPTION 'Exercice % definitivement cloture : reouverture de periode interdite', v_annee
                USING ERRCODE = '23514';
        END IF;
    END IF;

    -- La limite historique de deux periodes ouvertes et l'interdiction de
    -- rouvrir une periode fermee manuellement ne s'appliquent plus.
    -- Le trigger d'audit append-only existant reste actif.
    RETURN NEW;
END;
$$;

-- Le trigger trg_hisabpro_proteger_statut_periode cree par 038 reste en place
-- et utilise automatiquement la nouvelle definition de la fonction.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgrelid = 'periodes_comptables'::regclass
           AND tgname = 'trg_hisabpro_proteger_statut_periode'
           AND NOT tgisinternal
    ) THEN
        RAISE EXCEPTION 'Migration 038 manquante : trigger de protection des periodes absent';
    END IF;
END;
$$;

COMMIT;
