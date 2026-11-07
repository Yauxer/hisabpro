# Recette connectée : cession et mise au rebut d'immobilisations

8 octobre 2026 — lot RECETTE-IMMO-SORTIE-20261008, demande AUG20-13.

## Périmètre et oracle indépendant

La recette acquisition/amortissement du lot 175 reste acquise dans son périmètre.
Ce nouveau lot ajoute uniquement un test et ce rapport : aucune modification
du moteur, des routes, des règles fiscales ou des données de l'utilisateur.

Chaque cas utilise sa propre société fictive. Les prérequis sont créés par les
API réelles : exercices 2024/2025, immobilisation acquise et mise en service le
1er janvier 2024, HT 10 000 MAD, TVA configurée 20 %, durée linéaire 5 ans, valeur
résiduelle 0. L'acquisition et la dotation 2024 sont validées avant la sortie.

Les constantes attendues sont fixées dans le test sans appeler le calculateur
applicatif. Annuité 10 000 / 5 = 2 000 MAD ; année complète 2024 puis année complète
ou demi-année 2025 selon la convention 30/360 déjà implémentée par le produit.
Cette recette n'établit aucune nouvelle règle d'amortissement ou de TVA.

| Cas | Date de sortie | Cumul amorti | VNC | Prix HT | TVA | TTC encaissé | Résultat de sortie |
|---|---|---:|---:|---:|---:|---:|---:|
| Cession | 31/12/2025 | 4000 | 6000 | 7500 | 1500 | 9000 | +1500 |
| Mise au rebut | 30/06/2025 | 3000 | 7000 | 0 | 0 | 0 | −7000 |

Le résultat ci-dessus concerne la sortie proprement dite (prix moins VNC),
distinct du résultat annuel incluant également les dotations.

## Écritures réellement contrôlées

Acquisition commune : D2355=10000, D34551=2000, C4481=12000.
Dotation2024 commune : D61935=2000, C28355=2000.

| Cas / pièce générée | Débit | Crédit |
|---|---|---|
| Cession — dotation 2025 | 61935 : 2000 | 28355 : 2000 |
| Cession — sortie du bilan | 28355 : 4000 ; 6513 : 6000 | 2355 : 10000 |
| Cession — produit et TVA | 3481 : 9000 | 7513 : 7500 ; 4455 : 1500 |
| Cession — encaissement immédiat | 5141 : 9000 | 3481 : 9000 |
| Rebut — dotation 2025 jusqu'au 30 juin | 61935 : 1000 | 28355 : 1000 |
| Rebut — sortie du bilan | 28355 : 3000 ; 6513 : 7000 | 2355 : 10000 |

Les comptes correspondent aux paramètres actuels du matériel informatique et
aux comptes de sortie existants. Le test vérifie les lignes exactes, l'équilibre
de chaque écriture et l'absence de produit, TVA ou encaissement pour le rebut.
La cession crée quatre nouvelles écritures ; le rebut en crée deux. La validation
de toutes ces pièces s'effectue ensuite par le journal dans le navigateur.

## Parcours et refus contrôlés

Edge charge l'interface complète et déclenche « Cession / mise au rebut », puis
« Comptabiliser la sortie ». Les montants de la réponse API sont comparés à
l'oracle ; le registre affiche Cédé/Rebut après mutation et rechargement. La
fenêtre se ferme, les actions de sortie/encaissement disparaissent et le message
de résultat apparaît sans rafraîchissement manuel.

L'acquisition et la dotation 2024 validées sont photographiées intégralement
(lignes SQL et toutes les colonnes des écritures) avant l'opération, puis
comparées après sortie, validation et essais refusés. Une tentative SQL de
modification de l'acquisition validée est refusée 23514 dans une transaction
annulée ; les snapshots restent exactement identiques.

Deuxième sortie, deuxième encaissement de la cession déjà encaissée, encaissement
d'un rebut et suppression de l'immobilisation comptabilisée : HTTP 409, sans
nouvelle écriture. Un profil lecture connecté réellement reçoit 403 pour les
mutations. L'administrateur d'une autre société fictive ne voit aucune de ces
immobilisations et reçoit 404 en tentant la sortie de leur identifiant. Les
écritures de la première société restent inchangées.

## Commandes exécutées

Exécutable : `hisabpro-backend/.venv/Scripts/python.exe -X utf8`.

| Commande après l'exécutable | Résultat réel |
|---|---|
| `Test/run_unit_tests.py Test/test_e2e_immobilisations_sortie_isole.py --tb=short` | 2 réussis, aucun échec ou ignoré, 25,20 s, exit 0, première exécution. |
| `Test/run_unit_tests.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py --tb=short` | 13 réussis, 0,24 s, exit 0. |
| `-m py_compile Test/test_e2e_immobilisations_sortie_isole.py` | Exit 0. |

Les 25 avertissements du parcours concernent les dépréciations Pydantic et
python_multipart déjà présentes. Aucune erreur JavaScript ni réponse 5xx
observée. Aucun bug applicatif ni correctif de règle n'a été nécessaire.

## Isolation et limites

Le support existant crée un cluster PostgreSQL dédié avec nonce, marqueur,
répertoire autorisé et port loopback distinct de 5432. La garde est revérifiée
avant la recette. API, frontend compilé, authentification et navigateur sont
réels ; aucun endpoint métier n'est intercepté. Le support termine seulement
ses propres processus et supprime son propre laboratoire.

Aucune connexion PostgreSQL réelle, lecture de données comptables réelles ou
action sur les processus main/Vite de l'utilisateur n'a lieu. Les sources de
l'application restent figées pendant la consolidation globale parallèle ; ces
nouveaux tests ne sont pas ajoutés rétroactivement à sa collecte.

Ces deux parcours ne couvrent pas l'encaissement différé réussi, une cession
partielle, une réévaluation, le dégressif, toutes les qualifications TVA ou la
facturation de la cession à un client identifié. Ils ne valident ni les règles
fiscales de plus-value, ni la recette annuelle utilisateur complète, ni les
pièces justificatives réelles, ni la mise en production.
