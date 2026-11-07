BEGIN;

-- Patch 07B cleanup — séparer clairement le libellé métier de la référence justificative.
-- Ne modifie PAS les écritures comptables existantes : uniquement les modèles de saisie.

UPDATE modeles_ecritures
SET libelle_auto = 'Facture fournisseur — réf. {ref} — {tiers}'
WHERE libelle_auto = 'FN°{ref} {tiers}';

UPDATE modeles_ecritures
SET libelle_auto = 'Facture client — réf. {ref} — {tiers}'
WHERE libelle_auto = 'FA°{ref} {tiers}';

COMMIT;
