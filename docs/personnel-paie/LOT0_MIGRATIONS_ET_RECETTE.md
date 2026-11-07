# Personnel & Paie — Lot 0C : migrations, intégration et recette

Plan proposé, pas migrations livrées. Le plus grand préfixe SQL constaté est **104** (`104_liasse_balance_documents.sql`). Les numéros suivants doivent être vérifiés et réservés au moment du développement ; aucun fichier 080/081/082/092/095 ou autre migration historique n'est réécrit.

## 1. Ordre et dépendances existantes

1. Racines société/utilisateur/employé, exercices et plan comptable existants.
2. 080 ajoute les champs optionnels de dossier ; 081 ajoute les FK composites et l'historique d'absences ; 082 conserve les preuves de référentiel.
3. Le bootstrap de développement `grh_bootstrap_service.initialiser_schema_developpement` crée les clés composites requises **avant** `create_all` sur ancien schéma, puis rejoue 080/081/082. Préserver ce chemin et les tests de l'ancien plantage ForeignKey.
4. Les modèles d'écritures personnel sont en 092 ; le registre d'avances est en 095 et dépend de la fonction de détection d'exercice clos déjà présente. Sa table est SQL, pas uniquement définie dans l'ORM.
5. La politique de production sépare migrations et démarrage applicatif. Les nouvelles migrations passent par le rôle propriétaire/migrateur ; le rôle runtime reçoit uniquement les permissions requises. Ne pas ajouter silencieusement toute la roadmap au `create_all` de production.

## 2. Sous-migrations additives envisagées pour Lot 1A

| Étape | Contenu proposé | Contrôle avant validation |
|---|---|---|
| Préflight | Versions installées, types réels, clés composites, doublons/matricules manquants, droits runtime ; agrégats et diagnostics sous habilitation | Zéro écriture de réparation ; aucun contenu sensible dans un rapport diffusé largement |
| Fondation | Habilitations Personnel, événements métier append-only, extension 1:1 du dossier | PK/FK composites, révocation, restrictions SQL, aucun droit financier implicite |
| Versions | Contrats/rémunérations et demandes ; précision monétaire et dates d'effet | Versions uniques, absence de chevauchement approuvé, acteur indépendant, concurrence |
| Unicité matricule | Index de société sur valeurs textuelles qualifiées après préflight | Si doublons historiques : pas de renommage/fusion ; arrêt de cette étape et diagnostic explicite |
| Compatibilité | Reprise des seules métadonnées prouvées et activation contrôlée du service commun | Actif historique distinct d'une validation paie ; salaire/date inconnue non attestés ; anciennes routes sans contournement |
| Durcissement | Contraintes validées après contrôle, droits minimaux et déploiement documenté | Rejeu idempotent, runtime LOGIN non propriétaire, ancien schéma conservé, contrôle de sauvegarde/restauration |

Contraintes et longueurs doivent être définies dans la migration ET les schémas API. Les états d'approbation ne sont pas calculés à partir de la seule colonne historique `actif`. Aucune masse de données de paie ne doit être backfillée sous forme de règles ou d'historique supposé.

## 3. Déploiement et retour arrière

- Préparer et vérifier une sauvegarde chiffrée et ses pièces dans l'environnement cible autorisé. Cette préparation future n'autorise aucune opération sur une base utilisateur pendant Lot 0.
- Tester une copie vierge, un ancien schéma, une base au dernier état et le rejeu des migrations. Vérifier schéma/données/permissions/séquences, pas seulement le succès SQL.
- Déployer d'abord les structures compatibles, puis les API contrôlées, puis la navigation ; activer après habilitations, données et tests vérifiés. Aucune paie définitive autorisée par la simple activation d'un écran.
- En cas de retrait applicatif, désactiver les nouvelles mutations et garder les tables/historiques ajoutés. Vérifier qu'une ancienne version de l'application ne puisse pas contourner les approbations ou modifier les miroirs historiques.
- Ne pas présenter un `DROP TABLE` comme rollback de production. La restauration vers une autre cible est une opération contrôlée avec vérification avant bascule ; ne jamais restaurer automatiquement sur la source.
- Tester la lecture des archives, pièces, signatures de snapshots et clés de chiffrement restaurées ; la perte d'une clé ne se résout pas par un simple dump PostgreSQL.

## 4. Contrats API et invariants communs

Préfixe cible indicatif : `/api/personnel-paie`. Conserver les URL historiques avec un adaptateur explicite lorsque le nouveau service est activé. Toutes les lectures et mutations portent l'utilisateur authentifié, la société validée et une capacité requise. Ne pas accepter un `societe_id` du corps comme autorité.

- `POST /personnel` : dossier brouillon, aucune écriture ; minimum de données justifié, aucune obligation légale supposée depuis le seul formulaire.
- `GET /personnel`, `GET /personnel/{id}` : projection autorisée, filtrage/recherche/pagination stables, masque serveur salaire/identifiants selon capacités ; 404 pour objet d'une autre société.
- `POST /personnel/{id}/modifications` : changement typé, valeur décimale exacte et date d'effet si requise, motif et révision attendue ; aucun écrasement d'un salaire approuvé.
- `POST /modifications/{id}/soumettre`, `/approuver`, `/rejeter` : transitions autorisées, préparateur distinct de l'approbateur, motif/historique ; collision concurrente 409, absence de permission 403.
- `GET /personnel/{id}/historique` : événements et versions autorisés, pas un journal global exposant les données sensibles.
- Le contrat de sortie financière utilise des chaînes décimales exactes ; erreurs de validation structurées, pas `[object Object]`.

Ces chemins sont des propositions, pas des endpoints existants. Les paiements/déclarations/écritures ne font pas partie des API à développer en 1A.

## 5. Plan de recette cible

| Groupe | Cas minimaux et oracles |
|---|---|
| PP-SEC | Deux sociétés et trois rôles historiques ; capacités révoquées effectives ; fonction Personnel seule sans accès aux autres modules avant de l'autoriser ; API directe/ancien chemin/export protégés ; liste/log sans donnée masquée récupérable |
| PP-PER | Trois salariés ; refus doublon de matricule société A ; même matricule B autorisé ; espaces/texte et `02`/`002` préservés ; archive logique ; aucun mouvement comptable |
| PP-VER | Salaire actuel/futur, refus chevauchement approuvé, historique inchangé, version de révision périmée 409 ; hypothèse historique inconnue visible et exclue d'une paie définitive |
| PP-APP | Brouillon → soumis → approuvé/rejeté ; auto-approbation et approbation de sa propre paie refusées ; deux validations concurrentes ne créent pas deux versions |
| PP-MIG | Vierge/ancien/rejeu deux fois ; doublon historique détecté sans réparation ; clés composées correctes ; FK inter-société et droits SQL ; reprise de l'ancien bootstrap sans InvalidForeignKey |
| PP-RUB | Au/sous/au-dessus plafond, IR et CNSS distincts, non-cumul et justificatif, montant non fini/booléen, nouvelle règle applicable seulement à sa date ; aucune écriture à la saisie |
| PP-CAL | Dossiers de référence à faire valider : salaire fixe, variable, entrée/sortie, absence, rappel, temps partiel, avantages ; sous-totaux et coût employeur exacts ; ancien bulletin stable après changement de règle |
| PP-CPT | Campagne approuvée → OD équilibrée unique ; double clic/retry/concurrence ; plan actif, période fermée, exercice clos ; validation comptable séparée ; contrepassation contrôlée |
| PP-AVA | Avance 2000MAD approuvée/décaissée/retenue autorisée, pas de double charge/déduction ; solde à la sortie ; prêt selon classification validée et remboursement anticipé |
| PP-PAY | Trois salariés : deux réglés totalement, un partiellement ; transmis distinct d'exécuté ; refus/retour bancaire ; soldes organisme/État ; rapprochement sans seconde charge |
| PP-DEC | Préparée/validée distinct de déposée ; schéma officiel vérifié avant export ; preuve et date ; aucune API bancaire ou dépôt inventé |
| PP-CLO | Congés/primes acquis, absence de double dette, OD contrôlée puis extourne si applicable ; décembre N/janvier N+1 ; rapprochement avec bilan/liasse existants |
| PP-RES | Sauvegarde/restauration native isolée des tables, droits, séquences, fichiers, logos et snapshots ; accès restreints conservés |
| PP-UX | Sidebar neuf rubriques, route active, URL directe, rôle/société, mobile390x844 et ordinateur1366x768, formulaires/détails accessibles, rafraîchissement sansF5, aucune section future affichée comme livrée |

Chaque futur cas doit enregistrer données exactes, actions UI/API, résultats réels, écritures/impacts attendus, preuves et limites. Les exemples financiers pédagogiques du master ne sont pas des barèmes légaux. Le rapport de tests 871 porte exclusivement sur l'existant et les caractérisations.

## 6. Sources réglementaires et mapping

Le master §14 et les anciens rapports de sources sont des points de départ. Pour chaque règle : source officielle consolidée applicable, article, conditions, date d'effet, date de consultation et validateur. La simple présence d'une URL ou d'un chiffre dans le dépôt ne vaut pas validation. Les paramètres DGI, CNSS, AMO/autres restent séparés ; aucune nouvelle règle n'est codée ni déclarée obligatoire dans Lot 0.

Le mapping candidat du master §12 doit être rapproché du plan par société et de ses comptes utilisables : rémunérations/charges, dettes personnel/organismes/État, avances/prêts et banque. Les comptes et le traitement juridique des retenues, congés, prêts et départs nécessitent leur contrôle avant leurs lots respectifs. Le moteur ne devra jamais choisir un compte erroné comme défaut silencieux.
