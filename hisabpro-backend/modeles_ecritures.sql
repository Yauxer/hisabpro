-- ============================================================
-- HisabPro — Modèles d'écritures comptables
-- Basé sur le Guide des Écritures Comptables Marocain
-- À exécuter dans pgAdmin après redémarrage du backend
-- ============================================================

-- ── ACHATS ───────────────────────────────────────────────────────────────────

-- Achat de marchandises (6111 → 34552 + 4411)
INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto) VALUES
('achat_marchandises',   'Achat de marchandises',              'AC', '6111', 'Facture fournisseur — réf. {ref} — {tiers}'),
('achat_matieres',       'Achat de matières premières',        'AC', '6121', 'Facture fournisseur — réf. {ref} — {tiers}'),
('achat_fournitures',    'Achat de fournitures de bureau',     'AC', '61227','Facture fournisseur — réf. {ref} — {tiers}'),
('achat_services',       'Achat de prestations de services',   'AC', '61263','Facture fournisseur — réf. {ref} — {tiers}'),
('achat_honoraires',     'Honoraires',                         'AC', '61365','Facture fournisseur — réf. {ref} — {tiers}'),
('achat_loyer',          'Loyer - Location de constructions',  'AC', '61312','Facture fournisseur — réf. {ref} — {tiers}'),
('achat_transport',      'Transport sur achats',               'AC', '61425','Facture fournisseur — réf. {ref} — {tiers}'),
('achat_telephone',      'Frais de téléphone',                 'AC', '61455','Facture fournisseur — réf. {ref} — {tiers}'),
('achat_assurance',      'Assurances multirisques',            'AC', '61341','Facture fournisseur — réf. {ref} — {tiers}'),
('achat_entretien',      'Entretien et réparations',           'AC', '61331','Facture fournisseur — réf. {ref} — {tiers}'),
('achat_electricite',    'Eau et électricité',                 'AC', '61251','Facture fournisseur — réf. {ref} — {tiers}'),
('achat_immo',           'Acquisition immobilisation',         'AC', '2355', 'Facture fournisseur — réf. {ref} — {tiers}')
ON CONFLICT (code) DO NOTHING;

-- ── VENTES ───────────────────────────────────────────────────────────────────
INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto) VALUES
('vente_marchandises',   'Vente de marchandises au Maroc',     'VT', '7111', 'Facture client — réf. {ref} — {tiers}'),
('vente_produits',       'Vente de produits finis',            'VT', '71211','Facture client — réf. {ref} — {tiers}'),
('vente_services',       'Vente de prestations de services',   'VT', '71243','Facture client — réf. {ref} — {tiers}'),
('vente_travaux',        'Vente de travaux',                   'VT', '71241','Facture client — réf. {ref} — {tiers}'),
('vente_locations',      'Locations diverses reçues',          'VT', '71271','Facture client — réf. {ref} — {tiers}')
ON CONFLICT (code) DO NOTHING;

-- ── BANQUE ────────────────────────────────────────────────────────────────────
INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto) VALUES
('encaissement_client',  'Encaissement créance client',        'BQ', '5141', 'Règlement {tiers}'),
('paiement_fournisseur', 'Paiement fournisseur',               'BQ', '4411', 'Règlement {tiers}'),
('frais_bancaires',      'Frais et commissions bancaires',     'BQ', '61473','Agios {ref}'),
('virement_salaires',    'Virement salaires',                  'BQ', '4432', 'Salaires {ref}'),
('paiement_tva',         'Paiement TVA',                       'BQ', '4456', 'TVA {ref}'),
('paiement_cnss',        'Paiement CNSS/AMO',                  'BQ', '4441', 'CNSS {ref}'),
('paiement_ir',          'Paiement IGR/IR',                    'BQ', '44525','IGR {ref}'),
('paiement_is',          'Paiement IS',                        'BQ', '4453', 'IS {ref}')
ON CONFLICT (code) DO NOTHING;

-- ── PAIE ──────────────────────────────────────────────────────────────────────
INSERT INTO modeles_ecritures (code, libelle, journal, compte_declencheur, libelle_auto) VALUES
('paie_salaires',        'Écriture de paie mensuelle',         'OD', '6171', 'Salaires {ref}')
ON CONFLICT (code) DO NOTHING;

-- ── LIGNES DES MODÈLES ────────────────────────────────────────────────────────

-- Achat de marchandises : 6111 (D) + 34552 TVA (D) + 4411 (C)
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '6111',  'Achats de marchandises',                  'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_marchandises'
UNION ALL
SELECT m.id, 2, '34552', 'État — TVA récupérable sur charges 20%',  'debit',  false, true,  20   FROM modeles_ecritures m WHERE m.code = 'achat_marchandises'
UNION ALL
SELECT m.id, 3, '4411',  'Fournisseurs',                            'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_marchandises'
ON CONFLICT DO NOTHING;

-- Achat matières premières
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '6121',  'Achats de matières premières',            'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_matieres'
UNION ALL
SELECT m.id, 2, '34552', 'État — TVA récupérable sur charges 20%',  'debit',  false, true,  20   FROM modeles_ecritures m WHERE m.code = 'achat_matieres'
UNION ALL
SELECT m.id, 3, '4411',  'Fournisseurs',                            'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_matieres'
ON CONFLICT DO NOTHING;

-- Achat fournitures bureau
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '61227', 'Achats de fournitures de bureau',         'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_fournitures'
UNION ALL
SELECT m.id, 2, '34552', 'État — TVA récupérable sur charges 20%',  'debit',  false, true,  20   FROM modeles_ecritures m WHERE m.code = 'achat_fournitures'
UNION ALL
SELECT m.id, 3, '4411',  'Fournisseurs',                            'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_fournitures'
ON CONFLICT DO NOTHING;

-- Achat services/honoraires
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '61263', 'Achats de prestations de services',       'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_services'
UNION ALL
SELECT m.id, 2, '34552', 'État — TVA récupérable sur charges 20%',  'debit',  false, true,  20   FROM modeles_ecritures m WHERE m.code = 'achat_services'
UNION ALL
SELECT m.id, 3, '4411',  'Fournisseurs',                            'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_services'
ON CONFLICT DO NOTHING;

-- Honoraires
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '61365', 'Honoraires',                              'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_honoraires'
UNION ALL
SELECT m.id, 2, '34552', 'État — TVA récupérable sur charges 20%',  'debit',  false, true,  20   FROM modeles_ecritures m WHERE m.code = 'achat_honoraires'
UNION ALL
SELECT m.id, 3, '4411',  'Fournisseurs',                            'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_honoraires'
ON CONFLICT DO NOTHING;

-- Loyer
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '61312', 'Location de constructions',               'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_loyer'
UNION ALL
SELECT m.id, 2, '34552', 'État — TVA récupérable sur charges 20%',  'debit',  false, true,  20   FROM modeles_ecritures m WHERE m.code = 'achat_loyer'
UNION ALL
SELECT m.id, 3, '4411',  'Fournisseurs',                            'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_loyer'
ON CONFLICT DO NOTHING;

-- Téléphone
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '61455', 'Frais de téléphone',                      'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_telephone'
UNION ALL
SELECT m.id, 2, '34552', 'État — TVA récupérable sur charges 20%',  'debit',  false, true,  20   FROM modeles_ecritures m WHERE m.code = 'achat_telephone'
UNION ALL
SELECT m.id, 3, '4411',  'Fournisseurs',                            'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_telephone'
ON CONFLICT DO NOTHING;

-- Eau/Électricité
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '61251', 'Eau et électricité',                      'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_electricite'
UNION ALL
SELECT m.id, 2, '34552', 'État — TVA récupérable sur charges 20%',  'debit',  false, true,  20   FROM modeles_ecritures m WHERE m.code = 'achat_electricite'
UNION ALL
SELECT m.id, 3, '4411',  'Fournisseurs',                            'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_electricite'
ON CONFLICT DO NOTHING;

-- Acquisition immobilisation (matériel informatique)
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '2355',  'Matériel informatique',                   'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_immo'
UNION ALL
SELECT m.id, 2, '34551', 'État — TVA récupérable sur immobilisations 20%', 'debit', false, true, 20 FROM modeles_ecritures m WHERE m.code = 'achat_immo'
UNION ALL
SELECT m.id, 3, '1486',  'Fournisseurs d''immobilisations',         'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'achat_immo'
ON CONFLICT DO NOTHING;

-- Vente marchandises : 3421 (D) + 4455 TVA (C) + 7111 (C)
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '3421',  'Clients',                                 'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'vente_marchandises'
UNION ALL
SELECT m.id, 2, '4455',  'État — TVA facturée 20%',                 'credit', false, true,  20   FROM modeles_ecritures m WHERE m.code = 'vente_marchandises'
UNION ALL
SELECT m.id, 3, '7111',  'Ventes de marchandises au Maroc',         'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'vente_marchandises'
ON CONFLICT DO NOTHING;

-- Vente services
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '3421',  'Clients',                                 'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'vente_services'
UNION ALL
SELECT m.id, 2, '4455',  'État — TVA facturée 20%',                 'credit', false, true,  20   FROM modeles_ecritures m WHERE m.code = 'vente_services'
UNION ALL
SELECT m.id, 3, '71243', 'Ventes de prestations de services',       'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'vente_services'
ON CONFLICT DO NOTHING;

-- Encaissement client : 5141 (D) + 3421 (C)
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '5141',  'Banques',                                 'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'encaissement_client'
UNION ALL
SELECT m.id, 2, '3421',  'Clients',                                 'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'encaissement_client'
ON CONFLICT DO NOTHING;

-- Paiement fournisseur : 4411 (D) + 5141 (C)
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '4411',  'Fournisseurs',                            'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'paiement_fournisseur'
UNION ALL
SELECT m.id, 2, '5141',  'Banques',                                 'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'paiement_fournisseur'
ON CONFLICT DO NOTHING;

-- Frais bancaires : 61473 (D) + 34552 (D) + 5141 (C)
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '61473', 'Frais et commissions bancaires',          'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'frais_bancaires'
UNION ALL
SELECT m.id, 2, '34552', 'État — TVA récupérable 10%',              'debit',  false, true,  10   FROM modeles_ecritures m WHERE m.code = 'frais_bancaires'
UNION ALL
SELECT m.id, 3, '5141',  'Banques',                                 'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'frais_bancaires'
ON CONFLICT DO NOTHING;

-- Paie salaires
INSERT INTO lignes_modele (modele_id, ordre, compte, libelle, sens, est_principal, est_tva, taux_tva)
SELECT m.id, 1, '6171',  'Appointements et salaires',               'debit',  true,  false, NULL::float FROM modeles_ecritures m WHERE m.code = 'paie_salaires'
UNION ALL
SELECT m.id, 2, '6174',  'Charges patronales CNSS/AMO',             'debit',  false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'paie_salaires'
UNION ALL
SELECT m.id, 3, '4441',  'CNSS/AMO à payer',                        'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'paie_salaires'
UNION ALL
SELECT m.id, 4, '4452',  'État — IGR retenu',                       'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'paie_salaires'
UNION ALL
SELECT m.id, 5, '4432',  'Rémunérations dues au personnel',         'credit', false, false, NULL::float FROM modeles_ecritures m WHERE m.code = 'paie_salaires'
ON CONFLICT DO NOTHING;

-- Vérification
SELECT m.code, m.libelle, COUNT(l.id) as nb_lignes
FROM modeles_ecritures m
LEFT JOIN lignes_modele l ON l.modele_id = m.id
GROUP BY m.id, m.code, m.libelle
ORDER BY m.code;
