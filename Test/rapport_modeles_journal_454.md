# Modèles du Journal, tiers, lettrage et FEC — lot 454

Extension de la recette des modèles existants sur le vrai `main:app`, installation
explicite 091, LOGIN SQL limité et PostgreSQL jetable. Aucun modèle, taux,
écriture historique, droit ou fichier produit modifié dans ce lot.

## Deux parcours contrôlés

Les tiers, sociétés, montants et documents sont fictifs. Le taux de 20 % provient
du modèle déjà présent et sert uniquement à l'oracle du banc ; son utilisation
ici ne qualifie ni un taux légal réel ni un droit à déduction.

| Étape | Achat, ordinateur 1 440 px | Vente, mobile 390 px |
|---|---|---|
| Modèle d'opération choisi dans Edge | Achat de marchandises | Vente de marchandises au Maroc |
| Saisie HT | 100 | 100 |
| TVA automatiquement calculée | 20 | 20 |
| TTC automatiquement calculé | 120 | 120 |
| Écriture attendue | 6111 D100, 34552 D20, 4411 C120 | 3421 D120, 4455 C20, 7111 C100 |
| Modèle de trésorerie choisi dans Edge | Paiement fournisseur | Encaissement créance client |
| Écriture de trésorerie attendue | 4411 D120, 5141 C120 | 5141 D120, 3421 C120 |
| Lettrage dans Edge | Deux lignes fournisseur, solde 0 | Deux lignes client, solde 0 |
| Total des deux pièces | Débit = crédit = 240 | Débit = crédit = 240 |

Les deux écritures sont validées immédiatement dans le formulaire. Le tiers est
sélectionné dans la liste réelle ; son identifiant natif est vérifié en base,
sans invention de libellé ou d'auxiliaire pour faire passer le contrôle.

Une pièce PDF est ajoutée après validation et téléchargée par API. Le lettrage
est conservé après rechargement. Les lignes et écritures sont comparées dans leur
représentation brute avant/après le rattachement et le lettrage : aucune réécriture.
Le FEC exporté contient cinq lignes de données, 18 champs par ligne, les totaux
indépendants de 240 et un code de lettrage commun d'au moins trois lettres.

Il s'agit de saisie comptable manuelle assistée, pas d'une facture commerciale.
Le test vérifie qu'aucune facture et aucun règlement commercial ne sont créés.
Le flux de trésorerie hors facture est celui du Journal prévu par le produit ;
le refus de l'API Règlements hors facture est respecté. Aucun exercice complet,
solde bancaire initial ou déclaration fiscale n'est implicitement validé ici.

## Résultats et preuves

- Premier essai : deux échecs en 41,03 s, sélecteur de modèle recoupant un avoir
  et attente GET tiers ne tenant pas compte de la pagination. Banc corrigé.
- Deuxième essai : un réussi, un échec en 29,80 s ; la vente mobile passe
  intégralement. Le second sélecteur achat recoupait le modèle de paiement en
  espèces. Correction du banc sur le libellé enfant exact, sans modification
  du produit ni relaxation d'oracle métier.
- Ciblé final : **2 réussis en 34,09 s**, 29 avertissements,
  zéro échec/erreur/ignoré (`modeles454_final.*`).
- Connexes : **48 réussis en 108,88 s**, 29 avertissements,
  zéro échec/erreur/ignoré (`modeles454_connexes.*`). Inclut les justificatifs,
  refus de téléchargement, modèles/capital/tiers, identité SQL du lettrage et FEC.
- Compilation Python du nouveau test : code 0. Aucun nouveau build nécessaire
  pour ce lot sans changement frontend ; le build 453 s'applique au même code.

Les XML/logs/exit `modeles454_cible`, `modeles454_v2`, `modeles454_final` et
`modeles454_connexes` sont conservés dans `.codex-tests/`, exclus du ZIP.
Les FEC et captures fictifs restent dans le dossier temporaire de pytest.
Les suites recouvrantes ne s'additionnent pas.

## Limites et suite

Cette recette couvre les quatre modèles mentionnés, pas l'intégralité de la
bibliothèque ni ses règles fiscales. La sélection explicite du modèle est testée ;
la proposition automatique et les modèles complexes restent à étendre.
Les sources officielles restent nécessaires avant toute nouvelle règle comptable
ou fiscale. Aucun PostgreSQL réel touché. Recette utilisateur et production
non prévalidées ; point 6 en attente.

Suite : mise à jour de la couverture et des procédures, ZIP différentiel de
chaque lot et cumulatif des seuls changements de cette reprise.
