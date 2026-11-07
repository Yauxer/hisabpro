-- FACT-G — Finalisation Acomptes & Avoirs
-- - cycle d'encaissement des acomptes par chèque/effet
-- - compte bancaire identifié sans ambiguïté
-- - annulation traçable des imputations d'acomptes
-- - vrais RRR / corrections de prix sur avoirs
-- - utilisation/remboursement du crédit disponible d'un avoir
-- Migration idempotente et rejouable après 044_factF_delais_paiement.sql.
BEGIN;

-- ── 1. Acomptes : paiement et compte bancaire ──────────────────────────────
ALTER TABLE acomptes
    ADD COLUMN IF NOT EXISTS compte_bancaire_id INTEGER NULL,
    ADD COLUMN IF NOT EXISTS date_echeance DATE NULL,
    ADD COLUMN IF NOT EXISTS statut_paiement VARCHAR(20) NOT NULL DEFAULT 'encaisse',
    ADD COLUMN IF NOT EXISTS date_encaissement DATE NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_acomptes_compte_bancaire') THEN
        ALTER TABLE acomptes
            ADD CONSTRAINT fk_acomptes_compte_bancaire
            FOREIGN KEY (compte_bancaire_id) REFERENCES comptes_bancaires(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_acomptes_compte_bancaire_factg ON acomptes (societe_id, compte_bancaire_id) WHERE compte_bancaire_id IS NOT NULL;

ALTER TABLE acomptes DROP CONSTRAINT IF EXISTS ck_acomptes_mode_factg;
ALTER TABLE acomptes ADD CONSTRAINT ck_acomptes_mode_factg
    CHECK (mode IN ('virement','cheque','especes','effet','carte','prelevement','autre')) NOT VALID;
ALTER TABLE acomptes DROP CONSTRAINT IF EXISTS ck_acomptes_statut_paiement_factg;
ALTER TABLE acomptes ADD CONSTRAINT ck_acomptes_statut_paiement_factg
    CHECK (statut_paiement IN ('en_attente','encaisse','rejete')) NOT VALID;

UPDATE acomptes
   SET statut_paiement = CASE WHEN mode IN ('cheque','effet') AND est_comptabilisee = FALSE THEN 'en_attente' ELSE 'encaisse' END
 WHERE statut_paiement IS NULL OR statut_paiement = ''
    OR (mode IN ('cheque','effet') AND est_comptabilisee = FALSE);
UPDATE acomptes
   SET date_encaissement = date
 WHERE statut_paiement = 'encaisse' AND date_encaissement IS NULL;

-- ── 2. Imputations d'acomptes : piste d'audit et contrepassation ───────────
ALTER TABLE imputations_acomptes
    ADD COLUMN IF NOT EXISTS statut VARCHAR(20) NOT NULL DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS date_annulation TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS annulee_par INTEGER NULL,
    ADD COLUMN IF NOT EXISTS ecriture_id INTEGER NULL,
    ADD COLUMN IF NOT EXISTS ecriture_annulation_id INTEGER NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_imputations_acomptes_annulee_par') THEN
        ALTER TABLE imputations_acomptes
            ADD CONSTRAINT fk_imputations_acomptes_annulee_par
            FOREIGN KEY (annulee_par) REFERENCES utilisateurs(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_imputations_acomptes_ecriture') THEN
        ALTER TABLE imputations_acomptes
            ADD CONSTRAINT fk_imputations_acomptes_ecriture
            FOREIGN KEY (ecriture_id) REFERENCES ecritures(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_imputations_acomptes_ecriture_annulation') THEN
        ALTER TABLE imputations_acomptes
            ADD CONSTRAINT fk_imputations_acomptes_ecriture_annulation
            FOREIGN KEY (ecriture_annulation_id) REFERENCES ecritures(id) ON DELETE SET NULL;
    END IF;
END $$;

ALTER TABLE imputations_acomptes DROP CONSTRAINT IF EXISTS ck_imputations_acomptes_statut_factg;
ALTER TABLE imputations_acomptes ADD CONSTRAINT ck_imputations_acomptes_statut_factg
    CHECK (statut IN ('active','annulee')) NOT VALID;
CREATE INDEX IF NOT EXISTS idx_imputations_acomptes_actives
    ON imputations_acomptes (societe_id, acompte_id, facture_id)
    WHERE statut = 'active';

-- ── 3. Avoirs : calculs métier réels ──────────────────────────────────────
ALTER TABLE lignes_avoir
    ADD COLUMN IF NOT EXISTS montant_ht_force NUMERIC(18,2) NULL,
    ADD COLUMN IF NOT EXISTS mode_calcul VARCHAR(30) NOT NULL DEFAULT 'quantite',
    ADD COLUMN IF NOT EXISTS taux_rrr NUMERIC(7,4) NULL,
    ADD COLUMN IF NOT EXISTS nouveau_prix_unitaire NUMERIC(18,4) NULL;

ALTER TABLE lignes_avoir DROP CONSTRAINT IF EXISTS ck_lignes_avoir_mode_calcul_factg;
ALTER TABLE lignes_avoir ADD CONSTRAINT ck_lignes_avoir_mode_calcul_factg
    CHECK (mode_calcul IN ('quantite','rrr_pourcentage','rrr_montant','correction_prix','autre_montant')) NOT VALID;
ALTER TABLE lignes_avoir DROP CONSTRAINT IF EXISTS ck_lignes_avoir_montant_force_factg;
ALTER TABLE lignes_avoir ADD CONSTRAINT ck_lignes_avoir_montant_force_factg
    CHECK (montant_ht_force IS NULL OR montant_ht_force > 0) NOT VALID;

-- ── 4. Utilisation d'un crédit d'avoir ────────────────────────────────────
CREATE TABLE IF NOT EXISTS utilisations_avoirs (
    id                       SERIAL PRIMARY KEY,
    societe_id               INTEGER NOT NULL REFERENCES societes(id) ON DELETE CASCADE,
    avoir_id                 INTEGER NOT NULL REFERENCES avoirs(id) ON DELETE RESTRICT,
    type_utilisation         VARCHAR(20) NOT NULL,
    facture_id               INTEGER NULL REFERENCES factures(id) ON DELETE RESTRICT,
    date_utilisation         DATE NOT NULL,
    montant                  NUMERIC(18,2) NOT NULL,
    mode                     VARCHAR(20) NULL,
    compte_bancaire_id       INTEGER NULL REFERENCES comptes_bancaires(id) ON DELETE SET NULL,
    banque                   VARCHAR(100) NULL,
    reference                VARCHAR(100) NULL,
    ecriture_id              INTEGER NULL REFERENCES ecritures(id) ON DELETE SET NULL,
    statut                   VARCHAR(20) NOT NULL DEFAULT 'active',
    date_annulation          TIMESTAMP NULL,
    annulee_par              INTEGER NULL REFERENCES utilisateurs(id) ON DELETE SET NULL,
    ecriture_annulation_id   INTEGER NULL REFERENCES ecritures(id) ON DELETE SET NULL,
    created_at               TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_utilisations_avoirs_type_factg CHECK (type_utilisation IN ('imputation','remboursement')),
    CONSTRAINT ck_utilisations_avoirs_statut_factg CHECK (statut IN ('active','annulee')),
    CONSTRAINT ck_utilisations_avoirs_montant_factg CHECK (montant > 0),
    CONSTRAINT ck_utilisations_avoirs_facture_factg CHECK (
        (type_utilisation = 'imputation' AND facture_id IS NOT NULL)
        OR (type_utilisation = 'remboursement')
    )
);
CREATE INDEX IF NOT EXISTS idx_utilisations_avoirs_avoir
    ON utilisations_avoirs (societe_id, avoir_id, statut);
CREATE INDEX IF NOT EXISTS idx_utilisations_avoirs_facture
    ON utilisations_avoirs (societe_id, facture_id, statut)
    WHERE facture_id IS NOT NULL;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE utilisations_avoirs TO hisabpro;
GRANT USAGE, SELECT ON SEQUENCE utilisations_avoirs_id_seq TO hisabpro;

COMMIT;
