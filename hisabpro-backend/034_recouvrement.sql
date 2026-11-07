-- FACT.7 — Échéances, impayés, balance âgée et recouvrement
BEGIN;

CREATE TABLE IF NOT EXISTS relances_recouvrement (
    id BIGSERIAL PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    facture_id INTEGER NOT NULL REFERENCES factures(id) ON DELETE RESTRICT,
    niveau SMALLINT NOT NULL DEFAULT 1,
    date_relance DATE NOT NULL DEFAULT CURRENT_DATE,
    canal VARCHAR(20) NOT NULL DEFAULT 'email',
    commentaire TEXT,
    date_promesse_reglement DATE,
    montant_promis NUMERIC(18,2),
    prochaine_relance DATE,
    statut VARCHAR(20) NOT NULL DEFAULT 'effectuee',
    created_by INTEGER REFERENCES utilisateurs(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_relance_niveau CHECK (niveau BETWEEN 1 AND 3),
    CONSTRAINT ck_relance_canal CHECK (canal IN ('email','telephone','courrier','whatsapp','autre')),
    CONSTRAINT ck_relance_montant_promis CHECK (montant_promis IS NULL OR montant_promis > 0),
    CONSTRAINT ck_relance_statut CHECK (statut IN ('effectuee','annulee')),
    CONSTRAINT ck_relance_promesse_date CHECK (date_promesse_reglement IS NULL OR date_promesse_reglement >= date_relance),
    CONSTRAINT ck_relance_prochaine_date CHECK (prochaine_relance IS NULL OR prochaine_relance > date_relance)
);

CREATE INDEX IF NOT EXISTS ix_relances_recouvrement_societe_facture
    ON relances_recouvrement(societe_id, facture_id, date_relance DESC);
CREATE INDEX IF NOT EXISTS ix_relances_recouvrement_prochaine
    ON relances_recouvrement(societe_id, prochaine_relance)
    WHERE statut = 'effectuee' AND prochaine_relance IS NOT NULL;

-- Les requêtes de balance âgée filtrent constamment ces colonnes.
CREATE INDEX IF NOT EXISTS ix_factures_recouvrement
    ON factures(societe_id, exercice, type, est_validee, est_proforma, date_echeance);
CREATE INDEX IF NOT EXISTS ix_reglements_facture_statut
    ON reglements(societe_id, facture_id, statut);
CREATE INDEX IF NOT EXISTS ix_acomptes_facture_statut
    ON acomptes(societe_id, facture_id, statut);
CREATE INDEX IF NOT EXISTS ix_avoirs_facture_statut
    ON avoirs(societe_id, facture_id, statut);

COMMIT;
