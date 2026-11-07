# Recette regroupée — logos et modèles

Le 16 octobre 2026, la commande réellement exécutée a terminé avec **136 réussis,
0 échec, 0 erreur, 0 ignoré**, en **406,28 s**, avec 29 avertissements de
dépréciation Pydantic/multipart. Code de sortie 0.

```powershell
python -X utf8 Test/run_unit_tests.py Test/test_consolidation_logos_modeles_20261016.py Test/test_lecture_ecritures_invalides_isole.py -ra
```

Le regroupement réutilise les scénarios existants : pièces et refus de
téléchargement, modèles et HT/TVA/TTC, avances personnel, logos PDF/XLSX et
impression, facturation achat/vente jusqu'au règlement et lettrage, paramètres
TVA, effets, FEC, clôture et restauration native. Les tests utilisent API réelle,
Edge et des clusters PostgreSQL à nonce, sous LOGIN applicatif `hisabpro` limité.
Les tests Node et de rendu PDF sont également exécutés, pas seulement collectés.

Les 131 cas du regroupement positif partagent le runtime 093 ; les cinq cas
négatifs de lecture sont exécutés dans un autre laboratoire. Les brouillons
anormaux de ce dernier ne sont pas inclus dans les invariants du laboratoire
positif. Aucun PostgreSQL utilisateur n'est consulté ou modifié.

## Contrôles après exécution

La preuve locale `consolidation469_preuve.json` a été contrôlée conjointement
avec le code de sortie et le résumé pytest, puis ses 134 empreintes ont été
comparées aux sources courantes : 93 migrations, tests et sources fonctionnelles.
Les ACL sont identiques avant/après. Les trois compteurs sont à zéro : pièces
déséquilibrées, montants non finis, écritures définitives sans numéro/date.

Le jeu positif comporte 58 sociétés fictives, 99 écritures, 249 lignes,
2 clôtures, 26 groupes de lettrage, 64 modèles et 150 lignes de modèle. Ce sont
des volumes de laboratoire, aucune affirmation sur les données de l'utilisateur.
La restauration 468 enrichie avec 092/093 conserve tables, séquences, ACL,
logos, pièces et FEC ; les essais de panne explicitement prévus dans les
scénarios ne sont pas assimilés à une absence générale de réponse 500.

## Anomalies rencontrées et corrigées

- Première campagne : 125 réussites et deux échecs en 375,47 s. Les corrections
  minimales sont livrées séparément en 471 (date locale d'effet) et 472 (TVA).
- Relance : 135 réussites et un échec en 405,92 s. Le droit SETVAL hérité a été
  retiré sur la seule séquence TVA dans 093 avant sa livraison ; six tests de
  droits/restauration ont ensuite réussi en 117,62 s.
- Relance suivante : 135 réussites et un échec en 418,53 s. La révocation du
  compte fictif du scénario 453 précédait la fin du chargement ; un 401 d'une
  lecture initiale provoquait légitimement un retour connexion avant le clic.
  Le test attend désormais `networkidle` avant révocation, sans intercepter
  l'API ni modifier le produit. Les assertions restent : téléchargement
  réellement refusé 401/404, message visible, aucun faux PDF, originaux inchangés.
  Les deux cas ciblés ont réussi en 39,58 s avant la campagne finale verte.

Compilation : 28 fichiers Python ajoutés/modifiés compilés sans erreur. Le
dernier build Vite des sources frontend de cette campagne est celui du lot 471,
réussi en 8,49 s. Les nombres des suites ciblées ne s'additionnent pas à 136.

Restent hors qualification : PostgreSQL réel, application manuelle des
migrations 092/093, boîte système d'impression, version Excel du partenaire,
recette humaine et production. Les autres consommateurs de lecture sont suivis
dans un lot distinct ; aucune écriture historique n'est réparée ici.
