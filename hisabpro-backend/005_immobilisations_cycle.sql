-- HisabPro Patch 03 — Immobilisations : acquisition, TVA, amortissement, sortie/cession
-- PostgreSQL — à exécuter UNE FOIS après sauvegarde de la base.

BEGIN;

-- 1) Montants exacts
ALTER TABLE immobilisations
    ALTER COLUMN valeur_brute TYPE NUMERIC(18,2) USING valeur_brute::numeric(18,2),
    ALTER COLUMN valeur_residuelle TYPE NUMERIC(18,2) USING COALESCE(valeur_residuelle,0)::numeric(18,2),
    ALTER COLUMN taux_degressif TYPE NUMERIC(8,4) USING taux_degressif::numeric(8,4);

ALTER TABLE immobilisations ALTER COLUMN duree_amort DROP NOT NULL;
UPDATE immobilisations SET methode='lineaire' WHERE methode IS NULL;
ALTER TABLE immobilisations ALTER COLUMN methode SET NOT NULL;

-- 2) Acquisition / TVA / mise en service
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS date_mise_en_service DATE;
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS prix_acquisition_ht NUMERIC(18,2);
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS taux_tva NUMERIC(5,2) NOT NULL DEFAULT 20;
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS tva_recuperable_pct NUMERIC(5,2) NOT NULL DEFAULT 100;
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS fournisseur VARCHAR(200);
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS date_paiement DATE;
-- FALSE pour l'historique : on ne reconstitue pas artificiellement une TVA passée.
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS tva_suivie_directement BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS amortissable BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS vehicule_tourisme BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS compte_tva VARCHAR(10) NOT NULL DEFAULT '34551';
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS compte_fournisseur VARCHAR(10) NOT NULL DEFAULT '4481';
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS compte_reglement VARCHAR(10) NOT NULL DEFAULT '5141';
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS ecriture_acquisition_id INTEGER REFERENCES ecritures(id);
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS ecriture_paiement_id INTEGER REFERENCES ecritures(id);

-- Compatibilité avec les immobilisations déjà présentes : leur ancienne valeur brute
-- est considérée comme prix HT historique, sans inventer de date de paiement TVA.
UPDATE immobilisations
SET date_mise_en_service = COALESCE(date_mise_en_service, date_acquisition),
    prix_acquisition_ht = COALESCE(prix_acquisition_ht, valeur_brute)
WHERE date_mise_en_service IS NULL OR prix_acquisition_ht IS NULL;

-- Les anciens comptes proposés par l'ancienne interface ne sont PAS réécrits
-- automatiquement ici : une écriture comptable historique peut déjà utiliser ce
-- compte. Le README fournit une requête de diagnostic. Les nouvelles acquisitions
-- utilisent désormais les comptes CGNC corrigés.
UPDATE immobilisations
SET amortissable = FALSE,
    duree_amort = NULL
WHERE LOWER(COALESCE(categorie,'')) = 'terrain';

ALTER TABLE immobilisations ALTER COLUMN date_mise_en_service SET NOT NULL;
ALTER TABLE immobilisations ALTER COLUMN prix_acquisition_ht SET NOT NULL;
ALTER TABLE immobilisations ALTER COLUMN valeur_residuelle SET NOT NULL;
ALTER TABLE immobilisations ALTER COLUMN valeur_residuelle SET DEFAULT 0;
ALTER TABLE immobilisations ALTER COLUMN compte_immo SET DEFAULT '2332';
ALTER TABLE immobilisations ALTER COLUMN compte_amort SET DEFAULT '28332';
ALTER TABLE immobilisations ALTER COLUMN compte_dotation SET DEFAULT '61933';

-- Rattachement aux écritures d'acquisition déjà générées par les anciennes versions.
UPDATE immobilisations i
SET ecriture_acquisition_id = e.id
FROM ecritures e
WHERE i.ecriture_acquisition_id IS NULL
  AND e.societe_id = i.societe_id
  AND e.reference = ('ACQ-' || EXTRACT(YEAR FROM i.date_acquisition)::int || '-' || i.id);

-- 3) Sortie / cession
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS date_sortie DATE;
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS type_sortie VARCHAR(20);
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS prix_cession_ht NUMERIC(18,2);
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS taux_tva_cession NUMERIC(5,2);
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS regime_tva_cession VARCHAR(30);
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS date_encaissement_cession DATE;
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS compte_produit_cession VARCHAR(10) NOT NULL DEFAULT '7513';
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS compte_vna_cession VARCHAR(10) NOT NULL DEFAULT '6513';
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS compte_creance_cession VARCHAR(10) NOT NULL DEFAULT '3481';
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS compte_tva_cession VARCHAR(10) NOT NULL DEFAULT '4455';
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS ecriture_cession_id INTEGER REFERENCES ecritures(id);
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS ecriture_sortie_id INTEGER REFERENCES ecritures(id);
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS ecriture_encaissement_cession_id INTEGER REFERENCES ecritures(id);

-- Comptes de cession adaptés aux immobilisations incorporelles/corporelles.
UPDATE immobilisations
SET compte_produit_cession = CASE WHEN compte_immo LIKE '22%' OR LOWER(COALESCE(categorie,''))='logiciel' THEN '7512' ELSE '7513' END,
    compte_vna_cession = CASE WHEN compte_immo LIKE '22%' OR LOWER(COALESCE(categorie,''))='logiciel' THEN '6512' ELSE '6513' END;

-- 4) Contraintes d'intégrité
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_prix_ht_non_negatif;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_prix_ht_non_negatif CHECK (prix_acquisition_ht >= 0);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_valeur_brute_non_negative;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_valeur_brute_non_negative CHECK (valeur_brute >= 0);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_valeur_residuelle;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_valeur_residuelle CHECK (valeur_residuelle >= 0 AND valeur_residuelle <= valeur_brute);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_taux_tva;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_taux_tva CHECK (taux_tva >= 0 AND taux_tva <= 100);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_tva_recuperable_pct;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_tva_recuperable_pct CHECK (tva_recuperable_pct >= 0 AND tva_recuperable_pct <= 100);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_taux_tva_cession;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_taux_tva_cession CHECK (taux_tva_cession IS NULL OR (taux_tva_cession >= 0 AND taux_tva_cession <= 100));
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_duree_amort;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_duree_amort CHECK (duree_amort IS NULL OR duree_amort > 0);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_mise_service_apres_acquisition;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_mise_service_apres_acquisition CHECK (date_mise_en_service >= date_acquisition);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_paiement_apres_acquisition;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_paiement_apres_acquisition CHECK (date_paiement IS NULL OR date_paiement >= date_acquisition);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_sortie_apres_service;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_sortie_apres_service CHECK (date_sortie IS NULL OR date_sortie >= date_mise_en_service);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_type_sortie;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_type_sortie CHECK (type_sortie IS NULL OR type_sortie IN ('cession','rebut'));
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_amortissable_duree;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_amortissable_duree CHECK (NOT amortissable OR duree_amort IS NOT NULL);
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_methode;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_methode CHECK (methode IN ('lineaire','degressif'));
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_encaissement_cession;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_encaissement_cession CHECK (date_encaissement_cession IS NULL OR (date_sortie IS NOT NULL AND date_encaissement_cession >= date_sortie));

CREATE INDEX IF NOT EXISTS ix_immo_societe_date_paiement ON immobilisations(societe_id, date_paiement);
CREATE INDEX IF NOT EXISTS ix_immo_societe_date_sortie ON immobilisations(societe_id, date_sortie);

-- 5) Droits applicatifs. Nécessaire si la migration est exécutée via postgres/pgAdmin.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE immobilisations TO hisabpro;
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE ecritures TO hisabpro;
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE lignes_ecriture TO hisabpro;
        GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO hisabpro;
    END IF;
END $$;

COMMIT;
