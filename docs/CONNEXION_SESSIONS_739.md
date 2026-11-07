# MODE D’EMPLOI ET RECETTE — CONNEXION ET SESSION HISABPRO

Version 1 du 22 octobre 2026, correctif739.

## Utilisation

Un mauvais email ou mot de passe affiche désormais le refus du serveur dans
le formulaire. La page reste ouverte et l’email saisi est conservé. Corriger
le mot de passe puis cliquer Se connecter : la connexion valide ouvre le
tableau de bord. Le refus ne permet aucun accès aux données.

Si le serveur refuse le jeton de la session courante, HisabPro déconnecte
l’utilisateur et revient à la connexion. Il faut se reconnecter. Les requêtes
refusées ne sont jamais rejouées automatiquement, notamment les écritures,
les factures ou les paiements.

Si une ancienne requête est refusée après qu’une nouvelle session a remplacé
son jeton, elle affiche une erreur de changement de session sans déconnecter
la nouvelle session. Ce contrôle concerne le client partagé JSON et les
exports téléchargés par ce client. La requête ancienne reste refusée.

Le changement de mot de passe personnel conserve son fonctionnement : une
mauvaise confirmation reçoit HTTP 400 et reste une erreur de formulaire ;
ce lot ne modifie ni le backend ni la durée des jetons.

## Données de recette

Utiliser exclusivement un bac isolé et une société fictive Session recette739,
MAD, exercice 2026. Créer par le formulaire habituel un compte administrateur
avec un email de recette unique, par exemple session739@example.com, et un
secret fictif RecetteSession739!. Ne jamais réutiliser ces identifiants dans
un dossier réel. Pour le refus, saisir SecretIncorrect739!.

Aucune facture, écriture, déclaration ou règlement n’est nécessaire. Aucun
montant fiscal n’est calculé. Les comptes et pièces témoins du bac doivent
rester identiques après les essais de lecture et d’authentification.

## Vérifications utilisateur à effectuer

Les statuts ci-dessous restent Non testé malgré les tests automatisés. Les
situations de jeton expiré ou de réponse retenue doivent être préparées par
le responsable technique dans le seul bac isolé. Ne pas modifier les jetons
ni interrompre le serveur de production pour effectuer cette recette.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|SES739-01|Connexion ; email de recette créé ci-dessus, SecretIncorrect739! ; Se connecter.|Email ou mot de passe incorrect visible, même page, email conservé, aucune ouverture du dossier ; capture.|Non testé|
|SES739-02|Après SES739-01, remplacer uniquement le secret par RecetteSession739! ; Se connecter.|Tableau de bord de Session recette739, identité correcte ; capture. Répéter sur ordinateur et téléphone.|Non testé|
|SES739-03|Responsable prépare un jeton refusé de la session courante dans le bac ; demander une lecture ou un export.|Retour à Connexion, aucune donnée ou fichier reçu pour la requête refusée ; capture et trace HTTP 401. Sans préparation, classer Bloqué.|Non testé|
|SES739-04|Responsable retient une vraie réponse 401 d’une ancienne session puis ouvre une nouvelle session valide et libère le refus ; tester JSON puis export.|Nouvelle session conservée, ancienne demande refusée, aucune relance de mutation ; capture et trace réseau. Ce cas technique ne remplace pas une recette du sélecteur multi-société.|Non testé|
|SES739-05|Compte personnel → changement du mot de passe ; confirmer avec SecretIncorrect739! sans changer le vrai secret.|Erreur de confirmation visible, session conservée, secret et pièces inchangés ; capture. Comportement préexistant à vérifier.|Non testé|

## Preuves et limites

Le nouveau test utilise Edge, la vraie API et un PostgreSQL éphémère identifié
par nonce. Pour la course de sessions, il charge le client api.js réel compilé
dans le navigateur et retient une réponse réellement reçue du serveur ; aucun
succès ou refus métier n’est inventé. Le nouveau jeton valide provient de la
vraie API de connexion. Il ne s’agit pas d’un test complet du sélecteur de
société. Les refus courants comme anciens doivent laisser les données métier
inchangées. Les tests de connexion passent sur 1440 et 390 pixels.

Une ancienne occurrence de timeout avant le tableau de bord reste sous
surveillance : ce correctif ciblé des401 n’en établit pas la cause. Les tests
ne valent pas validation de la recette humaine ou de la mise en production.
Aucune migration ni donnée réelle modifiée. RH/paie et point 6 humain différés.
