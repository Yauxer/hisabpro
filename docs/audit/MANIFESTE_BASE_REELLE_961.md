# Manifeste détecté de la base réelle — 30 octobre 2026 (lot 961)

Méthode : lecture du **catalogue PostgreSQL uniquement** (noms de tables, colonnes, fonctions, triggers, contraintes), session `default_transaction_read_only=on`, rôle applicatif. **Aucune ligne de donnée lue, aucune écriture.** Pour chaque script, les objets qu'il crée sont recherchés ; un script de droits seuls n'est pas déterminable ainsi.

| Statut | Nombre |
|---|---|
| présente | 62 |
| ABSENTE | 39 |
| indéterminable (droits seulement) | 20 |
| PARTIELLE | 6 |

## Scripts absents ou partiels

| Script | Statut | Objets trouvés / attendus | Exemples manquants |
|---|---|---|---|
| `014_ecriture_metadata.sql` | PARTIELLE | 5/6 | trigger trg_hisabpro_numero_ecriture |
| `071_liasse_balances_preparation.sql` | PARTIELLE | 1/3 | fonction hisabpro_balance_preparation_immuable, trigger trg_balance_preparation_immuable |
| `072_integrite_ecritures_definitives.sql` | PARTIELLE | 1/3 | fonction hisabpro_verifier_equilibre_definitif, trigger trg_hisabpro_equilibre_definitif |
| `073_archives_fiscales_permissions.sql` | ABSENTE | 0/1 | trigger trg_hisabpro_liasse_archive_truncate |
| `074_archives_comptables_immutables.sql` | ABSENTE | 0/4 | fonction hisabpro_livre_inventaire_immutable, trigger trg_livre_inventaire_immutable |
| `075_complements_auxiliaires_structure.sql` | PARTIELLE | 6/7 | trigger trg_ligne_aux_complements_no_truncate |
| `078_factures_definitives_suppression.sql` | ABSENTE | 0/2 | fonction hisabpro_guard_suppression_facture_definitive, trigger trg_facture_definitive_no_delete |
| `083_ras_reglements.sql` | ABSENTE | 0/10 | table ras_reglement_captures, table ras_reglement_annulations |
| `084_rapprochement_ventilations.sql` | PARTIELLE | 1/11 | table rapprochement_ventilations, fonction hisabpro_guard_rapprochement_ventilation |
| `094_protection_parametres_tva_clotures.sql` | ABSENTE | 0/3 | fonction hisabpro_tva_exercice_clos, fonction hisabpro_proteger_parametres_tva_clotures |
| `095_registre_avances_salaries.sql` | ABSENTE | 0/6 | table grh_avances_affectations, fonction hisabpro_proteger_affectation_avance |
| `096_verrou_parametres_tva.sql` | ABSENTE | 0/1 | fonction hisabpro_proteger_parametres_tva_clotures |
| `097_verrou_tva_trace_cloture.sql` | ABSENTE | 0/6 | fonction hisabpro_verrou_tva_cloture, fonction hisabpro_proteger_parametres_tva_clotures |
| `098_verrou_journal_cloture.sql` | ABSENTE | 0/5 | fonction hisabpro_verifier_journal_ouvert, fonction hisabpro_verrou_entete_journal |
| `099_ras_tva_details.sql` | ABSENTE | 0/5 | table ras_tva_reglement_details, fonction hisabpro_ras_tva_details_liens |
| `100_reprises_provisions.sql` | ABSENTE | 0/15 | table reprises_provisions, table reprises_provisions_annulations |
| `101_societes_liees.sql` | ABSENTE | 0/6 | table societes_liees, table societes_liees_retraits |
| `102_factures_correspondantes.sql` | ABSENTE | 0/5 | table factures_correspondantes, fonction hisabpro_factures_correspondantes_controle |
| `103_ras_rapprochements_versement.sql` | ABSENTE | 0/8 | table ras_tva_rapprochements, table ras_tva_rapprochement_retraits |
| `104_liasse_balance_documents.sql` | ABSENTE | 0/6 | table liasse_balance_documents, fonction hisabpro_balance_document_liens |
| `105_personnel_habilitations.sql` | ABSENTE | 0/8 | table personnel_acces_societes, table personnel_habilitations |
| `106_personnel_dossiers_versions.sql` | ABSENTE | 0/11 | table personnel_dossiers, table personnel_demandes |
| `107_personnel_workflow.sql` | ABSENTE | 0/12 | table personnel_demandes_details, colonne personnel_dossiers.beneficiaire_sans_compte_confirme |
| `108_personnel_rejet_auteur_inactif.sql` | ABSENTE | 0/1 | fonction hisabpro_personnel_conserver_versions |
| `110_personnel_regimes_contrat.sql` | ABSENTE | 0/4 | colonne personnel_contrats_versions.regime_amo, colonne personnel_contrats_versions.regime_retraite |
| `111_personnel_coffre.sql` | ABSENTE | 0/5 | table personnel_coffre_politiques, table personnel_coffre_pieces |
| `112_personnel_banque_chiffree.sql` | ABSENTE | 0/5 | table personnel_banque_versions, fonction hisabpro_personnel_banque_immuable |
| `113_paie_catalogue.sql` | ABSENTE | 0/6 | table paie_rubriques, table paie_rubrique_versions |
| `114_paie_variables.sql` | ABSENTE | 0/5 | table paie_variables, table paie_variables_evenements |
| `115_paie_campagnes_brut.sql` | ABSENTE | 0/5 | table paie_campagnes, table paie_simulations_brut |
| `116_paie_referentiel_social.sql` | ABSENTE | 0/6 | table paie_branches_sociales, table paie_branche_sociale_versions |
| `117_paie_simulations_sociales.sql` | ABSENTE | 0/3 | table paie_simulations_sociales, trigger trg_paie_social_snapshot |
| `118_paie_controles_ir_annuels.sql` | ABSENTE | 0/3 | table paie_controles_ir_annuels, trigger trg_paie_ir_annuel |
| `119_paie_qualifications_fiscales.sql` | ABSENTE | 0/2 | fonction hisabpro_paie_qualification_ir119, trigger trg_paie_ir_qualification119 |
| `120_paie_preparations_fiscales.sql` | ABSENTE | 0/3 | table paie_preparations_fiscales, trigger trg_paie_bases_fiscales |
| `121_paie_frais_annuels.sql` | ABSENTE | 0/7 | table paie_controles_frais_annuels, table paie_controle_frais_sources |
| `122_paie_ir_sources_annuelles.sql` | ABSENTE | 0/4 | table paie_ir_sources_annuelles, fonction hisabpro_paie_ir_source122 |
| `123_paie_rattachement_revenus.sql` | ABSENTE | 0/2 | fonction hisabpro_paie_reference123, trigger aaa_paie_reference123 |
| `124_paie_controles_mensuels.sql` | ABSENTE | 0/4 | table paie_controles_mensuels, fonction hisabpro_paie_mensuel124 |
| `125_factures_copies_conservees.sql` | ABSENTE | 0/4 | table factures_copies_conservees, fonction hisabpro_facture_copie125 |
| `126_avoirs_compensations_tva.sql` | ABSENTE | 0/2 | colonne utilisations_avoirs.date_acceptation_compensation, contrainte ck_utilisations_compensation126 |
| `127_reglements_annulation_effective.sql` | ABSENTE | 0/3 | colonne reglements.date_annulation_effective, contrainte ck_reglements_annulation_effective127 |
| `128_registre_migrations.sql` | ABSENTE | 0/1 | table hisabpro_migrations |
| `129_declarations_tva_deposees.sql` | ABSENTE | 0/3 | table declarations_tva_deposees, fonction hisabpro_proteger_declaration_tva_deposee |
| `130_lettrage_partiel.sql` | PARTIELLE | 1/2 | colonne lettrages_comptables.partiel |

## Scripts non déterminables par le catalogue (droits uniquement)

`016_libelles_justificatifs.sql`, `021b_fiscalite_permissions.sql`, `034b_recouvrement_permissions.sql`, `050_balance_grand_livre_final.sql`, `058_droits_plan_comptable.sql`, `064_fiscal_retraitement_compte_source.sql`, `065_reparation_liquidations_is_reference_acomptes.sql`, `067_reparation_fec_historique_sure.sql`, `069_fec_complements_historiques_saisie_manuelle.sql`, `070_reparation_is_cloture_historique_2026.sql`, `077_permissions_cycle_facturation.sql`, `079_permissions_suppression_brouillons.sql`, `085_permissions_documents_commerciaux.sql`, `086_permissions_acomptes_avoirs.sql`, `087_permissions_banque_releves.sql`, `088_permissions_cycle_annuel.sql`, `090_permissions_multi_societes.sql`, `091_permissions_affectation_resultat.sql`, `092_modeles_avances_personnel.sql`, `093_permissions_parametres_tva.sql`

## Conséquences

- La base réelle est au niveau d'environ 070, avec des compléments isolés (089 notamment). Le code actuel, et pas seulement 957/959, n'y a jamais été exécuté.
- Deux protections d'intégrité manquent : 072 (équilibre des écritures définitives) n'est que partielle et 078 (refus de supprimer une facture définitive) est absente.
- Le rôle applicatif ne peut pas lire `decisions_affectation_resultat` (droits voulus) : une sauvegarde complète exige le rôle de migration ou d'administration.
- La mise à niveau doit appliquer environ quarante scripts dans l'ordre (dont Personnel/Paie 105–124 si ce module est retenu), d'abord sur une copie complète restaurée, avec `ops/migrations_hisabpro.py` (constater les présents ci-dessus, puis appliquer).
- Les scripts « partiels » doivent être examinés un par un : il peut s'agir d'une version antérieure du même script, ou d'un objet renommé depuis.

Aucune modification de la base réelle n'a été faite. Une copie de données a été refusée par le contrôle de permissions (données personnelles) ; elle reste à décider par l'utilisateur.
