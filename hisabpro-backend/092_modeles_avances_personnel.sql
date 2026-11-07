-- HisabPro092 : modèles facultatifs d'avances au personnel à moins d'un an.
-- Après091, par le propriétaire des tables. Aucun bulletin ni mouvement créé.
-- Sources et limites : docs/audit/SOURCES_MODELES_PERSONNEL_20261015.md.
-- Ne remplace pas un modèle déjà présent, même désactivé ou personnalisé.
BEGIN;
WITH nouveaux AS (
    INSERT INTO modeles_ecritures
        (code, libelle, journal, compte_declencheur, libelle_auto, actif)
    SELECT v.* FROM (VALUES
      ('paie_avance_banque', 'Avance au personnel — versement bancaire', 'BQ', '3431', 'Avance au personnel par banque — {ref}', TRUE),
      ('paie_avance_especes', 'Avance au personnel — versement en espèces', 'CA', '3431', 'Avance au personnel en espèces — {ref}', TRUE),
      ('paie_recuperation_avance', 'Avance au personnel — récupération sur rémunération due', 'SA', '4432', 'Récupération avance sur rémunération due — {ref}', TRUE),
      ('paie_remboursement_avance_banque', 'Avance au personnel — remboursement bancaire', 'BQ', '3431', 'Remboursement avance par banque — {ref}', TRUE),
      ('paie_remboursement_avance_especes', 'Avance au personnel — remboursement en espèces', 'CA', '3431', 'Remboursement avance en espèces — {ref}', TRUE)
    ) AS v(code,libelle,journal,compte_declencheur,libelle_auto,actif)
    WHERE NOT EXISTS (SELECT 1 FROM modeles_ecritures m WHERE m.code=v.code)
    ON CONFLICT (code) DO NOTHING
    RETURNING id, code
)
INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, v.ordre, v.compte, v.libelle, v.sens, v.principal, FALSE, NULL
FROM nouveaux m JOIN (VALUES
    ('paie_avance_banque',1,'3431','Avances et acomptes au personnel','debit',TRUE),
    ('paie_avance_banque',2,'5141','Banques','credit',FALSE),
    ('paie_avance_especes',1,'3431','Avances et acomptes au personnel','debit',TRUE),
    ('paie_avance_especes',2,'5161','Caisses','credit',FALSE),
    ('paie_recuperation_avance',1,'4432','Rémunérations dues au personnel','debit',TRUE),
    ('paie_recuperation_avance',2,'3431','Avances et acomptes au personnel','credit',FALSE),
    ('paie_remboursement_avance_banque',1,'3431','Avances et acomptes au personnel','credit',TRUE),
    ('paie_remboursement_avance_banque',2,'5141','Banques','debit',FALSE),
    ('paie_remboursement_avance_especes',1,'3431','Avances et acomptes au personnel','credit',TRUE),
    ('paie_remboursement_avance_especes',2,'5161','Caisses','debit',FALSE)
) AS v(code,ordre,compte,libelle,sens,principal) ON v.code=m.code;
COMMIT;
