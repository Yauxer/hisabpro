-- CONFORM.1 — conformité TVA, frais accessoires et RRR
BEGIN;

ALTER TABLE factures
    ADD COLUMN IF NOT EXISTS qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable',
    ADD COLUMN IF NOT EXISTS frais_transport_mode VARCHAR(30) NOT NULL DEFAULT 'accessoire',
    ADD COLUMN IF NOT EXISTS frais_transport_qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable',
    ADD COLUMN IF NOT EXISTS frais_emballage_mode VARCHAR(30) NOT NULL DEFAULT 'perdu',
    ADD COLUMN IF NOT EXISTS frais_emballage_qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable';

ALTER TABLE lignes_facture ADD COLUMN IF NOT EXISTS qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable';
ALTER TABLE lignes_devis ADD COLUMN IF NOT EXISTS qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable';
ALTER TABLE lignes_bon_commande ADD COLUMN IF NOT EXISTS qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable';
ALTER TABLE lignes_bon_livraison ADD COLUMN IF NOT EXISTS qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable';
ALTER TABLE lignes_avoir ADD COLUMN IF NOT EXISTS qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable';
ALTER TABLE avoirs ADD COLUMN IF NOT EXISTS nature_avoir VARCHAR(30) NOT NULL DEFAULT 'retour_annulation';

-- Acomptes et immobilisations utilisent le même référentiel TVA que les factures.
ALTER TABLE acomptes ADD COLUMN IF NOT EXISTS qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable';
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS qualification_tva VARCHAR(40) NOT NULL DEFAULT 'taxable';
ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS qualification_tva_cession VARCHAR(40) NOT NULL DEFAULT 'taxable';

-- Validation centrale SQL de la combinaison date / taux / qualification.
-- Le catalogue reste volontairement large pour 2024-2025 afin de couvrir les
-- transitions sectorielles ; à compter de 2026 la saisie générique est 10/20.
CREATE OR REPLACE FUNCTION hisabpro_tva_combinaison_valide(p_date DATE, p_taux NUMERIC, p_qualification VARCHAR)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
  y INTEGER := EXTRACT(YEAR FROM p_date)::INTEGER;
  q VARCHAR := COALESCE(p_qualification, 'taxable');
  t NUMERIC := COALESCE(p_taux, 0);
BEGIN
  IF q NOT IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension') THEN
    RETURN FALSE;
  END IF;
  IF q <> 'taxable' THEN
    RETURN t = 0;
  END IF;
  IF t <= 0 THEN RETURN FALSE; END IF;
  IF y <= 2023 THEN RETURN t IN (7,10,14,20); END IF;
  IF y = 2024 THEN RETURN t IN (8,10,11,12,13,14,16,20); END IF;
  IF y = 2025 THEN RETURN t IN (9,10,12,15,18,20); END IF;
  RETURN t IN (10,20);
END;
$$;


-- Normalisation des anciennes données avant activation définitive des contraintes.
UPDATE acomptes SET qualification_tva = 'exonere_sans_deduction', taux_tva = 0, tva_applicable = FALSE
WHERE COALESCE(tva_applicable,FALSE) = FALSE OR COALESCE(taux_tva,0) = 0;
UPDATE immobilisations SET qualification_tva = 'exonere_sans_deduction', taux_tva = 0, tva_recuperable_pct = 0
WHERE COALESCE(taux_tva,0) = 0;
UPDATE immobilisations SET qualification_tva_cession = 'hors_champ', taux_tva_cession = 0
WHERE type_sortie = 'rebut';
UPDATE immobilisations SET qualification_tva_cession = 'exonere_sans_deduction', taux_tva_cession = 0
WHERE type_sortie = 'cession' AND COALESCE(taux_tva_cession,0) = 0;

-- Cohérence TVA sur acomptes et immobilisations. Des triggers ciblés sont
-- préférés à des CHECK date-aware afin de ne pas bloquer la modification d'un
-- libellé sur une ancienne donnée historique qui porterait un taux désormais obsolète.
ALTER TABLE acomptes DROP CONSTRAINT IF EXISTS ck_acomptes_qualification_tva;
ALTER TABLE acomptes ADD CONSTRAINT ck_acomptes_qualification_tva CHECK (
  qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension')
) NOT VALID;
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_qualification_tva;
ALTER TABLE immobilisations ADD CONSTRAINT ck_immo_qualification_tva CHECK (
  qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension')
  AND qualification_tva_cession IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension')
) NOT VALID;
ALTER TABLE immobilisations DROP CONSTRAINT IF EXISTS ck_immo_qualification_tva_cession;

CREATE OR REPLACE FUNCTION hisabpro_guard_acompte_tva_date()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NOT hisabpro_tva_combinaison_valide(NEW.date, NEW.taux_tva, NEW.qualification_tva)
     OR COALESCE(NEW.tva_applicable,FALSE) <> (NEW.qualification_tva = 'taxable') THEN
    RAISE EXCEPTION 'TVA de l''acompte incohérente avec sa date ou sa qualification.';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_hisabpro_acompte_tva_date ON acomptes;
CREATE TRIGGER trg_hisabpro_acompte_tva_date
BEFORE INSERT OR UPDATE OF date, taux_tva, qualification_tva, tva_applicable ON acomptes
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_acompte_tva_date();

CREATE OR REPLACE FUNCTION hisabpro_guard_immo_tva_date()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NOT hisabpro_tva_combinaison_valide(NEW.date_acquisition, NEW.taux_tva, NEW.qualification_tva) THEN
    RAISE EXCEPTION 'TVA d''acquisition de l''immobilisation incohérente avec sa date ou sa qualification.';
  END IF;
  IF NEW.qualification_tva <> 'taxable' AND COALESCE(NEW.tva_recuperable_pct,0) <> 0 THEN
    RAISE EXCEPTION 'Une acquisition sans TVA ne peut pas porter de TVA récupérable.';
  END IF;
  IF NEW.taux_tva_cession IS NOT NULL AND NOT hisabpro_tva_combinaison_valide(
      COALESCE(NEW.date_sortie, NEW.date_acquisition), NEW.taux_tva_cession, NEW.qualification_tva_cession) THEN
    RAISE EXCEPTION 'TVA de cession de l''immobilisation incohérente avec sa date ou sa qualification.';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_hisabpro_immo_tva_date ON immobilisations;
CREATE TRIGGER trg_hisabpro_immo_tva_date
BEFORE INSERT OR UPDATE OF date_acquisition, taux_tva, qualification_tva, tva_recuperable_pct, date_sortie, taux_tva_cession, qualification_tva_cession ON immobilisations
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_immo_tva_date();

ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_factures_qualification_tva;
ALTER TABLE factures ADD CONSTRAINT ck_factures_qualification_tva CHECK (
  qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension')
);

ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_factures_transport_qualification_tva;
ALTER TABLE factures ADD CONSTRAINT ck_factures_transport_qualification_tva CHECK (
  frais_transport_qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension')
);
ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_factures_emballage_qualification_tva;
ALTER TABLE factures ADD CONSTRAINT ck_factures_emballage_qualification_tva CHECK (
  frais_emballage_qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension')
);

ALTER TABLE lignes_facture DROP CONSTRAINT IF EXISTS ck_lignes_facture_qualification_tva;
ALTER TABLE lignes_facture ADD CONSTRAINT ck_lignes_facture_qualification_tva CHECK (qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension'));
ALTER TABLE lignes_devis DROP CONSTRAINT IF EXISTS ck_lignes_devis_qualification_tva;
ALTER TABLE lignes_devis ADD CONSTRAINT ck_lignes_devis_qualification_tva CHECK (qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension'));
ALTER TABLE lignes_bon_commande DROP CONSTRAINT IF EXISTS ck_lignes_bc_qualification_tva;
ALTER TABLE lignes_bon_commande ADD CONSTRAINT ck_lignes_bc_qualification_tva CHECK (qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension'));
ALTER TABLE lignes_bon_livraison DROP CONSTRAINT IF EXISTS ck_lignes_bl_qualification_tva;
ALTER TABLE lignes_bon_livraison ADD CONSTRAINT ck_lignes_bl_qualification_tva CHECK (qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension'));
ALTER TABLE lignes_avoir DROP CONSTRAINT IF EXISTS ck_lignes_avoir_qualification_tva;
ALTER TABLE lignes_avoir ADD CONSTRAINT ck_lignes_avoir_qualification_tva CHECK (qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension'));
ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_factures_transport_mode;
ALTER TABLE factures ADD CONSTRAINT ck_factures_transport_mode CHECK (frais_transport_mode IN ('accessoire','distinct'));
ALTER TABLE factures DROP CONSTRAINT IF EXISTS ck_factures_emballage_mode;
ALTER TABLE factures ADD CONSTRAINT ck_factures_emballage_mode CHECK (frais_emballage_mode IN ('perdu','consigne','vente_distincte'));
ALTER TABLE avoirs DROP CONSTRAINT IF EXISTS ck_avoirs_nature;
ALTER TABLE avoirs ADD CONSTRAINT ck_avoirs_nature CHECK (nature_avoir IN ('retour_annulation','rrr','correction_prix','autre'));

ALTER TABLE avoirs DROP CONSTRAINT IF EXISTS ck_avoirs_rrr_sans_stock;
ALTER TABLE avoirs ADD CONSTRAINT ck_avoirs_rrr_sans_stock CHECK (NOT (nature_avoir = 'rrr' AND COALESCE(retour_stock, FALSE)));

-- Les lignes portent leur date sur le document parent : le trigger ci-dessous
-- applique le même contrôle date/taux en base, y compris si l'API est contournée.
CREATE OR REPLACE FUNCTION hisabpro_guard_ligne_tva_date()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  d DATE;
BEGIN
  CASE TG_TABLE_NAME
    WHEN 'lignes_facture' THEN SELECT date INTO d FROM factures WHERE id = NEW.facture_id;
    WHEN 'lignes_devis' THEN SELECT date INTO d FROM devis WHERE id = NEW.devis_id;
    WHEN 'lignes_bon_commande' THEN SELECT date INTO d FROM bons_commande WHERE id = NEW.bon_commande_id;
    WHEN 'lignes_bon_livraison' THEN SELECT date INTO d FROM bons_livraison WHERE id = NEW.bon_livraison_id;
    WHEN 'lignes_avoir' THEN SELECT date INTO d FROM avoirs WHERE id = NEW.avoir_id;
  END CASE;
  IF d IS NULL OR NOT hisabpro_tva_combinaison_valide(d, NEW.tva, NEW.qualification_tva) THEN
    RAISE EXCEPTION 'Combinaison taux/qualification TVA invalide pour la date du document.';
  END IF;
  RETURN NEW;
END;
$$;

DO $$
DECLARE t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY['lignes_facture','lignes_devis','lignes_bon_commande','lignes_bon_livraison','lignes_avoir'] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS trg_hisabpro_tva_date ON %I', t);
    EXECUTE format('CREATE TRIGGER trg_hisabpro_tva_date BEFORE INSERT OR UPDATE OF tva, qualification_tva ON %I FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_ligne_tva_date()', t);
  END LOOP;
END $$;

CREATE OR REPLACE FUNCTION hisabpro_guard_frais_tva_date()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF COALESCE(NEW.frais_transport_ht,0) > 0 AND NEW.frais_transport_mode = 'distinct'
     AND NOT hisabpro_tva_combinaison_valide(NEW.date, NEW.frais_transport_tva, NEW.frais_transport_qualification_tva) THEN
    RAISE EXCEPTION 'TVA des frais de transport distincts invalide pour la date de facture.';
  END IF;
  IF COALESCE(NEW.frais_emballage_ht,0) > 0 AND NEW.frais_emballage_mode = 'vente_distincte'
     AND NOT hisabpro_tva_combinaison_valide(NEW.date, NEW.frais_emballage_tva, NEW.frais_emballage_qualification_tva) THEN
    RAISE EXCEPTION 'TVA des emballages vendus distinctement invalide pour la date de facture.';
  END IF;
  IF NEW.frais_emballage_mode = 'consigne' THEN
    NEW.frais_emballage_tva := 0;
    NEW.frais_emballage_qualification_tva := 'hors_champ';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_guard_frais_tva_date ON factures;
CREATE TRIGGER trg_hisabpro_guard_frais_tva_date
BEFORE INSERT OR UPDATE OF date, frais_transport_ht, frais_transport_tva, frais_transport_mode, frais_transport_qualification_tva, frais_emballage_ht, frais_emballage_tva, frais_emballage_mode, frais_emballage_qualification_tva ON factures
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_frais_tva_date();

CREATE OR REPLACE FUNCTION hisabpro_guard_conformite_facture_validee()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF COALESCE(OLD.est_proforma, FALSE) = FALSE AND COALESCE(OLD.est_validee, FALSE) = TRUE THEN
    IF NEW.qualification_tva IS DISTINCT FROM OLD.qualification_tva
       OR NEW.frais_transport_mode IS DISTINCT FROM OLD.frais_transport_mode
       OR NEW.frais_transport_qualification_tva IS DISTINCT FROM OLD.frais_transport_qualification_tva
       OR NEW.frais_emballage_mode IS DISTINCT FROM OLD.frais_emballage_mode
       OR NEW.frais_emballage_qualification_tva IS DISTINCT FROM OLD.frais_emballage_qualification_tva
    THEN
      RAISE EXCEPTION 'Facture validée : son traitement TVA et ses frais accessoires sont immuables.';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hisabpro_guard_conformite_facture_validee ON factures;
CREATE TRIGGER trg_hisabpro_guard_conformite_facture_validee
BEFORE UPDATE ON factures
FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_conformite_facture_validee();

-- Historique : un taux 0 existant ne doit pas être présenté comme « taxable à 0 % ».
-- Les lignes des factures validées sont normalement immuables. Ce backfill ajoute
-- uniquement une qualification fiscale technique ; le guard est donc suspendu
-- pendant cette mise à niveau puis réactivé dans la même transaction.
ALTER TABLE lignes_facture DISABLE TRIGGER trg_hisabpro_guard_ligne_facture_validee;
UPDATE lignes_facture SET qualification_tva = 'exonere_sans_deduction' WHERE COALESCE(tva,0) = 0 AND qualification_tva = 'taxable';
UPDATE lignes_devis SET qualification_tva = 'exonere_sans_deduction' WHERE COALESCE(tva,0) = 0 AND qualification_tva = 'taxable';
UPDATE lignes_bon_commande SET qualification_tva = 'exonere_sans_deduction' WHERE COALESCE(tva,0) = 0 AND qualification_tva = 'taxable';
UPDATE lignes_bon_livraison SET qualification_tva = 'exonere_sans_deduction' WHERE COALESCE(tva,0) = 0 AND qualification_tva = 'taxable';
UPDATE lignes_avoir SET qualification_tva = 'exonere_sans_deduction' WHERE COALESCE(tva,0) = 0 AND qualification_tva = 'taxable';
ALTER TABLE lignes_facture ENABLE TRIGGER trg_hisabpro_guard_ligne_facture_validee;

GRANT EXECUTE ON FUNCTION hisabpro_tva_combinaison_valide(DATE, NUMERIC, VARCHAR) TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_guard_acompte_tva_date() TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_guard_immo_tva_date() TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_guard_ligne_tva_date() TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_guard_frais_tva_date() TO hisabpro;
GRANT EXECUTE ON FUNCTION hisabpro_guard_conformite_facture_validee() TO hisabpro;

COMMIT;
