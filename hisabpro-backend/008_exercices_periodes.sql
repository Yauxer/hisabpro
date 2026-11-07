-- Patch 04B — Exercices & périodes comptables
-- PostgreSQL — à exécuter avec un compte pouvant modifier le schéma.

BEGIN;

CREATE TABLE IF NOT EXISTS exercices_comptables (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    annee INTEGER NOT NULL,
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'ouvert',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_exercice_societe_annee UNIQUE (societe_id, annee),
    CONSTRAINT ck_exercice_dates CHECK (date_fin >= date_debut),
    CONSTRAINT ck_exercice_duree_max CHECK ((date_fin - date_debut) <= 366),
    CONSTRAINT ck_exercice_meme_annee CHECK (
        EXTRACT(YEAR FROM date_debut)::int = annee
        AND EXTRACT(YEAR FROM date_fin)::int = annee
    ),
    CONSTRAINT ck_exercice_statut CHECK (statut IN ('a_venir','ouvert','cloture'))
);

CREATE INDEX IF NOT EXISTS ix_exercices_comptables_societe_annee
    ON exercices_comptables(societe_id, annee);

CREATE TABLE IF NOT EXISTS periodes_comptables (
    id SERIAL PRIMARY KEY,
    exercice_id INTEGER NOT NULL REFERENCES exercices_comptables(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    libelle VARCHAR(40) NOT NULL,
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'ouverte',
    date_fermeture TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_periode_exercice_numero UNIQUE (exercice_id, numero),
    CONSTRAINT ck_periode_dates CHECK (date_fin >= date_debut),
    CONSTRAINT ck_periode_statut CHECK (statut IN ('ouverte','fermee'))
);

CREATE INDEX IF NOT EXISTS ix_periodes_comptables_exercice
    ON periodes_comptables(exercice_id, numero);

-- Reconstituer les exercices qui existent déjà dans les données, puis préparer
-- l'exercice courant et le suivant. Aucune écriture historique n'est modifiée.
WITH annees AS (
    SELECT id AS societe_id, COALESCE(exercice_debut, EXTRACT(YEAR FROM CURRENT_DATE)::int) AS annee FROM societes
    UNION
    SELECT id, EXTRACT(YEAR FROM CURRENT_DATE)::int FROM societes
    UNION
    SELECT id, EXTRACT(YEAR FROM CURRENT_DATE)::int + 1 FROM societes
    UNION
    SELECT societe_id, exercice FROM ecritures WHERE exercice IS NOT NULL
    UNION
    SELECT societe_id, exercice FROM factures WHERE exercice IS NOT NULL
    UNION
    SELECT societe_id, exercice FROM clotures_exercice WHERE exercice IS NOT NULL
    UNION
    SELECT societe_id, exercice FROM ajustements_inventaire WHERE exercice IS NOT NULL
)
INSERT INTO exercices_comptables (societe_id, annee, date_debut, date_fin, statut)
SELECT
    a.societe_id,
    a.annee,
    make_date(a.annee, 1, 1),
    make_date(a.annee, 12, 31),
    CASE
        WHEN EXISTS (
            SELECT 1 FROM clotures_exercice c
            WHERE c.societe_id = a.societe_id AND c.exercice = a.annee
        ) THEN 'cloture'
        WHEN make_date(a.annee, 1, 1) > CURRENT_DATE THEN 'a_venir'
        ELSE 'ouvert'
    END
FROM annees a
WHERE a.annee BETWEEN 1900 AND 2200
ON CONFLICT (societe_id, annee) DO NOTHING;

-- Douze périodes mensuelles (ou moins pour les exercices raccourcis à venir).
INSERT INTO periodes_comptables (exercice_id, numero, libelle, date_debut, date_fin, statut)
SELECT
    e.id,
    ROW_NUMBER() OVER (PARTITION BY e.id ORDER BY gs)::int AS numero,
    CASE EXTRACT(MONTH FROM gs)::int
        WHEN 1 THEN 'Janvier' WHEN 2 THEN 'Février' WHEN 3 THEN 'Mars'
        WHEN 4 THEN 'Avril' WHEN 5 THEN 'Mai' WHEN 6 THEN 'Juin'
        WHEN 7 THEN 'Juillet' WHEN 8 THEN 'Août' WHEN 9 THEN 'Septembre'
        WHEN 10 THEN 'Octobre' WHEN 11 THEN 'Novembre' ELSE 'Décembre'
    END || ' ' || EXTRACT(YEAR FROM gs)::int,
    GREATEST(gs::date, e.date_debut),
    LEAST((date_trunc('month', gs) + interval '1 month - 1 day')::date, e.date_fin),
    'ouverte'
FROM exercices_comptables e
CROSS JOIN LATERAL generate_series(
    date_trunc('month', e.date_debut)::date,
    date_trunc('month', e.date_fin)::date,
    interval '1 month'
) gs
ON CONFLICT (exercice_id, numero) DO NOTHING;

-- Protection DB : même une route qui oublierait un contrôle applicatif ne peut
-- plus écrire dans un exercice/période fermé(e) ni hors des dates de l'exercice.
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

    -- Compatibilité historique : si aucune fiche n'existe encore, le backend la
    -- créera au prochain chargement. On ne bloque pas artificiellement l'historique.
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

    IF FOUND AND per.statut = 'fermee' THEN
        RAISE EXCEPTION 'Période % fermée : écriture interdite', per.libelle;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_hisabpro_verifier_periode_ecriture ON ecritures;
CREATE TRIGGER trg_hisabpro_verifier_periode_ecriture
BEFORE INSERT OR UPDATE OF date, exercice, societe_id ON ecritures
FOR EACH ROW EXECUTE FUNCTION hisabpro_verifier_periode_ecriture();

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE exercices_comptables TO hisabpro;
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE periodes_comptables TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO hisabpro;
    END IF;
END $$;

COMMIT;
