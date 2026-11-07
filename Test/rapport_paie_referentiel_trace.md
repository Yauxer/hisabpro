# Référentiel annuel de paie — traçabilité des preuves partielles

Lot PAIE-REFERENTIEL-TRACE-20261008, repris et testé le 8 octobre 2026.

## Modification

Les routes authentifiées `GET` et `POST /api/employes/referentiel?annee=…`
permettent de lire et consigner des versions par société et année. La lecture
reste accessible aux profils autorisés ; la consignation exige le droit
d'écriture et le rôle administrateur réellement contrôlés par le serveur.

Le serveur capture les trois listes présentes en base (barème IR, taux de
cotisations, déductions IR) dans une seule instruction PostgreSQL. L'empreinte
SHA-256 comprend la société, l'année et ces paramètres ordonnés. Une ancienne
empreinte provenant d'une autre société ou année est refusée même lorsque les
taux globaux sont identiques. Une modification des paramètres rend la version
consignée périmée ; son contenu historique reste intact.

Le client fournit uniquement des métadonnées bornées : références, périmètre,
limites, régime et commentaire. Une référence peut être une pièce sans URL ;
si une URL est renseignée, elle doit être HTTPS et sans identifiants. Aucune
URL n'est téléchargée. Les dates facultatives absentes restent absentes.

La migration additive et rejouable `082_paie_referentiels.sql` crée l'historique
avec unicité société/année/version. Le verrou transactionnel consultatif
sérialise deux consignations concurrentes sans demander de droit UPDATE sur
la société ni de verrou de table. Le rôle PostgreSQL `hisabpro` dispose
uniquement de SELECT/INSERT sur cette nouvelle table ; des triggers refusent
UPDATE, DELETE et TRUNCATE, également pour le propriétaire lors d'une
opération ordinaire.

Les statuts sont exclusivement `non_verifie`, `preuves_partielles` et, calculé
à la lecture, `perime`. `paie_definitive_autorisee` reste toujours faux. Aucun
taux nouveau, certificat, règle fiscale ni écriture de salaire n'est ajouté.
Des paramètres manquants autorisent la consignation partielle sans devenir
des taux inventés. Les valeurs historiques NaN/Infinity restent lisibles sous
forme de marqueurs JSON avec diagnostics ; leur consignation est refusée 409.

## Tests réellement exécutés

Exécutable de toutes les commandes :
`hisabpro-backend/.venv/Scripts/python.exe -X utf8`.

| Commande après l'exécutable | Résultat |
|---|---|
| `Test/run_unit_tests.py Test/test_paie_referentiel_service.py Test/test_paie_referentiel_postgres.py` | Première exécution : 14 réussis, 10 échoués, 17,81 s. Fixture CGNC vide empêchant l'inscription réelle ; ajout d'un compte de référence fictif requis, sans contournement métier. |
| Même commande avec `--tb=short` | 24 réussis, 14,90 s, exit 0. |
| `Test/run_unit_tests.py Test/test_paie_referentiel_service.py Test/test_paie_referentiel_postgres.py Test/test_paie_grh_service.py Test/test_paie_grh_postgres.py Test/test_parametres_paie_finis.py --tb=short` | 172 réussis, 64,13 s, exit 0. |
| Première commande avec `--tb=short`, après renforcement des assertions de préservation au replay | 24 réussis, 15,20 s, exit 0. |
| `-m py_compile hisabpro-backend/models.py hisabpro-backend/services/paie_referentiel_service.py hisabpro-backend/routers/employes.py Test/test_paie_referentiel_service.py Test/test_paie_referentiel_postgres.py` | Exit 0. |

Les 24 cas ciblés regroupent 14 tests purs et 10 cas API/PostgreSQL. L'API
FastAPI est appelée via TestClient avec authentification et permissions
réelles ; seule la dépendance de connexion est dirigée vers le laboratoire.
Le cluster PostgreSQL est exclusivement éphémère, loopback, port distinct de
5432 et nonce vérifié avant DDL. Le runtime se connecte réellement avec LOGIN
`hisabpro`, confirmé par `current_user` et `session_user`, sans CREATE sur le
schéma et sans privilèges de superutilisateur.

Les tests couvrent deux sociétés, années séparées, empreintes devenues
obsolètes, deux POST concurrents créant les versions 1 et 2, permissions lecture
et comptable, corps supplémentaires refusés, paramètres NaN/Infinity, sources
facultatives, immutabilité SQL et double replay. Ils comparent les paramètres
fictifs antérieurs ainsi que les trois référentiels, les comptes et les
écritures avant/après la migration. Les avertissements constatés sont des
dépréciations Pydantic et python_multipart existantes ; aucun test n'est ignoré.

## Limites et suite

Le PostgreSQL réel, l'application utilisateur et ses processus main/Vite n'ont
pas été utilisés ni arrêtés. Les essais de modification de paramètres portent
uniquement sur des données expressément fictives du cluster isolé. La recette
navigateur de la nouvelle carte relève du lot UI distinct.

La présence de sources déclarées ne prouve ni leur exactitude, ni leur
applicabilité annuelle, ni la conformité du barème complet. La confirmation
réglementaire 2026 et la paie définitive restent à établir séparément. Les
paramètres existants demeurent globaux par année ; cette étape ajoute une
preuve par société sans prétendre créer une configuration de taux par société.
La migration doit être appliquée pour activer ses protections SQL ; son
intégration à l'installation et au démarrage est vérifiée dans des lots séparés.

Fichiers du lot : `hisabpro-backend/models.py`,
`hisabpro-backend/082_paie_referentiels.sql`,
`hisabpro-backend/services/paie_referentiel_service.py`,
`hisabpro-backend/routers/employes.py`,
`Test/test_paie_referentiel_service.py`,
`Test/test_paie_referentiel_postgres.py`, et ce rapport.
