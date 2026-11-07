# Bilan de session — Personnel & Paie, 28 octobre2026

Départ :Personnel/coffre887 livré. L'utilisateur a demandé de développer aussi la paie. La session a poursuivi le master sans réappliquer les lots précédents et sans accès à la base PostgreSQL utilisateur.

## Changements utilisables sur copie

| Lot | Écran et comportement livré | Migration |
|---|---|---|
| 889 | **02 · Éléments de paie** :catalogue, règles séparées IR/CNSS/AMO, versions, dates, preuves déclarées, approbation indépendante ethabilitation réglementaire dédiée, aperçu pédagogique | 113 |
| 891 | **Variables mensuelles** :montant exact ouquantité×taux, contrat/salaire/rubrique approuvés àdate, source, pièces référencées, doublons/récurrences/non-cumuls, soumission/décision, historique etmasques | 114 |
| 893 | **03 · Traitement de la paie** :campagnes normales, simulation du brut, anomalies explicites, idempotence, recalcul parnouvelle version etanciens snapshots conservés | 115 |
| 895 | Consolidation documentaire etpréparation précise de 3B àpartir ducode réel etde sources officielles ; aucun moteur supplémentaire déclaré livré | Aucune |

Une entrée inconnue, un salaire non confirmé, une variable enattente, une modification intramensuelle ouun impact non qualifié ne devient jamais unzéro de secours. Les nouvelles simulations ne créent aucune écriture, dette, paiement oudéclaration.

## Vérifications exécutées

| Qualification | Résultat réel | Lecture du résultat |
|---|---|---|
| 889 | 175 cas distincts réussis ; build203 modules, 7, 74 s | Après corrections documentées ; catalogue, RH/navigation etpaie historique |
| 891 | 98 cas distincts finalement réussis ; build204 modules, 8, 36 s | Qualification96 pass2 fail puis2E2E corrigés qui remplacent ces deux échecs de sélecteur ; aucun doublecompte |
| 893 | 171 cas distincts réussis ; build205 modules, 5, 82 s | 169 qualifications élargies +restauration91 tables +contre-régression coffre85 tables |

**Ne pas additionner175+98+171** :les campagnes se recouvrent. La dernière qualification compte104 unitaires/source, 51API/SQL/restaurationPGnatifsisolés et 16Edge/API/PG. Le candidat courant fige502 fichiers produit. Aucun nouveau test produit n'est prétendu pour la seule consolidation895 ; les empreintes sont de nouveau vérifiées avant livraison.

La restauration91 tables vérifie schéma, données, séquences, ACL, rôle applicatif limité etlecture du snapshot avecson empreinte. Un index réellement altéré surla seconde cible temporaire est détecté. La première différence textuelle de casts PostgreSQL a été corrigée dans le comparateur de tests, avec reparsage serveur, sans modifier les migrations déjàlivrées. Le scénario coffre85 tables, avec clés séparées, refus sans clé etrécupération, a ensuite été rejoué avec succès.

Les tests utilisent uniquement des clusters PostgreSQL natifs temporaires vérifiés parnonce. Aucun `.env`, clé réelle, donnée comptable réelle oudump utilisateur n'a été utilisé. Les dumps temporaires ne sont pas livrés. Les processus utilisateur existants sont préservés ; aucun commit nipush Git effectué.

## Documents de recette

Le [point d'entrée](MODE_EMPLOI_PERSONNEL_PAIE.md) relie les guides, jeux exacts, PDF etclasseurs :59 cas Personnel887, 12 catalogue889, 10 variables891 et 6 campagnes893. **87 cas humains documentés**, tous Non testé ; les résultats réels, anomalies, observations etpreuves restent àremplir parles utilisateurs. Les sommes fictives sont cohérentes entre base, gains etversions de simulation.

Les rapports détaillés conservent les tentatives initiales échouées, les causes, les corrections etles limites. Aucun test interrompu ouignoré n'est annoncé réussi. Les captures proviennent réellement des parcours Edge avec données fictives.

## État et suite

| Axe | État courant |
|---|---|
| Personnel disponible, catalogue, variables, campagnes brutes | Livrés pour recette |
| Tests automatisés pertinents des lots livrés | Réussis surenvironnements isolés |
| Recette utilisateur | Àeffectuer |
| Cotisations/IR/net etbulletins définitifs | Àdévelopper ; 3B/3C puis3D/3E |
| Comptabilisation, paiements, déclarations etclôture de paie | Lots4–7 àsuivre |
| Installation réelle113–115, exploitation etproduction | Non effectuées/nonvalidées ; commencer surcopie |

La prochaine action est décrite dans [Préparation3B](PREPARATION_COTISATIONS_3B_895.md) :référentiel social exact parbranche etdate, sources/qualification dédiées, assiettes propres, moteur social séparé de l'IR, formulaires ettests. Un décret primaire nouveau a été retrouvé surl'ACAPS, mais l'exhaustivité des modifications etle champ2026 restent àqualifier avantactivation. Aucun taux de sites privés n'a remplacé un texte manquant.

La session s'arrête après livraison de son cumul etpoint de reprise, àl'approche de son budget de 2 heures. Elle ne déclare pas HisabPro oula paie complètement terminés etne demande pas unnouveau tour de confirmation technique pour reprendre les tâches déjàautorisées.
