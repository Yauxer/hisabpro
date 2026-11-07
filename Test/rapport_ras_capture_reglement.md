# Capture explicite de RAS par règlement — lot 293

Reprise du 10 octobre 2026. Flux déclaratif séparé de l'estimation de facture : aucun taux, prorata ou régime fiscal n'est déterminé automatiquement. L'utilisateur indique le montant effectivement opéré, sa date, la référence de pièce et le compte destination actif de sa société. La référence déclarée ne constitue pas une attestation fiscale vérifiée par HisabPro.

## Périmètre et sécurité de déploiement

La migration additive `hisabpro-backend/083_ras_reglements.sql` s'applique **manuellement et explicitement**, après sauvegarde et revue par l'opérateur. Les deux tables de captures et d'annulations ne figurent jamais dans `Base.metadata` et ne sont pas ajoutées au bootstrap de développement. L'inclusion du routeur dans `main.py` n'exécute aucun DDL.

Sans cette migration, le GET de capacité retourne `disponible=false` et le POST refuse409 avant toute mutation. Les fonctionnalités du lot291 restent utilisables sans083. Les tests utilisent seulement des clusters PostgreSQL nonce contrôlés ; aucune application au PostgreSQL réel de l'utilisateur.

La capture reste immuable et unique par règlement. L'annulation ajoute un autre enregistrement immuable et une contrepassation liée par identifiants ; elle ne réécrit pas la capture ou son OD d'origine. Les liens SQL vérifient société, règlement, facture, acteur actif ayant les droits dans la société principale ou via son appartenance multi-société, montant, date, référence et les deux lignes comptables. L'annulation exige le miroir des lignes d'origine et le statut annulé du règlement, dans la même transaction.

Les OD des captures et annulations ne peuvent être éditées, supprimées ou contrepassées par les routes générales. Leur validation comptable reste possible ; leurs états et numéros réels sont exposés par le GET. Les protections SQL empêchent aussi l'ajout d'une troisième ligne à une OD déjà liée et les modifications des données comptables, même avant validation.

Le périmètre initial admet seulement les virements et espèces immédiatement comptabilisés. Chèques et effets, fiscalité RAS TVA, attestations et déclarations réglementaires restent hors de ce lot. Une facture portant déjà le flag historique `ras_comptabilisee=true` refuse le mélange avec ces captures ; aucun backfill ni modification des OD historiques.

## Contrat

- GET `/api/reglements/{id}/ras` : disponibilité, migration requise le cas échéant, blocages, `peut_capturer`, solde courant et historique des captures. Les états définitifs et numéros des OD et contrepassations reflètent la base.
- POST même chemin : `montant` positif fini au centime, `date_operation`, `reference` non vide, `compte_destination` actif et distinct des comptes auxiliaires/collectifs. Les champs supplémentaires sont refusés. Le montant conserve Decimal jusqu'aux lignes NUMERIC(18,2) ; un montant dépassant la capacité réelle de ces colonnes est refusé avant mutation, sans plafond fiscal inventé.
- Un rejeu exactement identique retrouve la capture existante ; une modification de ses données est refusée409. Verrou règlement puis facture avant contrôle du reliquat, pour empêcher des captures concurrentes excédant le dû.
- L'estimation documentaire reste sur la facture et son PDF. Les soldes, recouvrement, crédits d'avoirs et suivi des délais intègrent la somme des captures actives ; `ras_origine=capture_reglement` les distingue de l'historique. La date d'événement provient de la capture déclarée, jamais de l'échéance.
- L'annulation du règlement contrepassera simultanément son écriture de trésorerie et l'OD exacte de sa capture. Un refus pendant l'opération provoque le rollback de l'ensemble.

## Oracle indépendant

Facture fictive1000 HT +200 TVA =1200 TTC, RAS estimée100 sans effet de paiement. Règlement400 et capture explicitement déclarée30 : dû770. Règlement700 et capture70 : dû0 et RAS imputée100. Annulation du second règlement : restitution de700+70, dû770, seule capture30 active. Les deux sens client/fournisseur sont testés ; les OD30/70 possèdent deux lignes équilibrées, avec le vrai tiers et son snapshot auxiliaire. Les OD originales validées restent identiques après annulation. Le montant fractionnaire0,29 est conservé exactement dans les lignes comptables.

## Tests réellement exécutés et incidents

Anciennes commandes récupérées, avant les derniers renforts SQL :

- Session71731 :11 réussis,1 échec,47,21s ; la fixture tentait de recréer le rôlehisabpro déjà présent. Corrigé exclusivement dans le cluster nonce.
- Session8157 :12 réussis,1 échec,46,31s ; le TRUNCATE isolé était déjà refusé par FK avant le trigger attendu. Le test tronque maintenant les deux tables ensemble et vérifie le refus.
- Session66703 :40 réussis,25 avertissements,108,13s, sortie0, **avant le dernier renforcement SQL**, résultat historique distinct de la validation finale.

Reprise du10 octobre :

- Session68703 :40 réussis,25 avertissements,99,97s, sortie0, avant l'ajout final des vérifications runtime et miroir d'annulation.
- Session80783 :12 réussis,1 échec,25 avertissements,46,91s ; vraie connexion LOGINhisabpro, INSERT bloqué par la lecture de `utilisateurs_societes` dans le trigger de liens. Ce résultat n'est pas présenté comme validation des droits runtime.
- Session31332 :14 réussis,25 avertissements,33,74s, sortie0. API réelle : soldes, annulation, validation, conservation des originaux, idempotence, concurrence80+80 sur reliquat100 (un succès, un refus), accès autre société404, rôle lecture403, données invalides422 sans mutation, centimes0,29.

Les premières vérifications de déplacement d'une ligne indépendante vers l'OD capturée ont révélé des barrières ACL historiques avant le nouveau trigger : session34476,14 réussis/1 échec49,21s ; session33362,1 échec23,85s ; session91292,1 échec24,99s ; session57965,14 réussis/1 échec47,94s ; session60123,14 réussis/1 échec50,31s. Les derniers refus proviennent respectivement de la lecture verrouillée du parent comptable et du contrôle historique `comptes_societe`. Aucun ancien trigger ni droit global de production n'a été modifié pour obtenir un résultat vert.

Le test final distingue donc deux preuves : sous LOGIN runtime, les droits historiques refusent le déplacement avec SQLSTATE42501 ; sous propriétaire du cluster de recette, les gardes OLD/NEW, INSERT d'une troisième ligne et modification de l'en-tête lié refusent chacune avec SQLSTATE23514 et le diagnostic « capture RAS ». Quelques permissions par colonne ont été accordées **temporairement dans le cluster nonce**, puis révoquées dans `finally`, pour diagnostiquer les premières barrières. Elles ne constituent pas une proposition de provisioning de production.

La connexion runtime réelle lit les captures, insère une seconde capture cohérente et refuse une annulation dont les lignes ne sont pas le miroir exact. Les contrôles de privilèges vérifient SELECT et INSERT individuellement : ils ne se fondent pas sur la sémantique « au moins un privilège » d'une liste PostgreSQL. Seul le trigger de contrôle des liens est SECURITY DEFINER, avec `search_path=pg_catalog,public` et relations qualifiées `public` ; son propriétaire doit être l'administrateur de migration de confiance. Cela n'accorde aucun SELECT global sur les appartenances multi-société.

Commandes de validation finales, environnement `PYTHON_DOTENV_DISABLED=1`, Python du venv et runner `Test/run_unit_tests.py` :

```powershell
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_ras_capture_reglement_postgres.py Test/test_ras_capture_migration_isole.py Test/test_ras_estimation_solde_postgres.py Test/test_fact7_recouvrement.py Test/test_factG_acomptes_avoirs.py Test/test_factF_delais_paiement.py Test/test_e2e_reglement_edition_isole.py --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_patch127_etic_ras_recoupement.py Test/test_ras_lecture_conservation.py Test/test_factD_reglements_delais.py Test/test_ras_consommateurs_inconnus_postgres.py --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_ras_capture_migration_isole.py --tb=short
```

- Session23483 :42 réussis,25 avertissements,100,72s, sortie0. La dernière assertion d'en-tête a été ajoutée pendant cette commande : ce résultat intermédiaire ne suffit pas à prouver son chargement.
- Session3668 :29 réussis,25 avertissements,50,66s, sortie0. ETIC127, lecture historique RAS, règlements/délais et consommateurs NULL.
- Session63423 :1 réussi,25 avertissements,19,79s, sortie0, **fichier migration final relancé après toute modification** ; les trois gardes physiques23514, les droits runtime, les liens et le rejeu sont ainsi validés.
- `python -m py_compile` des dix fichiers Python applicatifs du lot et des deux fichiers de tests : sortie0 après leur dernière modification.

Les tests API incluent aussi une appartenance multi-société active réellement créée par invitation et utilisée avec son propre token, et le refus du mélange avec une facture historique dont le flag a été renseigné dans la fixture **avant validation**. Aucun flag historique d'une pièce déjà validée n'est modifié par cette préparation.

## Limites

Les agrégats historiques de facture utilisent encore des floats ; les montants extrêmes et leur restitution JSON relèvent de la limite générale LIM16 du produit, et ne sont pas présentés comme une recette financière complète. Le dossier de recette doit distinguer préparation de l'OD et validation définitive, ainsi que déclaration utilisateur et preuve fiscale vérifiée. L'UI et la recette Edge sont dans le lot303 ; les sauvegardes/restaurations des nouvelles tables sont traitées séparément dans le lot305.
