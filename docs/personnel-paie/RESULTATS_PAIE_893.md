# Qualification des campagnes et du brut simulé — 28 octobre 2026

Campagnes normales mensuelles et snapshots du brut sont livrés pour recette. Le calcul additionne la base mensuelle sur mois complet confirmé et les gains approuvés ; les situations incomplètes ou ambiguës produisent des anomalies explicites. Cotisations, IR, net, coût employeur et bulletins restent non calculés.

## Tests exécutés

**171 cas distincts réussis** : 104 unitaires/source, 51 API/SQL/restauration PostgreSQL natif isolé et 16 Edge/API/PostgreSQL isolé. La sélection finale comporte169 cas de qualification élargie et deux restaurations distinctes ; les petites campagnes antérieures ne sont pas additionnées.

| Campagne | Résultat | Durée |
|---|---|---:|
| paie893_api | 19 réussis | 73,32 s |
| paie893_ui | 17 réussis, dont2Edge | 53,01 s |
| paie893_final, 14 fichiers pytest | 169 réussis ;aucun échec, erreur ou ignoré | 674,92 s |
| paie893_restauration | 1 échoué | 69,43 s |
| paie893_restauration_corrige | 1 réussi | 60,71 s |
| paie893_restauration_coffre | 1 réussi | 55,34 s |
| Build frontend final | code0, 205 modules | Vite5,82 s |

Compilation Python : **12 fichiers**. Candidat : **502 fichiers produit** par SHA-256. Le produit est resté inchangé pendant la qualification finale. Les avertissements xlsx/chunk, Pydantic et SQLAlchemy existants restent visibles, sans être requalifiés en échecs.

## Restauration et correction du comparateur

Le premier test de restauration a révélé une différence textuelle de représentation des casts dans les prédicats d'index partiels : PostgreSQL redistribue des casts de tableau lors du dump/restauration. Le comparateur de tests vérifie maintenant ces prédicats après reparsage par PostgreSQL sur tables temporaires ; les clés, l'unicité, la méthode et les options d'index restent comparées exactement. Aucun index ni prédicat n'est ignoré et aucune migration déjà livrée n'a été modifiée.

Une preuve négative a été exécutée : le prédicat d'un index a été réellement modifié **sur la seconde cible nonce temporaire**, la comparaison l'a refusé, puis l'index original a été restauré et le schéma à nouveau vérifié. La base source est restée inchangée.

La restauration corrigée porte sur **91 tables**, schéma, données, séquences et ACL. La simulation, son contenu et son empreinte sont restitués sous un rôle applicatif non propriétaire et limité. La cible temporaire est supprimée après contrôle. En complément, le scénario de restauration du coffre **85 tables**, avec clés séparées, refus sans clé et récupération, a été rejoué avec le nouveau comparateur :réussi.

Ces tests utilisent uniquement PostgreSQL natif isolé avec nonce. Aucun PostgreSQL utilisateur, `.env`, clé réelle ou donnée comptable réelle n'a été utilisé. Les dumps restent dans les bacs temporaires et ne sont pas livrés.

## Parcours et contrôles couverts

Brut exact9000,10+800,01+1,01=9801,12MAD ; absence de faux net ; date d'entrée inconnue ; entrée/sortie ou changement de salaire/contrat dans le mois ; bases horaires ; variables en attente ; retenues/remboursements non qualifiés ; changement de source d'une variable approuvée ; reprise idempotente et concurrence ; versions immuables ; isolation des sociétés ; droits et révocation ; contrôle SQL des snapshots ; absence d'écriture et préservation de l'historique.

Les E2E des campagnes emploient un jeu plus réduit, avec un seul gain800,01MAD :première simulation bloquée par le brouillon, deuxième version9800,11MAD après approbation, ancienne version toujours incomplète. Les deux calculs correspondent à leurs jeux distincts ; ils ne sont pas confondus. Les parcours desktop1440 et mobile390 contrôlent aussi l'absence de débordement horizontal global et de conservation du résultat dans le stockage navigateur.

Les modules catalogue/variables et les parcours Personnel impactés ont été rejoués. Le nombre d'entrées « À venir » dans la sidebar est passé à6 parce que les rubriques02 et03 sont réellement accessibles ; le test de rubrique future vérifie désormais Charges sociales.

## Documents et statuts

[Preuve structurée et JUnit](../../Test/PREUVE_PAIE_893.json), [guide](CAMPAGNES_BRUT_893.md), [PDF6cas/4pages](RECETTE_CAMPAGNES_PAIE_893.pdf), [Excel3feuilles](SUIVI_CAMPAGNES_PAIE_893.xlsx), [jeu exact](JEU_CAMPAGNES_PAIE_893.json), [desktop](preuves/893_1440_campagne.png), [mobile](preuves/893_390_campagne.png). Tous les statuts humains restent **Non testé**. Le [point d'entrée](MODE_EMPLOI_PERSONNEL_PAIE.md) relie les quatre cahiers.

| Axe | Statut |
|---|---|
| Campagnes normales et simulation explicite du brut | Livré pour recette |
| Tests automatisés de ce périmètre | Réussis en environnement isolé |
| Cotisations/IR/net, cas complexes, approbation/verrouillage définitifs, bulletins | À développer dans les sous-étapes suivantes |
| Recette utilisateur et installation réelle115 | À effectuer sur copie |
| Production | Non validée |

Aucune certification ou conformité officielle n'est revendiquée. Les simulations brutes restent non validées juridiquement, même lorsque leurs totaux arithmétiques sont complets.
