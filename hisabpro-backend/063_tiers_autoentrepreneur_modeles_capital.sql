-- HisabPro 063 — statut auto-entrepreneur + schémas de capital explicités.
-- Exécuter avec le rôle propriétaire des tables sur la base HisabPro, APRÈS 062.
-- Ne modifie aucune écriture, facture ou ligne comptable déjà enregistrée.
BEGIN;

-- « Auto-entrepreneur » est un profil distinct d'un particulier et d'une
-- société. Ne change jamais implicitement le régime TVA ou les taux d'une pièce.
ALTER TABLE tiers DROP CONSTRAINT IF EXISTS ck_tiers_categorie_fiscale;
ALTER TABLE tiers ADD CONSTRAINT ck_tiers_categorie_fiscale
  CHECK (categorie_fiscale IN ('professionnel', 'autoentrepreneur', 'particulier', 'indetermine'));

-- 3461 = engagement d'apport en société ; 3462 = appel de capital des
-- actionnaires, normalement crédité par 1119 lors de l'appel de fonds.
-- Corrige uniquement les modèles, jamais les écritures historisées.
UPDATE modeles_ecritures
SET libelle = 'Souscription du capital — engagement des associés',
    journal = 'OD', compte_declencheur = '3461',
    libelle_auto = 'Souscription du capital — {ref}'
WHERE code = 'capital_souscription';

UPDATE lignes_modele
SET compte = '3461', libelle = 'Associés, comptes d’apport en société'
WHERE modele_id IN (SELECT id FROM modeles_ecritures WHERE code = 'capital_souscription')
  AND ordre = 1;

UPDATE modeles_ecritures
SET libelle = 'Libération d’apport par virement bancaire (après souscription)',
    journal = 'BQ', compte_declencheur = '5141',
    libelle_auto = 'Libération du capital par banque — {ref}'
WHERE code = 'capital_liberation';

UPDATE lignes_modele
SET compte = '3461', libelle = 'Associés, comptes d’apport en société'
WHERE modele_id IN (SELECT id FROM modeles_ecritures WHERE code = 'capital_liberation')
  AND ordre = 2;

-- Constatation de la paie dans SA (rémunérations) ; son règlement bancaire
-- reste dans BQ (modèle virement_salaires), sans changer les écritures passées.
UPDATE modeles_ecritures
SET libelle = 'Rémunérations du personnel — constatation de la paie',
    journal = 'SA', libelle_auto = 'Rémunérations du personnel — {ref}'
WHERE code = 'paie_salaires';

-- Modèles ajoutés : les modalités de libération ont des journaux et comptes
-- différents. On ne force pas tous les apports dans le journal Banque.
INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES
('capital_liberation_especes', 'Libération d’apport en espèces (après souscription)', 'CA', '5161', 'Libération du capital en espèces — {ref}', TRUE),
('capital_liberation_materiel', 'Libération d’apport en matériel informatique (après souscription)', 'OD', '2355', 'Libération du capital par apport de matériel informatique — {ref}', TRUE),
('capital_appel_actionnaires', 'Appel de capital souscrit non appelé (actionnaires)', 'OD', '3462', 'Appel du capital souscrit — {ref}', TRUE),
('capital_versement_actionnaires', 'Versement bancaire du capital appelé (actionnaires)', 'BQ', '5141', 'Versement du capital appelé par banque — {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
  libelle = EXCLUDED.libelle, journal = EXCLUDED.journal,
  compte_declencheur = EXCLUDED.compte_declencheur,
  libelle_auto = EXCLUDED.libelle_auto, actif = TRUE;

-- Les nouvelles lignes ne sont insérées qu'une fois ; les modèles préexistants
-- sont mis à jour par code puis ordre de ligne, sans doublon à la relance.
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, v.ordre, v.compte, v.libelle, v.sens, v.est_principal, FALSE, NULL
FROM (VALUES
  ('capital_liberation_especes', 1, '5161', 'Caisses', 'debit', TRUE),
  ('capital_liberation_especes', 2, '3461', 'Associés, comptes d’apport en société', 'credit', FALSE),
  ('capital_liberation_materiel', 1, '2355', 'Matériel informatique', 'debit', TRUE),
  ('capital_liberation_materiel', 2, '3461', 'Associés, comptes d’apport en société', 'credit', FALSE),
  ('capital_appel_actionnaires', 1, '3462', 'Actionnaires, capital souscrit et appelé non versé', 'debit', TRUE),
  ('capital_appel_actionnaires', 2, '1119', 'Actionnaires, capital souscrit non appelé', 'credit', FALSE),
  ('capital_versement_actionnaires', 1, '5141', 'Banques', 'debit', TRUE),
  ('capital_versement_actionnaires', 2, '3462', 'Actionnaires, capital souscrit et appelé non versé', 'credit', FALSE)
) AS v(code, ordre, compte, libelle, sens, est_principal)
JOIN modeles_ecritures m ON m.code = v.code
WHERE NOT EXISTS (
  SELECT 1 FROM lignes_modele l WHERE l.modele_id = m.id AND l.ordre = v.ordre
);

COMMIT;
