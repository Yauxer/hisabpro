-- FACT-E — fin de durcissement Facturation
-- Normalisation prudente des identifiants + garde-fous DB sur les lignes métier.
-- Les contraintes sont NOT VALID afin de ne pas rendre la migration impossible
-- à cause d'une donnée historique : elles s'appliquent néanmoins aux nouvelles
-- insertions / mises à jour. L'audit production signale les données legacy.
BEGIN;

-- Identifiants : on ne transforme que les valeurs dont le nettoyage est sûr.
UPDATE societes
   SET ice = regexp_replace(ice, '[[:space:]./-]+', '', 'g')
 WHERE NULLIF(btrim(COALESCE(ice, '')), '') IS NOT NULL
   AND regexp_replace(ice, '[[:space:]./-]+', '', 'g') ~ '^[0-9]{15}$';

UPDATE tiers
   SET ice = regexp_replace(ice, '[[:space:]./-]+', '', 'g')
 WHERE NULLIF(btrim(COALESCE(ice, '')), '') IS NOT NULL
   AND regexp_replace(ice, '[[:space:]./-]+', '', 'g') ~ '^[0-9]{15}$';

UPDATE societes
   SET identifiant_fiscal = regexp_replace(identifiant_fiscal, '[[:space:]./-]+', '', 'g')
 WHERE NULLIF(btrim(COALESCE(identifiant_fiscal, '')), '') IS NOT NULL
   AND regexp_replace(identifiant_fiscal, '[[:space:]./-]+', '', 'g') ~ '^[0-9]+$';

UPDATE tiers
   SET identifiant_fiscal = regexp_replace(identifiant_fiscal, '[[:space:]./-]+', '', 'g')
 WHERE NULLIF(btrim(COALESCE(identifiant_fiscal, '')), '') IS NOT NULL
   AND regexp_replace(identifiant_fiscal, '[[:space:]./-]+', '', 'g') ~ '^[0-9]+$';

UPDATE societes
   SET patente = upper(btrim(regexp_replace(patente, '[[:space:]]+', ' ', 'g')))
 WHERE NULLIF(btrim(COALESCE(patente, '')), '') IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_societes_ice_format_facte') THEN
        ALTER TABLE societes ADD CONSTRAINT ck_societes_ice_format_facte
          CHECK (ice IS NULL OR btrim(ice)='' OR ice ~ '^[0-9]{15}$') NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_tiers_ice_format_facte') THEN
        ALTER TABLE tiers ADD CONSTRAINT ck_tiers_ice_format_facte
          CHECK (ice IS NULL OR btrim(ice)='' OR ice ~ '^[0-9]{15}$') NOT VALID;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_lignes_facture_valeurs_facte') THEN
        ALTER TABLE lignes_facture ADD CONSTRAINT ck_lignes_facture_valeurs_facte CHECK (
          quantite > 0 AND prix_unitaire >= 0 AND tva BETWEEN 0 AND 100
          AND COALESCE(remise,0) BETWEEN 0 AND 100
          AND COALESCE(remise2,0) BETWEEN 0 AND 100
          AND COALESCE(rabais,0) >= 0
        ) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_lignes_devis_valeurs_facte') THEN
        ALTER TABLE lignes_devis ADD CONSTRAINT ck_lignes_devis_valeurs_facte CHECK (
          quantite > 0 AND prix_unitaire >= 0 AND tva BETWEEN 0 AND 100
        ) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_lignes_bc_valeurs_facte') THEN
        ALTER TABLE lignes_bon_commande ADD CONSTRAINT ck_lignes_bc_valeurs_facte CHECK (
          quantite > 0 AND prix_unitaire >= 0 AND tva BETWEEN 0 AND 100
          AND COALESCE(remise,0) BETWEEN 0 AND 100
          AND COALESCE(remise2,0) BETWEEN 0 AND 100
          AND COALESCE(rabais,0) >= 0
        ) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_lignes_bl_valeurs_facte') THEN
        ALTER TABLE lignes_bon_livraison ADD CONSTRAINT ck_lignes_bl_valeurs_facte CHECK (
          quantite_prevue > 0 AND quantite_livree >= 0 AND quantite_livree <= quantite_prevue
          AND prix_unitaire >= 0 AND tva BETWEEN 0 AND 100
          AND COALESCE(remise,0) BETWEEN 0 AND 100
          AND COALESCE(remise2,0) BETWEEN 0 AND 100
          AND COALESCE(rabais,0) >= 0
        ) NOT VALID;
    END IF;
END $$;

COMMIT;
