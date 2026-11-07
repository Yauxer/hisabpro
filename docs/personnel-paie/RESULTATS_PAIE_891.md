# Qualification des variables mensuelles — 28 octobre 2026

Variables exactes avec source et justificatifs, snapshots du contrat/salaire/rubrique approuvés à date, annulation de brouillon, soumission, décision indépendante et historique sont livrés pour recette. Les doublons, récurrences et incompatibilités sont contrôlés ; une modification de source entre préparation et décision bloque la validation au lieu de recalculer silencieusement.

## Tests réellement exécutés

**98 cas distincts finalement réussis** : 54 unitaires/source, 40 API/SQL PostgreSQL natif isolé, 4 Edge/API/PostgreSQL isolé. Le résultat est constitué de la qualification élargie et du rejeu ciblé des deux tests navigateur corrigés, sans additionner les cas qui se recouvrent.

| Campagne | Résultat | Durée |
|---|---|---:|
| paie891_api | 24 réussis, 6 échoués | 96,93 s |
| paie891_corrige | 30 réussis | 101,57 s |
| paie891_ui | 2 échoués | 55,80 s |
| paie891_qualification | 96 réussis, 2 échoués, aucune erreur ou ignoré | 381,30 s |
| paie891_ui_corrige | 2 réussis | 62,43 s |
| Build frontend final | code0, 204 modules | Vite 8,36 s |

La première API a révélé une date de rémunération non sérialisée dans le snapshot JSON. Correction : encodage explicite des dates, en conservant les montants exacts sous forme textuelle. Les six cas ont ensuite réussi. Des contrôles supplémentaires ont été ajoutés pour le bénéficiaire, l'auteur inactif, les masques et la migration rejouée avec données.

Les deux échecs navigateur sont une ambiguïté de sélecteur Playwright entre l'option « Approuvée » du filtre et le statut affiché dans la ligne. Le parcours avait atteint la vraie approbation. Le sélecteur est maintenant limité à la région de la variable ; les deux cas ont été rejoués jusqu'aux contrôles finaux de révocation et d'absence d'écriture. Le produit est identique entre la qualification élargie et ce rejeu ; seuls les sélecteurs de test ont changé. Les résultats initiaux sont conservés, sans succès fictif ni double comptage.

Compilation Python : **9 fichiers**. Candidat : **497 fichiers produit** vérifiés par SHA-256. Build initial et final réussis ; avertissements xlsx/chunk historiques conservés. La migration114 est additive, rejouée avant et après données ; les empreintes de toutes les anciennes tables restent identiques. Aucune ancienne migration exécutée n'a été modifiée.

Les tests utilisent uniquement des instances PostgreSQL natives temporaires protégées par nonce, avec rôle applicatif non propriétaire. Aucun PostgreSQL utilisateur ni `.env` réel n'a été utilisé. Les tests ne sont pas assimilés à une validation de la base de production.

## Contrôles couverts et livrables

Montants exacts, NaN/non finis/float/booléens refusés, période et date distinctes, arrondi documenté quantité×taux, pièces référencées manquantes, dossier incomplet, sources modifiées, approbation indépendante du préparateur et du bénéficiaire, auteur inactif rejetable, annulation traçable, source en double, récurrence mensuelle/annuelle, incompatibilités, isolation des sociétés, masques sans audit, décisions concurrentes, SQL immuable, absence de mouvement comptable et maintien du mois après Actualiser.

[Preuve structurée et JUnit](../../Test/PREUVE_PAIE_891.json), [guide](VARIABLES_PAIE_891.md), [PDF de recette](RECETTE_VARIABLES_PAIE_891.pdf), [Excel](SUIVI_VARIABLES_PAIE_891.xlsx), [jeu exact](JEU_VARIABLES_PAIE_891.json). Le complément contient10cas humains, PDF5pages et classeur3feuilles, tous **Non testé**. Données fictives :800,01MAD et3×0,335→1,01MAD ; total des deux gains801,02MAD. Avec la base contractuelle9000,10MAD, somme illustrative9801,12MAD, sans cotisations/IR/net. Captures : [desktop](preuves/891_1440_variables.png), [mobile](preuves/891_390_variables.png).

Les références de pièces sont déclarées et vérifiées humainement, sans preuve automatique d'un document externe. Le verrouillage des périodes par les campagnes et les règles réglementaires complexes restent à raccorder au lot3. Les variables approuvées ne sont pas des bulletins ni des paiements ; aucune exonération fiscale n'est activée par cette approbation. Recette utilisateur, installation réelle114 et production restent à valider sur copie.
