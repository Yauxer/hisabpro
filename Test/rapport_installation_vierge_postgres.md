# Expérience réelle d'installation PostgreSQL vierge

Date UTC : 2026-10-07T11:46:12.951154+00:00
Statut : **64_scripts_executés_installation_incomplete**
Durée : 27.92 s ; scripts terminés : 64/64.
Cluster temporaire supprimé : True.

Commande : `hisabpro-backend/.venv/Scripts/python.exe Test/recette_installation_vierge.py`.

Aucune connexion réelle, aucun .env lu, aucune donnée comptable créée. Rôle hisabpro NOLOGIN et socle ORM préparés sur le seul cluster marqué. Garde de cible et comptes des tables métier vérifiés avant et après chaque SQL. Registre SHA-256 local conservé dans le cluster pendant l'expérience puis supprimé avec lui.

## Résultat exact

Dernier objet tenté : `073_archives_fiscales_permissions.sql`.

```text
Aucun échec des scripts candidats.
```

## Scripts effectivement terminés

| Fichier | Phase | SHA-256 |
|---|---|---|
| `001_accounting_integrity.sql` | comptabilite | `e65806463fd4604e3c4b8d98017e54886924ad9414eb9c4eeb9a3d3185716fcd` |
| `002_tva_exigibilite.sql` | comptabilite | `6e95caf5b97ee19bc3a0c9dcf7440ccb76a69e642a75302d4e3a3c8e37852f25` |
| `003_tva_02b.sql` | comptabilite | `5ca5e81c445989dbdac7d7c0ad8e067ea6facca14041a2c1ba495314356d9b92` |
| `004_reglement_date_effective.sql` | comptabilite | `b67c44be9d9e33dc3726ed3dc2fed6a2ff4376581d4aa4a0c2067d5d385ad4f8` |
| `005_immobilisations_cycle.sql` | comptabilite | `842c326a524145807c42348bc47cf712534a0b88ce00f7d36d95eaa0232ea047` |
| `006_immobilisations_fournisseur_tiers.sql` | comptabilite | `909bedf1f635166c19e323992b82a77653c0797a6d55dd562ade154983a38aad` |
| `007_cloture_inventaire.sql` | comptabilite | `4381140e9b43f663f8ec252a863ebc349a0f58842ead2d029cfe7617d50d9c72` |
| `008_exercices_periodes.sql` | comptabilite | `d85a725fd53d189acafafb414177adf1667e05b632723609293653ab9ec86d4e` |
| `009_livre_inventaire.sql` | comptabilite | `c3d8456d7b846da75ed68241071511d59defb35eb616c1df26b96434fdb773e4` |
| `010_stock_cloture.sql` | comptabilite | `2b8935717af89f2c2e03d4480ee713c44f2b937694e51613bbb4617582fde0ca` |
| `011_livre_inventaire_v2.sql` | comptabilite | `29a07478d9051dea0b0d3a45b3a26b9cb53c662567b082f55c0598e9d2e19132` |
| `012_stock_movement_engine.sql` | comptabilite | `e84feb0a5060a851d9b434cebe2992f5254ef8e4c12a11a705601f6145b800d5` |
| `013_audit_ecritures.sql` | comptabilite | `95fa48ca355408c458a7d5574f1ca4d92f2ead8d08c7a039c42351ba0a06df84` |
| `014_ecriture_metadata.sql` | comptabilite | `8317520d51c7564e5848843d0d4d0951b8a54767e14cf6b8b057ec71912afcbb` |
| `015_ecriture_numero_scope.sql` | comptabilite | `3c1b838fd3ce055d28b6b117f874fe778f08fba8e2d5923b4d40f0732cc65de9` |
| `016_libelles_justificatifs.sql` | comptabilite | `be474458e1fcd7aeaf65d96316e55ce671c01217f745103819146b4e20890493` |
| `017_ecriture_numero_large_sequence.sql` | comptabilite | `930cc616fbaaf3ec6950edee1d4b5432ff9c860bafa3be531abd5b77ac6e2ba8` |
| `018_numero_ecriture_a_validation.sql` | comptabilite | `e9a5f8d7ea729dfd9d91b41461d0ba452268137ae926624f06cb869528cc842d` |
| `019_journal_cloture_dedie.sql` | comptabilite | `ba5c3bfca5a24e894c07257045db2533519edc55dffa0a0f8bf15ce92227549c` |
| `021_fiscalite_is.sql` | fiscalite | `15b99b88ea304bfdc66bcdefd1adfb90c31c02c8c20e55e4d693e26a56e0a312` |
| `021b_fiscalite_permissions.sql` | fiscalite | `84a34e96676e0171c2ec1bdeab998cd6ba8156332f976a7db40c33ffa5c28384` |
| `022_deficits_fiscaux_millesimes.sql` | fiscalite | `16615ca04096d94e151881ab32fae53751096dd7ab1e2f19b5812791700993b6` |
| `023_cotisation_minimale.sql` | fiscalite | `f8647b92776777ab9d52094b98cbfa76fa1bd971f6a8c93c2981fe67956acff1` |
| `024_acomptes_liquidation_is.sql` | fiscalite | `be6131c72f83081f771f17e89b05e015e20efb9aaa3667f9cb5a0d51808d9541` |
| `025_css_credits_is.sql` | fiscalite | `3f788f58c1acc922dbc54790dc53a35486b69a5f100b7beaf6909e503707c36b` |
| `026_etic_exercice.sql` | fiscalite | `19aac6bfa2e528833398e9b1fc997e5dabb208181851d84e0dee705f4f169612` |
| `027_liasse_fiscale_archive.sql` | fiscalite | `24e1ed1590dec9b333d36c660285ee159ccb854a0b5637326916d50e76b35431` |
| `028_facturation_fondations.sql` | facturation_audit | `a518cce1d42fa33aaf6a59fa8fdf551e297d905f3ae99a5f3892993f6c1f5b72` |
| `029_factures_validation.sql` | facturation_audit | `b4f15b7c3ac40adad6247107f68cacf0df4c9f6e6770f58ff20915113e75caab` |
| `030_facturation_durcissement.sql` | facturation_audit | `324b73786c81fcb3cc17f4abbbc86859c17c941cbf61e6d2b8cea48a3760b069` |
| `031_avoirs_retours.sql` | facturation_audit | `09eea9c8f337ec2dc299cb120486a7451efe5771f4181fea1513c37dff34aa5b` |
| `032_compta_mapping.sql` | facturation_audit | `8bfee4d9d9c451cbcfd8ac224a64c63b574dfc6262661b0e641c168ec128fafa` |
| `033_conformite_tva_frais.sql` | facturation_audit | `d84e647bdc46f14aba8ebace3533886b800c79e5a317a749db6c1b2db79e3e56` |
| `034_recouvrement.sql` | facturation_audit | `e602eead590310d7991e5be586fc086c641b268539e45d27f6b5f1fc312d4fc6` |
| `034b_recouvrement_permissions.sql` | facturation_audit | `344e4b21a1a7bd21dc0035194e0b06e8ab8e62e767f4463bd3d186b4d36e677a` |
| `035_echeanciers_acomptes.sql` | facturation_audit | `43b1400572f6d36849deb1ba200305ba0e9d354211eec53286badaf273752ed5` |
| `036_production_hardening.sql` | facturation_audit | `60d70facc2faf9bc05dbd84c5709ee07a0774d6ac1c5e3efa25fe90912ffead5` |
| `037_compta2_modeles_ecritures.sql` | facturation_audit | `daf4b99a9fca8cc606c15161666d7015b857f8ca246fe37fbfbdec822708dc25` |
| `038_compta3_avis24_durcissement.sql` | facturation_audit | `c1013f796409c6e3967261e1242b7ad57fb65b5f93faf8952577ef8422b4751b` |
| `039_compta4_justificatifs_fec.sql` | facturation_audit | `99a5ea82784f170cdf867d8d2b890bdb2cf3866c88f9438a500a639f173b9be0` |
| `040_factB_identites_dates.sql` | facturation_audit | `1540b1e15190fcc85703558a645c16894b9cfe48d0dd451b235d59a02a07beab` |
| `041_factC_cycle_documentaire.sql` | facturation_audit | `27e65a40d47da745bf396f79098634ac7c995d95d902810610ff547d8ce6f31f` |
| `042_factD_reglements_delais.sql` | facturation_audit | `6ad54b5957795b7f616d7091df42b97ed94426d6294f62da444bff4f70ada35a` |
| `043_factE_audit_identifiants.sql` | facturation_audit | `8bb2fc3d08e21597341d49a81ef9356e839c964534d70922ce83cf9daba2ae9c` |
| `044_factF_delais_paiement.sql` | facturation_audit | `cbd1dba35eca430e12219f6957b0c476c887a7d61a8d46f91a2130228d4fd575` |
| `045_factG_acomptes_avoirs.sql` | facturation_audit | `86179226f82d13ff0d59ff2cd4418988f8df443a147c1ea2c2e3218839b925f9` |
| `046_factH_audit_final_facturation.sql` | facturation_audit | `d710d81c80ba587f999eb487083d7f5261931c919b33ab0ca1c87054fac925bf` |
| `047_compta_final_audit.sql` | facturation_audit | `48e3a296ecbb7a7c322fc44c3585992f639dde2bce56fd4e4afa83673f11d6e5` |
| `048_rapprochement_bancaire_final.sql` | facturation_audit | `fc3b96e80963ddee9f7330fa28d2f260837914f1498b8da2a4305f64e699419a` |
| `049_lettrage_final.sql` | facturation_audit | `360f8d47f3a2b58d32666b25d30ce98db6438d716307e298389798426e16aff4` |
| `050_balance_grand_livre_final.sql` | facturation_audit | `09e49efe761d25d90bdad04e3860c3c75271a3588c1c569d6c08dfaafa4aa54f` |
| `052_conformite_normative.sql` | facturation_audit | `14a70c0a4d80899154fe590174ba4d2aaa18f87d4c9a80331573a69aef89d496` |
| `053_comptabilite_auxiliaire_avis24.sql` | facturation_audit | `bf9e8ee3b66b3e5f9125a2fe2034d9817d85dd80bf795e457ae313dfe2552915` |
| `055_plan_comptable_societe_exercices_decales.sql` | referentiel | `920ddd0a9dfe1c7c8be65ce610be77b9cc498b678d465675d2094822f0dbc0f5` |
| `058_droits_plan_comptable.sql` | referentiel | `66d8b53563eeb005a9b957f349123bff9d069551869d0ea97a38637b24d3bfa2` |
| `059_ouverture_periodes_comptables.sql` | referentiel | `7d360aa7178a6769dda33b2d917fc61b093b3a7d31b0b3dbce89a2d2ce633dfa` |
| `060_compatibilite_tva_double_precision.sql` | referentiel | `3cd7acf82190b7996d40a0b66887a7cc2f503a2fc9e2c37f30ef9760d8faa5d3` |
| `063_tiers_autoentrepreneur_modeles_capital.sql` | referentiel | `6e0257b5fb1791bac45eb738f35d869188acfa08868b2d530813d21b8671da5d` |
| `064_fiscal_retraitement_compte_source.sql` | referentiel | `4e0dadd525605675979f20d3dccec3373974c972c0650a9c491ee6c95ccbb3df` |
| `066_liquidation_is_snapshot_detail.sql` | referentiel | `e6df448010fc3a457f14d9ada4da600e7b56c488e3eb975c6989e7b05f6ab4fa` |
| `069_fec_complements_historiques_saisie_manuelle.sql` | complements_permissions | `e650c35dad1e1d5955565f9190911162425da135e4ce9155507a4bd55665b71e` |
| `071_liasse_balances_preparation.sql` | protections_finales | `2cf0b2cacb474a07072ed23dd30a5af0b7e164d65e3563173e66edbaa9100b3a` |
| `072_integrite_ecritures_definitives.sql` | protections_finales | `0960542f7f77323d47dca30026123022e7c6680e53c9b492a04731e11cf58dc1` |
| `073_archives_fiscales_permissions.sql` | protections_finales | `00cf665ddfeb525c845eb3e0581c88ac8ca100fcb8698f41d9151d9025657ff7` |

## Catalogue observé

```json
{
  "check_code_etic": false,
  "check_sha256_archive": false,
  "trigger_complements_append_only": false,
  "trigger_archive_truncate": true,
  "type_contenu_preparation": "json",
  "nombre_triggers_metier": 43
}
```

## Limites

Installation exhaustive et permissions runtime non validées. Les tables métier restent vides ; aucun parcours utilisateur exécuté ici. Les réparations 065/067/068/070, init.sql et seed paie sont exclus. Les protections structurales de 068 manquent toujours dans cette route candidate ; une exécution réussie des 64 scripts ne prouverait donc pas une installation complète. Les nouvelles migrations après 073 ne sont pas incluses dans cette première expérience. Arrêt au premier échec, aucun SQL original modifié ni contourné.
