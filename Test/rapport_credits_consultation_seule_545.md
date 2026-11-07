# Lot545 — consultation seule des avoirs et acomptes

## Périmètre et correction

Les pages Avoirs et Acomptes proposaient au lecteur des commandes déjà refusées
par l'API : création d'acompte, comptabilisation, imputation, remboursement,
annulation d'utilisation/imputation et confirmation ou rejet d'un chèque.

Les deux pages réutilisent `peutEcrire()` comme Factures et Journal. Les
commandes et formulaires de mutation sont réservés aux rôles autorisés ; le
bouton Nouvel acompte est désactivé et grisé pour la consultation seule.
Les détails, montants disponibles, statuts, historiques et PDF restent
consultables. Masquer le bouton d'annulation ne change jamais une utilisation
active en « Annulée ». Le comptable garde les commandes existantes.
Aucun backend, permission, calcul, migration ou donnée comptable modifié.

## Tests exécutés

- Avant correction : **4 échecs, 2 réussites, 29 avertissements, 52.00s**,code1.
  Les deux parcours comptables passent. Les lecteurs collectent les écarts des
  deux pages ; PDF, historiques, absence de mutation et403 directs sont aussi
  vérifiés avant l'assertion finale des commandes.
- Après correction : **6 réussites,29avertissements,51.22s**,code0.
- Connexes : **28 réussites,29avertissements,202.47s**,code0.
  `Test/run_unit_tests.py Test/test_e2e_acompte_fournisseur_isole.py
  Test/test_e2e_avoir_fournisseur_isole.py
  Test/test_concurrence_avoirs_runtime_postgres.py
  Test/test_permissions_acomptes_avoirs_postgres.py
  Test/test_e2e_factures_lecture_isole.py Test/test_e2e_journal_lecture_isole.py -ra`.
  Les bacs TestClient/PostgreSQL historiques et les E2E sont distingués du
  serveur LOGIN098 des six nouveaux cas. Aucun échec/erreur/ignoré.
- Build `npm run build` : réussi,**7.10s**,code0. Les avertissements de taille
  et découpage des bundles restent visibles. Un Python ajouté compilé,
  98SQL et115guides inchangés. Ces commandes ne constituent pas une nouvelle
  exécution des603tests backend précédents : tous les fichiers backend sont
  vérifiés identiques à la baseline après543.

Commande ciblée : `Test/run_unit_tests.py
Test/test_e2e_credits_lecture_isole.py -ra`, `PYTHON_DOTENV_DISABLED=1`.

Vente/achat, lecteur390/1440px et comptable1440px : factures120/240MAD,
règlement120, avoirs60 et30 dont le premier est comptabilisé et imputé20
(crédit libre40), acomptes120/60/80 dont60 est imputé30 et80 est un chèque
en attente. Toutes ces données sont fictives et créées par les API du bac.
Les écritures créées pour la préparation sont réellement validées.

Chaque parcours consulte les deux pages, télécharge un vrai PDF d'avoir et
contrôle les historiques actifs et le chèque en attente. Les tables métier
doivent rester identiques. Le lecteur n'émet aucune requête de mutation depuis
les écrans ; les six types d'appels directs aux API restent refusés403.
Le comptable doit retrouver les commandes habituelles, sans effectuer de
mutation pendant cette recette de consultation.

Une première application du patch a expiré pendant la revue automatique
d'autorisation ; inspection confirmant aucun fichier changé ni test lancé.
L'unique nouvelle tentative a réussi. Ce délai n'était pas un refus de sécurité.

## Limites

PostgreSQL nonce et Edge locaux exclusivement, rôle API non propriétaire pour
les six cas ciblés. Aucun PostgreSQL de l'utilisateur, aucun courriel envoyé.
La qualification backend543 de356+247 exécutions reste une preuve antérieure
sur des fichiers backend inchangés ; elle n'est pas déclarée relancée ici.
Les nouvelles vérifications portent sur les interfaces et leurs parcours liés.
Recette utilisateur et production non validées ; point6 humain toujours réservé.

Installer `src/pages/Avoirs.jsx` et `src/pages/Acomptes.jsx`, puis reconstruire
le frontend avec `npm run build` pour une installation compilée. Aucun SQL.
