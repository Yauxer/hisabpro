# Démarrage de développement et protections du référentiel paie — 8 octobre 2026

Le modèle livré227 permet à `create_all()` de créer la table de versions, mais
ne suffit pas à installer ses triggers d'immutabilité ni ses permissions SQL.
Le helper du correctif229 applique désormais aussi le script082 existant,
après080/081. Aucun script historique modifié. La politique de création du
schéma reste inchangée : développement autorisé, production désactivée par
défaut. Le rôle d'installation doit appliquer les migrations séparément en
production ; le rôle runtime n'est pas transformé en administrateur.

Les versions documentaires ne modifient ni les taux ni la comptabilité.
La relance conserve les preuves existantes et installe les protections
UPDATE/DELETE/TRUNCATE, également pour un propriétaire lors d'une opération
ordinaire. Les champs de contrats historiques restent facultatifs.

## Exécutions du principal

Avant cette extension, relance des régressions229 et de la politique de
démarrage : **14 réussis en41,33s**, code0. Après extension à082 :

```text
PYTHON_DOTENV_DISABLED=1 python -X utf8 Test/run_unit_tests.py Test/test_demarrage_grh_base_existante_postgres.py Test/test_session132_bootstrap.py --tb=short --show-capture=no
```

**15 réussis en54,52s**, code0. Le vrai import de main dans un sous-processus,
suivi de HTTP200 sur `/api/health`, vérifie la présence des deux triggers082.
Le nouveau scénario conserve une version fictive au travers de deux relances,
refuse UPDATE/DELETE/TRUNCATE23514 puis compare chaque colonne. Référentiels
et tables salariés/écritures inchangés. L'ancienne écriture validée fictive100/100
et ses lignes restent identiques dans les tests229 réutilisés.

Compilation du helper et du fichier de tests : code0. Aucun frontend changé
par ce lot ; build de la carte documentaire vérifié dans son lot séparé.

Toutes les bases sont des PostgreSQL éphémères gardés par nonce, répertoire,
port et URL. Aucun PostgreSQL réel, aucun serveur utilisateur arrêté ou appelé.
Application du correctif sur la base réelle : validation utilisateur distincte.

## Suite

Le script082 doit être présent avec080/081 dans le dossier backend lors du
démarrage autorisé. La présence de preuves partielles ne valide aucun taux et
ne débloque jamais une paie définitive. Installation vierge et permissions
runtime082 sont vérifiées dans le lot d'installation séparé231.
