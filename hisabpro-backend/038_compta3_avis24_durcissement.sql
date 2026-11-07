-- COMPTA.3 — Durcissement Avis n°24 / Loi 9-88
-- À exécuter APRÈS 037_compta2_modeles_ecritures.sql avec un rôle propriétaire.
--
-- Objectifs :
--   1) rendre irréversibles les écritures ayant reçu un numéro définitif ;
--   2) interdire toute altération de leurs lignes ;
--   3) remplacer la dévalidation par une contrepassation traçable ;
--   4) limiter à deux les périodes comptables ouvertes simultanément ;
--   5) rendre la fermeture d'une période et la clôture d'un exercice définitives ;
--   6) conserver une piste d'audit append-only des changements de statut de période.

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Chaîne de correction : une écriture définitive est corrigée par une nouvelle
--    écriture compensatoire, jamais en réécrivant l'original.
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE ecritures
    ADD COLUMN IF NOT EXISTS contrepassation_de_id INTEGER NULL,
    ADD COLUMN IF NOT EXISTS motif_correction VARCHAR(500) NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_ecritures_contrepassation_de'
    ) THEN
        ALTER TABLE ecritures
            ADD CONSTRAINT fk_ecritures_contrepassation_de
            FOREIGN KEY (contrepassation_de_id)
            REFERENCES ecritures(id)
            ON DELETE RESTRICT;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_ecritures_contrepassation_de
    ON ecritures (contrepassation_de_id)
    WHERE contrepassation_de_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_ecritures_contrepassation_de
    ON ecritures (contrepassation_de_id);

-- Toute écriture qui possède déjà un numéro comptable est intangible.
-- Le passage brouillon -> validée reste autorisé car OLD.numero_ecriture est NULL.
CREATE OR REPLACE FUNCTION hisabpro_proteger_ecriture_definitive()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.numero_ecriture IS NOT NULL AND NEW IS DISTINCT FROM OLD THEN
        RAISE EXCEPTION
            'Écriture définitive % (%) : modification interdite. Utilisez une contrepassation.',
            OLD.id, OLD.numero_ecriture
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_proteger_ecriture_definitive ON ecritures;
CREATE TRIGGER trg_hisabpro_proteger_ecriture_definitive
BEFORE UPDATE ON ecritures
FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_ecriture_definitive();

-- Les lignes d'une écriture numérotée ne peuvent plus être ajoutées, modifiées
-- ou supprimées. Les brouillons restent librement éditables.
CREATE OR REPLACE FUNCTION hisabpro_proteger_lignes_ecriture_definitive()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_ecriture_id INTEGER;
    v_numero VARCHAR(40);
BEGIN
    v_ecriture_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.ecriture_id ELSE NEW.ecriture_id END;

    SELECT numero_ecriture
      INTO v_numero
      FROM ecritures
     WHERE id = v_ecriture_id;

    IF v_numero IS NOT NULL THEN
        RAISE EXCEPTION
            'Lignes de l''écriture définitive % : % interdit. Utilisez une contrepassation.',
            v_numero, TG_OP
            USING ERRCODE = '23514';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_proteger_lignes_definitives ON lignes_ecriture;
CREATE TRIGGER trg_hisabpro_proteger_lignes_definitives
BEFORE INSERT OR UPDATE OR DELETE ON lignes_ecriture
FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_lignes_ecriture_definitive();

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Périodes : distinction future / ouverte / fermée et maximum 2 ouvertes.
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE periodes_comptables DROP CONSTRAINT IF EXISTS ck_periode_statut;
ALTER TABLE periodes_comptables
    ADD CONSTRAINT ck_periode_statut
    CHECK (statut IN ('a_venir','ouverte','fermee'));

-- Refus de normaliser silencieusement si plus de deux périodes contiennent des
-- brouillons. L'utilisateur doit d'abord traiter ces brouillons.
DO $$
DECLARE
    v_bad RECORD;
BEGIN
    SELECT e.id AS exercice_id, e.annee, COUNT(DISTINCT p.id) AS nb
      INTO v_bad
      FROM exercices_comptables e
      JOIN periodes_comptables p ON p.exercice_id = e.id
      JOIN ecritures ec
        ON ec.societe_id = e.societe_id
       AND ec.exercice = e.annee
       AND ec.date BETWEEN p.date_debut AND p.date_fin
       AND COALESCE(ec.est_validee, FALSE) = FALSE
     WHERE e.statut <> 'cloture'
     GROUP BY e.id, e.annee
    HAVING COUNT(DISTINCT p.id) > 2
     ORDER BY e.annee
     LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'COMPTA.3 bloqué : l''exercice % contient des brouillons dans % périodes. Traitez-les avant d''appliquer la limite Avis 24 de deux périodes ouvertes.',
            v_bad.annee, v_bad.nb
            USING ERRCODE = '23514';
    END IF;
END $$;

CREATE TEMP TABLE hp_038_periodes_a_garder_ouvertes (
    exercice_id INTEGER NOT NULL,
    periode_id INTEGER NOT NULL,
    PRIMARY KEY (exercice_id, periode_id)
) ON COMMIT DROP;

-- Priorité 1 : conserver ouvertes les périodes contenant encore des brouillons.
INSERT INTO hp_038_periodes_a_garder_ouvertes (exercice_id, periode_id)
SELECT DISTINCT e.id, p.id
  FROM exercices_comptables e
  JOIN periodes_comptables p ON p.exercice_id = e.id
  JOIN ecritures ec
    ON ec.societe_id = e.societe_id
   AND ec.exercice = e.annee
   AND ec.date BETWEEN p.date_debut AND p.date_fin
   AND COALESCE(ec.est_validee, FALSE) = FALSE
 WHERE e.statut <> 'cloture'
   AND p.statut <> 'fermee';

-- Priorité 2 : période courante (ou première/dernière période si l'exercice est
-- préparé en avance / resté ouvert après sa date de fin), s'il reste une place.
INSERT INTO hp_038_periodes_a_garder_ouvertes (exercice_id, periode_id)
SELECT e.id, p.id
  FROM exercices_comptables e
  CROSS JOIN LATERAL (
      SELECT p2.id
        FROM periodes_comptables p2
       WHERE p2.exercice_id = e.id
         AND p2.statut <> 'fermee'
       ORDER BY
         CASE
           WHEN CURRENT_DATE BETWEEN p2.date_debut AND p2.date_fin THEN 0
           WHEN CURRENT_DATE < e.date_debut THEN p2.numero
           WHEN CURRENT_DATE > e.date_fin THEN (1000 - p2.numero)
           ELSE 500
         END,
         p2.numero
       LIMIT 1
  ) p
 WHERE e.statut = 'ouvert'
   AND (SELECT COUNT(*) FROM hp_038_periodes_a_garder_ouvertes k WHERE k.exercice_id = e.id) < 2
ON CONFLICT DO NOTHING;

-- Priorité 3 : période immédiatement précédente à la plus récente période
-- retenue, si elle n'était pas déjà fermée et qu'une seconde place reste libre.
INSERT INTO hp_038_periodes_a_garder_ouvertes (exercice_id, periode_id)
SELECT e.id, p.id
  FROM exercices_comptables e
  CROSS JOIN LATERAL (
      SELECT p2.id
        FROM periodes_comptables p2
       WHERE p2.exercice_id = e.id
         AND p2.statut <> 'fermee'
         AND p2.numero < COALESCE((
             SELECT MAX(px.numero)
               FROM periodes_comptables px
               JOIN hp_038_periodes_a_garder_ouvertes kx ON kx.periode_id = px.id
              WHERE kx.exercice_id = e.id
         ), 9999)
       ORDER BY p2.numero DESC
       LIMIT 1
  ) p
 WHERE e.statut = 'ouvert'
   AND (SELECT COUNT(*) FROM hp_038_periodes_a_garder_ouvertes k WHERE k.exercice_id = e.id) < 2
ON CONFLICT DO NOTHING;

-- Une clôture existante ferme définitivement toutes ses périodes.
UPDATE periodes_comptables p
   SET statut = 'fermee',
       date_fermeture = COALESCE(p.date_fermeture, NOW())
  FROM exercices_comptables e
 WHERE p.exercice_id = e.id
   AND e.statut = 'cloture';

-- Normalisation des exercices non clôturés. Les anciennes périodes non retenues
-- deviennent fermées ; les périodes postérieures à la dernière période de travail
-- deviennent "à venir".
WITH bornes AS (
    SELECT e.id AS exercice_id,
           COALESCE(MAX(p.numero) FILTER (
               WHERE EXISTS (
                   SELECT 1 FROM hp_038_periodes_a_garder_ouvertes k
                    WHERE k.exercice_id = e.id AND k.periode_id = p.id
               )
           ), 0) AS max_ouverte
      FROM exercices_comptables e
      JOIN periodes_comptables p ON p.exercice_id = e.id
     WHERE e.statut <> 'cloture'
     GROUP BY e.id
)
UPDATE periodes_comptables p
   SET statut = CASE
       WHEN EXISTS (
           SELECT 1 FROM hp_038_periodes_a_garder_ouvertes k
            WHERE k.exercice_id = p.exercice_id AND k.periode_id = p.id
       ) THEN 'ouverte'
       WHEN p.numero > b.max_ouverte THEN 'a_venir'
       ELSE 'fermee'
   END,
   date_fermeture = CASE
       WHEN EXISTS (
           SELECT 1 FROM hp_038_periodes_a_garder_ouvertes k
            WHERE k.exercice_id = p.exercice_id AND k.periode_id = p.id
       ) THEN NULL
       WHEN p.numero > b.max_ouverte THEN NULL
       ELSE COALESCE(p.date_fermeture, NOW())
   END
  FROM bornes b
 WHERE p.exercice_id = b.exercice_id;

-- Garde-fou DB : une période fermée ne se rouvre jamais et au plus deux périodes
-- peuvent être ouvertes pour un exercice.
CREATE OR REPLACE FUNCTION hisabpro_proteger_statut_periode()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_nb INTEGER;
BEGIN
    IF TG_OP = 'UPDATE'
       AND OLD.statut = 'fermee'
       AND NEW.statut IS DISTINCT FROM OLD.statut THEN
        RAISE EXCEPTION
            'Période % fermée : réouverture interdite. Les corrections doivent être comptabilisées sur une période ouverte.',
            OLD.libelle
            USING ERRCODE = '23514';
    END IF;

    IF NEW.statut = 'ouverte' THEN
        IF TG_OP = 'INSERT' THEN
            SELECT COUNT(*)
              INTO v_nb
              FROM periodes_comptables p
             WHERE p.exercice_id = NEW.exercice_id
               AND p.statut = 'ouverte';
        ELSIF OLD.statut IS DISTINCT FROM 'ouverte'
           OR OLD.exercice_id IS DISTINCT FROM NEW.exercice_id THEN
            SELECT COUNT(*)
              INTO v_nb
              FROM periodes_comptables p
             WHERE p.exercice_id = NEW.exercice_id
               AND p.statut = 'ouverte'
               AND p.id <> NEW.id;
        ELSE
            RETURN NEW;
        END IF;

        IF v_nb >= 2 THEN
            RAISE EXCEPTION
                'Avis 24 : au plus deux périodes peuvent être ouvertes simultanément pour un exercice.'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_proteger_statut_periode ON periodes_comptables;
CREATE TRIGGER trg_hisabpro_proteger_statut_periode
BEFORE INSERT OR UPDATE OF statut, exercice_id ON periodes_comptables
FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_statut_periode();

-- Le contrôle bas niveau des écritures n'accepte désormais que les périodes
-- explicitement ouvertes ("à venir" est donc bloqué comme "fermée").
CREATE OR REPLACE FUNCTION hisabpro_verifier_periode_ecriture()
RETURNS TRIGGER AS $$
DECLARE
    ex RECORD;
    per RECORD;
BEGIN
    SELECT * INTO ex
      FROM exercices_comptables
     WHERE societe_id = NEW.societe_id AND annee = NEW.exercice
     LIMIT 1;

    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    IF NEW.date < ex.date_debut OR NEW.date > ex.date_fin THEN
        RAISE EXCEPTION 'Date % hors de l''exercice % (% - %)', NEW.date, ex.annee, ex.date_debut, ex.date_fin;
    END IF;

    IF ex.statut = 'cloture' THEN
        RAISE EXCEPTION 'Exercice % clôturé : écriture interdite', ex.annee;
    END IF;

    SELECT * INTO per
      FROM periodes_comptables
     WHERE exercice_id = ex.id
       AND NEW.date BETWEEN date_debut AND date_fin
     LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Aucune période comptable ne couvre la date % de l''exercice %', NEW.date, ex.annee;
    END IF;

    IF per.statut <> 'ouverte' THEN
        RAISE EXCEPTION 'Période % non ouverte (%) : écriture interdite', per.libelle, per.statut;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Traçabilité append-only des changements de période.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_periodes_comptables (
    id BIGSERIAL PRIMARY KEY,
    exercice_id INTEGER NOT NULL,
    periode_id INTEGER NOT NULL,
    numero INTEGER NOT NULL,
    ancien_statut VARCHAR(20),
    nouveau_statut VARCHAR(20),
    acteur_id INTEGER NULL,
    motif VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_audit_periodes_exercice
    ON audit_periodes_comptables (exercice_id, created_at DESC);

CREATE OR REPLACE FUNCTION hisabpro_auditer_periode()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_acteur_txt TEXT;
    v_acteur_id INTEGER;
    v_motif TEXT;
BEGIN
    IF OLD.statut IS NOT DISTINCT FROM NEW.statut THEN
        RETURN NEW;
    END IF;

    v_acteur_txt := NULLIF(current_setting('hisabpro.audit_actor_id', true), '');
    IF v_acteur_txt ~ '^[0-9]+$' THEN
        v_acteur_id := v_acteur_txt::INTEGER;
    END IF;
    v_motif := NULLIF(current_setting('hisabpro.audit_motif', true), '');

    INSERT INTO audit_periodes_comptables (
        exercice_id, periode_id, numero, ancien_statut, nouveau_statut,
        acteur_id, motif
    ) VALUES (
        NEW.exercice_id, NEW.id, NEW.numero, OLD.statut, NEW.statut,
        v_acteur_id, v_motif
    );

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_audit_periode ON periodes_comptables;
CREATE TRIGGER trg_hisabpro_audit_periode
AFTER UPDATE OF statut ON periodes_comptables
FOR EACH ROW EXECUTE FUNCTION hisabpro_auditer_periode();

CREATE OR REPLACE FUNCTION hisabpro_audit_periodes_append_only()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'audit_periodes_comptables est append-only : UPDATE/DELETE interdit';
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_audit_periodes_append_only ON audit_periodes_comptables;
CREATE TRIGGER trg_hisabpro_audit_periodes_append_only
BEFORE UPDATE OR DELETE ON audit_periodes_comptables
FOR EACH ROW EXECUTE FUNCTION hisabpro_audit_periodes_append_only();

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Clôture définitive : impossible de faire repasser un exercice clôturé en
--    "ouvert" ou de supprimer la trace de clôture.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION hisabpro_proteger_exercice_cloture()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' AND OLD.statut = 'cloture' THEN
        RAISE EXCEPTION 'Exercice % clôturé : suppression interdite.', OLD.annee
            USING ERRCODE = '23514';
    END IF;

    IF TG_OP = 'UPDATE' AND OLD.statut = 'cloture' AND NEW IS DISTINCT FROM OLD THEN
        RAISE EXCEPTION 'Exercice % clôturé : modification/réouverture interdite.', OLD.annee
            USING ERRCODE = '23514';
    END IF;

    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_proteger_exercice_cloture ON exercices_comptables;
CREATE TRIGGER trg_hisabpro_proteger_exercice_cloture
BEFORE UPDATE OR DELETE ON exercices_comptables
FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_exercice_cloture();

CREATE OR REPLACE FUNCTION hisabpro_proteger_trace_cloture()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Une clôture comptable enregistrée est définitive : UPDATE/DELETE interdit.'
        USING ERRCODE = '23514';
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_proteger_trace_cloture ON clotures_exercice;
CREATE TRIGGER trg_hisabpro_proteger_trace_cloture
BEFORE UPDATE OR DELETE ON clotures_exercice
FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_trace_cloture();

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT ON TABLE audit_periodes_comptables TO hisabpro;
        REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON audit_periodes_comptables FROM hisabpro;
        GRANT USAGE, SELECT ON SEQUENCE audit_periodes_comptables_id_seq TO hisabpro;
    END IF;
END $$;

COMMIT;
