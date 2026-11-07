-- FACT-H — Audit final Facturation
-- - correction traçable des règlements comptabilisés
-- - snapshots légaux immuables des avoirs
-- - migration idempotente / rejouable après 045_factG_acomptes_avoirs.sql
BEGIN;

ALTER TABLE reglements
    ADD COLUMN IF NOT EXISTS ecriture_id INTEGER NULL,
    ADD COLUMN IF NOT EXISTS ecriture_annulation_id INTEGER NULL,
    ADD COLUMN IF NOT EXISTS date_annulation TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS annulee_par INTEGER NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_reglements_ecriture_facth') THEN
        ALTER TABLE reglements ADD CONSTRAINT fk_reglements_ecriture_facth
            FOREIGN KEY (ecriture_id) REFERENCES ecritures(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_reglements_ecriture_annulation_facth') THEN
        ALTER TABLE reglements ADD CONSTRAINT fk_reglements_ecriture_annulation_facth
            FOREIGN KEY (ecriture_annulation_id) REFERENCES ecritures(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_reglements_annulee_par_facth') THEN
        ALTER TABLE reglements ADD CONSTRAINT fk_reglements_annulee_par_facth
            FOREIGN KEY (annulee_par) REFERENCES utilisateurs(id) ON DELETE SET NULL;
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_reglements_ecriture_facth ON reglements (societe_id, ecriture_id) WHERE ecriture_id IS NOT NULL;

ALTER TABLE avoirs
    ADD COLUMN IF NOT EXISTS societe_snapshot_json TEXT NULL,
    ADD COLUMN IF NOT EXISTS tiers_ice_snapshot VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS tiers_if_snapshot VARCHAR(50) NULL,
    ADD COLUMN IF NOT EXISTS tiers_rc_snapshot VARCHAR(50) NULL,
    ADD COLUMN IF NOT EXISTS tiers_adresse_snapshot TEXT NULL,
    ADD COLUMN IF NOT EXISTS tiers_ville_snapshot VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS tiers_telephone_snapshot VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS tiers_email_snapshot VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS tiers_categorie_snapshot VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS notes_snapshot TEXT NULL;

-- Backfill : les avoirs existants héritent du snapshot de leur facture source.
UPDATE avoirs a SET
    societe_snapshot_json = COALESCE(a.societe_snapshot_json, f.societe_snapshot_json),
    tiers_ice_snapshot = COALESCE(a.tiers_ice_snapshot, f.tiers_ice_snapshot),
    tiers_if_snapshot = COALESCE(a.tiers_if_snapshot, f.tiers_if_snapshot),
    tiers_rc_snapshot = COALESCE(a.tiers_rc_snapshot, f.tiers_rc_snapshot),
    tiers_adresse_snapshot = COALESCE(a.tiers_adresse_snapshot, f.tiers_adresse_snapshot),
    tiers_ville_snapshot = COALESCE(a.tiers_ville_snapshot, f.tiers_ville_snapshot),
    tiers_telephone_snapshot = COALESCE(a.tiers_telephone_snapshot, f.tiers_telephone_snapshot),
    tiers_email_snapshot = COALESCE(a.tiers_email_snapshot, f.tiers_email_snapshot),
    tiers_categorie_snapshot = COALESCE(a.tiers_categorie_snapshot, f.tiers_categorie_snapshot),
    notes_snapshot = COALESCE(a.notes_snapshot, a.notes)
FROM factures f
WHERE f.id = a.facture_id;

-- Documents commerciaux finalisés : identité historique immuable.
ALTER TABLE devis ADD COLUMN IF NOT EXISTS societe_snapshot_json TEXT NULL,
    ADD COLUMN IF NOT EXISTS tiers_snapshot_json TEXT NULL,
    ADD COLUMN IF NOT EXISTS notes_snapshot TEXT NULL;
ALTER TABLE bons_commande ADD COLUMN IF NOT EXISTS societe_snapshot_json TEXT NULL,
    ADD COLUMN IF NOT EXISTS tiers_snapshot_json TEXT NULL,
    ADD COLUMN IF NOT EXISTS notes_snapshot TEXT NULL;
ALTER TABLE bons_livraison ADD COLUMN IF NOT EXISTS societe_snapshot_json TEXT NULL,
    ADD COLUMN IF NOT EXISTS tiers_snapshot_json TEXT NULL,
    ADD COLUMN IF NOT EXISTS notes_snapshot TEXT NULL;

-- Le backfill fige l'état connu au moment de la migration pour les pièces legacy
-- déjà sorties du brouillon ; on ne prétend pas reconstruire une identité passée.
UPDATE devis d SET
    societe_snapshot_json = COALESCE(d.societe_snapshot_json, json_build_object(
        'raison_sociale',s.raison_sociale,'identifiant_fiscal',s.identifiant_fiscal,'ice',s.ice,'rc',s.rc,'patente',s.patente,
        'adresse',s.adresse,'ville',s.ville,'pays',s.pays,'telephone',s.telephone,'email',s.email,'banque',s.banque,'rib',s.rib
    )::text),
    tiers_snapshot_json = COALESCE(d.tiers_snapshot_json,
        (SELECT json_build_object('nom',t.nom,'ice',t.ice,'if',t.identifiant_fiscal,'rc',t.rc,'adresse',t.adresse,
            'ville',t.ville,'telephone',t.telephone,'email',t.email,'categorie_fiscale',t.categorie_fiscale)::text
         FROM tiers t WHERE t.id=d.tiers_id AND t.societe_id=d.societe_id),
        json_build_object('nom',d.tiers)::text),
    notes_snapshot = COALESCE(d.notes_snapshot,d.notes)
FROM societes s
WHERE s.id=d.societe_id AND COALESCE(d.statut,'brouillon') <> 'brouillon';

UPDATE bons_commande b SET
    societe_snapshot_json = COALESCE(b.societe_snapshot_json, json_build_object(
        'raison_sociale',s.raison_sociale,'identifiant_fiscal',s.identifiant_fiscal,'ice',s.ice,'rc',s.rc,'patente',s.patente,
        'adresse',s.adresse,'ville',s.ville,'pays',s.pays,'telephone',s.telephone,'email',s.email,'banque',s.banque,'rib',s.rib
    )::text),
    tiers_snapshot_json = COALESCE(b.tiers_snapshot_json,
        (SELECT json_build_object('nom',t.nom,'ice',t.ice,'if',t.identifiant_fiscal,'rc',t.rc,'adresse',t.adresse,
            'ville',t.ville,'telephone',t.telephone,'email',t.email,'categorie_fiscale',t.categorie_fiscale)::text
         FROM tiers t WHERE t.id=b.tiers_id AND t.societe_id=b.societe_id),
        json_build_object('nom',b.tiers)::text),
    notes_snapshot = COALESCE(b.notes_snapshot,b.notes)
FROM societes s
WHERE s.id=b.societe_id AND COALESCE(b.statut,'en_attente') <> 'en_attente';

UPDATE bons_livraison bl SET
    societe_snapshot_json = COALESCE(bl.societe_snapshot_json, json_build_object(
        'raison_sociale',s.raison_sociale,'identifiant_fiscal',s.identifiant_fiscal,'ice',s.ice,'rc',s.rc,'patente',s.patente,
        'adresse',s.adresse,'ville',s.ville,'pays',s.pays,'telephone',s.telephone,'email',s.email,'banque',s.banque,'rib',s.rib
    )::text),
    tiers_snapshot_json = COALESCE(bl.tiers_snapshot_json,
        (SELECT json_build_object('nom',t.nom,'ice',t.ice,'if',t.identifiant_fiscal,'rc',t.rc,'adresse',t.adresse,
            'ville',t.ville,'telephone',t.telephone,'email',t.email,'categorie_fiscale',t.categorie_fiscale)::text
         FROM tiers t WHERE t.id=bl.tiers_id AND t.societe_id=bl.societe_id),
        json_build_object('nom',bl.tiers)::text),
    notes_snapshot = COALESCE(bl.notes_snapshot,bl.notes)
FROM societes s
WHERE s.id=bl.societe_id AND COALESCE(bl.statut,'en_preparation') <> 'en_preparation';

COMMIT;
