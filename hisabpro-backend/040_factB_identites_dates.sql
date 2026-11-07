-- FACT-B — identité historique des factures et profil fiscal des tiers
-- IMPORTANT : si une migration précédente a échoué dans la même session PostgreSQL,
-- exécuter ROLLBACK avant de lancer ce fichier (SQLSTATE 25P02).
-- Idempotent autant que possible pour les environnements de développement.

-- Compatibilité avec les factures historiques : l'ancienne version du trigger
-- réappliquait les contrôles de validation à chaque UPDATE. Les backfills de
-- snapshots ci-dessous pouvaient donc échouer sur une ancienne facture achat
-- sans référence fournisseur. On corrige la fonction AVANT tout backfill.

CREATE OR REPLACE FUNCTION hisabpro_guard_facture_validee()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_dup INTEGER;
    v_devient_validee BOOLEAN := FALSE;
BEGIN
    -- Les contrôles de complétude (échéance, fournisseur, référence externe)
    -- s'appliquent uniquement au passage brouillon -> définitif. Une mise à jour
    -- technique autorisée d'une facture historique déjà validée (snapshot,
    -- statut de paiement, etc.) ne doit pas être bloquée par des données legacy.
    IF TG_OP = 'INSERT' THEN
        v_devient_validee := COALESCE(NEW.est_proforma, FALSE) = FALSE
                              AND COALESCE(NEW.est_validee, FALSE) = TRUE;
    ELSE
        v_devient_validee := COALESCE(NEW.est_proforma, FALSE) = FALSE
                              AND COALESCE(NEW.est_validee, FALSE) = TRUE
                              AND (
                                  COALESCE(OLD.est_validee, FALSE) = FALSE
                                  OR COALESCE(OLD.est_proforma, FALSE) = TRUE
                              );
    END IF;
    -- Un numéro interne définitif ne doit jamais être réutilisé.
    IF NEW.numero IS NOT NULL THEN
        SELECT f.id INTO v_dup
        FROM factures f
        WHERE f.societe_id = NEW.societe_id
          AND f.numero = NEW.numero
          AND f.id <> COALESCE(NEW.id, -1)
        LIMIT 1;
        IF v_dup IS NOT NULL THEN
            RAISE EXCEPTION 'Numéro de facture interne déjà utilisé : %', NEW.numero;
        END IF;
    END IF;

    IF v_devient_validee THEN
        IF NEW.numero IS NULL OR BTRIM(NEW.numero) = '' THEN
            RAISE EXCEPTION 'Une facture validée doit avoir un numéro interne définitif';
        END IF;
        IF NEW.date_echeance IS NULL THEN
            RAISE EXCEPTION 'Une facture validée doit avoir une date d''échéance';
        END IF;

        -- Pour un achat, la référence est le numéro porté par la facture du fournisseur.
        IF NEW.type::TEXT = 'achat' THEN
            IF NEW.tiers_id IS NULL THEN
                RAISE EXCEPTION 'Une facture fournisseur validée doit être rattachée à un fournisseur';
            END IF;
            IF NEW.reference IS NULL OR BTRIM(NEW.reference) = '' THEN
                RAISE EXCEPTION 'Le numéro de facture fournisseur est obligatoire avant validation';
            END IF;
            SELECT f.id INTO v_dup
            FROM factures f
            WHERE f.societe_id = NEW.societe_id
              AND f.type::TEXT = 'achat'
              AND COALESCE(f.est_proforma, FALSE) = FALSE
              AND COALESCE(f.est_validee, FALSE) = TRUE
              AND f.tiers_id = NEW.tiers_id
              AND f.exercice = NEW.exercice
              AND LOWER(BTRIM(COALESCE(f.reference, ''))) = LOWER(BTRIM(NEW.reference))
              AND f.id <> COALESCE(NEW.id, -1)
            LIMIT 1;
            IF v_dup IS NOT NULL THEN
                RAISE EXCEPTION 'Facture fournisseur en doublon : ce numéro existe déjà pour ce fournisseur sur l''exercice %', NEW.exercice;
            END IF;
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' AND COALESCE(OLD.est_proforma, FALSE) = FALSE AND COALESCE(OLD.est_validee, FALSE) = TRUE THEN
        IF COALESCE(NEW.est_validee, FALSE) = FALSE THEN
            RAISE EXCEPTION 'Une facture validée ne peut pas être repassée en brouillon';
        END IF;
        IF NEW.numero IS DISTINCT FROM OLD.numero
           OR NEW.date IS DISTINCT FROM OLD.date
           OR NEW.exercice IS DISTINCT FROM OLD.exercice
           OR NEW.type IS DISTINCT FROM OLD.type
           OR NEW.tiers_id IS DISTINCT FROM OLD.tiers_id
           OR NEW.tiers IS DISTINCT FROM OLD.tiers
           OR NEW.reference IS DISTINCT FROM OLD.reference
           OR NEW.date_echeance IS DISTINCT FROM OLD.date_echeance
           OR NEW.delai_paiement IS DISTINCT FROM OLD.delai_paiement
           OR NEW.remise_globale IS DISTINCT FROM OLD.remise_globale
           OR NEW.ristourne IS DISTINCT FROM OLD.ristourne
           OR NEW.escompte IS DISTINCT FROM OLD.escompte
           OR NEW.frais_transport_ht IS DISTINCT FROM OLD.frais_transport_ht
           OR NEW.frais_transport_tva IS DISTINCT FROM OLD.frais_transport_tva
           OR NEW.frais_emballage_ht IS DISTINCT FROM OLD.frais_emballage_ht
           OR NEW.frais_emballage_tva IS DISTINCT FROM OLD.frais_emballage_tva
           OR NEW.ras_taux IS DISTINCT FROM OLD.ras_taux
           OR NEW.nature_tva_achat IS DISTINCT FROM OLD.nature_tva_achat
           OR NEW.tva_deductible_pct IS DISTINCT FROM OLD.tva_deductible_pct
        THEN
            RAISE EXCEPTION 'Facture validée : les données de facturation sont immuables. Utilisez un avoir ou un document correctif.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;



ALTER TABLE tiers
    ADD COLUMN IF NOT EXISTS categorie_fiscale VARCHAR(20);

UPDATE tiers
SET categorie_fiscale = CASE
    WHEN COALESCE(NULLIF(TRIM(ice), ''), NULLIF(TRIM(identifiant_fiscal), ''), NULLIF(TRIM(rc), '')) IS NOT NULL
        THEN 'professionnel'
    ELSE 'indetermine'
END
WHERE categorie_fiscale IS NULL OR categorie_fiscale NOT IN ('professionnel','particulier','indetermine');

ALTER TABLE tiers ALTER COLUMN categorie_fiscale SET DEFAULT 'professionnel';
ALTER TABLE tiers ALTER COLUMN categorie_fiscale SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_tiers_categorie_fiscale') THEN
        ALTER TABLE tiers ADD CONSTRAINT ck_tiers_categorie_fiscale
            CHECK (categorie_fiscale IN ('professionnel','particulier','indetermine'));
    END IF;
END $$;

ALTER TABLE factures
    ADD COLUMN IF NOT EXISTS tiers_telephone_snapshot VARCHAR(20),
    ADD COLUMN IF NOT EXISTS tiers_email_snapshot VARCHAR(100),
    ADD COLUMN IF NOT EXISTS tiers_categorie_snapshot VARCHAR(20),
    ADD COLUMN IF NOT EXISTS societe_snapshot_json TEXT,
    ADD COLUMN IF NOT EXISTS notes_snapshot TEXT;

UPDATE factures f
SET tiers_telephone_snapshot = COALESCE(f.tiers_telephone_snapshot, t.telephone),
    tiers_email_snapshot = COALESCE(f.tiers_email_snapshot, t.email),
    tiers_categorie_snapshot = COALESCE(f.tiers_categorie_snapshot, t.categorie_fiscale)
FROM tiers t
WHERE t.id = f.tiers_id AND t.societe_id = f.societe_id;

-- Backfill des factures déjà définitives : à partir de cette migration, le PDF
-- restera basé sur cette photographie même si les paramètres société changent.
UPDATE factures f
SET societe_snapshot_json = json_build_object(
    'raison_sociale', s.raison_sociale,
    'identifiant_fiscal', s.identifiant_fiscal,
    'ice', s.ice,
    'rc', s.rc,
    'patente', s.patente,
    'cnss_numero', s.cnss_numero,
    'adresse', s.adresse,
    'ville', s.ville,
    'pays', s.pays,
    'telephone', s.telephone,
    'fax', s.fax,
    'email', s.email,
    'site_web', s.site_web,
    'forme_juridique', s.forme_juridique,
    'capital_social', s.capital_social,
    'banque', s.banque,
    'agence', s.agence,
    'rib', s.rib,
    'logo_url', s.logo_url
)::text
FROM societes s
WHERE s.id = f.societe_id
  AND COALESCE(f.est_validee, FALSE) = TRUE
  AND f.societe_snapshot_json IS NULL;


-- Les notes imprimées font partie du document historique. On les fige pour les
-- factures déjà définitives tout en gardant ``notes`` disponible pour le suivi interne.
UPDATE factures
SET notes_snapshot = notes
WHERE COALESCE(est_validee, FALSE) = TRUE
  AND notes_snapshot IS NULL;
