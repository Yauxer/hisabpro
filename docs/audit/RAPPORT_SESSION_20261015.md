# HisabPro — avancement vérifié du 15 octobre 2026

Les lots 433–448, puis 451–459, corrigent plusieurs blocages du rôle SQL applicatif, améliorent
la reproductibilité des exports etcomplètent les preuves d'installation et de
restauration. Le dépôt local reste la source de vérité ;les anciens lots ne sont
pas réappliqués. Aucun PostgreSQL réel ou donnée comptable réelle utilisé.

## Ce qui est livré

- CSV :montants invalides explicites, textes de formule protégés etretours chariot.
- Documents commerciaux, acomptes/avoirs etbanque :droits SQL fermés, modes simples
  etventilés, snapshots préservés ;concurrence des avoirs corrigée.
- Clôture et lettrage :traces annuelles autorisées, tiers natif reconnu sur les
  à-nouveaux etpaiements, contrôles d'équilibre/identité/historique conservés.
- Multi-société :seconde société, invités etaccès secondaires fonctionnels sous
  LOGIN limité ;seules les colonnes rôle/activation des accès sont modifiables.
- Sauvegarde :option explicite d'ACL, restauration 090 avec 26 droits de colonnes,
  mêmes données/schéma/séquences, FEC identique et nouveau cycle API après restore.
- Installation :CLI 090 à 81 SQL distincts/17 rejeux/36 tables métier vides.
  091 est ajoutée explicitement au banc regroupé pour les décisions d'affectation.
- Recette regroupée :10 Edge sur la même application complète, stock/TVA/inventaire/
  amortissement/clôture/AN/FEC/exports ;affectation fictive de perte 3000 tracée.

## Tests réellement exécutés

| Lot | Réussis | Échecs / erreurs / ignorés | Durée XML | Preuve |
|---|---:|---|---|---|
| 433 | 8 | 0 / 0 / 0 | 144.791 s | [Rapport](../../Test/rapport_installation_vierge_084.md) |
| 434 | 11 | 0 / 0 / 0 | 228.611 s | [Rapport](../../Test/rapport_restauration_consolidee_084.md) |
| 435 | 68 | 0 / 0 / 0 | 100.407 s | [Rapport](../../Test/rapport_csv_partage_435.md) |
| 436 | 73 | 0 / 0 / 0 | 146.876 s | [Rapport](../../Test/rapport_permissions_documents_commerciaux_436.md) |
| 437 | 49 | 0 / 0 / 0 | 174.255 s | [Rapport](../../Test/rapport_permissions_acomptes_avoirs_437.md) |
| 438 | 57 | 0 / 0 / 0 | 195.368 s | [Rapport](../../Test/rapport_concurrence_avoirs_438.md) |
| 441 | 93 | 0 / 0 / 0 | 411.476 s | [Rapport](../../Test/rapport_permissions_banque_releves_441.md) |
| 442 | 15 | 0 / 0 / 0 | 234.142 s | [Rapport](../../Test/rapport_e2e_runtime_consolide_442.md) |
| 443 | 35 | 0 / 0 / 0 | 234.423 s | [Rapport](../../Test/rapport_installation_vierge_087.md) |
| 444 | 43 | 0 / 0 / 0 | 208.474 s | [Rapport](../../Test/rapport_e2e_runtime_annuel_444.md) |
| 445 | 16 | 0 / 0 / 0 | 101.842 s | [Rapport](../../Test/rapport_installation_vierge_089.md) |
| 446 | 47 | 0 / 0 / 0 | 298.645 s | [Rapport](../../Test/rapport_restauration_runtime_acl_446.md) |
| 447 | 27 | 0 / 0 / 0 | 203.580 s | [Rapport](../../Test/rapport_multi_societes_runtime_447.md) |
| 448 | 44 | 0 / 0 / 0 | 97.187 s | [Rapport](../../Test/rapport_consolidation_runtime_448.md) |

Les suites se recouvrent :les nombres ne s'additionnent pas. Les échecs de
reproduction etdu support sont conservés dans les rapports de chaque lot.
La globale 430 de 3426 réussites est historique, antérieure aux dernières sources ;
elle n'est pas présentée comme réexécutée. Le buildVite 435 avait réussi 5.86 s avec
avertissement de taille ;aucun frontend produit n'a changé depuis ce lot.
Les fichiers Python modifiés ont été compilés et les vrais bundlesUI/Edge exécutés.

## ZIPs différentiels vérifiés

- [433](../../HisabPro_433_Installation_Consolidee_084.zip)
- [434](../../HisabPro_434_Restauration_Consolidee_084.zip)
- [435](../../HisabPro_435_CSV_Montants_Textes.zip)
- [436](../../HisabPro_436_Permissions_Documents_Commerciaux.zip)
- [437](../../HisabPro_437_Permissions_Acomptes_Avoirs.zip)
- [438](../../HisabPro_438_Concurrence_Avoirs.zip)
- [441](../../HisabPro_441_Permissions_Banque_Releves.zip)
- [442](../../HisabPro_442_E2E_Login_SQL_Applicatif.zip)
- [443](../../HisabPro_443_Installation_Consolidee_087.zip)
- [444](../../HisabPro_444_Cloture_Lettrage_Identite.zip)
- [445](../../HisabPro_445_Installation_Consolidee_089.zip)
- [446](../../HisabPro_446_Restauration_ACL_FEC_Stable.zip)
- [447](../../HisabPro_447_Multi_Societes_Runtime.zip)
- [448](../../HisabPro_448_Recette_Regroupee_Affectation.zip)

- [439 — couverture antérieure](../../HisabPro_439_Couverture_Exploitation.zip)

Les lots 439/449 documentent la couverture sans modifier les résultats humains.
Le cumulatif final est calculé après 449 depuis les 1096 empreintes du début du
15 octobre 00:07 UTC. Il contient les versions finales des seuls fichiers changés,
pas le projet complet ;le checkpoint 440 reste une livraison historique distincte.

## État du projet et limites

| Axe | Statut |
|---|---|
| Développement global | Partiel :70 fonctions, 15 terminé/47 partiel/4 absent/4 bloqué |
| Tests automatisés | Validés sur les périmètres etsources des preuves ci-dessus |
| Recette utilisateur | À effectuer ;218 cas non prévalidés, 115 guides/recettes préservés |
| Mise en production | Non validée ;migrations réelles non effectuées |

085–091 sont manuelles etne s'appliquent pas par copie des fichiers ou bootstrap.
Le CLI 090 ne comprend pas 091 ;la décision091 et son PV fictif sont désormais restaurés avec fichiers et ACL au lot452. Les rôles/secrets, autres propriétaires, fichiers joints, droits des
autres modules et variantes annuelles doivent encore être qualifiés pour la cible.
Paie définitive, annexes officielles etschémaEDI gardent leurs blocages documentaires.
Les justificatifs historiques FEC/ETIC ne sont pas inventés, aucune certification
ou décision humaine automatique n'est annoncée. **Point 6 reste en attente.**

Prochaine tâche précise :contrôles des montants des autres flux commerciaux, propositions ambiguës et modèles complexes ; ne pas réappliquer451–459. Les anomalies nécessitant des pièces ou une
décision humaine restent visibles ;les autres tâches peuvent continuer en isolement.

## Reprise après le cumulatif450 — lots451–459

- Pièces : conservation au refus SQL et sérialisation avec validation ; les
  originaux comptables restent intacts et les erreurs de suppression visibles.
- Téléchargements :404/401 affichés, aucun JSON enregistré comme faux PDF.
- Modèles : choix achat/vente et trésorerie jusqu’au lettrage/FEC ; proposition
  de vente100HT auparavant déséquilibrée D100/C140, maintenant100/20/120.
- Journal : consultation seule cohérente, pièces/audit/diagnostics conservés,
  aucun POST automatique de réparation pour le lecteur ; backend403 inchangé.
- Montants : dépassement fini de capacité refusé422 au lieu de500, sans changer
  les schémas ni l’arrondi existant. Autres flux et précision extrême à étendre.
- Restauration :73tables, quatre PDF et décision/PV fictifs091 avec ACL natives,
  cible main:app sous LOGIN limité. Chèques/effets, impayés/frais et deux annuels
  également rejoués sur installation complète.

Toutes ces vérifications utilisent des sociétés et montants fictifs et PostgreSQL
nonce. Aucune base réelle, migration historique, guide ou recette humaine modifiée.

| Lot | Réussis | Échecs / erreurs / ignorés | Durée XML | Preuve |
|---|---:|---|---|---|
| 451 | 44 | 0 / 0 / 0 | 154.322 s | [Rapport](../../Test/rapport_justificatifs_modeles_451.md) |
| 452 | 24 | 0 / 0 / 0 | 140.157 s | [Rapport](../../Test/rapport_restauration_justificatifs_452.md) |
| 453 | 46 | 0 / 0 / 0 | 142.678 s | [Rapport](../../Test/rapport_pieces_telechargement_453.md) |
| 454 | 48 | 0 / 0 / 0 | 108.875 s | [Rapport](../../Test/rapport_modeles_journal_454.md) |
| 455 | 80 | 0 / 0 / 0 | 184.900 s | [Rapport](../../Test/rapport_modeles_detection_455.md) |
| 456 | 79 | 0 / 0 / 0 | 161.817 s | [Rapport](../../Test/rapport_instruments_runtime_456.md) |
| 457 | 94 | 0 / 0 / 0 | 227.102 s | [Rapport](../../Test/rapport_journal_lecture_457.md) |
| 458 | 79 | 0 / 0 / 0 | 193.364 s | [Rapport](../../Test/rapport_ecritures_capacite_458.md) |
| 459 | 61 | 0 / 0 / 0 | 161.461 s | [Rapport](../../Test/rapport_consolidation_reprise_459.md) |

Les suites se recouvrent : ne pas additionner ces nombres. Les erreurs initiales
et corrections du banc sont conservées dans leurs rapports. La consolidation
finale passe61cas ; source commune31sociétés/63écritures/168lignes,2clôtures,
20liens de lettrage et15justificatifs. Zéro déséquilibre/non-fini/définitive sans
numéro/date ; droits et16sources inchangés. Les dossiers négatifs gardent leurs
anomalies visibles : pas de déclaration globale « prêt à déposer ».

Build final Vite réussi4,70s, avertissements xlsx/bundle conservés ; compilation
Python exécutée pour les fichiers modifiés et nouveaux bancs. La globale430 reste
historique ; aucune nouvelle globale complète ni recette humaine revendiquée.

### ZIPs différentiels de reprise

- [451](../../HisabPro_451_Justificatifs_Modeles_Runtime.zip)
- [452](../../HisabPro_452_Restauration_Justificatifs_ACL.zip)
- [453](../../HisabPro_453_Telechargements_Pieces_Refuses.zip)
- [454](../../HisabPro_454_Modeles_Journal_Lettrage_FEC.zip)
- [455](../../HisabPro_455_Modeles_Detection_Montants.zip)
- [456](../../HisabPro_456_Instruments_Annuels_Runtime.zip)
- [457](../../HisabPro_457_Journal_Consultation_Seule.zip)
- [458](../../HisabPro_458_Ecritures_Capacite_Montants.zip)
- [459](../../HisabPro_459_Recette_Regroupee_Reprise.zip)

Le lot460 actualise la couverture sans promouvoir de statut humain. Le cumulatif
sera calculé depuis les empreintes de début de cette reprise, après450 ; seules
les versions finales des fichiers changés seront incluses. Le reçu de vérification
final sera consigné dans CODEX_PROGRESS.md, les anciens ZIPs restant conservés.

Développement global partiel, tests automatisés validés dans leurs périmètres,
recette utilisateur à effectuer et production non validée. Les textes officiels,
annexes et justificatifs manquants ne sont pas inventés. **Point6 en attente.**
