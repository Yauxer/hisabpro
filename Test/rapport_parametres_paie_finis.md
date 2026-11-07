# Paramètres de cotisations — valeurs finies, 8 octobre 2026

## Preuve avant correction

`TauxCotisationUpdate` accepte trois floats facultatifs sans validation métier.
Le moteur `services/paie_service.py` exige déjà des ratios de 0 à 1 inclus et,
lorsqu'il existe, un plafond strictement positif. Cette incohérence autorise
l'enregistrement de paramètres que le moteur ne peut ensuite exploiter.

Commande réellement exécutée avant toute modification de l'application :

```text
PYTHON_DOTENV_DISABLED=1 python -X utf8 Test/run_unit_tests.py Test/test_parametres_paie_finis.py -k "schema or api_refuse" --tb=short
```

Résultat : **54 échoués, 18 réussis, 15 désélectionnés, 17,64 s**.
Les 72 cas sélectionnés comprenaient 36 contrôles de schéma et 36 PATCH réels.
Pour chaque champ, les non finis, booléens et bornes incohérentes sont acceptés ;
les objets/listes et textes non numériques sont déjà refusés.

Une seconde expérience compacte, avec connexion JWT réelle et PostgreSQL
éphémère, établit précisément :

| Champ | Valeur envoyée | HTTP avant correction | Valeur réellement stockée |
|---|---|---:|---|
| taux_sal | NaN | 500 | NaN |
| taux_pat | NaN | 500 | NaN |
| plafond | NaN | 500 | NaN |
| taux_sal | true | 200 | 1.0 |
| taux_pat | true | 200 | 1.0 |
| plafond | true | 200 | 1.0 |

Le handler commit avant de sérialiser sa réponse : HTTP 500 ne signifie donc
pas absence de mutation. Les tests vérifient tout le référentiel et les autres
valeurs valides du même PATCH, afin de contrôler l'atomicité du refus.

## Correction et validation

Lecture historique avant correction : première exécution arrêtée par une
fixture SQLAlchemy mêlant entiers et chaînes numériques (15 échecs en 19,47 s,
aucun appel API exploitable). Semis corrigé avec des floats explicites.
Relance `-k historique --tb=short` : **15 échoués, 87 désélectionnés, 16,36 s**.
Les neuf non finis provoquent HTTP 500 sur GET taux et GET préparation ; les
deux taux NULL échouent également à la lecture. Les quatre valeurs finies hors
bornes sont lisibles mais ne fournissent aucun diagnostic `anomalies`.

Après levée explicite du gel par l'agent principal, validation `before` des
trois champs : booléens et non finis refusés, ratios dans [0, 1] et plafond
strictement positif. `None` et omission conservent les valeurs comme avant.
Les PATCH invalides rendent HTTP 422 avant toute mutation, y compris leurs
autres champs valides. Les bornes 0 et 1 restent autorisées pour les taux.

Un helper pur commun sérialise les taux dans GET, PATCH et la préparation
mensuelle. Les non finis et taux absents deviennent `null` avec diagnostic
explicite ; les valeurs finies hors bornes restent affichées avec diagnostic.
Un plafond NULL reste légitime. Le moteur utilise toujours les valeurs brutes
et bloque la simulation invalide avec totaux NULL. Aucune donnée historique
n'est réécrite. Les tests vérifient sa conservation avant correction explicite
du paramètre via PATCH valide, puis la reprise de la simulation.

Commande réellement exécutée après correction :

```text
PYTHON_DOTENV_DISABLED=1 python -X utf8 Test/run_unit_tests.py Test/test_parametres_paie_finis.py Test/test_paie_grh_service.py Test/test_paie_grh_postgres.py --tb=short
```

Résultat : **148 réussis, 28 avertissements, 43,26 s**, aucun ignoré ni échec.
Répartition : 102 cas du nouveau module, 46 cas connexes service/GRH PostgreSQL.
Authentification et API réelles, PostgreSQL éphémère gardé par nonce.
La compilation `python -m py_compile` des trois fichiers applicatifs et du
nouveau test a terminé avec code 0.

## Limites distinctes

Les taux sont actuellement globaux par année, sans `societe_id`. Un administrateur
d'une société peut modifier un référentiel potentiellement utilisé par d'autres.
Cette limite d'administration et de cloisonnement doit faire l'objet d'une
décision et d'un lot distincts ; la présente correction numérique ne la résout pas.

Les anciennes valeurs invalides ne seront pas réparées automatiquement : un
taux CNSS/AMO ne peut être inventé pour remplacer une valeur manquante ou NaN.
Le GET des taux historiques non finis et la préparation sont désormais
diagnostiqués sans erreur 500 pour les cas exécutés. Toute correction effective
du référentiel demeure une décision justifiée à effectuer par un administrateur.

Aucune nouvelle cotisation, assiette ou taux réglementaire n'est prescrit. Les
valeurs de laboratoire2099 sont exclusivement des fixtures synthétiques, pas
un référentiel fiscal ou social. PostgreSQL réel et données comptables réelles
jamais utilisés. Toutes les expériences utilisent les gardes URL loopback,
répertoire et nonce et arrêtent/nettoient leurs processus temporaires.
