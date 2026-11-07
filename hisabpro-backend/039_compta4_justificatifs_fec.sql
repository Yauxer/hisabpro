-- COMPTA.4 — Justificatifs non bloquants + consolidation FEC Avis n°24
-- À exécuter APRÈS 038_compta3_avis24_durcissement.sql avec un rôle propriétaire.
-- Objectifs :
--   * ne jamais imposer une saisie manuelle de date de pièce à la validation ;
--   * permettre de rattacher une référence/document APRÈS validation sans modifier
--     l'écriture comptable définitive ;
--   * garantir qu'une Date_Piece existe toujours pour les nouvelles écritures ;
--   * conserver un historique append-only des références complémentaires.

BEGIN;

CREATE TABLE IF NOT EXISTS ecriture_justificatifs (
    id          SERIAL PRIMARY KEY,
    societe_id  INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    ecriture_id INTEGER NOT NULL REFERENCES ecritures(id) ON DELETE CASCADE,
    reference   VARCHAR(100) NOT NULL,
    date_piece  DATE NOT NULL,
    source_type VARCHAR(30) NOT NULL DEFAULT 'manuel',
    source_id   INTEGER,
    fichier_nom VARCHAR(255),
    prioritaire BOOLEAN NOT NULL DEFAULT FALSE,
    motif       VARCHAR(500),
    created_by  INTEGER REFERENCES utilisateurs(id),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_ecriture_justificatif_reference_non_vide
        CHECK (length(trim(reference)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_ecriture_justificatifs_societe
    ON ecriture_justificatifs (societe_id);
CREATE INDEX IF NOT EXISTS ix_ecriture_justificatifs_ecriture
    ON ecriture_justificatifs (ecriture_id, id);
CREATE INDEX IF NOT EXISTS ix_ecriture_justificatifs_reference
    ON ecriture_justificatifs (societe_id, reference);

-- Les anciennes écritures définitives ne sont volontairement PAS réécrites :
-- COMPTA.3 les a rendues intangibles. Pour elles, le moteur FEC utilise déjà
-- la date comptable comme Date_Piece de repli. Les nouvelles écritures sont
-- complétées automatiquement par le trigger ci-dessous.

CREATE OR REPLACE FUNCTION hisabpro_completer_date_piece()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.date_piece IS NULL THEN
        NEW.date_piece := NEW.date;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_ecritures_completer_date_piece ON ecritures;
CREATE TRIGGER trg_ecritures_completer_date_piece
BEFORE INSERT OR UPDATE OF date, date_piece ON ecritures
FOR EACH ROW
EXECUTE FUNCTION hisabpro_completer_date_piece();

-- Les compléments de justification sont append-only : une correction ultérieure
-- ajoute une nouvelle référence prioritaire, sans réécrire ni supprimer l'historique.
CREATE OR REPLACE FUNCTION hisabpro_verrouiller_justificatif_ecriture()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_est_validee BOOLEAN;
BEGIN
    SELECT est_validee INTO v_est_validee
      FROM ecritures
     WHERE id = OLD.ecriture_id;

    IF COALESCE(v_est_validee, FALSE) THEN
        RAISE EXCEPTION 'Les références d''une écriture définitive sont append-only : ajoutez une nouvelle référence au lieu de modifier/supprimer l''historique.';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_ecriture_justificatifs_append_only ON ecriture_justificatifs;
CREATE TRIGGER trg_ecriture_justificatifs_append_only
BEFORE UPDATE OR DELETE ON ecriture_justificatifs
FOR EACH ROW
EXECUTE FUNCTION hisabpro_verrouiller_justificatif_ecriture();

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, DELETE ON TABLE ecriture_justificatifs TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE ecriture_justificatifs_id_seq TO hisabpro;
    END IF;
END $$;

COMMIT;
