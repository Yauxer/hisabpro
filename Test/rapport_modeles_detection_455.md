# Montants d'un modèle détecté automatiquement — lot 455

## Défaut reproduit

Dans le Journal, saisir le compte 7111 et 100 au crédit, puis appliquer le modèle
détecté de vente, produisait 3421 D100, 4455 C20 et 7111 C120 : débit 100, crédit
140. Le montant de la ligne source était interprété comme un montant principal
sans distinguer HT et TTC. La vente restait déséquilibrée et ne pouvait pas être
validée. Le cas achat équivalent passait.

La reproduction réelle dans Edge mobile/ordinateur, vrai `main:app`, PostgreSQL
nonce 091 et LOGIN non propriétaire donne un réussi/un échec en 27,47 s.
Aucune écriture erronée n'a été validée et aucune donnée historique n'est réparée.

## Correction minimale

Le calcul déjà employé lors de la saisie assistée est partagé dans
`src/utils/montantsModeles.js`, avec la distribution sur les lignes du modèle.
L'application d'une proposition reçoit désormais le compte source saisi et
conserve sa nature HT/TTC/TVA. Pour 7111 C100, elle calcule 3421 D120, 4455 C20,
7111 C100. Le même calcul sert ensuite aux modifications de montant du formulaire.

Les modèles complexes restent exclus de l'automatisation existante. Aucun modèle,
compte, taux ou règle fiscale nouvelle n'est ajouté ; les arrondis de présentation
existants sont conservés. Un montant, taux non fini ou débordement ne produit pas
de résultat automatique. Le choix explicite d'un modèle sans montant conserve
ses lignes à compléter.

## Tests et preuves

- Après correction : **2 Edge réussis en 26,93 s**, jusqu'à la création réellement
  validée et au tiers natif. Le parcours achat reste correct.
- Cibles complètes : **28 réussis en 28,81 s**, 29 avertissements,
  zéro échec/erreur/ignoré : 26 cas Node important le vrai module et deux Edge.
- Oracles Node indépendants : saisie HT, TTC ou TVA pour achat/vente ; paramètres
  fictifs 20/10/0 ; centimes, capital sans TVA, NaN/infini/source absente/taux infini
  et débordement. Montants attendus fixés dans les jeux, pas recopiés du calcul.
- Suite connexe : **80 réussis en 184,91 s**, 29 avertissements,
  zéro échec/erreur/ignoré. Inclut les modèles choisis/détectés, les justificatifs,
  téléchargements, capital/tiers, identité SQL du lettrage, FEC, erreurs de saisie
  et les deux cycles facture/paiements/lettrage existants.
- Build Vite : code 0, **4,67 s**, avertissement de taille de bundle conservé.
- `node --check` du module et compilation Python des deux tests : code 0.

Preuves locales exclues du ZIP : `modeles455_avant.*`, `modeles455_apres.*`,
`modeles455_cibles.*`, `modeles455_connexes.*`, `modeles455_build.*`.
Les suites recouvrantes ne s'additionnent pas. La globale historique 430 n'est pas
une qualification de ces modifications.

## Limites et suite

La recette porte sur la conservation des montants et le fonctionnement des modèles
existants, pas sur l'éligibilité fiscale des opérations d'un dossier réel. La
bibliothèque entière, les modèles complexes et les propositions ambiguës restent
à étendre. Les sociétés, tiers et montants de test sont fictifs ; aucune base
utilisateur, migration ou écriture définitive existante modifiée.

Recette utilisateur et production non prévalidées, point 6 en attente. Suite :
contrôler les instruments de paiement sous le même rôle SQL limité, actualiser la
couverture et les procédures, puis livrer le cumulatif de cette reprise.
