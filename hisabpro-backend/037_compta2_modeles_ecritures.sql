-- ============================================================
-- HisabPro — COMPTA.2 / Bibliothèque d'écritures comptables
-- Migration 037 — idempotente
-- - complète les modèles existants
-- - corrige l'acquisition d'immobilisation (4481 <= 1 an)
-- - corrige l'IR salarié vers 44525
-- - ajoute les opérations courantes manquantes
-- ============================================================

BEGIN;

ALTER TABLE modeles_ecritures
    ADD COLUMN IF NOT EXISTS compte_declencheur VARCHAR(10),
    ADD COLUMN IF NOT EXISTS libelle_auto VARCHAR(255);

ALTER TABLE lignes_modele
    ADD COLUMN IF NOT EXISTS est_principal BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS est_tva BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS ix_modeles_ecritures_compte_declencheur
    ON modeles_ecritures (compte_declencheur);

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_marchandises', 'Achat de marchandises', 'AC', '6111', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_matieres', 'Achat de matières premières', 'AC', '6121', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_fournitures', 'Achat de fournitures de bureau', 'AC', '61227', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_services', 'Achat de prestations de services', 'AC', '61263', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_honoraires', 'Honoraires', 'AC', '61365', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_loyer', 'Loyer - Location de constructions', 'AC', '61312', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_transport', 'Transport sur achats', 'AC', '61425', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_telephone', 'Frais de téléphone', 'AC', '61455', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_assurance', 'Assurances multirisques', 'AC', '61341', 'Prime d''assurance — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_entretien', 'Entretien et réparations', 'AC', '61331', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_electricite', 'Eau et électricité', 'AC', '61251', 'Facture fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('achat_immo', 'Acquisition immobilisation (dette ≤ 1 an)', 'AC', '2355', 'Facture immobilisation — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('vente_marchandises', 'Vente de marchandises au Maroc', 'VT', '7111', 'Facture client — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('vente_produits', 'Vente de produits finis', 'VT', '71211', 'Facture client — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('vente_services', 'Vente de prestations de services', 'VT', '71243', 'Facture client — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('vente_travaux', 'Vente de travaux', 'VT', '71241', 'Facture client — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('vente_locations', 'Locations diverses reçues', 'VT', '71271', 'Facture client — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('encaissement_client', 'Encaissement créance client', 'BQ', '5141', 'Règlement {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('paiement_fournisseur', 'Paiement fournisseur', 'BQ', '4411', 'Règlement {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('frais_bancaires', 'Frais et commissions bancaires', 'BQ', '61473', 'Agios {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('virement_salaires', 'Virement salaires', 'BQ', '4432', 'Salaires {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('paiement_tva', 'Paiement TVA', 'BQ', '4456', 'TVA {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('paiement_cnss', 'Paiement CNSS/AMO', 'BQ', '4441', 'CNSS/AMO {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('paiement_ir', 'Paiement IR', 'BQ', '44525', 'IR {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('paiement_is', 'Paiement IS', 'BQ', '4453', 'IS {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('paie_salaires', 'Écriture de paie mensuelle', 'OD', '6171', 'Paie {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('treso_encaissement_especes', 'Encaissement client en espèces', 'CA', '5161', 'Encaissement espèces {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('treso_paiement_especes', 'Paiement fournisseur en espèces', 'CA', '4411', 'Paiement espèces {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('treso_banque_vers_caisse', 'Retrait banque vers caisse', 'BQ', '5161', 'Retrait banque vers caisse', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('treso_caisse_vers_banque', 'Versement caisse en banque', 'BQ', '5141', 'Versement caisse en banque', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('effet_client_acceptation', 'Client — effet à recevoir', 'AE', '3425', 'Effet client {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('effet_client_encaissement', 'Encaissement d’un effet client', 'BQ', '5141', 'Encaissement effet {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('effet_fournisseur_acceptation', 'Fournisseur — effet à payer', 'OD', '4415', 'Effet fournisseur {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('effet_fournisseur_paiement', 'Paiement d’un effet fournisseur', 'BQ', '4415', 'Paiement effet {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('financement_emprunt_recu', 'Déblocage d’un emprunt bancaire', 'BQ', '1481', 'Emprunt bancaire {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('financement_remboursement_emprunt', 'Remboursement du principal d’un emprunt', 'BQ', '1481', 'Remboursement emprunt {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('financement_interets_emprunt', 'Paiement des intérêts d’emprunt', 'BQ', '6311', 'Intérêts emprunt {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('financement_interets_courus', 'Intérêts courus non échus à payer', 'OD', '4493', 'Intérêts courus {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('associe_apport_compte_courant', 'Apport en compte courant d’associé', 'BQ', '4463', 'Apport compte courant associé', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('associe_remboursement_compte_courant', 'Remboursement compte courant d’associé', 'BQ', '4463', 'Remboursement compte courant associé', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('capital_souscription', 'Souscription de capital appelé non versé', 'OD', '3462', 'Souscription capital {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('capital_liberation', 'Libération du capital appelé', 'BQ', '3462', 'Libération capital {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('cloture_cca', 'CCA — charge constatée d’avance (compte de charge à adapter)', 'OD', '3491', 'CCA {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('cloture_pca', 'PCA — produit constaté d’avance (compte de produit à adapter)', 'OD', '4491', 'PCA {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('cloture_fnp', 'FNP — facture fournisseur non parvenue (charge à adapter)', 'OD', '4417', 'FNP {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('cloture_fae', 'FAE — facture client à établir (produit à adapter)', 'OD', '3427', 'FAE {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('cloture_client_douteux', 'Reclassement d’un client douteux', 'OD', '3424', 'Client douteux {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('cloture_provision_client', 'Provision pour dépréciation d’une créance client', 'PR', '3942', 'Provision client {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('cloture_reprise_provision_client', 'Reprise de provision sur créance client', 'PR', '3942', 'Reprise provision client {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('cloture_provision_litige', 'Provision pour litige durable', 'PR', '1511', 'Provision litige {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('cloture_reprise_provision_litige', 'Reprise de provision pour litige', 'PR', '1511', 'Reprise provision litige {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('fiscal_acompte_is', 'Paiement d’un acompte sur IS', 'BQ', '3453', 'Acompte IS {ref}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('vente_export', 'Vente de marchandises à l’étranger', 'VT', '7113', 'Facture export — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('avoir_client', 'Avoir client sur vente de marchandises', 'AV', '3421', 'Avoir client — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto, actif)
VALUES ('avoir_fournisseur', 'Avoir fournisseur sur achat de marchandises', 'AV', '4411', 'Avoir fournisseur — réf. {ref} — {tiers}', TRUE)
ON CONFLICT (code) DO UPDATE SET
    libelle = EXCLUDED.libelle,
    journal = EXCLUDED.journal,
    compte_declencheur = EXCLUDED.compte_declencheur,
    libelle_auto = EXCLUDED.libelle_auto,
    actif = TRUE;

-- Remplace uniquement les lignes des modèles gérés par COMPTA.2.
DELETE FROM lignes_modele
WHERE modele_id IN (
    SELECT id FROM modeles_ecritures WHERE code IN ('achat_marchandises', 'achat_matieres', 'achat_fournitures', 'achat_services', 'achat_honoraires', 'achat_loyer', 'achat_transport', 'achat_telephone', 'achat_assurance', 'achat_entretien', 'achat_electricite', 'achat_immo', 'vente_marchandises', 'vente_produits', 'vente_services', 'vente_travaux', 'vente_locations', 'encaissement_client', 'paiement_fournisseur', 'frais_bancaires', 'virement_salaires', 'paiement_tva', 'paiement_cnss', 'paiement_ir', 'paiement_is', 'paie_salaires', 'treso_encaissement_especes', 'treso_paiement_especes', 'treso_banque_vers_caisse', 'treso_caisse_vers_banque', 'effet_client_acceptation', 'effet_client_encaissement', 'effet_fournisseur_acceptation', 'effet_fournisseur_paiement', 'financement_emprunt_recu', 'financement_remboursement_emprunt', 'financement_interets_emprunt', 'financement_interets_courus', 'associe_apport_compte_courant', 'associe_remboursement_compte_courant', 'capital_souscription', 'capital_liberation', 'cloture_cca', 'cloture_pca', 'cloture_fnp', 'cloture_fae', 'cloture_client_douteux', 'cloture_provision_client', 'cloture_reprise_provision_client', 'cloture_provision_litige', 'cloture_reprise_provision_litige', 'fiscal_acompte_is', 'vente_export', 'avoir_client', 'avoir_fournisseur')
);

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '6111', 'Achats de marchandises (groupe A)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_marchandises';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_marchandises';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_marchandises';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '6121', 'Achats de matières premières', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_matieres';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_matieres';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_matieres';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61227', 'Achats de fournitures de bureau', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_fournitures';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_fournitures';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_fournitures';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61263', 'Achats des prestations de service', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_services';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_services';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_services';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61365', 'Honoraires', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_honoraires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_honoraires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_honoraires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61312', 'Locations de constructions', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_loyer';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_loyer';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_loyer';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61425', 'Transports sur achats', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_transport';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_transport';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_transport';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61455', 'Frais de téléphone', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_telephone';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_telephone';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_telephone';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61341', 'Assurances multirisque (vol, incendie, RC)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_assurance';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_assurance';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61331', 'Entretien et réparations des biens immobiliers', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_entretien';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_entretien';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_entretien';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61251', 'Achats de fournitures non stockables (eau, électricité)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_electricite';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_electricite';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4411', 'Fournisseurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_electricite';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '2355', 'Matériel informatique', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_immo';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34551', 'État - TVA récupérable sur immobilisations', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'achat_immo';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4481', 'Dettes sur acquisitions d''immobilisations', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'achat_immo';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3421', 'Clients', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_marchandises';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4455', 'État - TVA facturée', 'credit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'vente_marchandises';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '7111', 'Ventes de marchandises au Maroc', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_marchandises';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3421', 'Clients', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_produits';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4455', 'État - TVA facturée', 'credit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'vente_produits';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '71211', 'Ventes de produits finis', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_produits';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3421', 'Clients', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_services';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4455', 'État - TVA facturée', 'credit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'vente_services';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '71243', 'Prestations de services', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_services';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3421', 'Clients', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_travaux';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4455', 'État - TVA facturée', 'credit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'vente_travaux';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '71241', 'Travaux', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_travaux';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3421', 'Clients', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_locations';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4455', 'État - TVA facturée', 'credit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'vente_locations';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '71271', 'Locations diverses reçues', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_locations';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '5141', 'Banques (solde débiteur)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'encaissement_client';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '3421', 'Clients', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'encaissement_client';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4411', 'Fournisseurs', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_fournisseur';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_fournisseur';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61473', 'Frais et commissions sur services bancaires', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'frais_bancaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '34552', 'État - TVA récupérable sur charges', 'debit',
       FALSE, TRUE, 10.0
FROM modeles_ecritures
WHERE code = 'frais_bancaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'frais_bancaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4432', 'Rémunérations dues au personnel', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'virement_salaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'virement_salaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4456', 'État - TVA due (suivant déclarations)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_tva';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_tva';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4441', 'Caisse Nationale de la Sécurité Sociale', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_cnss';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_cnss';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '44525', 'État, IGR', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_ir';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_ir';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4453', 'État - impôts sur les résultats', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_is';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paiement_is';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '6171', 'Rémunérations du personnel', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paie_salaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '6174', 'Charges sociales', 'debit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paie_salaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '4441', 'Caisse Nationale de la Sécurité Sociale', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paie_salaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 4, '44525', 'État, IGR', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paie_salaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 5, '4432', 'Rémunérations dues au personnel', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'paie_salaires';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '5161', 'Caisses', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'treso_encaissement_especes';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '3421', 'Clients', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'treso_encaissement_especes';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4411', 'Fournisseurs', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'treso_paiement_especes';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5161', 'Caisses', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'treso_paiement_especes';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '5161', 'Caisses', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'treso_banque_vers_caisse';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'treso_banque_vers_caisse';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '5141', 'Banques (solde débiteur)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'treso_caisse_vers_banque';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5161', 'Caisses', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'treso_caisse_vers_banque';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3425', 'Clients - effets à recevoir', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'effet_client_acceptation';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '3421', 'Clients', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'effet_client_acceptation';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '5141', 'Banques (solde débiteur)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'effet_client_encaissement';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '3425', 'Clients - effets à recevoir', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'effet_client_encaissement';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4411', 'Fournisseurs', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'effet_fournisseur_acceptation';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4415', 'Fournisseurs - effets à payer', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'effet_fournisseur_acceptation';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4415', 'Fournisseurs - effets à payer', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'effet_fournisseur_paiement';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'effet_fournisseur_paiement';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '5141', 'Banques (solde débiteur)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'financement_emprunt_recu';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '1481', 'Emprunts auprès des établissements de crédit', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'financement_emprunt_recu';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '1481', 'Emprunts auprès des établissements de crédit', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'financement_remboursement_emprunt';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'financement_remboursement_emprunt';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '6311', 'Intérêts des emprunts et dettes', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'financement_interets_emprunt';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'financement_interets_emprunt';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '6311', 'Intérêts des emprunts et dettes', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'financement_interets_courus';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4493', 'Intérêts courus et non échus à payer', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'financement_interets_courus';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '5141', 'Banques (solde débiteur)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'associe_apport_compte_courant';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4463', 'Comptes courants des associés créditeurs', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'associe_apport_compte_courant';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4463', 'Comptes courants des associés créditeurs', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'associe_remboursement_compte_courant';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'associe_remboursement_compte_courant';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3462', 'Actionnaires - capital souscrit et appelé non versé', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'capital_souscription';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '1111', 'Capital social', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'capital_souscription';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '5141', 'Banques (solde débiteur)', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'capital_liberation';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '3462', 'Actionnaires - capital souscrit et appelé non versé', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'capital_liberation';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3491', 'Charges constatées d''avance', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_cca';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '61312', 'Compte de charge à adapter', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_cca';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '71243', 'Compte de produit à adapter', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_pca';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4491', 'Produits constatés d''avance', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_pca';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61263', 'Compte de charge à adapter', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_fnp';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4417', 'Fournisseurs - factures non parvenues', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_fnp';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3427', 'Clients - factures à établir et créances sur travaux non encore facturés', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_fae';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '71243', 'Compte de produit à adapter', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_fae';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3424', 'Clients douteux ou litigieux', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_client_douteux';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '3421', 'Clients', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_client_douteux';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '6196', 'Dotations d''exploitation aux provisions pour dépréciations de l''actif circulant', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_provision_client';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '3942', 'Provisions pour dépréciation des clients et comptes rattachés', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_provision_client';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3942', 'Provisions pour dépréciation des clients et comptes rattachés', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_reprise_provision_client';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '7196', 'Reprises sur provisions pour dépréciation de l''actif circulant', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_reprise_provision_client';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '61955', 'DEP pour risques et charges durables', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_provision_litige';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '1511', 'Provisions pour litiges', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_provision_litige';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '1511', 'Provisions pour litiges', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_reprise_provision_litige';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '7195', 'Reprises sur provisions pour risques et charges', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'cloture_reprise_provision_litige';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3453', 'Acomptes sur impôts sur les résultats', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'fiscal_acompte_is';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '5141', 'Banques (solde débiteur)', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'fiscal_acompte_is';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '3421', 'Clients', 'debit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_export';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '7113', 'Ventes de marchandises à l''étranger', 'credit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'vente_export';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '7111', 'Ventes de marchandises au Maroc', 'debit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'avoir_client';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '4455', 'État - TVA facturée', 'debit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'avoir_client';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '3421', 'Clients', 'credit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'avoir_client';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 1, '4411', 'Fournisseurs', 'debit',
       FALSE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'avoir_fournisseur';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 2, '6111', 'Achats de marchandises (groupe A)', 'credit',
       TRUE, FALSE, NULL
FROM modeles_ecritures
WHERE code = 'avoir_fournisseur';

INSERT INTO lignes_modele
    (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT id, 3, '34552', 'État - TVA récupérable sur charges', 'credit',
       FALSE, TRUE, 20.0
FROM modeles_ecritures
WHERE code = 'avoir_fournisseur';


-- Contrôle défensif : aucun modèle actif COMPTA.2 ne doit rester vide.
UPDATE modeles_ecritures m
SET actif = FALSE
WHERE m.code IN ('achat_marchandises', 'achat_matieres', 'achat_fournitures', 'achat_services', 'achat_honoraires', 'achat_loyer', 'achat_transport', 'achat_telephone', 'achat_assurance', 'achat_entretien', 'achat_electricite', 'achat_immo', 'vente_marchandises', 'vente_produits', 'vente_services', 'vente_travaux', 'vente_locations', 'encaissement_client', 'paiement_fournisseur', 'frais_bancaires', 'virement_salaires', 'paiement_tva', 'paiement_cnss', 'paiement_ir', 'paiement_is', 'paie_salaires', 'treso_encaissement_especes', 'treso_paiement_especes', 'treso_banque_vers_caisse', 'treso_caisse_vers_banque', 'effet_client_acceptation', 'effet_client_encaissement', 'effet_fournisseur_acceptation', 'effet_fournisseur_paiement', 'financement_emprunt_recu', 'financement_remboursement_emprunt', 'financement_interets_emprunt', 'financement_interets_courus', 'associe_apport_compte_courant', 'associe_remboursement_compte_courant', 'capital_souscription', 'capital_liberation', 'cloture_cca', 'cloture_pca', 'cloture_fnp', 'cloture_fae', 'cloture_client_douteux', 'cloture_provision_client', 'cloture_reprise_provision_client', 'cloture_provision_litige', 'cloture_reprise_provision_litige', 'fiscal_acompte_is', 'vente_export', 'avoir_client', 'avoir_fournisseur')
  AND (SELECT COUNT(*) FROM lignes_modele l WHERE l.modele_id = m.id) < 2;

COMMIT;
