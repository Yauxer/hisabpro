# Sauvegarde et restauration de l’installation consolidée084

Commande : `hisabpro-backend/.venv/Scripts/python.exe Test/recette_restauration_consolidee_084.py`.

Le rapport176 reste historique et inchange. Socle ORM puis64SQL candidats001-073, puis074 à082 et rejeu de ces neuf compléments uniquement. Les rapports176/209 restent historiques. Aucune URL externe acceptee, aucun .env lu, aucun traitement065/067/068/070 ni init/seedpaie. Tables metier verifiees vides avant/apres chaque SQL. Registre SHA local supprime avec le cluster.

## Resultats exacts

```json
{
  "date_utc": "2026-10-15T00:24:54.787285+00:00",
  "statut": "installation_084_restauree_schema_donnees_acl_limitees_valides",
  "fichier_en_cours": "084_rapprochement_ventilations.sql",
  "erreur": null,
  "appliquees": [
    {
      "fichier": "001_accounting_integrity.sql",
      "phase": "base_001_073",
      "sha256": "e65806463fd4604e3c4b8d98017e54886924ad9414eb9c4eeb9a3d3185716fcd"
    },
    {
      "fichier": "002_tva_exigibilite.sql",
      "phase": "base_001_073",
      "sha256": "6e95caf5b97ee19bc3a0c9dcf7440ccb76a69e642a75302d4e3a3c8e37852f25"
    },
    {
      "fichier": "003_tva_02b.sql",
      "phase": "base_001_073",
      "sha256": "5ca5e81c445989dbdac7d7c0ad8e067ea6facca14041a2c1ba495314356d9b92"
    },
    {
      "fichier": "004_reglement_date_effective.sql",
      "phase": "base_001_073",
      "sha256": "b67c44be9d9e33dc3726ed3dc2fed6a2ff4376581d4aa4a0c2067d5d385ad4f8"
    },
    {
      "fichier": "005_immobilisations_cycle.sql",
      "phase": "base_001_073",
      "sha256": "842c326a524145807c42348bc47cf712534a0b88ce00f7d36d95eaa0232ea047"
    },
    {
      "fichier": "006_immobilisations_fournisseur_tiers.sql",
      "phase": "base_001_073",
      "sha256": "909bedf1f635166c19e323992b82a77653c0797a6d55dd562ade154983a38aad"
    },
    {
      "fichier": "007_cloture_inventaire.sql",
      "phase": "base_001_073",
      "sha256": "4381140e9b43f663f8ec252a863ebc349a0f58842ead2d029cfe7617d50d9c72"
    },
    {
      "fichier": "008_exercices_periodes.sql",
      "phase": "base_001_073",
      "sha256": "d85a725fd53d189acafafb414177adf1667e05b632723609293653ab9ec86d4e"
    },
    {
      "fichier": "009_livre_inventaire.sql",
      "phase": "base_001_073",
      "sha256": "c3d8456d7b846da75ed68241071511d59defb35eb616c1df26b96434fdb773e4"
    },
    {
      "fichier": "010_stock_cloture.sql",
      "phase": "base_001_073",
      "sha256": "2b8935717af89f2c2e03d4480ee713c44f2b937694e51613bbb4617582fde0ca"
    },
    {
      "fichier": "011_livre_inventaire_v2.sql",
      "phase": "base_001_073",
      "sha256": "29a07478d9051dea0b0d3a45b3a26b9cb53c662567b082f55c0598e9d2e19132"
    },
    {
      "fichier": "012_stock_movement_engine.sql",
      "phase": "base_001_073",
      "sha256": "e84feb0a5060a851d9b434cebe2992f5254ef8e4c12a11a705601f6145b800d5"
    },
    {
      "fichier": "013_audit_ecritures.sql",
      "phase": "base_001_073",
      "sha256": "95fa48ca355408c458a7d5574f1ca4d92f2ead8d08c7a039c42351ba0a06df84"
    },
    {
      "fichier": "014_ecriture_metadata.sql",
      "phase": "base_001_073",
      "sha256": "8317520d51c7564e5848843d0d4d0951b8a54767e14cf6b8b057ec71912afcbb"
    },
    {
      "fichier": "015_ecriture_numero_scope.sql",
      "phase": "base_001_073",
      "sha256": "3c1b838fd3ce055d28b6b117f874fe778f08fba8e2d5923b4d40f0732cc65de9"
    },
    {
      "fichier": "016_libelles_justificatifs.sql",
      "phase": "base_001_073",
      "sha256": "be474458e1fcd7aeaf65d96316e55ce671c01217f745103819146b4e20890493"
    },
    {
      "fichier": "017_ecriture_numero_large_sequence.sql",
      "phase": "base_001_073",
      "sha256": "930cc616fbaaf3ec6950edee1d4b5432ff9c860bafa3be531abd5b77ac6e2ba8"
    },
    {
      "fichier": "018_numero_ecriture_a_validation.sql",
      "phase": "base_001_073",
      "sha256": "e9a5f8d7ea729dfd9d91b41461d0ba452268137ae926624f06cb869528cc842d"
    },
    {
      "fichier": "019_journal_cloture_dedie.sql",
      "phase": "base_001_073",
      "sha256": "ba5c3bfca5a24e894c07257045db2533519edc55dffa0a0f8bf15ce92227549c"
    },
    {
      "fichier": "021_fiscalite_is.sql",
      "phase": "base_001_073",
      "sha256": "15b99b88ea304bfdc66bcdefd1adfb90c31c02c8c20e55e4d693e26a56e0a312"
    },
    {
      "fichier": "021b_fiscalite_permissions.sql",
      "phase": "base_001_073",
      "sha256": "84a34e96676e0171c2ec1bdeab998cd6ba8156332f976a7db40c33ffa5c28384"
    },
    {
      "fichier": "022_deficits_fiscaux_millesimes.sql",
      "phase": "base_001_073",
      "sha256": "16615ca04096d94e151881ab32fae53751096dd7ab1e2f19b5812791700993b6"
    },
    {
      "fichier": "023_cotisation_minimale.sql",
      "phase": "base_001_073",
      "sha256": "f8647b92776777ab9d52094b98cbfa76fa1bd971f6a8c93c2981fe67956acff1"
    },
    {
      "fichier": "024_acomptes_liquidation_is.sql",
      "phase": "base_001_073",
      "sha256": "be6131c72f83081f771f17e89b05e015e20efb9aaa3667f9cb5a0d51808d9541"
    },
    {
      "fichier": "025_css_credits_is.sql",
      "phase": "base_001_073",
      "sha256": "3f788f58c1acc922dbc54790dc53a35486b69a5f100b7beaf6909e503707c36b"
    },
    {
      "fichier": "026_etic_exercice.sql",
      "phase": "base_001_073",
      "sha256": "19aac6bfa2e528833398e9b1fc997e5dabb208181851d84e0dee705f4f169612"
    },
    {
      "fichier": "027_liasse_fiscale_archive.sql",
      "phase": "base_001_073",
      "sha256": "24e1ed1590dec9b333d36c660285ee159ccb854a0b5637326916d50e76b35431"
    },
    {
      "fichier": "028_facturation_fondations.sql",
      "phase": "base_001_073",
      "sha256": "a518cce1d42fa33aaf6a59fa8fdf551e297d905f3ae99a5f3892993f6c1f5b72"
    },
    {
      "fichier": "029_factures_validation.sql",
      "phase": "base_001_073",
      "sha256": "b4f15b7c3ac40adad6247107f68cacf0df4c9f6e6770f58ff20915113e75caab"
    },
    {
      "fichier": "030_facturation_durcissement.sql",
      "phase": "base_001_073",
      "sha256": "324b73786c81fcb3cc17f4abbbc86859c17c941cbf61e6d2b8cea48a3760b069"
    },
    {
      "fichier": "031_avoirs_retours.sql",
      "phase": "base_001_073",
      "sha256": "09eea9c8f337ec2dc299cb120486a7451efe5771f4181fea1513c37dff34aa5b"
    },
    {
      "fichier": "032_compta_mapping.sql",
      "phase": "base_001_073",
      "sha256": "8bfee4d9d9c451cbcfd8ac224a64c63b574dfc6262661b0e641c168ec128fafa"
    },
    {
      "fichier": "033_conformite_tva_frais.sql",
      "phase": "base_001_073",
      "sha256": "d84e647bdc46f14aba8ebace3533886b800c79e5a317a749db6c1b2db79e3e56"
    },
    {
      "fichier": "034_recouvrement.sql",
      "phase": "base_001_073",
      "sha256": "e602eead590310d7991e5be586fc086c641b268539e45d27f6b5f1fc312d4fc6"
    },
    {
      "fichier": "034b_recouvrement_permissions.sql",
      "phase": "base_001_073",
      "sha256": "344e4b21a1a7bd21dc0035194e0b06e8ab8e62e767f4463bd3d186b4d36e677a"
    },
    {
      "fichier": "035_echeanciers_acomptes.sql",
      "phase": "base_001_073",
      "sha256": "43b1400572f6d36849deb1ba200305ba0e9d354211eec53286badaf273752ed5"
    },
    {
      "fichier": "036_production_hardening.sql",
      "phase": "base_001_073",
      "sha256": "60d70facc2faf9bc05dbd84c5709ee07a0774d6ac1c5e3efa25fe90912ffead5"
    },
    {
      "fichier": "037_compta2_modeles_ecritures.sql",
      "phase": "base_001_073",
      "sha256": "daf4b99a9fca8cc606c15161666d7015b857f8ca246fe37fbfbdec822708dc25"
    },
    {
      "fichier": "038_compta3_avis24_durcissement.sql",
      "phase": "base_001_073",
      "sha256": "c1013f796409c6e3967261e1242b7ad57fb65b5f93faf8952577ef8422b4751b"
    },
    {
      "fichier": "039_compta4_justificatifs_fec.sql",
      "phase": "base_001_073",
      "sha256": "99a5ea82784f170cdf867d8d2b890bdb2cf3866c88f9438a500a639f173b9be0"
    },
    {
      "fichier": "040_factB_identites_dates.sql",
      "phase": "base_001_073",
      "sha256": "1540b1e15190fcc85703558a645c16894b9cfe48d0dd451b235d59a02a07beab"
    },
    {
      "fichier": "041_factC_cycle_documentaire.sql",
      "phase": "base_001_073",
      "sha256": "27e65a40d47da745bf396f79098634ac7c995d95d902810610ff547d8ce6f31f"
    },
    {
      "fichier": "042_factD_reglements_delais.sql",
      "phase": "base_001_073",
      "sha256": "6ad54b5957795b7f616d7091df42b97ed94426d6294f62da444bff4f70ada35a"
    },
    {
      "fichier": "043_factE_audit_identifiants.sql",
      "phase": "base_001_073",
      "sha256": "8bb2fc3d08e21597341d49a81ef9356e839c964534d70922ce83cf9daba2ae9c"
    },
    {
      "fichier": "044_factF_delais_paiement.sql",
      "phase": "base_001_073",
      "sha256": "cbd1dba35eca430e12219f6957b0c476c887a7d61a8d46f91a2130228d4fd575"
    },
    {
      "fichier": "045_factG_acomptes_avoirs.sql",
      "phase": "base_001_073",
      "sha256": "86179226f82d13ff0d59ff2cd4418988f8df443a147c1ea2c2e3218839b925f9"
    },
    {
      "fichier": "046_factH_audit_final_facturation.sql",
      "phase": "base_001_073",
      "sha256": "d710d81c80ba587f999eb487083d7f5261931c919b33ab0ca1c87054fac925bf"
    },
    {
      "fichier": "047_compta_final_audit.sql",
      "phase": "base_001_073",
      "sha256": "48e3a296ecbb7a7c322fc44c3585992f639dde2bce56fd4e4afa83673f11d6e5"
    },
    {
      "fichier": "048_rapprochement_bancaire_final.sql",
      "phase": "base_001_073",
      "sha256": "fc3b96e80963ddee9f7330fa28d2f260837914f1498b8da2a4305f64e699419a"
    },
    {
      "fichier": "049_lettrage_final.sql",
      "phase": "base_001_073",
      "sha256": "360f8d47f3a2b58d32666b25d30ce98db6438d716307e298389798426e16aff4"
    },
    {
      "fichier": "050_balance_grand_livre_final.sql",
      "phase": "base_001_073",
      "sha256": "09e49efe761d25d90bdad04e3860c3c75271a3588c1c569d6c08dfaafa4aa54f"
    },
    {
      "fichier": "052_conformite_normative.sql",
      "phase": "base_001_073",
      "sha256": "14a70c0a4d80899154fe590174ba4d2aaa18f87d4c9a80331573a69aef89d496"
    },
    {
      "fichier": "053_comptabilite_auxiliaire_avis24.sql",
      "phase": "base_001_073",
      "sha256": "bf9e8ee3b66b3e5f9125a2fe2034d9817d85dd80bf795e457ae313dfe2552915"
    },
    {
      "fichier": "055_plan_comptable_societe_exercices_decales.sql",
      "phase": "base_001_073",
      "sha256": "920ddd0a9dfe1c7c8be65ce610be77b9cc498b678d465675d2094822f0dbc0f5"
    },
    {
      "fichier": "058_droits_plan_comptable.sql",
      "phase": "base_001_073",
      "sha256": "66d8b53563eeb005a9b957f349123bff9d069551869d0ea97a38637b24d3bfa2"
    },
    {
      "fichier": "059_ouverture_periodes_comptables.sql",
      "phase": "base_001_073",
      "sha256": "7d360aa7178a6769dda33b2d917fc61b093b3a7d31b0b3dbce89a2d2ce633dfa"
    },
    {
      "fichier": "060_compatibilite_tva_double_precision.sql",
      "phase": "base_001_073",
      "sha256": "3cd7acf82190b7996d40a0b66887a7cc2f503a2fc9e2c37f30ef9760d8faa5d3"
    },
    {
      "fichier": "063_tiers_autoentrepreneur_modeles_capital.sql",
      "phase": "base_001_073",
      "sha256": "6e0257b5fb1791bac45eb738f35d869188acfa08868b2d530813d21b8671da5d"
    },
    {
      "fichier": "064_fiscal_retraitement_compte_source.sql",
      "phase": "base_001_073",
      "sha256": "4e0dadd525605675979f20d3dccec3373974c972c0650a9c491ee6c95ccbb3df"
    },
    {
      "fichier": "066_liquidation_is_snapshot_detail.sql",
      "phase": "base_001_073",
      "sha256": "e6df448010fc3a457f14d9ada4da600e7b56c488e3eb975c6989e7b05f6ab4fa"
    },
    {
      "fichier": "069_fec_complements_historiques_saisie_manuelle.sql",
      "phase": "base_001_073",
      "sha256": "e650c35dad1e1d5955565f9190911162425da135e4ce9155507a4bd55665b71e"
    },
    {
      "fichier": "071_liasse_balances_preparation.sql",
      "phase": "base_001_073",
      "sha256": "2cf0b2cacb474a07072ed23dd30a5af0b7e164d65e3563173e66edbaa9100b3a"
    },
    {
      "fichier": "072_integrite_ecritures_definitives.sql",
      "phase": "base_001_073",
      "sha256": "0960542f7f77323d47dca30026123022e7c6680e53c9b492a04731e11cf58dc1"
    },
    {
      "fichier": "073_archives_fiscales_permissions.sql",
      "phase": "base_001_073",
      "sha256": "00cf665ddfeb525c845eb3e0581c88ac8ca100fcb8698f41d9151d9025657ff7"
    },
    {
      "fichier": "074_archives_comptables_immutables.sql",
      "phase": "complements",
      "sha256": "40bad8b322da799bc32550133b613ccc5bd1ca6cd7b718fc6bee735a996f8fe3"
    },
    {
      "fichier": "075_complements_auxiliaires_structure.sql",
      "phase": "complements",
      "sha256": "898ad572c5ceb277d45f1c2dfe5178dc4aedbbdb6a7662d1a2582aee40ae1257"
    },
    {
      "fichier": "076_contraintes_etic_archives.sql",
      "phase": "complements",
      "sha256": "986252e2d96b9e0bded2a0519422c24c31662405d3d8778b54bf36f8e23141b9"
    },
    {
      "fichier": "077_permissions_cycle_facturation.sql",
      "phase": "complements",
      "sha256": "c6f139d418f877d912c1877e6470a6e2bd64aeaf76b203c320f0c4295b1ebde3"
    },
    {
      "fichier": "078_factures_definitives_suppression.sql",
      "phase": "complements",
      "sha256": "8f6017ba928fc84bf7bdfd59d3612371a093beeccbfb681be491db6876229d71"
    },
    {
      "fichier": "079_permissions_suppression_brouillons.sql",
      "phase": "complements",
      "sha256": "988ad4d7d5ca880a64d6d94b97289903118d1ea5581b95fd4dba1d3eca7ed2e0"
    },
    {
      "fichier": "080_dossiers_employes.sql",
      "phase": "complements",
      "sha256": "4c1b71e0e09763f91ed3fe25b67ad60b65a77de30b911e066658d30e2f704431"
    },
    {
      "fichier": "081_grh_absences.sql",
      "phase": "complements",
      "sha256": "d11b50625261e35d9769ef8f654812622b5ff3244852eb6529dcae6fb7f593e2"
    },
    {
      "fichier": "082_paie_referentiels.sql",
      "phase": "complements",
      "sha256": "f67ab12ac510ae66b0f3e0437586533a483bc448ef628a2fb83381d508fd6548"
    },
    {
      "fichier": "074_archives_comptables_immutables.sql",
      "phase": "rejeu_complements",
      "sha256": "40bad8b322da799bc32550133b613ccc5bd1ca6cd7b718fc6bee735a996f8fe3"
    },
    {
      "fichier": "075_complements_auxiliaires_structure.sql",
      "phase": "rejeu_complements",
      "sha256": "898ad572c5ceb277d45f1c2dfe5178dc4aedbbdb6a7662d1a2582aee40ae1257"
    },
    {
      "fichier": "076_contraintes_etic_archives.sql",
      "phase": "rejeu_complements",
      "sha256": "986252e2d96b9e0bded2a0519422c24c31662405d3d8778b54bf36f8e23141b9"
    },
    {
      "fichier": "077_permissions_cycle_facturation.sql",
      "phase": "rejeu_complements",
      "sha256": "c6f139d418f877d912c1877e6470a6e2bd64aeaf76b203c320f0c4295b1ebde3"
    },
    {
      "fichier": "078_factures_definitives_suppression.sql",
      "phase": "rejeu_complements",
      "sha256": "8f6017ba928fc84bf7bdfd59d3612371a093beeccbfb681be491db6876229d71"
    },
    {
      "fichier": "079_permissions_suppression_brouillons.sql",
      "phase": "rejeu_complements",
      "sha256": "988ad4d7d5ca880a64d6d94b97289903118d1ea5581b95fd4dba1d3eca7ed2e0"
    },
    {
      "fichier": "080_dossiers_employes.sql",
      "phase": "rejeu_complements",
      "sha256": "4c1b71e0e09763f91ed3fe25b67ad60b65a77de30b911e066658d30e2f704431"
    },
    {
      "fichier": "081_grh_absences.sql",
      "phase": "rejeu_complements",
      "sha256": "d11b50625261e35d9769ef8f654812622b5ff3244852eb6529dcae6fb7f593e2"
    },
    {
      "fichier": "082_paie_referentiels.sql",
      "phase": "rejeu_complements",
      "sha256": "f67ab12ac510ae66b0f3e0437586533a483bc448ef628a2fb83381d508fd6548"
    },
    {
      "fichier": "083_ras_reglements.sql",
      "phase": "extension_explicite_083_084",
      "sha256": "b62cc45eeee75c264a972bf10c9597ac67c8de0a372f2832d7871705960cf762"
    },
    {
      "fichier": "084_rapprochement_ventilations.sql",
      "phase": "extension_explicite_083_084",
      "sha256": "efeb097d0de37d83433ac1993cfc263376442151ce94c1e8f9f4ab4eecf3203a"
    },
    {
      "fichier": "083_ras_reglements.sql",
      "phase": "rejeu_extensions_083_084",
      "sha256": "b62cc45eeee75c264a972bf10c9597ac67c8de0a372f2832d7871705960cf762"
    },
    {
      "fichier": "084_rapprochement_ventilations.sql",
      "phase": "rejeu_extensions_083_084",
      "sha256": "efeb097d0de37d83433ac1993cfc263376442151ce94c1e8f9f4ab4eecf3203a"
    }
  ],
  "nombre_tables_orm": 65,
  "zero_initial": {
    "societes": 0,
    "utilisateurs": 0,
    "utilisateurs_societes": 0,
    "tiers": 0,
    "articles": 0,
    "factures": 0,
    "reglements": 0,
    "ecritures": 0,
    "lignes_ecriture": 0,
    "mouvements_stock": 0,
    "inventaires_stock": 0,
    "immobilisations": 0,
    "clotures_exercice": 0,
    "fiscal_liquidations_is": 0,
    "liasses_fiscales_archives": 0,
    "etic_sections_exercice": 0,
    "livres_inventaire_archives": 0,
    "ligne_auxiliaire_complements": 0,
    "employes": 0,
    "grh_absences": 0,
    "grh_absence_evenements": 0,
    "paie_referentiel_versions": 0
  },
  "catalogue": {
    "checks": {
      "etic_sections_exercice": [
        {
          "conname": "ck_etic_section_code",
          "convalidated": false,
          "definition": "CHECK (((code)::text = ANY ((ARRAY['A1'::character varying, 'A2'::character varying, 'A3'::character varying, 'B1'::character varying, 'B2'::character varying, 'B2bis'::character varying, 'B3'::character varying, 'B4'::character varying, 'B5'::character varying, 'B6'::character varying, 'B7'::character varying, 'B8'::character varying, 'B9'::character varying, 'B10'::character varying, 'B11'::character varying, 'B12'::character varying, 'B13'::character varying, 'B14'::character varying, 'C1'::character varying, 'C2'::character varying, 'C3'::character varying, 'C4'::character varying, 'C5'::character varying])::text[]))) NOT VALID"
        }
      ],
      "liasses_fiscales_archives": [
        {
          "conname": "ck_liasse_archive_sha256",
          "convalidated": false,
          "definition": "CHECK (((empreinte_sha256)::text ~ '^[0-9a-f]{64}$'::text)) NOT VALID"
        },
        {
          "conname": "ck_liasse_archive_version_positive",
          "convalidated": true,
          "definition": "CHECK ((version > 0))"
        }
      ],
      "ligne_auxiliaire_complements": [
        {
          "conname": "ck_ligne_aux_complement_compte_non_vide",
          "convalidated": true,
          "definition": "CHECK ((length(TRIM(BOTH FROM compte_auxiliaire_snapshot)) > 0))"
        },
        {
          "conname": "ck_ligne_aux_complement_libelle_non_vide",
          "convalidated": true,
          "definition": "CHECK ((length(TRIM(BOTH FROM libelle_auxiliaire_snapshot)) > 0))"
        },
        {
          "conname": "ck_ligne_aux_complement_nature",
          "convalidated": true,
          "definition": "CHECK (((nature_auxiliaire)::text = ANY ((ARRAY['client'::character varying, 'fournisseur'::character varying])::text[])))"
        }
      ],
      "employes": [
        {
          "conname": "ck_employes_dates",
          "convalidated": false,
          "definition": "CHECK (((date_sortie IS NULL) OR (date_embauche IS NULL) OR (date_sortie >= date_embauche))) NOT VALID"
        },
        {
          "conname": "ck_employes_personnes_charge_ir",
          "convalidated": false,
          "definition": "CHECK (((personnes_charge_ir IS NULL) OR ((personnes_charge_ir >= 0) AND (personnes_charge_ir <= 6)))) NOT VALID"
        }
      ],
      "grh_absences": [
        {
          "conname": "ck_grh_absences_dates",
          "convalidated": true,
          "definition": "CHECK ((date_fin >= date_debut))"
        },
        {
          "conname": "ck_grh_absences_statut",
          "convalidated": true,
          "definition": "CHECK (((statut)::text = ANY ((ARRAY['demande'::character varying, 'approuve'::character varying, 'refuse'::character varying, 'annule'::character varying])::text[])))"
        },
        {
          "conname": "ck_grh_absences_type",
          "convalidated": true,
          "definition": "CHECK (((type_absence)::text = ANY ((ARRAY['conge'::character varying, 'absence'::character varying, 'autre'::character varying])::text[])))"
        }
      ],
      "grh_absence_evenements": [
        {
          "conname": "ck_grh_absence_evenements_statut",
          "convalidated": true,
          "definition": "CHECK (((nouveau_statut)::text = ANY ((ARRAY['demande'::character varying, 'approuve'::character varying, 'refuse'::character varying, 'annule'::character varying])::text[])))"
        }
      ],
      "paie_referentiel_versions": [
        {
          "conname": "ck_paie_referentiel_annee",
          "convalidated": true,
          "definition": "CHECK (((annee >= 2025) AND (annee <= 2100)))"
        },
        {
          "conname": "ck_paie_referentiel_qualification",
          "convalidated": true,
          "definition": "CHECK (((qualification)::text = ANY ((ARRAY['non_verifie'::character varying, 'preuves_partielles'::character varying])::text[])))"
        },
        {
          "conname": "ck_paie_referentiel_version",
          "convalidated": true,
          "definition": "CHECK ((version > 0))"
        }
      ]
    },
    "triggers": {
      "livres_inventaire_archives": [
        {
          "tgname": "trg_livre_inventaire_immutable",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_livre_inventaire_immutable BEFORE DELETE OR UPDATE ON public.livres_inventaire_archives FOR EACH ROW EXECUTE FUNCTION hisabpro_livre_inventaire_immutable()"
        },
        {
          "tgname": "trg_livre_inventaire_truncate",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_livre_inventaire_truncate BEFORE TRUNCATE ON public.livres_inventaire_archives FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_livre_inventaire_immutable()"
        }
      ],
      "liasse_balances_preparation": [
        {
          "tgname": "trg_balance_preparation_immuable",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_balance_preparation_immuable BEFORE DELETE OR UPDATE ON public.liasse_balances_preparation FOR EACH ROW EXECUTE FUNCTION hisabpro_balance_preparation_immuable()"
        },
        {
          "tgname": "trg_balance_preparation_truncate",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_balance_preparation_truncate BEFORE TRUNCATE ON public.liasse_balances_preparation FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_balance_preparation_immuable()"
        }
      ],
      "ligne_auxiliaire_complements": [
        {
          "tgname": "trg_ligne_aux_complements_append_only",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_ligne_aux_complements_append_only BEFORE DELETE OR UPDATE ON public.ligne_auxiliaire_complements FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_ligne_aux_complement_append_only()"
        },
        {
          "tgname": "trg_ligne_aux_complements_no_truncate",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_ligne_aux_complements_no_truncate BEFORE TRUNCATE ON public.ligne_auxiliaire_complements FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_guard_ligne_aux_complement_append_only()"
        }
      ],
      "grh_absence_evenements": [
        {
          "tgname": "trg_grh_historique_immutable",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_grh_historique_immutable BEFORE DELETE OR UPDATE ON public.grh_absence_evenements FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_historique_grh()"
        },
        {
          "tgname": "trg_grh_historique_truncate",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_grh_historique_truncate BEFORE TRUNCATE ON public.grh_absence_evenements FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_proteger_historique_grh()"
        }
      ],
      "paie_referentiel_versions": [
        {
          "tgname": "trg_paie_referentiel_immutable",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_paie_referentiel_immutable BEFORE DELETE OR UPDATE ON public.paie_referentiel_versions FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_referentiel_paie()"
        },
        {
          "tgname": "trg_paie_referentiel_truncate",
          "tgenabled": "O",
          "definition": "CREATE TRIGGER trg_paie_referentiel_truncate BEFORE TRUNCATE ON public.paie_referentiel_versions FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_proteger_referentiel_paie()"
        }
      ]
    },
    "uniques_paie": [
      {
        "conname": "uq_paie_referentiel_version",
        "definition": "UNIQUE (societe_id, annee, version)"
      }
    ]
  },
  "catalogue_identique_apres_rejeu": true,
  "role_runtime": [
    "hisabpro",
    "hisabpro",
    true,
    false,
    false,
    false,
    false,
    false
  ],
  "runtime_create_public": false,
  "droits_tables": [
    {
      "relname": "acomptes",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "ajustements_inventaire",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "articles",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "audit_actions",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "audit_ecritures",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "audit_periodes_comptables",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "avoirs",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "bareme_ir",
      "lecture": false,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "bons_commande",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "bons_livraison",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "clotures_exercice",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "commercial_sequences",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "comptes_bancaires",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "comptes_societe",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "decisions_affectation_resultat",
      "lecture": false,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "deductions_ir",
      "lecture": false,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "devis",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "echeances_facture",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "ecriture_justificatifs",
      "lecture": true,
      "insertion": true,
      "modification": false,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "ecriture_sequences",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "ecritures",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "employes",
      "lecture": true,
      "insertion": true,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "etic_sections_exercice",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "exercices_comptables",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "facturation_sequences",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "factures",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "familles_articles",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "fiscal_acomptes_is",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "fiscal_credits_is",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "fiscal_css_paiements",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "fiscal_deficit_imputations",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "fiscal_deficits",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "fiscal_liquidations_is",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "fiscal_parametres_exercice",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "fiscal_retraitements",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "grh_absence_evenements",
      "lecture": true,
      "insertion": true,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "grh_absences",
      "lecture": true,
      "insertion": true,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "immobilisations",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "imputations_acomptes",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "inventaires_stock",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "inventaires_stock_lignes",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "lettrages_comptables",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "liasse_balances_preparation",
      "lecture": true,
      "insertion": true,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "liasses_fiscales_archives",
      "lecture": true,
      "insertion": true,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "ligne_auxiliaire_complements",
      "lecture": true,
      "insertion": true,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "lignes_avoir",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "lignes_bon_commande",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "lignes_bon_livraison",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "lignes_devis",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "lignes_ecriture",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "lignes_facture",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "lignes_modele",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "livres_inventaire_archives",
      "lecture": true,
      "insertion": true,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "modeles_ecritures",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "modules_actifs",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "mouvements_stock",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "paie_referentiel_versions",
      "lecture": true,
      "insertion": true,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "periodes_comptables",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "plan_comptable_cgnc_reference",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "rapprochement_etats",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "rapprochement_lignes",
      "lecture": false,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "reglements",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "relances_recouvrement",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "societes",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "taux_cotisations",
      "lecture": false,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "tiers",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    },
    {
      "relname": "tva_parametres_exercice",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "utilisateurs",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "utilisateurs_societes",
      "lecture": true,
      "insertion": false,
      "modification": false,
      "suppression": false,
      "troncature": false
    },
    {
      "relname": "utilisations_avoirs",
      "lecture": true,
      "insertion": true,
      "modification": true,
      "suppression": true,
      "troncature": false
    }
  ],
  "runtime_grh_colonnes_protegees": true,
  "contrat_historique_sans_defaut": true,
  "runtime_referentiel_lecture_insertion_sequence": true,
  "truncate_vides_refuses_owner_runtime": true,
  "zero_final": {
    "societes": 0,
    "utilisateurs": 0,
    "utilisateurs_societes": 0,
    "tiers": 0,
    "articles": 0,
    "factures": 0,
    "reglements": 0,
    "ecritures": 0,
    "lignes_ecriture": 0,
    "mouvements_stock": 0,
    "inventaires_stock": 0,
    "immobilisations": 0,
    "clotures_exercice": 0,
    "fiscal_liquidations_is": 0,
    "liasses_fiscales_archives": 0,
    "etic_sections_exercice": 0,
    "livres_inventaire_archives": 0,
    "ligne_auxiliaire_complements": 0,
    "employes": 0,
    "grh_absences": 0,
    "grh_absence_evenements": 0,
    "paie_referentiel_versions": 0,
    "ras_reglement_captures": 0,
    "ras_reglement_annulations": 0,
    "rapprochement_ventilations": 0
  },
  "extensions_absentes_avant_application": true,
  "zero_extension_initial": {
    "societes": 0,
    "utilisateurs": 0,
    "utilisateurs_societes": 0,
    "tiers": 0,
    "articles": 0,
    "factures": 0,
    "reglements": 0,
    "ecritures": 0,
    "lignes_ecriture": 0,
    "mouvements_stock": 0,
    "inventaires_stock": 0,
    "immobilisations": 0,
    "clotures_exercice": 0,
    "fiscal_liquidations_is": 0,
    "liasses_fiscales_archives": 0,
    "etic_sections_exercice": 0,
    "livres_inventaire_archives": 0,
    "ligne_auxiliaire_complements": 0,
    "employes": 0,
    "grh_absences": 0,
    "grh_absence_evenements": 0,
    "paie_referentiel_versions": 0,
    "ras_reglement_captures": 0,
    "ras_reglement_annulations": 0,
    "rapprochement_ventilations": 0
  },
  "catalogue_extension": {
    "contraintes": {
      "ras_reglement_captures": [
        {
          "conname": "ras_reglement_captures_compte_destination_not_null",
          "contype": "n",
          "definition": "NOT NULL compte_destination"
        },
        {
          "conname": "ras_reglement_captures_created_at_not_null",
          "contype": "n",
          "definition": "NOT NULL created_at"
        },
        {
          "conname": "ras_reglement_captures_created_by_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (created_by) REFERENCES utilisateurs(id)"
        },
        {
          "conname": "ras_reglement_captures_created_by_not_null",
          "contype": "n",
          "definition": "NOT NULL created_by"
        },
        {
          "conname": "ras_reglement_captures_date_operation_not_null",
          "contype": "n",
          "definition": "NOT NULL date_operation"
        },
        {
          "conname": "ras_reglement_captures_ecriture_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (ecriture_id) REFERENCES ecritures(id)"
        },
        {
          "conname": "ras_reglement_captures_ecriture_id_key",
          "contype": "u",
          "definition": "UNIQUE (ecriture_id)"
        },
        {
          "conname": "ras_reglement_captures_ecriture_id_not_null",
          "contype": "n",
          "definition": "NOT NULL ecriture_id"
        },
        {
          "conname": "ras_reglement_captures_facture_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (facture_id) REFERENCES factures(id)"
        },
        {
          "conname": "ras_reglement_captures_facture_id_not_null",
          "contype": "n",
          "definition": "NOT NULL facture_id"
        },
        {
          "conname": "ras_reglement_captures_id_not_null",
          "contype": "n",
          "definition": "NOT NULL id"
        },
        {
          "conname": "ras_reglement_captures_montant_check",
          "contype": "c",
          "definition": "CHECK (((montant > (0)::numeric) AND (montant = round(montant, 2)) AND (montant <> ALL (ARRAY['NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric]))))"
        },
        {
          "conname": "ras_reglement_captures_montant_not_null",
          "contype": "n",
          "definition": "NOT NULL montant"
        },
        {
          "conname": "ras_reglement_captures_pkey",
          "contype": "p",
          "definition": "PRIMARY KEY (id)"
        },
        {
          "conname": "ras_reglement_captures_reference_check",
          "contype": "c",
          "definition": "CHECK ((length(btrim((reference)::text)) > 0))"
        },
        {
          "conname": "ras_reglement_captures_reference_not_null",
          "contype": "n",
          "definition": "NOT NULL reference"
        },
        {
          "conname": "ras_reglement_captures_reglement_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (reglement_id) REFERENCES reglements(id)"
        },
        {
          "conname": "ras_reglement_captures_reglement_id_key",
          "contype": "u",
          "definition": "UNIQUE (reglement_id)"
        },
        {
          "conname": "ras_reglement_captures_reglement_id_not_null",
          "contype": "n",
          "definition": "NOT NULL reglement_id"
        },
        {
          "conname": "ras_reglement_captures_societe_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (societe_id) REFERENCES societes(id)"
        },
        {
          "conname": "ras_reglement_captures_societe_id_not_null",
          "contype": "n",
          "definition": "NOT NULL societe_id"
        }
      ],
      "ras_reglement_annulations": [
        {
          "conname": "ras_reglement_annulations_capture_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (capture_id) REFERENCES ras_reglement_captures(id)"
        },
        {
          "conname": "ras_reglement_annulations_capture_id_key",
          "contype": "u",
          "definition": "UNIQUE (capture_id)"
        },
        {
          "conname": "ras_reglement_annulations_capture_id_not_null",
          "contype": "n",
          "definition": "NOT NULL capture_id"
        },
        {
          "conname": "ras_reglement_annulations_created_at_not_null",
          "contype": "n",
          "definition": "NOT NULL created_at"
        },
        {
          "conname": "ras_reglement_annulations_created_by_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (created_by) REFERENCES utilisateurs(id)"
        },
        {
          "conname": "ras_reglement_annulations_created_by_not_null",
          "contype": "n",
          "definition": "NOT NULL created_by"
        },
        {
          "conname": "ras_reglement_annulations_date_operation_not_null",
          "contype": "n",
          "definition": "NOT NULL date_operation"
        },
        {
          "conname": "ras_reglement_annulations_ecriture_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (ecriture_id) REFERENCES ecritures(id)"
        },
        {
          "conname": "ras_reglement_annulations_ecriture_id_key",
          "contype": "u",
          "definition": "UNIQUE (ecriture_id)"
        },
        {
          "conname": "ras_reglement_annulations_ecriture_id_not_null",
          "contype": "n",
          "definition": "NOT NULL ecriture_id"
        },
        {
          "conname": "ras_reglement_annulations_id_not_null",
          "contype": "n",
          "definition": "NOT NULL id"
        },
        {
          "conname": "ras_reglement_annulations_motif_check",
          "contype": "c",
          "definition": "CHECK ((length(btrim((motif)::text)) > 0))"
        },
        {
          "conname": "ras_reglement_annulations_motif_not_null",
          "contype": "n",
          "definition": "NOT NULL motif"
        },
        {
          "conname": "ras_reglement_annulations_pkey",
          "contype": "p",
          "definition": "PRIMARY KEY (id)"
        },
        {
          "conname": "ras_reglement_annulations_societe_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (societe_id) REFERENCES societes(id)"
        },
        {
          "conname": "ras_reglement_annulations_societe_id_not_null",
          "contype": "n",
          "definition": "NOT NULL societe_id"
        }
      ],
      "rapprochement_ventilations": [
        {
          "conname": "rapprochement_ventilations_ecriture_ligne_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (ecriture_ligne_id) REFERENCES lignes_ecriture(id) ON DELETE RESTRICT"
        },
        {
          "conname": "rapprochement_ventilations_ecriture_ligne_id_not_null",
          "contype": "n",
          "definition": "NOT NULL ecriture_ligne_id"
        },
        {
          "conname": "rapprochement_ventilations_operation_id_not_null",
          "contype": "n",
          "definition": "NOT NULL operation_id"
        },
        {
          "conname": "rapprochement_ventilations_pkey",
          "contype": "p",
          "definition": "PRIMARY KEY (releve_id, ecriture_ligne_id)"
        },
        {
          "conname": "rapprochement_ventilations_releve_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (releve_id) REFERENCES rapprochement_lignes(id) ON DELETE RESTRICT"
        },
        {
          "conname": "rapprochement_ventilations_releve_id_not_null",
          "contype": "n",
          "definition": "NOT NULL releve_id"
        },
        {
          "conname": "rapprochement_ventilations_societe_id_fkey",
          "contype": "f",
          "definition": "FOREIGN KEY (societe_id) REFERENCES societes(id)"
        },
        {
          "conname": "rapprochement_ventilations_societe_id_not_null",
          "contype": "n",
          "definition": "NOT NULL societe_id"
        },
        {
          "conname": "trg_hisabpro_ventilation_commit",
          "contype": "t",
          "definition": "TRIGGER DEFERRABLE INITIALLY DEFERRED"
        },
        {
          "conname": "uq_rapprochement_ventilation_ligne",
          "contype": "u",
          "definition": "UNIQUE (ecriture_ligne_id)"
        }
      ]
    },
    "triggers": {
      "ras_reglement_captures": [
        {
          "tgname": "trg_ras_immutable",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_ras_immutable BEFORE DELETE OR UPDATE ON public.ras_reglement_captures FOR EACH ROW EXECUTE FUNCTION hisabpro_ras_trace_immutable()"
        },
        {
          "tgname": "trg_ras_liens",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_ras_liens BEFORE INSERT ON public.ras_reglement_captures FOR EACH ROW EXECUTE FUNCTION hisabpro_ras_trace_liens()"
        },
        {
          "tgname": "trg_ras_truncate",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_ras_truncate BEFORE TRUNCATE ON public.ras_reglement_captures FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_ras_trace_immutable()"
        }
      ],
      "ras_reglement_annulations": [
        {
          "tgname": "trg_ras_immutable",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_ras_immutable BEFORE DELETE OR UPDATE ON public.ras_reglement_annulations FOR EACH ROW EXECUTE FUNCTION hisabpro_ras_trace_immutable()"
        },
        {
          "tgname": "trg_ras_liens",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_ras_liens BEFORE INSERT ON public.ras_reglement_annulations FOR EACH ROW EXECUTE FUNCTION hisabpro_ras_trace_liens()"
        },
        {
          "tgname": "trg_ras_truncate",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_ras_truncate BEFORE TRUNCATE ON public.ras_reglement_annulations FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_ras_trace_immutable()"
        }
      ],
      "ecritures": [
        {
          "tgname": "trg_00_hisabpro_numero_ecriture",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_00_hisabpro_numero_ecriture BEFORE INSERT ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_attribuer_numero_ecriture()"
        },
        {
          "tgname": "trg_00_hisabpro_numero_validation",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_00_hisabpro_numero_validation BEFORE UPDATE OF est_validee ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_numero_a_la_validation()"
        },
        {
          "tgname": "trg_01_hisabpro_journal_cloture",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_01_hisabpro_journal_cloture BEFORE INSERT OR UPDATE OF journal, source, reference ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_controler_journal_cloture()"
        },
        {
          "tgname": "trg_ecritures_completer_date_piece",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_ecritures_completer_date_piece BEFORE INSERT OR UPDATE OF date, date_piece ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_completer_date_piece()"
        },
        {
          "tgname": "trg_hisabpro_audit_ecritures",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_audit_ecritures BEFORE INSERT OR DELETE OR UPDATE ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_tracer_ecriture()"
        },
        {
          "tgname": "trg_hisabpro_auxiliaire_validation",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_auxiliaire_validation BEFORE UPDATE OF est_validee ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_auxiliaire_validation()"
        },
        {
          "tgname": "trg_hisabpro_equilibre_definitif",
          "tgenabled": "O",
          "tgdeferrable": true,
          "tginitdeferred": true,
          "definition": "CREATE CONSTRAINT TRIGGER trg_hisabpro_equilibre_definitif AFTER INSERT OR UPDATE ON public.ecritures DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION hisabpro_verifier_equilibre_definitif()"
        },
        {
          "tgname": "trg_hisabpro_interdire_suppression_numero",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_interdire_suppression_numero BEFORE DELETE ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_interdire_suppression_numero()"
        },
        {
          "tgname": "trg_hisabpro_proteger_ecriture_definitive",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_proteger_ecriture_definitive BEFORE UPDATE ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_ecriture_definitive()"
        },
        {
          "tgname": "trg_hisabpro_proteger_numero_ecriture",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_proteger_numero_ecriture BEFORE UPDATE OF numero_ecriture, societe_id, exercice, journal, date ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_numero_ecriture()"
        },
        {
          "tgname": "trg_hisabpro_verifier_periode_ecriture",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_verifier_periode_ecriture BEFORE INSERT OR UPDATE OF date, exercice, societe_id ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_verifier_periode_ecriture()"
        },
        {
          "tgname": "trg_ras_ledger_lie",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_ras_ledger_lie BEFORE DELETE OR UPDATE ON public.ecritures FOR EACH ROW EXECUTE FUNCTION hisabpro_ras_ledger_lie()"
        }
      ],
      "lignes_ecriture": [
        {
          "tgname": "trg_hisabpro_audit_lignes_ecriture",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_audit_lignes_ecriture BEFORE INSERT OR DELETE OR UPDATE ON public.lignes_ecriture FOR EACH ROW EXECUTE FUNCTION hisabpro_tracer_ecriture()"
        },
        {
          "tgname": "trg_hisabpro_ligne_auxiliaire_definitive",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_ligne_auxiliaire_definitive BEFORE INSERT OR UPDATE OF compte, tiers_id, compte_auxiliaire_snapshot, libelle_auxiliaire_snapshot ON public.lignes_ecriture FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_ligne_auxiliaire_definitive()"
        },
        {
          "tgname": "trg_hisabpro_proteger_lignes_definitives",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_proteger_lignes_definitives BEFORE INSERT OR DELETE OR UPDATE ON public.lignes_ecriture FOR EACH ROW EXECUTE FUNCTION hisabpro_proteger_lignes_ecriture_definitive()"
        },
        {
          "tgname": "trg_hisabpro_verifier_compte_societe",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_verifier_compte_societe BEFORE INSERT OR UPDATE OF compte, ecriture_id ON public.lignes_ecriture FOR EACH ROW EXECUTE FUNCTION hisabpro_verifier_compte_societe()"
        },
        {
          "tgname": "trg_ras_ligne_liee",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_ras_ligne_liee BEFORE INSERT OR DELETE OR UPDATE ON public.lignes_ecriture FOR EACH ROW EXECUTE FUNCTION hisabpro_ras_ledger_lie()"
        }
      ],
      "rapprochement_ventilations": [
        {
          "tgname": "trg_hisabpro_no_truncate_ventilation",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_no_truncate_ventilation BEFORE TRUNCATE ON public.rapprochement_ventilations FOR EACH STATEMENT EXECUTE FUNCTION hisabpro_no_truncate_ventilation()"
        },
        {
          "tgname": "trg_hisabpro_rapprochement_ventilation",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_rapprochement_ventilation BEFORE INSERT OR DELETE OR UPDATE ON public.rapprochement_ventilations FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_rapprochement_ventilation()"
        },
        {
          "tgname": "trg_hisabpro_ventilation_commit",
          "tgenabled": "O",
          "tgdeferrable": true,
          "tginitdeferred": true,
          "definition": "CREATE CONSTRAINT TRIGGER trg_hisabpro_ventilation_commit AFTER INSERT OR DELETE ON public.rapprochement_ventilations DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_ventilation_commit()"
        }
      ],
      "rapprochement_lignes": [
        {
          "tgname": "trg_hisabpro_guard_rapprochement_comptable",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_guard_rapprochement_comptable BEFORE INSERT OR UPDATE OF ecriture_ligne_id, rapprochee, compte, sens, montant, societe_id ON public.rapprochement_lignes FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_rapprochement_comptable()"
        },
        {
          "tgname": "trg_hisabpro_rapprochement_exercice_cloture",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_rapprochement_exercice_cloture BEFORE INSERT OR DELETE OR UPDATE ON public.rapprochement_lignes FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_rapprochement_exercice_cloture()"
        },
        {
          "tgname": "trg_hisabpro_releve_ventilation",
          "tgenabled": "O",
          "tgdeferrable": false,
          "tginitdeferred": false,
          "definition": "CREATE TRIGGER trg_hisabpro_releve_ventilation BEFORE INSERT OR UPDATE ON public.rapprochement_lignes FOR EACH ROW EXECUTE FUNCTION hisabpro_guard_releve_ventilation()"
        }
      ]
    },
    "fonction_liens_ras": {
      "prosecdef": true,
      "proconfig": [
        "search_path=pg_catalog, public"
      ],
      "proprietaire": "hisabpro_recette"
    }
  },
  "droits_extension": {
    "tables": {
      "ras_reglement_captures": {
        "SELECT": true,
        "INSERT": true,
        "UPDATE": false,
        "DELETE": false,
        "TRUNCATE": false
      },
      "ras_reglement_annulations": {
        "SELECT": true,
        "INSERT": true,
        "UPDATE": false,
        "DELETE": false,
        "TRUNCATE": false
      },
      "rapprochement_ventilations": {
        "SELECT": true,
        "INSERT": true,
        "UPDATE": false,
        "DELETE": true,
        "TRUNCATE": false
      }
    },
    "sequences": {
      "ras_reglement_captures": {
        "USAGE": true,
        "SELECT": true,
        "UPDATE": false
      },
      "ras_reglement_annulations": {
        "USAGE": true,
        "SELECT": true,
        "UPDATE": false
      }
    }
  },
  "extension_identique_apres_rejeu": true,
  "refus_extension": [
    {
      "controle": "owner_truncate_ras_reglement_captures",
      "code": "23514"
    },
    {
      "controle": "runtime_truncate_ras_reglement_captures",
      "code": "42501"
    },
    {
      "controle": "runtime_update_ras_reglement_captures",
      "code": "42501"
    },
    {
      "controle": "owner_truncate_ras_reglement_annulations",
      "code": "23514"
    },
    {
      "controle": "runtime_truncate_ras_reglement_annulations",
      "code": "42501"
    },
    {
      "controle": "runtime_update_ras_reglement_annulations",
      "code": "42501"
    },
    {
      "controle": "owner_truncate_rapprochement_ventilations",
      "code": "23514"
    },
    {
      "controle": "runtime_truncate_rapprochement_ventilations",
      "code": "42501"
    },
    {
      "controle": "runtime_update_rapprochement_ventilations",
      "code": "42501"
    },
    {
      "controle": "runtime_delete_ras_reglement_captures",
      "code": "42501"
    },
    {
      "controle": "runtime_setval_ras_reglement_captures",
      "code": "42501"
    },
    {
      "controle": "runtime_delete_ras_reglement_annulations",
      "code": "42501"
    },
    {
      "controle": "runtime_setval_ras_reglement_annulations",
      "code": "42501"
    },
    {
      "controle": "runtime_ddl",
      "code": "42501"
    },
    {
      "controle": "capture_acteur_absent",
      "code": "23514"
    },
    {
      "controle": "annulation_acteur_absent",
      "code": "23514"
    },
    {
      "controle": "ventilation_liens_absents",
      "code": "23514"
    }
  ],
  "restauration": {
    "cible_supprimee": true,
    "erreur": null,
    "clusters_distincts": true,
    "taille_dump": 559813,
    "sha256_dump": "28ecf000b2e690b82f442898ab3e7baaa29632e4aa33ea5852facf705c7f6dfa",
    "schema_et_donnees_identiques": true,
    "tables": {
      "acomptes": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "ajustements_inventaire": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "articles": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "audit_actions": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "audit_ecritures": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "audit_periodes_comptables": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "avoirs": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "bareme_ir": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "bons_commande": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "bons_livraison": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "clotures_exercice": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "commercial_sequences": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "comptes_bancaires": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "comptes_societe": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "decisions_affectation_resultat": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "deductions_ir": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "devis": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "echeances_facture": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "ecriture_justificatifs": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "ecriture_sequences": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "ecritures": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "employes": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "etic_sections_exercice": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "exercices_comptables": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "facturation_sequences": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "factures": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "familles_articles": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "fiscal_acomptes_is": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "fiscal_credits_is": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "fiscal_css_paiements": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "fiscal_deficit_imputations": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "fiscal_deficits": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "fiscal_liquidations_is": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "fiscal_parametres_exercice": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "fiscal_retraitements": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "grh_absence_evenements": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "grh_absences": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "immobilisations": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "imputations_acomptes": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "inventaires_stock": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "inventaires_stock_lignes": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "lettrages_comptables": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "liasse_balances_preparation": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "liasses_fiscales_archives": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "ligne_auxiliaire_complements": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "lignes_avoir": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "lignes_bon_commande": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "lignes_bon_livraison": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "lignes_devis": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "lignes_ecriture": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "lignes_facture": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "lignes_modele": {
        "nombre": 140,
        "sha256": "d240c577793abbb5cea2fb11fc831a566d4db9409cbcf60dcd66c8d6f317b8b4"
      },
      "livres_inventaire_archives": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "modeles_ecritures": {
        "nombre": 59,
        "sha256": "74e07140c2306679fae0a1ab61b82e16acecb6cb94c4ee565f7dc3f69c43e7f9"
      },
      "modules_actifs": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "mouvements_stock": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "paie_referentiel_versions": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "periodes_comptables": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "plan_comptable_cgnc_reference": {
        "nombre": 892,
        "sha256": "edd8866fd6528956e0be1035db32becf0e062dd6af227260489d2408b8372c0d"
      },
      "rapprochement_etats": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "rapprochement_lignes": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "rapprochement_ventilations": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "ras_reglement_annulations": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "ras_reglement_captures": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "reglements": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "relances_recouvrement": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "societes": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "taux_cotisations": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "tiers": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "tva_parametres_exercice": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "utilisateurs": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "utilisateurs_societes": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      },
      "utilisations_avoirs": {
        "nombre": 0,
        "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
      }
    },
    "schema": {
      "colonnes": {
        "nombre": 981,
        "sha256": "e7b0483164c9b033ffd276cac8fd3e7ac8b12211058502d784b23401d43ea88b"
      },
      "contraintes": {
        "nombre": 961,
        "sha256": "91fee94e98a341b72d2d01c19bc29a8b11eadcf46c2d7229083159cc76937b54"
      },
      "index": {
        "nombre": 376,
        "sha256": "97612669eb5890141a21883ebe1d86322900717b1adff31fa8f2fa199197337d"
      },
      "triggers": {
        "nombre": 69,
        "sha256": "d7426271adb22e634a742896e1bd889e773a81f2b9535be1fe3d72e6763bcc3a"
      },
      "fonctions": {
        "nombre": 60,
        "sha256": "ad474dec84622b15ae983dd2264e8b126fc3c26f30d08de63ae9d1f3fc50392f"
      },
      "sequences": {
        "nombre": 68,
        "sha256": "0eac809f5613063788f594bf3679293a782fe460b1477ef0db03b5f8787c73ec"
      },
      "etats_sequences": {
        "nombre": 68,
        "sha256": "edf21e356a833b4a9a7a77a8e8cf8a1a4cac493be833f9e40979e7be2da2379e"
      }
    },
    "normalisation_checks_source": [
      [
        "acomptes",
        "ck_acompte_taux_tva",
        false
      ],
      [
        "acomptes",
        "ck_acomptes_mode_factg",
        true
      ],
      [
        "acomptes",
        "ck_acomptes_qualification_tva",
        true
      ],
      [
        "acomptes",
        "ck_acomptes_qualification_tva_enum",
        true
      ],
      [
        "acomptes",
        "ck_acomptes_statut_paiement_factg",
        true
      ],
      [
        "acomptes",
        "ck_acomptes_tva_coherence",
        false
      ],
      [
        "ajustements_inventaire",
        "ck_ajustement_inventaire_montant_positif",
        false
      ],
      [
        "avoirs",
        "ck_avoirs_nature",
        true
      ],
      [
        "avoirs",
        "ck_avoirs_rrr_sans_stock",
        false
      ],
      [
        "commercial_sequences",
        "ck_commercial_sequences_positive",
        false
      ],
      [
        "commercial_sequences",
        "ck_commercial_sequences_type",
        true
      ],
      [
        "comptes_societe",
        "ck_compte_societe_classe",
        false
      ],
      [
        "comptes_societe",
        "ck_compte_societe_numero_longueur",
        false
      ],
      [
        "comptes_societe",
        "ck_compte_societe_origine",
        true
      ],
      [
        "decisions_affectation_resultat",
        "ck_decision_affectation_capital_non_negatif",
        false
      ],
      [
        "decisions_affectation_resultat",
        "ck_decision_affectation_pertes_non_negatif",
        false
      ],
      [
        "decisions_affectation_resultat",
        "ck_decision_affectation_reserve_non_negative",
        false
      ],
      [
        "decisions_affectation_resultat",
        "ck_decision_affectation_ventilation_non_negative",
        false
      ],
      [
        "echeances_facture",
        "ck_echeance_facture_montant",
        false
      ],
      [
        "echeances_facture",
        "ck_echeance_facture_ordre",
        false
      ],
      [
        "ecriture_justificatifs",
        "ck_ecriture_justificatif_reference_non_vide",
        false
      ],
      [
        "ecriture_sequences",
        "ck_ecriture_sequences_numero",
        false
      ],
      [
        "employes",
        "ck_employes_dates",
        false
      ],
      [
        "employes",
        "ck_employes_personnes_charge_ir",
        false
      ],
      [
        "etic_sections_exercice",
        "ck_etic_section_code",
        true
      ],
      [
        "exercices_comptables",
        "ck_exercice_annee_reference_fin",
        false
      ],
      [
        "exercices_comptables",
        "ck_exercice_dates",
        false
      ],
      [
        "exercices_comptables",
        "ck_exercice_duree_max",
        false
      ],
      [
        "exercices_comptables",
        "ck_exercice_statut",
        true
      ],
      [
        "facturation_sequences",
        "ck_facturation_sequences_positive",
        false
      ],
      [
        "facturation_sequences",
        "ck_facturation_sequences_type",
        true
      ],
      [
        "factures",
        "ck_facture_tva_deductible_pct",
        false
      ],
      [
        "factures",
        "ck_factures_delai_paiement_factd",
        false
      ],
      [
        "factures",
        "ck_factures_emballage_mode",
        true
      ],
      [
        "factures",
        "ck_factures_emballage_qualification_tva",
        true
      ],
      [
        "factures",
        "ck_factures_factf_hors_champ_motif",
        false
      ],
      [
        "factures",
        "ck_factures_factf_litige_reference",
        false
      ],
      [
        "factures",
        "ck_factures_mode_reglement_prevu_factd",
        true
      ],
      [
        "factures",
        "ck_factures_qualification_tva",
        true
      ],
      [
        "factures",
        "ck_factures_transport_mode",
        true
      ],
      [
        "factures",
        "ck_factures_transport_qualification_tva",
        true
      ],
      [
        "fiscal_acomptes_is",
        "ck_fiscal_acompte_dispense_justifiee",
        false
      ],
      [
        "fiscal_acomptes_is",
        "ck_fiscal_acompte_montant_non_negatif",
        false
      ],
      [
        "fiscal_acomptes_is",
        "ck_fiscal_acompte_numero",
        false
      ],
      [
        "fiscal_acomptes_is",
        "ck_fiscal_acompte_paiement_ou_dispense",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_autre_justifie",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_imputation_acomptes",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_montant_positif",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_reference",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_type",
        true
      ],
      [
        "fiscal_css_paiements",
        "ck_fiscal_css_paiement_montant_positif",
        false
      ],
      [
        "fiscal_css_paiements",
        "ck_fiscal_css_paiement_reference",
        false
      ],
      [
        "fiscal_deficit_imputations",
        "ck_fiscal_imputation_amort_non_negatif",
        false
      ],
      [
        "fiscal_deficit_imputations",
        "ck_fiscal_imputation_ordinaire_non_negatif",
        false
      ],
      [
        "fiscal_deficit_imputations",
        "ck_fiscal_imputation_total_positif",
        false
      ],
      [
        "fiscal_deficits",
        "ck_fiscal_deficit_amort_non_negatif",
        false
      ],
      [
        "fiscal_deficits",
        "ck_fiscal_deficit_ordinaire_non_negatif",
        false
      ],
      [
        "fiscal_deficits",
        "ck_fiscal_deficit_source",
        true
      ],
      [
        "fiscal_deficits",
        "ck_fiscal_deficit_total_positif",
        false
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_benefice_non_negatif",
        false
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_credits_non_negatifs",
        false
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_impots_non_negatifs",
        false
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_nature_impot",
        true
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_soldes_non_negatifs",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_acomptes_reference_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_acomptes_reference_non_negative",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_categorie_is",
        true
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_base_exclue_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_base_exclue_non_negative",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_base_reduite_non_negative",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_exoneration_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_minimum_exonere_justifie",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_taux_reduit_justifie",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_css_exoneration_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_css_reference_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_css_reference_non_negative",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_deficit_non_negatif",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_regime_special_justifie",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_taux_force",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_taux_force_justifie",
        false
      ],
      [
        "fiscal_retraitements",
        "ck_fiscal_retraitement_montant_positif",
        false
      ],
      [
        "fiscal_retraitements",
        "ck_fiscal_retraitement_type",
        true
      ],
      [
        "grh_absence_evenements",
        "ck_grh_absence_evenements_statut",
        true
      ],
      [
        "grh_absences",
        "ck_grh_absences_dates",
        false
      ],
      [
        "grh_absences",
        "ck_grh_absences_statut",
        true
      ],
      [
        "grh_absences",
        "ck_grh_absences_type",
        true
      ],
      [
        "immobilisations",
        "ck_immo_amortissable_duree",
        false
      ],
      [
        "immobilisations",
        "ck_immo_duree_amort",
        false
      ],
      [
        "immobilisations",
        "ck_immo_encaissement_cession",
        false
      ],
      [
        "immobilisations",
        "ck_immo_methode",
        true
      ],
      [
        "immobilisations",
        "ck_immo_mise_service_apres_acquisition",
        false
      ],
      [
        "immobilisations",
        "ck_immo_paiement_apres_acquisition",
        false
      ],
      [
        "immobilisations",
        "ck_immo_prix_ht_non_negatif",
        false
      ],
      [
        "immobilisations",
        "ck_immo_qualification_tva",
        true
      ],
      [
        "immobilisations",
        "ck_immo_qualification_tva_cession_enum",
        true
      ],
      [
        "immobilisations",
        "ck_immo_qualification_tva_coherence",
        false
      ],
      [
        "immobilisations",
        "ck_immo_qualification_tva_enum",
        true
      ],
      [
        "immobilisations",
        "ck_immo_sortie_apres_service",
        false
      ],
      [
        "immobilisations",
        "ck_immo_taux_tva",
        false
      ],
      [
        "immobilisations",
        "ck_immo_taux_tva_cession",
        false
      ],
      [
        "immobilisations",
        "ck_immo_tva_recuperable_pct",
        false
      ],
      [
        "immobilisations",
        "ck_immo_type_sortie",
        true
      ],
      [
        "immobilisations",
        "ck_immo_valeur_brute_non_negative",
        false
      ],
      [
        "immobilisations",
        "ck_immo_valeur_residuelle",
        false
      ],
      [
        "imputations_acomptes",
        "ck_imputation_acompte_montant",
        false
      ],
      [
        "imputations_acomptes",
        "ck_imputations_acomptes_statut_factg",
        true
      ],
      [
        "inventaires_stock_lignes",
        "ck_inventaire_stock_qte_reelle_non_negative",
        false
      ],
      [
        "liasse_balances_preparation",
        "ck_liasse_balance_version",
        false
      ],
      [
        "liasses_fiscales_archives",
        "ck_liasse_archive_sha256",
        false
      ],
      [
        "liasses_fiscales_archives",
        "ck_liasse_archive_version_positive",
        false
      ],
      [
        "ligne_auxiliaire_complements",
        "ck_ligne_aux_complement_compte_non_vide",
        false
      ],
      [
        "ligne_auxiliaire_complements",
        "ck_ligne_aux_complement_libelle_non_vide",
        false
      ],
      [
        "ligne_auxiliaire_complements",
        "ck_ligne_aux_complement_nature",
        true
      ],
      [
        "lignes_avoir",
        "ck_lignes_avoir_mode_calcul_factg",
        true
      ],
      [
        "lignes_avoir",
        "ck_lignes_avoir_montant_force_factg",
        false
      ],
      [
        "lignes_avoir",
        "ck_lignes_avoir_qualification_tva",
        true
      ],
      [
        "lignes_bon_commande",
        "ck_lignes_bc_qualification_tva",
        true
      ],
      [
        "lignes_bon_commande",
        "ck_lignes_bc_valeurs_facte",
        false
      ],
      [
        "lignes_bon_livraison",
        "ck_lignes_bl_qualification_tva",
        true
      ],
      [
        "lignes_bon_livraison",
        "ck_lignes_bl_valeurs_facte",
        false
      ],
      [
        "lignes_devis",
        "ck_lignes_devis_qualification_tva",
        true
      ],
      [
        "lignes_devis",
        "ck_lignes_devis_valeurs_facte",
        false
      ],
      [
        "lignes_ecriture",
        "ck_ligne_ecriture_credit_non_negatif",
        false
      ],
      [
        "lignes_ecriture",
        "ck_ligne_ecriture_debit_non_negatif",
        false
      ],
      [
        "lignes_ecriture",
        "ck_ligne_ecriture_un_seul_sens",
        false
      ],
      [
        "lignes_ecriture",
        "ck_lignes_ecriture_nature_aux053",
        true
      ],
      [
        "lignes_facture",
        "ck_lignes_facture_qualification_tva",
        true
      ],
      [
        "lignes_facture",
        "ck_lignes_facture_valeurs_facte",
        false
      ],
      [
        "livres_inventaire_archives",
        "ck_livre_inventaire_version_positive",
        false
      ],
      [
        "mouvements_stock",
        "ck_mouvements_stock_quantite_positive_06c",
        false
      ],
      [
        "mouvements_stock",
        "ck_mouvements_stock_type_06c",
        true
      ],
      [
        "paie_referentiel_versions",
        "ck_paie_referentiel_annee",
        false
      ],
      [
        "paie_referentiel_versions",
        "ck_paie_referentiel_qualification",
        true
      ],
      [
        "paie_referentiel_versions",
        "ck_paie_referentiel_version",
        false
      ],
      [
        "periodes_comptables",
        "ck_periode_dates",
        false
      ],
      [
        "periodes_comptables",
        "ck_periode_statut",
        true
      ],
      [
        "ras_reglement_annulations",
        "ras_reglement_annulations_motif_check",
        false
      ],
      [
        "ras_reglement_captures",
        "ras_reglement_captures_montant_check",
        false
      ],
      [
        "ras_reglement_captures",
        "ras_reglement_captures_reference_check",
        false
      ],
      [
        "reglements",
        "ck_reglements_mode_factd",
        true
      ],
      [
        "reglements",
        "ck_reglements_statut_date_effective",
        true
      ],
      [
        "relances_recouvrement",
        "ck_relance_canal",
        true
      ],
      [
        "relances_recouvrement",
        "ck_relance_montant_promis",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_niveau",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_prochaine_date",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_promesse_date",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_statut",
        true
      ],
      [
        "societes",
        "ck_societes_ice_format_facte",
        false
      ],
      [
        "tiers",
        "ck_tiers_categorie_fiscale",
        true
      ],
      [
        "tiers",
        "ck_tiers_ice_format_facte",
        false
      ],
      [
        "tva_parametres_exercice",
        "ck_tva_credit_ouverture_non_negatif",
        false
      ],
      [
        "tva_parametres_exercice",
        "ck_tva_prorata_pct",
        false
      ],
      [
        "utilisateurs",
        "ck_utilisateurs_role_hisabpro",
        true
      ],
      [
        "utilisateurs_societes",
        "ck_utilisateurs_societes_role_hisabpro",
        true
      ],
      [
        "utilisations_avoirs",
        "ck_utilisations_avoirs_facture_factg",
        false
      ],
      [
        "utilisations_avoirs",
        "ck_utilisations_avoirs_montant_factg",
        false
      ],
      [
        "utilisations_avoirs",
        "ck_utilisations_avoirs_statut_factg",
        true
      ],
      [
        "utilisations_avoirs",
        "ck_utilisations_avoirs_type_factg",
        true
      ]
    ],
    "normalisation_checks_cible": [
      [
        "acomptes",
        "ck_acompte_taux_tva",
        false
      ],
      [
        "acomptes",
        "ck_acomptes_mode_factg",
        false
      ],
      [
        "acomptes",
        "ck_acomptes_qualification_tva",
        false
      ],
      [
        "acomptes",
        "ck_acomptes_qualification_tva_enum",
        false
      ],
      [
        "acomptes",
        "ck_acomptes_statut_paiement_factg",
        false
      ],
      [
        "acomptes",
        "ck_acomptes_tva_coherence",
        false
      ],
      [
        "ajustements_inventaire",
        "ck_ajustement_inventaire_montant_positif",
        false
      ],
      [
        "avoirs",
        "ck_avoirs_nature",
        false
      ],
      [
        "avoirs",
        "ck_avoirs_rrr_sans_stock",
        false
      ],
      [
        "commercial_sequences",
        "ck_commercial_sequences_positive",
        false
      ],
      [
        "commercial_sequences",
        "ck_commercial_sequences_type",
        false
      ],
      [
        "comptes_societe",
        "ck_compte_societe_classe",
        false
      ],
      [
        "comptes_societe",
        "ck_compte_societe_numero_longueur",
        false
      ],
      [
        "comptes_societe",
        "ck_compte_societe_origine",
        false
      ],
      [
        "decisions_affectation_resultat",
        "ck_decision_affectation_capital_non_negatif",
        false
      ],
      [
        "decisions_affectation_resultat",
        "ck_decision_affectation_pertes_non_negatif",
        false
      ],
      [
        "decisions_affectation_resultat",
        "ck_decision_affectation_reserve_non_negative",
        false
      ],
      [
        "decisions_affectation_resultat",
        "ck_decision_affectation_ventilation_non_negative",
        false
      ],
      [
        "echeances_facture",
        "ck_echeance_facture_montant",
        false
      ],
      [
        "echeances_facture",
        "ck_echeance_facture_ordre",
        false
      ],
      [
        "ecriture_justificatifs",
        "ck_ecriture_justificatif_reference_non_vide",
        false
      ],
      [
        "ecriture_sequences",
        "ck_ecriture_sequences_numero",
        false
      ],
      [
        "employes",
        "ck_employes_dates",
        false
      ],
      [
        "employes",
        "ck_employes_personnes_charge_ir",
        false
      ],
      [
        "etic_sections_exercice",
        "ck_etic_section_code",
        false
      ],
      [
        "exercices_comptables",
        "ck_exercice_annee_reference_fin",
        false
      ],
      [
        "exercices_comptables",
        "ck_exercice_dates",
        false
      ],
      [
        "exercices_comptables",
        "ck_exercice_duree_max",
        false
      ],
      [
        "exercices_comptables",
        "ck_exercice_statut",
        false
      ],
      [
        "facturation_sequences",
        "ck_facturation_sequences_positive",
        false
      ],
      [
        "facturation_sequences",
        "ck_facturation_sequences_type",
        false
      ],
      [
        "factures",
        "ck_facture_tva_deductible_pct",
        false
      ],
      [
        "factures",
        "ck_factures_delai_paiement_factd",
        false
      ],
      [
        "factures",
        "ck_factures_emballage_mode",
        false
      ],
      [
        "factures",
        "ck_factures_emballage_qualification_tva",
        false
      ],
      [
        "factures",
        "ck_factures_factf_hors_champ_motif",
        false
      ],
      [
        "factures",
        "ck_factures_factf_litige_reference",
        false
      ],
      [
        "factures",
        "ck_factures_mode_reglement_prevu_factd",
        false
      ],
      [
        "factures",
        "ck_factures_qualification_tva",
        false
      ],
      [
        "factures",
        "ck_factures_transport_mode",
        false
      ],
      [
        "factures",
        "ck_factures_transport_qualification_tva",
        false
      ],
      [
        "fiscal_acomptes_is",
        "ck_fiscal_acompte_dispense_justifiee",
        false
      ],
      [
        "fiscal_acomptes_is",
        "ck_fiscal_acompte_montant_non_negatif",
        false
      ],
      [
        "fiscal_acomptes_is",
        "ck_fiscal_acompte_numero",
        false
      ],
      [
        "fiscal_acomptes_is",
        "ck_fiscal_acompte_paiement_ou_dispense",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_autre_justifie",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_imputation_acomptes",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_montant_positif",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_reference",
        false
      ],
      [
        "fiscal_credits_is",
        "ck_fiscal_credit_is_type",
        false
      ],
      [
        "fiscal_css_paiements",
        "ck_fiscal_css_paiement_montant_positif",
        false
      ],
      [
        "fiscal_css_paiements",
        "ck_fiscal_css_paiement_reference",
        false
      ],
      [
        "fiscal_deficit_imputations",
        "ck_fiscal_imputation_amort_non_negatif",
        false
      ],
      [
        "fiscal_deficit_imputations",
        "ck_fiscal_imputation_ordinaire_non_negatif",
        false
      ],
      [
        "fiscal_deficit_imputations",
        "ck_fiscal_imputation_total_positif",
        false
      ],
      [
        "fiscal_deficits",
        "ck_fiscal_deficit_amort_non_negatif",
        false
      ],
      [
        "fiscal_deficits",
        "ck_fiscal_deficit_ordinaire_non_negatif",
        false
      ],
      [
        "fiscal_deficits",
        "ck_fiscal_deficit_source",
        false
      ],
      [
        "fiscal_deficits",
        "ck_fiscal_deficit_total_positif",
        false
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_benefice_non_negatif",
        false
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_credits_non_negatifs",
        false
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_impots_non_negatifs",
        false
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_nature_impot",
        false
      ],
      [
        "fiscal_liquidations_is",
        "ck_fiscal_liq_soldes_non_negatifs",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_acomptes_reference_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_acomptes_reference_non_negative",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_categorie_is",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_base_exclue_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_base_exclue_non_negative",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_base_reduite_non_negative",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_exoneration_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_minimum_exonere_justifie",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_cm_taux_reduit_justifie",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_css_exoneration_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_css_reference_justifiee",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_css_reference_non_negative",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_deficit_non_negatif",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_regime_special_justifie",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_taux_force",
        false
      ],
      [
        "fiscal_parametres_exercice",
        "ck_fiscal_taux_force_justifie",
        false
      ],
      [
        "fiscal_retraitements",
        "ck_fiscal_retraitement_montant_positif",
        false
      ],
      [
        "fiscal_retraitements",
        "ck_fiscal_retraitement_type",
        false
      ],
      [
        "grh_absence_evenements",
        "ck_grh_absence_evenements_statut",
        false
      ],
      [
        "grh_absences",
        "ck_grh_absences_dates",
        false
      ],
      [
        "grh_absences",
        "ck_grh_absences_statut",
        false
      ],
      [
        "grh_absences",
        "ck_grh_absences_type",
        false
      ],
      [
        "immobilisations",
        "ck_immo_amortissable_duree",
        false
      ],
      [
        "immobilisations",
        "ck_immo_duree_amort",
        false
      ],
      [
        "immobilisations",
        "ck_immo_encaissement_cession",
        false
      ],
      [
        "immobilisations",
        "ck_immo_methode",
        false
      ],
      [
        "immobilisations",
        "ck_immo_mise_service_apres_acquisition",
        false
      ],
      [
        "immobilisations",
        "ck_immo_paiement_apres_acquisition",
        false
      ],
      [
        "immobilisations",
        "ck_immo_prix_ht_non_negatif",
        false
      ],
      [
        "immobilisations",
        "ck_immo_qualification_tva",
        false
      ],
      [
        "immobilisations",
        "ck_immo_qualification_tva_cession_enum",
        false
      ],
      [
        "immobilisations",
        "ck_immo_qualification_tva_coherence",
        false
      ],
      [
        "immobilisations",
        "ck_immo_qualification_tva_enum",
        false
      ],
      [
        "immobilisations",
        "ck_immo_sortie_apres_service",
        false
      ],
      [
        "immobilisations",
        "ck_immo_taux_tva",
        false
      ],
      [
        "immobilisations",
        "ck_immo_taux_tva_cession",
        false
      ],
      [
        "immobilisations",
        "ck_immo_tva_recuperable_pct",
        false
      ],
      [
        "immobilisations",
        "ck_immo_type_sortie",
        false
      ],
      [
        "immobilisations",
        "ck_immo_valeur_brute_non_negative",
        false
      ],
      [
        "immobilisations",
        "ck_immo_valeur_residuelle",
        false
      ],
      [
        "imputations_acomptes",
        "ck_imputation_acompte_montant",
        false
      ],
      [
        "imputations_acomptes",
        "ck_imputations_acomptes_statut_factg",
        false
      ],
      [
        "inventaires_stock_lignes",
        "ck_inventaire_stock_qte_reelle_non_negative",
        false
      ],
      [
        "liasse_balances_preparation",
        "ck_liasse_balance_version",
        false
      ],
      [
        "liasses_fiscales_archives",
        "ck_liasse_archive_sha256",
        false
      ],
      [
        "liasses_fiscales_archives",
        "ck_liasse_archive_version_positive",
        false
      ],
      [
        "ligne_auxiliaire_complements",
        "ck_ligne_aux_complement_compte_non_vide",
        false
      ],
      [
        "ligne_auxiliaire_complements",
        "ck_ligne_aux_complement_libelle_non_vide",
        false
      ],
      [
        "ligne_auxiliaire_complements",
        "ck_ligne_aux_complement_nature",
        false
      ],
      [
        "lignes_avoir",
        "ck_lignes_avoir_mode_calcul_factg",
        false
      ],
      [
        "lignes_avoir",
        "ck_lignes_avoir_montant_force_factg",
        false
      ],
      [
        "lignes_avoir",
        "ck_lignes_avoir_qualification_tva",
        false
      ],
      [
        "lignes_bon_commande",
        "ck_lignes_bc_qualification_tva",
        false
      ],
      [
        "lignes_bon_commande",
        "ck_lignes_bc_valeurs_facte",
        false
      ],
      [
        "lignes_bon_livraison",
        "ck_lignes_bl_qualification_tva",
        false
      ],
      [
        "lignes_bon_livraison",
        "ck_lignes_bl_valeurs_facte",
        false
      ],
      [
        "lignes_devis",
        "ck_lignes_devis_qualification_tva",
        false
      ],
      [
        "lignes_devis",
        "ck_lignes_devis_valeurs_facte",
        false
      ],
      [
        "lignes_ecriture",
        "ck_ligne_ecriture_credit_non_negatif",
        false
      ],
      [
        "lignes_ecriture",
        "ck_ligne_ecriture_debit_non_negatif",
        false
      ],
      [
        "lignes_ecriture",
        "ck_ligne_ecriture_un_seul_sens",
        false
      ],
      [
        "lignes_ecriture",
        "ck_lignes_ecriture_nature_aux053",
        false
      ],
      [
        "lignes_facture",
        "ck_lignes_facture_qualification_tva",
        false
      ],
      [
        "lignes_facture",
        "ck_lignes_facture_valeurs_facte",
        false
      ],
      [
        "livres_inventaire_archives",
        "ck_livre_inventaire_version_positive",
        false
      ],
      [
        "mouvements_stock",
        "ck_mouvements_stock_quantite_positive_06c",
        false
      ],
      [
        "mouvements_stock",
        "ck_mouvements_stock_type_06c",
        false
      ],
      [
        "paie_referentiel_versions",
        "ck_paie_referentiel_annee",
        false
      ],
      [
        "paie_referentiel_versions",
        "ck_paie_referentiel_qualification",
        false
      ],
      [
        "paie_referentiel_versions",
        "ck_paie_referentiel_version",
        false
      ],
      [
        "periodes_comptables",
        "ck_periode_dates",
        false
      ],
      [
        "periodes_comptables",
        "ck_periode_statut",
        false
      ],
      [
        "ras_reglement_annulations",
        "ras_reglement_annulations_motif_check",
        false
      ],
      [
        "ras_reglement_captures",
        "ras_reglement_captures_montant_check",
        false
      ],
      [
        "ras_reglement_captures",
        "ras_reglement_captures_reference_check",
        false
      ],
      [
        "reglements",
        "ck_reglements_mode_factd",
        false
      ],
      [
        "reglements",
        "ck_reglements_statut_date_effective",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_canal",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_montant_promis",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_niveau",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_prochaine_date",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_promesse_date",
        false
      ],
      [
        "relances_recouvrement",
        "ck_relance_statut",
        false
      ],
      [
        "societes",
        "ck_societes_ice_format_facte",
        false
      ],
      [
        "tiers",
        "ck_tiers_categorie_fiscale",
        false
      ],
      [
        "tiers",
        "ck_tiers_ice_format_facte",
        false
      ],
      [
        "tva_parametres_exercice",
        "ck_tva_credit_ouverture_non_negatif",
        false
      ],
      [
        "tva_parametres_exercice",
        "ck_tva_prorata_pct",
        false
      ],
      [
        "utilisateurs",
        "ck_utilisateurs_role_hisabpro",
        false
      ],
      [
        "utilisateurs_societes",
        "ck_utilisateurs_societes_role_hisabpro",
        false
      ],
      [
        "utilisations_avoirs",
        "ck_utilisations_avoirs_facture_factg",
        false
      ],
      [
        "utilisations_avoirs",
        "ck_utilisations_avoirs_montant_factg",
        false
      ],
      [
        "utilisations_avoirs",
        "ck_utilisations_avoirs_statut_factg",
        false
      ],
      [
        "utilisations_avoirs",
        "ck_utilisations_avoirs_type_factg",
        false
      ]
    ],
    "role_runtime": [
      "hisabpro",
      "hisabpro",
      true,
      false,
      false,
      false,
      false,
      false
    ],
    "droits_absents_avant_rejeu": {
      "ras_reglement_captures": false,
      "ras_reglement_annulations": false,
      "rapprochement_ventilations": false
    },
    "droits_083_084_restitues": true,
    "refus": [
      {
        "controle": "conservation_ras",
        "code": "23514"
      },
      {
        "controle": "conservation_ventilation",
        "code": "23514"
      },
      {
        "controle": "runtime_ras_update",
        "code": "42501"
      },
      {
        "controle": "runtime_ras_delete",
        "code": "42501"
      },
      {
        "controle": "runtime_ventilation_truncate",
        "code": "42501"
      },
      {
        "controle": "runtime_ddl",
        "code": "42501"
      }
    ],
    "cible_non_vide_refusee": true,
    "source_et_cible_inchangees": true
  },
  "duree_secondes": 39.44,
  "cluster_supprime": true
}
```

## Limites de provisionnement

LOGIN active uniquement dans le cluster pour prouver une connexion applicative non proprietaire ; aucun droit global ou GRANT invente. Les permissions insuffisantes observees restent a definir dans un manifeste exhaustif audite : tables sans SELECT ou INSERT = acomptes, audit_actions, audit_ecritures, audit_periodes_comptables, avoirs, bareme_ir, bons_commande, bons_livraison, clotures_exercice, comptes_bancaires, decisions_affectation_resultat, deductions_ir, devis, ecriture_sequences, lignes_avoir, lignes_bon_commande, lignes_bon_livraison, lignes_devis, lignes_modele, modeles_ecritures, plan_comptable_cgnc_reference, rapprochement_lignes, taux_cotisations, tva_parametres_exercice, utilisateurs_societes.

La matrice brute ci-dessus ne justifie pas des droits CRUD sur toutes les tables : audits et archives demandent des flux controles. Aucun parcours utilisateur ni installation production valide ici ; etat runtime incomplet explicite. Les controles NOT VALID nouveaux ne constituent pas une validation des donnees historiques. Les taux sociaux restent globaux et leurs anciennes permissions ne sont pas modifiees par cette recette ;082 ajoute seulement des versions de provenance propres aux societes.

## Périmètre exact

Socle082, extension explicite083/084 puis dump/restauration sur un second cluster nonce vide.
Comparaison de toutes les tables publiques, colonnes, contraintes, index, fonctions,
déclencheurs et séquences. Pour les CHECK, PostgreSQL reparse la définition dans
une table TEMP vide avant comparaison :le dump peut redistribuer les casts ARRAY
sans changer le prédicat. Aucune suppression de cast ou de NOT VALID ;les deux
diagnostics de normalisation sont conservés. Les autres définitions restent exactes.
Le dump ne restitue pas les rôles/ACL ;seuls les droits083/084
sont rétablis par leurs SQL existants. Aucune initialisation d’un rôle de production.
Cette recette est à vide pour les tables métier contrôlées par433 ;les référentiels
présents dans le SQL existant sont conservés et comparés. Elle complète les tests
séparés de restauration083/084avec pièces ;elle ne les remplace pas.
Fichiers externes, tous les droits applicatifs et reprise de production restent distincts.
Les deux clusters et le dump temporaire sont supprimés par les contextes du banc.

## Non-régression du lot434

11 tests connexes réussis, zéro échec/erreur/ignoré,228.611s ; compilation3scripts code0. CLI réel39.44s :73tables,981colonnes,961contraintes,376index,69déclencheurs,60fonctions,68séquences comparés ;2clusters supprimés.

Commande : `Test/run_unit_tests.py Test/test_restauration_consolidee_084.py Test/test_installation_vierge_084.py Test/test_installation_vierge_082.py Test/test_sauvegarde_ras_reglements_isole.py Test/test_sauvegarde_rapprochement_ventilation_isole.py Test/test_sauvegarde_paie_grh_postgres.py Test/test_sauvegarde_pieces_documents_isole.py`.

Essais conservés :1échec36.96s (comparaison brute),1échec29.74s (diagnostic casts),1échec/1réussi44.95s (paramètres DBAPI vides sur SQL contenant%). Les CHECK sont maintenant reparsés par PostgreSQL sur TEMP,etles SQL sans paramètres passés sans dictionnaire DBAPI. Les prédicats différents etNOT VALID différent sont effectivement refusés. Reprise ciblée :3réussis57.61s.

Défaut du banc corrigé :AssertionError() sans message produisait erreur vide etcode0 ;elle donne désormais code1,message nonvide,statut échec etnettoyage du cluster. Aucune migration ni règle comptable modifiée. La globale430 reste historique.
