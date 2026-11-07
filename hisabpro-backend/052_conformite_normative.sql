-- HISABPRO 052 — conformité normative affectation du résultat
-- Décision sociale traçable + immutable. À exécuter une seule fois dans pgAdmin.

BEGIN;

CREATE TABLE IF NOT EXISTS decisions_affectation_resultat (
    id                          SERIAL PRIMARY KEY,
    societe_id                  INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    exercice_origine            INTEGER NOT NULL,
    exercice_comptabilisation   INTEGER NOT NULL,
    date_decision               DATE NOT NULL,
    date_comptabilisation       DATE NOT NULL,
    reference_decision          VARCHAR(120) NOT NULL,
    organe_decision             VARCHAR(120) NOT NULL,
    forme_juridique_snapshot    VARCHAR(50),
    capital_social_snapshot     NUMERIC(18,2) NOT NULL DEFAULT 0,
    resultat_origine            NUMERIC(18,2) NOT NULL,
    pertes_anterieures_imputees NUMERIC(18,2) NOT NULL DEFAULT 0,
    reserve_legale_avant        NUMERIC(18,2) NOT NULL DEFAULT 0,
    reserve_legale_minimale     NUMERIC(18,2) NOT NULL DEFAULT 0,
    reserve_legale_affectee     NUMERIC(18,2) NOT NULL DEFAULT 0,
    autres_reserves             NUMERIC(18,2) NOT NULL DEFAULT 0,
    report_a_nouveau            NUMERIC(18,2) NOT NULL DEFAULT 0,
    dividendes                  NUMERIC(18,2) NOT NULL DEFAULT 0,
    compte_source               VARCHAR(10) NOT NULL,
    ecriture_id                 INTEGER NOT NULL REFERENCES ecritures(id) ON DELETE RESTRICT,
    created_by                  INTEGER REFERENCES utilisateurs(id) ON DELETE SET NULL,
    created_at                  TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT uq_decision_affectation_societe_exercice UNIQUE (societe_id, exercice_origine),
    CONSTRAINT uq_decision_affectation_ecriture UNIQUE (ecriture_id),
    CONSTRAINT ck_decision_affectation_reference_non_vide CHECK (length(trim(reference_decision)) > 0),
    CONSTRAINT ck_decision_affectation_organe_non_vide CHECK (length(trim(organe_decision)) > 0),
    CONSTRAINT ck_decision_affectation_compte_source CHECK (compte_source IN ('1181','1189','1191','1199')),
    CONSTRAINT ck_decision_affectation_capital_non_negatif CHECK (capital_social_snapshot >= 0),
    CONSTRAINT ck_decision_affectation_pertes_non_negatif CHECK (pertes_anterieures_imputees >= 0),
    CONSTRAINT ck_decision_affectation_reserve_non_negative CHECK (
        reserve_legale_avant >= 0 AND reserve_legale_minimale >= 0 AND reserve_legale_affectee >= 0
    ),
    CONSTRAINT ck_decision_affectation_ventilation_non_negative CHECK (
        autres_reserves >= 0 AND report_a_nouveau >= 0 AND dividendes >= 0
    )
);

CREATE INDEX IF NOT EXISTS ix_decision_affectation_societe_origine
    ON decisions_affectation_resultat (societe_id, exercice_origine);
CREATE INDEX IF NOT EXISTS ix_decision_affectation_societe_compta
    ON decisions_affectation_resultat (societe_id, exercice_comptabilisation);

-- La preuve de décision ne doit jamais être réécrite ni supprimée.
CREATE OR REPLACE FUNCTION hisabpro_guard_decision_affectation_immutable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Décision d''affectation définitive : modification/suppression interdite'
        USING ERRCODE = 'P0001';
END;
$$;

DROP TRIGGER IF EXISTS trg_decision_affectation_immutable ON decisions_affectation_resultat;
CREATE TRIGGER trg_decision_affectation_immutable
BEFORE UPDATE OR DELETE ON decisions_affectation_resultat
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_decision_affectation_immutable();

COMMIT;
