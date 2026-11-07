-- Structure seule : aucune recherche de tiers ni reparation de donnees.
-- Independante des traitements historiques contenus dans 068.
BEGIN;

CREATE TABLE IF NOT EXISTS public.ligne_auxiliaire_complements (
    id SERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES public.societes(id) ON DELETE CASCADE,
    ligne_ecriture_id INTEGER NOT NULL REFERENCES public.lignes_ecriture(id) ON DELETE RESTRICT,
    tiers_id INTEGER NOT NULL REFERENCES public.tiers(id) ON DELETE RESTRICT,
    nature_auxiliaire VARCHAR(20) NOT NULL,
    compte_auxiliaire_snapshot VARCHAR(20) NOT NULL,
    libelle_auxiliaire_snapshot VARCHAR(200) NOT NULL,
    source_type VARCHAR(30) NOT NULL DEFAULT 'reparation_historique',
    source_id INTEGER NULL,
    motif VARCHAR(500) NULL,
    created_by INTEGER NULL REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_ligne_aux_complements_ligne
    ON public.ligne_auxiliaire_complements(ligne_ecriture_id, id);
CREATE INDEX IF NOT EXISTS ix_ligne_aux_complements_societe
    ON public.ligne_auxiliaire_complements(societe_id);

-- NOT VALID conserve les historiques non conformes sans les modifier.
-- Les insertions futures sont controlees meme si l'historique reste a revoir.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE
        conrelid = 'public.ligne_auxiliaire_complements'::regclass
        AND conname = 'ck_ligne_aux_complement_nature') THEN
        ALTER TABLE public.ligne_auxiliaire_complements ADD CONSTRAINT
            ck_ligne_aux_complement_nature CHECK (nature_auxiliaire IN ('client', 'fournisseur')) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE
        conrelid = 'public.ligne_auxiliaire_complements'::regclass
        AND conname = 'ck_ligne_aux_complement_compte_non_vide') THEN
        ALTER TABLE public.ligne_auxiliaire_complements ADD CONSTRAINT
            ck_ligne_aux_complement_compte_non_vide CHECK (length(trim(compte_auxiliaire_snapshot)) > 0) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE
        conrelid = 'public.ligne_auxiliaire_complements'::regclass
        AND conname = 'ck_ligne_aux_complement_libelle_non_vide') THEN
        ALTER TABLE public.ligne_auxiliaire_complements ADD CONSTRAINT
            ck_ligne_aux_complement_libelle_non_vide CHECK (length(trim(libelle_auxiliaire_snapshot)) > 0) NOT VALID;
    END IF;
END $$;

CREATE OR REPLACE FUNCTION public.hisabpro_guard_ligne_aux_complement_append_only()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les complements auxiliaires historiques sont append-only : % interdit.', TG_OP
        USING ERRCODE = '23514';
END;
$$;
DROP TRIGGER IF EXISTS trg_ligne_aux_complements_append_only ON public.ligne_auxiliaire_complements;
CREATE TRIGGER trg_ligne_aux_complements_append_only
    BEFORE UPDATE OR DELETE ON public.ligne_auxiliaire_complements
    FOR EACH ROW EXECUTE FUNCTION public.hisabpro_guard_ligne_aux_complement_append_only();
DROP TRIGGER IF EXISTS trg_ligne_aux_complements_no_truncate ON public.ligne_auxiliaire_complements;
CREATE TRIGGER trg_ligne_aux_complements_no_truncate
    BEFORE TRUNCATE ON public.ligne_auxiliaire_complements
    FOR EACH STATEMENT EXECUTE FUNCTION public.hisabpro_guard_ligne_aux_complement_append_only();

REVOKE UPDATE, DELETE, TRUNCATE ON TABLE public.ligne_auxiliaire_complements FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        REVOKE UPDATE, DELETE, TRUNCATE ON TABLE public.ligne_auxiliaire_complements FROM hisabpro;
        GRANT SELECT, INSERT ON TABLE public.ligne_auxiliaire_complements TO hisabpro;
        GRANT USAGE, SELECT ON SEQUENCE public.ligne_auxiliaire_complements_id_seq TO hisabpro;
    END IF;
END $$;
COMMIT;
