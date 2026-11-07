# Installation vierge HisabPro — analyse du dépôt

Date : 7 octobre 2026. Analyse statique, aucun SQL exécuté et aucune base contactée. Ce document propose un ordre de provisionnement à tester ; il ne certifie pas qu'une installation exhaustive a réussi.

**Addendum — expérience isolée du 7 octobre à 11:46 UTC.** L'analyse initiale ci-dessous est conservée. Après sa rédaction, `Test/recette_installation_vierge.py` a réellement exécuté le socle ORM puis les 64 scripts candidats sur un cluster PostgreSQL éphémère marqué, sans `.env` ni connexion réelle. Résultat : 64/64 terminés, code de sortie 0, 27,92 s ; les 18 tables métier surveillées sont restées vides avant/après chaque SQL et le cluster a été supprimé. Compilation du script : OK. Il s'agit d'une expérience explicite, pas de 64 tests pytest ni d'une installation de production.

Le catalogue réel confirme l'absence du CHECK de code ETIC, du CHECK SHA-256 de l'archive et du trigger append-only des compléments auxiliaires ; le trigger TRUNCATE de l'archive est présent et le contenu des préparations reste de type JSON. 43 triggers non internes sont observés. Le rôle `hisabpro` a été créé NOLOGIN pour recevoir les ACL ; aucun parcours sous rôle runtime limité n'a été exécuté. Le registre local d'empreintes a été supprimé avec le cluster, ses 64 entrées sont reproduites dans [le rapport réel](../../Test/rapport_installation_vierge_postgres.md). Les migrations après 073 ne sont pas couvertes par cet essai.

## Conclusion

Le dépôt ne fournit pas encore une chaîne d'installation vierge complète, exécutée et enregistrée. Les scripts numérotés enrichissent un socle ORM ; ils ne créent pas à eux seuls toutes les tables. Un simple démarrage de FastAPI ou `Base.metadata.create_all` ne suffit pas pour les fonctions, triggers, contrôles SQL, référentiels et permissions.

L'ordre candidat ci-dessous doit être utilisé uniquement sur une nouvelle cible de laboratoire explicitement identifiée, sans société ni écriture existante. Il n'est pas un ordre de mise à niveau d'une base historique. Les SQL existants restent intacts.

## Inventaire vérifié

- `models.py` déclare 62 tables ORM. Un scan des `CREATE TABLE` des SQL numérotés laisse 32 tables ORM sans création SQL numérotée, dont `societes`, `utilisateurs`, `utilisateurs_societes`, `ecritures`, `lignes_ecriture`, `factures`, `articles`, `reglements`, `clotures_exercice` et les tables de paie. Le socle ORM est donc un prérequis réel.
- 70 fichiers numérotés entre 001 et 073. Aucun fichier correspondant aux nombres 020, 051, 054, 056, 057, 061 et 062 ; les trous ne doivent pas être comblés par des migrations inventées.
- Deux variantes 021 existent. `021_fiscalite_is_CORRIGE.sql` ne diffère de `021_fiscalite_is.sql` que par un bloc de permissions conditionnelles. La route candidate conserve l'original et applique `021b_fiscalite_permissions.sql` ; ne pas exécuter les deux variantes sans nécessité.
- `007b_cloture_hotfix.sql` répète la création et les droits de la table d'ajustements, déjà couverts par 007 ; il est exclu de la route minimale vierge, conservé dans le dépôt.
- Les fichiers non numérotés `init.sql`, `modeles_ecritures.sql` et `donnees_fiscales.sql` ont des rôles distincts, détaillés ci-dessous.

## Préconditions de sécurité

1. Créer une base et un schéma dédiés à une installation vierge avec un rôle de migration propriétaire distinct du rôle applicatif. Le rôle applicatif `hisabpro` doit exister avant 021b et 058, qui refusent explicitement son absence. Son secret doit être fourni hors dépôt ; `init.sql` embarque un mot de passe de démonstration et crée aussi une société démo, donc il est exclu.
2. Contrôler la cible par URL explicite, nom de base, propriétaire, marqueur d'installation, adresse autorisée et absence de données métier. Refuser la procédure si des sociétés, utilisateurs, tiers, écritures, factures, règlements, stocks, archives ou liquidations existent. Ne pas obtenir cet état par suppression de données.
3. Fournir `DATABASE_URL` et un secret JWT privé explicitement ; démarrage runtime avec `APP_ENV=production` et `HISABPRO_CREATE_TABLES=0`. `database.py` refuse une connexion absente en production, mais conserve un repli de développement ; ne pas l'utiliser pour provisionner.
4. Geler les empreintes SHA-256 des modèles, du manifeste et de chaque SQL. Une table de versions/empreintes appliquées et un verrou d'installation restent à implémenter ; aucun registre de migrations global n'a été retrouvé.
5. Aucun utilisateur ne doit utiliser la cible avant la fin des contrôles. Plusieurs migrations mélangent DDL et mises à niveau de données. Sur une cible réellement vierge, leurs backfills métier n'ont aucune ligne à traiter ; cette propriété doit être vérifiée avant et après chaque phase.

## Ordre candidat minimal couvrant les objets présents

### Phase 0 — socle

Créer le socle depuis les modèles complets avec le rôle de migration dans une procédure dédiée, en dehors du démarrage runtime. Cette procédure n'existe pas encore comme installateur exhaustif livré. Elle doit charger `models.py` et vérifier que toutes les 62 tables et les types ENUM sont présents, sans créer de société démo. Ne pas lancer automatiquement le serveur en production pour provoquer `create_all`.

### Phase 1 — comptabilité et inventaire

001 → 002 → 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010 → 011 → 012 → 013 → 014 → 015 → 016 → 017 → 018 → 019.

007b est redondant dans cette route. 019 ajoute le journal CL si nécessaire ; son traitement dépend du type réellement attaché à `ecritures.journal`. Chaque script contient ses propres limites de transaction : ne pas envelopper aveuglément tout le lot dans une transaction unique.

### Phase 2 — fiscalité, ETIC et première archive

021 original → 021b → 022 → 023 → 024 → 025 → 026 → 027.

Les contraintes définies uniquement dans un `CREATE TABLE IF NOT EXISTS` peuvent être absentes si l'ORM a déjà créé la table. Voir les contrôles obligatoires ci-dessous avant de considérer cette phase achevée.

### Phase 3 — facturation, audit et contrôles

028 → 029 → 030 → 031 → 032 → 033 → 034 → 034b → 035 → 036 → 037 → 038 → 039 → 040 → 041 → 042 → 043 → 044 → 045 → 046 → 047 → 048 → 049 → 050 → 052 → 053.

036 crée l'audit applicatif append-only et sa fonction `SECURITY DEFINER` avec `search_path` fixé. 013 fait de même pour l'audit comptable. 037 fournit une bibliothèque de modèles et reconstruit ses lignes ; ne pas rejouer ensuite le seed ancien `modeles_ecritures.sql`.

### Phase 4 — référentiel et compatibilité

055 → 058 → 059 → 060 → 063 → 064 → 066.

055 fournit le référentiel CGNC et les règles de plan par société, 058 ses droits. `assurer_plan_societe` refuse un référentiel vide ; l'inscription doit être testée seulement après cette phase. 060 exige la fonction TVA NUMERIC de 033 avant sa surcharge DOUBLE PRECISION. 063 complète/corrige les modèles déjà préparés par 037. 066 fournit le snapshot détaillé des liquidations.

### Phase 5 — compléments FEC sans réparation historique

Créer séparément les structures, index et fonction/trigger append-only contenus au début de 068, sans aucun rapprochement ni backfill. Puis appliquer 069, qui accorde seulement les droits SELECT/INSERT et séquence nécessaires à la saisie contrôlée.

**Blocage concret : aucun SQL structural séparé de 068 n'existe actuellement.** L'ORM crée la table `ligne_auxiliaire_complements`, mais pas sa fonction/son trigger append-only. Exclure 068 intégralement sans recréer ces protections est incomplet. Exécuter le monolithe 068 réintroduit une procédure de réparation historique dans l'installation. Une nouvelle migration additive ou un bootstrap structural distinct doit être préparé et testé ; ne pas modifier 068 ni supprimer son historique.

065, 067 et 070 sont exclus : réparations de liquidations, FEC et IS/clôtures historiques. Aucun de leurs backfills n'est nécessaire pour une nouvelle société. 068 complet est exclu pour la même séparation de responsabilités, mais sa structure reste indispensable. 069 malgré son nom n'effectue pas de réparation de données.

### Phase 6 — préparations et protections finales

071 → 072 → 073.

071 ajoute les préparations externes immuables, 072 protège l'équilibre et les lignes définitives. 073 exige la fonction de 027 et protège également TRUNCATE des archives fiscales. Vérifier les ACL finales après tous les scripts ; ne pas ajouter un `GRANT ALL` ni un grant global sur toutes les tables après ces révocations.

### Phase 7 — droits métier et références optionnelles

Les scripts attribuent beaucoup de droits uniquement au rôle nommé `hisabpro`. Les tables du socle ORM créées par le rôle de migration nécessitent également un manifeste explicite de droits métier et de séquences. Aucun manifeste exhaustif de droits pour les 62 tables n'est présent. Accorder uniquement les opérations nécessaires, conserver les exceptions audit/archives/référentiel ; vérifier le rôle applicatif connecté, jamais seulement le propriétaire ou un superutilisateur.

`modeles_ecritures.sql` est un seed ancien : ses `ON CONFLICT DO NOTHING` sur les lignes ne garantissent pas l'idempotence en l'absence d'unicité métier sur `lignes_modele`. La route minimale privilégie 037 puis 063 ; comparer les codes attendus avant de décider qu'un seed supplémentaire est nécessaire.

`donnees_fiscales.sql` remplace les référentiels IR/CNSS/AMO 2025/2026. Ce seed relève du périmètre paie facultatif et d'une revue de sources officielles, distinct de la création de schéma. Ne pas le rendre obligatoire pour la facturation/comptabilité sans vérification métier ni l'exécuter contre un référentiel personnalisé existant.

## Contrôles structurels manquants ou à qualifier

| Objet / risque | Preuve dans le dépôt | Contrôle requis sur futur laboratoire |
|---|---|---|
| Code de section ETIC | 026 définit `ck_etic_section_code` uniquement à la création ; modèle ETIC ne contient que l'unicité | Vérifier existence de CHECK et refus d'un code inconnu ; ajout structural idempotent si absent |
| SHA-256 archive fiscale | 027 définit `ck_liasse_archive_sha256` uniquement à la création ; modèle archive a unicité/version positive, sans regex | Vérifier format SQL de l'empreinte, pas seulement validation API |
| Type JSON des préparations | modèle071 : `JSON` ; SQL071 : `JSONB` dans CREATE IF NOT EXISTS | Comparer type réel et opérations attendues ; différence ne prouve pas à elle seule un bug |
| Compléments auxiliaires | structure ORM présente ; trigger/ACL seulement dans 068/069 | Fournir bootstrap structural sans repair, puis UPDATE/DELETE/TRUNCATE et rôle runtime testés |
| Droits sur tables ORM | create_all n'attribue pas les ACL à un autre rôle | Manifeste par table/séquence ; création société, facturation, paiement, comptabilité, stock et fiscalité exécutés avec rôle limité |
| Audit SECURITY DEFINER | fonctions013/036 avec `search_path` fixé ; droit d'exécution public PostgreSQL par défaut à examiner | Contrôler propriétaire non runtime, EXECUTE effectif/PUBLIC, privilèges d'insertion et impossibilité d'altération |
| Variantes/hotfix et rejouabilité | 021/CORRIGE/021b, 007/007b, scripts ayant DELETE de compteurs/templates | Registre avec empreintes ; aucune réapplication automatique sur données métier |
| Coverage du schéma | modèles plus migrations ciblées utilisés par E2E, pas installateur complet | Comparer tables, colonnes, types, CHECK, FK, index, fonctions, triggers et ACL après installation exhaustive |

Ne pas inférer l'absence d'une règle uniquement depuis son nom : certaines contraintes ORM équivalentes portent un autre nom. Les deux cas ETIC/code et archive/SHA ci-dessus ont été relus dans leurs classes réelles.

## Validation suivante recommandée

Préparer un installateur propre avec manifeste explicite, garde de cible vierge, verrou, suivi de versions et bootstrap structural des compléments. Exécuter cette chaîne sur un cluster PostgreSQL éphémère neuf, comparer le catalogue final au manifeste, puis rejouer uniquement ce qui est déclaré idempotent. Tester un rôle de migration propriétaire et un rôle runtime séparés. Poursuivre ensuite un parcours API/navigateur société → facture → paiement → lettrage → clôture → archive sur ce schéma complet.

Les E2E déjà réussis prouvent des périmètres avec leurs migrations sélectionnées ; ils ne sont pas une preuve de cette future chaîne exhaustive. Aucune installation, migration ou donnée réelle n'a été modifiée pendant cette analyse.

## Annexe — les 70 SQL numérotés lus dans le dépôt

64 fichiers candidats conservés, 6 exclus de cette route ; la phase structurale propre issue de 068 reste manquante. Cet inventaire exhaustif des fichiers ne transforme pas l'ordre proposé en installation validée.

| Fichier exact | Position / décision | SHA-256 du fichier lu |
|---|---|---|
| `001_accounting_integrity.sql` | Ordre numérique proposé | `e65806463fd4604e3c4b8d98017e54886924ad9414eb9c4eeb9a3d3185716fcd` |
| `002_tva_exigibilite.sql` | Ordre numérique proposé | `6e95caf5b97ee19bc3a0c9dcf7440ccb76a69e642a75302d4e3a3c8e37852f25` |
| `003_tva_02b.sql` | Ordre numérique proposé | `5ca5e81c445989dbdac7d7c0ad8e067ea6facca14041a2c1ba495314356d9b92` |
| `004_reglement_date_effective.sql` | Ordre numérique proposé | `b67c44be9d9e33dc3726ed3dc2fed6a2ff4376581d4aa4a0c2067d5d385ad4f8` |
| `005_immobilisations_cycle.sql` | Ordre numérique proposé | `842c326a524145807c42348bc47cf712534a0b88ce00f7d36d95eaa0232ea047` |
| `006_immobilisations_fournisseur_tiers.sql` | Ordre numérique proposé | `909bedf1f635166c19e323992b82a77653c0797a6d55dd562ade154983a38aad` |
| `007_cloture_inventaire.sql` | Ordre numérique proposé | `4381140e9b43f663f8ec252a863ebc349a0f58842ead2d029cfe7617d50d9c72` |
| `007b_cloture_hotfix.sql` | Redondant avec 007 pour installation vierge | `d2f580f8e0c115d95b83e209561526494f9aa39d48349fb6149518482a54b763` |
| `008_exercices_periodes.sql` | Ordre numérique proposé | `d85a725fd53d189acafafb414177adf1667e05b632723609293653ab9ec86d4e` |
| `009_livre_inventaire.sql` | Ordre numérique proposé | `c3d8456d7b846da75ed68241071511d59defb35eb616c1df26b96434fdb773e4` |
| `010_stock_cloture.sql` | Ordre numérique proposé | `2b8935717af89f2c2e03d4480ee713c44f2b937694e51613bbb4617582fde0ca` |
| `011_livre_inventaire_v2.sql` | Ordre numérique proposé | `29a07478d9051dea0b0d3a45b3a26b9cb53c662567b082f55c0598e9d2e19132` |
| `012_stock_movement_engine.sql` | Ordre numérique proposé | `e84feb0a5060a851d9b434cebe2992f5254ef8e4c12a11a705601f6145b800d5` |
| `013_audit_ecritures.sql` | Ordre numérique proposé | `95fa48ca355408c458a7d5574f1ca4d92f2ead8d08c7a039c42351ba0a06df84` |
| `014_ecriture_metadata.sql` | Ordre numérique proposé | `8317520d51c7564e5848843d0d4d0951b8a54767e14cf6b8b057ec71912afcbb` |
| `015_ecriture_numero_scope.sql` | Ordre numérique proposé | `3c1b838fd3ce055d28b6b117f874fe778f08fba8e2d5923b4d40f0732cc65de9` |
| `016_libelles_justificatifs.sql` | Ordre numérique proposé | `be474458e1fcd7aeaf65d96316e55ce671c01217f745103819146b4e20890493` |
| `017_ecriture_numero_large_sequence.sql` | Ordre numérique proposé | `930cc616fbaaf3ec6950edee1d4b5432ff9c860bafa3be531abd5b77ac6e2ba8` |
| `018_numero_ecriture_a_validation.sql` | Ordre numérique proposé | `e9a5f8d7ea729dfd9d91b41461d0ba452268137ae926624f06cb869528cc842d` |
| `019_journal_cloture_dedie.sql` | Ordre numérique proposé | `ba5c3bfca5a24e894c07257045db2533519edc55dffa0a0f8bf15ce92227549c` |
| `021_fiscalite_is.sql` | Ordre numérique proposé | `15b99b88ea304bfdc66bcdefd1adfb90c31c02c8c20e55e4d693e26a56e0a312` |
| `021_fiscalite_is_CORRIGE.sql` | Variante, original + 021b retenus | `ea7160b2e03a1c020353e6edd0821dec3e76a45945176bf31c9772495a979a97` |
| `021b_fiscalite_permissions.sql` | Ordre numérique proposé | `84a34e96676e0171c2ec1bdeab998cd6ba8156332f976a7db40c33ffa5c28384` |
| `022_deficits_fiscaux_millesimes.sql` | Ordre numérique proposé | `16615ca04096d94e151881ab32fae53751096dd7ab1e2f19b5812791700993b6` |
| `023_cotisation_minimale.sql` | Ordre numérique proposé | `f8647b92776777ab9d52094b98cbfa76fa1bd971f6a8c93c2981fe67956acff1` |
| `024_acomptes_liquidation_is.sql` | Ordre numérique proposé | `be6131c72f83081f771f17e89b05e015e20efb9aaa3667f9cb5a0d51808d9541` |
| `025_css_credits_is.sql` | Ordre numérique proposé | `3f788f58c1acc922dbc54790dc53a35486b69a5f100b7beaf6909e503707c36b` |
| `026_etic_exercice.sql` | Ordre numérique proposé | `19aac6bfa2e528833398e9b1fc997e5dabb208181851d84e0dee705f4f169612` |
| `027_liasse_fiscale_archive.sql` | Ordre numérique proposé | `24e1ed1590dec9b333d36c660285ee159ccb854a0b5637326916d50e76b35431` |
| `028_facturation_fondations.sql` | Ordre numérique proposé | `a518cce1d42fa33aaf6a59fa8fdf551e297d905f3ae99a5f3892993f6c1f5b72` |
| `029_factures_validation.sql` | Ordre numérique proposé | `b4f15b7c3ac40adad6247107f68cacf0df4c9f6e6770f58ff20915113e75caab` |
| `030_facturation_durcissement.sql` | Ordre numérique proposé | `324b73786c81fcb3cc17f4abbbc86859c17c941cbf61e6d2b8cea48a3760b069` |
| `031_avoirs_retours.sql` | Ordre numérique proposé | `09eea9c8f337ec2dc299cb120486a7451efe5771f4181fea1513c37dff34aa5b` |
| `032_compta_mapping.sql` | Ordre numérique proposé | `8bfee4d9d9c451cbcfd8ac224a64c63b574dfc6262661b0e641c168ec128fafa` |
| `033_conformite_tva_frais.sql` | Ordre numérique proposé | `d84e647bdc46f14aba8ebace3533886b800c79e5a317a749db6c1b2db79e3e56` |
| `034_recouvrement.sql` | Ordre numérique proposé | `e602eead590310d7991e5be586fc086c641b268539e45d27f6b5f1fc312d4fc6` |
| `034b_recouvrement_permissions.sql` | Ordre numérique proposé | `344e4b21a1a7bd21dc0035194e0b06e8ab8e62e767f4463bd3d186b4d36e677a` |
| `035_echeanciers_acomptes.sql` | Ordre numérique proposé | `43b1400572f6d36849deb1ba200305ba0e9d354211eec53286badaf273752ed5` |
| `036_production_hardening.sql` | Ordre numérique proposé | `60d70facc2faf9bc05dbd84c5709ee07a0774d6ac1c5e3efa25fe90912ffead5` |
| `037_compta2_modeles_ecritures.sql` | Ordre numérique proposé | `daf4b99a9fca8cc606c15161666d7015b857f8ca246fe37fbfbdec822708dc25` |
| `038_compta3_avis24_durcissement.sql` | Ordre numérique proposé | `c1013f796409c6e3967261e1242b7ad57fb65b5f93faf8952577ef8422b4751b` |
| `039_compta4_justificatifs_fec.sql` | Ordre numérique proposé | `99a5ea82784f170cdf867d8d2b890bdb2cf3866c88f9438a500a639f173b9be0` |
| `040_factB_identites_dates.sql` | Ordre numérique proposé | `1540b1e15190fcc85703558a645c16894b9cfe48d0dd451b235d59a02a07beab` |
| `041_factC_cycle_documentaire.sql` | Ordre numérique proposé | `27e65a40d47da745bf396f79098634ac7c995d95d902810610ff547d8ce6f31f` |
| `042_factD_reglements_delais.sql` | Ordre numérique proposé | `6ad54b5957795b7f616d7091df42b97ed94426d6294f62da444bff4f70ada35a` |
| `043_factE_audit_identifiants.sql` | Ordre numérique proposé | `8bb2fc3d08e21597341d49a81ef9356e839c964534d70922ce83cf9daba2ae9c` |
| `044_factF_delais_paiement.sql` | Ordre numérique proposé | `cbd1dba35eca430e12219f6957b0c476c887a7d61a8d46f91a2130228d4fd575` |
| `045_factG_acomptes_avoirs.sql` | Ordre numérique proposé | `86179226f82d13ff0d59ff2cd4418988f8df443a147c1ea2c2e3218839b925f9` |
| `046_factH_audit_final_facturation.sql` | Ordre numérique proposé | `d710d81c80ba587f999eb487083d7f5261931c919b33ab0ca1c87054fac925bf` |
| `047_compta_final_audit.sql` | Ordre numérique proposé | `48e3a296ecbb7a7c322fc44c3585992f639dde2bce56fd4e4afa83673f11d6e5` |
| `048_rapprochement_bancaire_final.sql` | Ordre numérique proposé | `fc3b96e80963ddee9f7330fa28d2f260837914f1498b8da2a4305f64e699419a` |
| `049_lettrage_final.sql` | Ordre numérique proposé | `360f8d47f3a2b58d32666b25d30ce98db6438d716307e298389798426e16aff4` |
| `050_balance_grand_livre_final.sql` | Ordre numérique proposé | `09e49efe761d25d90bdad04e3860c3c75271a3588c1c569d6c08dfaafa4aa54f` |
| `052_conformite_normative.sql` | Ordre numérique proposé | `14a70c0a4d80899154fe590174ba4d2aaa18f87d4c9a80331573a69aef89d496` |
| `053_comptabilite_auxiliaire_avis24.sql` | Ordre numérique proposé | `bf9e8ee3b66b3e5f9125a2fe2034d9817d85dd80bf795e457ae313dfe2552915` |
| `055_plan_comptable_societe_exercices_decales.sql` | Ordre numérique proposé | `920ddd0a9dfe1c7c8be65ce610be77b9cc498b678d465675d2094822f0dbc0f5` |
| `058_droits_plan_comptable.sql` | Ordre numérique proposé | `66d8b53563eeb005a9b957f349123bff9d069551869d0ea97a38637b24d3bfa2` |
| `059_ouverture_periodes_comptables.sql` | Ordre numérique proposé | `7d360aa7178a6769dda33b2d917fc61b093b3a7d31b0b3dbce89a2d2ce633dfa` |
| `060_compatibilite_tva_double_precision.sql` | Ordre numérique proposé | `3cd7acf82190b7996d40a0b66887a7cc2f503a2fc9e2c37f30ef9760d8faa5d3` |
| `063_tiers_autoentrepreneur_modeles_capital.sql` | Ordre numérique proposé | `6e0257b5fb1791bac45eb738f35d869188acfa08868b2d530813d21b8671da5d` |
| `064_fiscal_retraitement_compte_source.sql` | Ordre numérique proposé | `4e0dadd525605675979f20d3dccec3373974c972c0650a9c491ee6c95ccbb3df` |
| `065_reparation_liquidations_is_reference_acomptes.sql` | Réparation historique exclue | `1e59c17deddff2bc622a4e17340e6e3a645dbe9b01fab7239acb3993a2db703c` |
| `066_liquidation_is_snapshot_detail.sql` | Ordre numérique proposé | `e6df448010fc3a457f14d9ada4da600e7b56c488e3eb975c6989e7b05f6ab4fa` |
| `067_reparation_fec_historique_sure.sql` | Réparation historique exclue | `08892347ea46d1d68a03402c08b101607fe6f15b689487161eee8ed639cd4ef5` |
| `068_fec_complements_historiques_append_only.sql` | Monolithe exclu ; structure propre indispensable | `6bc924a24554f2969bb3289c149b9ffd6c2577819ad1b2998735077960b51134` |
| `069_fec_complements_historiques_saisie_manuelle.sql` | Ordre numérique proposé ; après structure 068 propre | `e650c35dad1e1d5955565f9190911162425da135e4ce9155507a4bd55665b71e` |
| `070_reparation_is_cloture_historique_2026.sql` | Réparation historique exclue | `56ea3c212c8953ff353f7bcd616013d7bff7832704d15aa6a9467a68713f7d46` |
| `071_liasse_balances_preparation.sql` | Ordre numérique proposé | `2cf0b2cacb474a07072ed23dd30a5af0b7e164d65e3563173e66edbaa9100b3a` |
| `072_integrite_ecritures_definitives.sql` | Ordre numérique proposé | `0960542f7f77323d47dca30026123022e7c6680e53c9b492a04731e11cf58dc1` |
| `073_archives_fiscales_permissions.sql` | Ordre numérique proposé | `00cf665ddfeb525c845eb3e0581c88ac8ca100fcb8698f41d9151d9025657ff7` |
