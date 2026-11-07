# AGENTS.md — HisabPro

## 1. Mission du projet

HisabPro est une application marocaine de facturation, comptabilité et fiscalité destinée notamment aux TPE/PME et cabinets comptables. Le produit vise une architecture cohérente avec le CGNC, la loi n° 9-88 relative aux obligations comptables des commerçants, l’Avis n° 24 du CNC relatif à la comptabilité électronique et la fiscalité marocaine applicable.

Ne jamais présenter HisabPro comme « certifié », « homologué » ou « conforme officiellement » sans preuve officielle explicite. Toute règle comptable ou fiscale marocaine nouvelle ou modifiée doit être vérifiée sur une source officielle avant d’être codée ou affirmée comme obligatoire.

## 2. Source de vérité

Le dépôt de travail courant est la source de vérité.

Ne jamais supposer qu’un patch, une migration, un contrôle ou une fonctionnalité existe uniquement parce qu’il est cité dans ce fichier, dans un ancien échange ou dans une note de continuité. Toujours vérifier sa présence réelle dans le code, les migrations et les tests avant toute modification.

Avant d’intervenir sur une zone :

1. inspecter l’arborescence concernée ;
2. identifier le frontend, le backend, les modèles, migrations et tests liés ;
3. rechercher les implémentations déjà présentes avant d’ajouter du code ;
4. vérifier les effets de bord sur les modules existants ;
5. conserver les données et comportements déjà validés.

## 3. Méthode de travail obligatoire

Toujours avancer dans cet ordre : **analyse → correction minimale → tests → validation → prochaine étape**.

Pour chaque intervention :

- analyser le problème avant de modifier le code ;
- corriger la cause racine plutôt que masquer le symptôme ;
- éviter les refactorings non nécessaires dans la même étape ;
- ajouter ou mettre à jour des tests de non-régression pour les bugs corrigés ;
- exécuter les tests réellement disponibles ;
- distinguer explicitement :
  - tests automatisés exécutés localement ;
  - validations qui nécessitent le PostgreSQL réel de l’utilisateur ;
  - validations visuelles / fonctionnelles à faire dans le navigateur ;
- ne jamais déclarer un comportement « validé » si le test réel n’a pas été exécuté ;
- ne pas accumuler plusieurs anomalies connues avant de continuer une recette : corriger l’anomalie rencontrée, puis reprendre.

## 4. Livraison après chaque modification

Après chaque modification demandée par l’utilisateur, fournir un **ZIP différentiel**, jamais le projet complet.

Le ZIP doit contenir uniquement les fichiers ajoutés ou modifiés pendant l’étape, avec l’arborescence exacte du dépôt, par exemple :

```text
hisabpro-backend/...
src/...
Test/...
```

Ne pas inclure :

- fichiers inchangés ;
- caches ;
- `node_modules` ;
- environnements virtuels ;
- fichiers temporaires ;
- dumps de base de données sauf demande explicite.

Avant de livrer le ZIP, vérifier son contenu avec une commande de listing.

Le compte rendu final doit rester court et contenir uniquement :

- ce qui a été modifié ;
- résultat des tests automatisés ;
- ce qui reste à vérifier sur PostgreSQL réel / navigateur ;
- prochaine étape recommandée ;
- lien vers le ZIP différentiel.

## 5. Règles de sécurité sur les données et la base

Préserver les données existantes et les migrations déjà passées.

Ne jamais :

- supprimer ou réinitialiser une base sans demande explicite ;
- réécrire l’historique d’une migration déjà appliquée lorsqu’une nouvelle migration additive suffit ;
- modifier silencieusement des écritures comptables validées ;
- inventer des données fiscales ou extra-comptables manquantes ;
- reclasser arbitrairement une information uniquement pour faire passer un contrôle.

Toute migration doit être additive, idempotente lorsque cela est pertinent, et accompagnée d’un test ou d’un contrôle de non-régression.

Les écritures définitives doivent conserver leur piste d’audit. Toute opération de réparation de données historiques doit être distincte du flux métier normal et clairement documentée.

## 6. Principes comptables / fiscaux HisabPro

### 6.1 Écritures et justificatifs

Ne pas imposer automatiquement une date de pièce ou une référence justificative pour valider une écriture si la règle métier du produit ne l’exige pas. Les contrôles FEC / Avis n° 24 peuvent signaler ces informations comme manquantes sans forcément invalider l’écriture comptable historique.

Une modification d’écriture validée doit rester une opération contrôlée, réservée au rôle autorisé et traçable.

### 6.2 Tiers / comptes collectifs

Pour les comptes collectifs clients / fournisseurs, privilégier le rattachement réel au tiers et au compte auxiliaire lorsqu’il existe déjà dans les données sources.

Ne jamais inventer un tiers ou une échéance pour faire disparaître une anomalie FEC ou ETIC.

Les réparations historiques doivent être déterministes et non ambiguës.

### 6.3 Résultat fiscal / IS

Les calculs fiscaux doivent distinguer :

- résultat comptable ;
- réintégrations ;
- déductions ;
- déficits imputés ;
- bénéfice fiscal imposable ;
- IS théorique ;
- CM lorsque pertinente ;
- retenues / crédits ;
- acomptes ;
- solde final.

Une liquidation fiscale confirmée doit être figée sous forme de snapshot cohérent et rester auditable.

### 6.4 Données extra-comptables

Ne jamais déduire une information extra-comptable uniquement parce qu’elle paraît probable.

Exemples :

- ventilation ETIC par échéance ;
- créances / dettes en devises ;
- entreprises liées ;
- effets ;
- informations d’actionnariat ;
- événements postérieurs ;
- sûretés ;
- engagements hors bilan.

Automatiser uniquement ce qui est déterminable avec certitude depuis les données disponibles. Sinon afficher « à compléter », demander confirmation ou laisser un reliquat explicite.

## 7. UX / UI

HisabPro doit rester exploitable sans manipulations pénibles.

Règles récurrentes :

- éviter les tableaux nécessitant un déplacement horizontal inutile lorsque la largeur peut être adaptée ;
- prévoir un scroll horizontal lorsqu’il est réellement nécessaire ;
- ne pas masquer des lignes ou colonnes essentielles ;
- éviter les formulaires tronqués dans des fenêtres trop étroites ;
- charger instantanément les données statiques ou fortement cachables comme le plan comptable quand cela est possible ;
- après une mutation réussie, rafraîchir l’état local automatiquement : ne pas obliger l’utilisateur à faire F5 pour voir une facture, un règlement ou une écriture ;
- afficher automatiquement le libellé d’un compte lorsqu’un compte est sélectionné ;
- conserver les écrans de détail lisibles verticalement ;
- ne pas sacrifier la lisibilité comptable au profit d’un design décoratif.

## 8. Tests

À chaque correction, lancer d’abord les tests ciblés, puis les tests connexes raisonnables.

Pour le backend :

- `pytest` sur le test ajouté ;
- tests du module concerné ;
- compilation Python (`py_compile` ou `compileall`) pour les fichiers modifiés.

Pour le frontend :

- lancer le build Vite/React si les dépendances sont disponibles ;
- sinon le signaler explicitement ;
- vérifier l’absence d’erreurs syntaxiques dans les composants modifiés.

Pour PostgreSQL :

- ne pas remplacer une validation PostgreSQL réelle par SQLite si le comportement dépend de PostgreSQL ;
- SQLite peut servir pour des tests unitaires purs, mais la réponse finale doit dire clairement ce qui n’a pas été validé sur PostgreSQL.

## 9. État fonctionnel connu à vérifier dans le dépôt

Les éléments ci-dessous décrivent le dernier état de recette connu, mais **ne sont jamais une preuve de présence dans le code**. Les vérifier avant de s’y appuyer.

### 9.1 Facturation / comptabilité déjà largement couverte

La recette a notamment porté sur :

- devis ;
- bons de commande ;
- bons de livraison ;
- factures ;
- avoirs ;
- validation et écritures automatiques ;
- règlements clients / fournisseurs ;
- lettrage ;
- écritures manuelles ;
- rapprochement bancaire ;
- import Excel de relevés ;
- immobilisations ;
- livre d’inventaire ;
- balance de clôture ;
- FEC ;
- bilan ;
- CPC ;
- ETIC ;
- à-nouveaux ;
- fiscalité IS.

Un ancien FEC de recette avait été contrôlé à 6 écritures / 15 lignes, débit = crédit = 6 100 MAD, avec références justificatives complètes. Ne pas supposer que le jeu de données actuel est encore ce jeu de recette.

### 9.2 Patches fiscaux historiques à vérifier

Patches historiquement mentionnés :

- 088 : premier exercice / acomptes : « Non applicable » vs « Réf. manquante » ;
- 089 : retenues déjà imputées ;
- 090 : `compte_source` retraitements fiscaux porté à 120 caractères ;
- 091 : vrais comptes dans les contrôles de retraitements ;
- 092 : blocage d’une liquidation IS incohérente ;
- 093 : acompte partiellement payé après échéance → « Partiel — en retard » + reste à payer.

Vérifier leur présence réelle avant toute nouvelle intervention.

### 9.3 Dernière recette IS connue

Derniers chiffres de recette connus pour 2026 :

- résultat fiscal : 124 864,88 MAD ;
- IS théorique à 20 % : 24 972,98 MAD ;
- acomptes versés : 7 000,00 MAD ;
- solde : 17 972,98 MAD ;
- référence annuelle forcée des acomptes : 20 000 MAD ;
- acompte 1 : 5 000 MAD, soldé ;
- acompte 2 : 2 000 MAD versés sur 5 000 MAD, « Partiel — en retard » ;
- acomptes 3 et 4 non payés au moment du test.

La liquidation IS 2026 a ensuite été confirmée dans la recette et un snapshot fiscal a été affiché. Vérifier le code et l’état réel avant de se baser sur cette information.

## 10. Liasse fiscale — architecture retenue

La page **Comptabilité → Liasse fiscale** doit évoluer vers un cockpit fiscal annuel.

Roadmap retenue :

- **09A** — recette finale états / ETIC / liasse existants ;
- **09B** — référentiel exhaustif des tableaux DGI ;
- **09C** — XML / EDI SIMPL-IS ;
- **09D** — import Balance N / N-1 + mode « Liasse seule » ;
- **09E** — état des ventes ;
- **09F** — rémunérations allouées à des tiers ;
- **09G** — taxe professionnelle / déclarations annexes ;
- **09H** — contrôle final « Prêt à déposer » + dossier fiscal annuel.

L’objectif fonctionnel final inclut notamment :

- synthèse du dossier fiscal ;
- bilan ;
- CPC ;
- ESG ;
- tableau de financement ;
- ETIC ;
- tableaux fiscaux DGI ;
- résultat fiscal / IS ;
- CM ;
- CSS ;
- déficits ;
- acomptes ;
- retenues / crédits ;
- annexes ;
- contrôles de cohérence ;
- balance N / N-1 ;
- import balance ;
- mode « Liasse seule » ;
- PDF ;
- Excel ;
- XML / EDI ;
- FEC ;
- archivage définitif.

Ne pas implémenter XML / EDI SIMPL-IS avant d’avoir vérifié le schéma et les spécifications officielles réellement applicables.

## 11. État récent ETIC B6 / B7 — très important

Cette section est un **contexte de continuité**, pas une vérité de code. Vérifier les patches réels présents dans le dépôt.

Les derniers travaux portaient sur :

- **Patch 106** : B6/B7 structurés avec ventilation par échéance et analyses complémentaires ;
- **Patch 107** : tentative de préremplissage automatique depuis les factures / échéanciers ;
- **Patch 108** : diagnostic visible lorsqu’un solde ne recoupe pas les factures ;
- **Patch 109** : décomposition comptable du reliquat 3421 ;
- **Patch 110** : récupération déterministe de factures historiques ;
- **Patch 111** : préremplissage partiel sécurisé de la partie certaine ;
- **Patch 112** : récupération ETIC de factures historiques sans `tiers_id`, uniquement par rapprochement exact et non ambigu.

### Dernier état B6 connu

Compte 3421 Clients :

- solde comptable : 161 302,80 MAD ;
- 31 factures retrouvées ;
- dont 3 via rapprochement historique exact ;
- partie certaine « échues et non recouvrées » : 92 390,80 MAD ;
- reliquat non qualifié : 68 912,00 MAD.

Ne pas classer automatiquement les 68 912 MAD en échus sans source fiable.

### Dernier état B7 connu avant validation du Patch 112

Compte 4411 Fournisseurs :

- solde comptable : 45 960,00 MAD ;
- 3 factures retrouvées : 33 720,00 MAD ;
- partie certaine « échues et non payées » : 33 720,00 MAD ;
- reliquat : 12 240,00 MAD.

Les mouvements historiques 4411 observés incluaient plusieurs factures anciennes, un avoir et un effet à payer. Patch 112 a été préparé pour récupérer davantage de factures historiques dépourvues de `tiers_id` technique. **La validation réelle de Patch 112 sur PostgreSQL / navigateur n’était pas encore terminée au moment de cette note.**

## 12. FEC / Avis n°24 — problèmes historiques à ne pas oublier

Un contrôle FEC 2026 avait remonté jusqu’à 41 anomalies, puis le nombre avait été réduit au fil des corrections.

Types d’anomalies rencontrées :

- `AUXILIAIRE_MANQUANT` sur comptes 3421 / 4411 ;
- `REFERENCE_PIECE_MANQUANTE` ;
- déséquilibres entre comptes collectifs et auxiliaires ;
- écriture de clôture hors journal dédié ;
- anciennes écritures ne conservant pas le lien technique vers la facture ou le tiers.

Ne pas « corriger » une ancienne écriture définitive uniquement pour faire passer le FEC. Préférer une réparation historique traçable ou une récupération déterministe de source lorsque cela est justifié.

## 13. Conventions de développement Codex

Lorsque Codex travaille dans le dépôt :

- lire ce fichier avant chaque tâche significative ;
- commencer par `git status` et l’inspection des fichiers concernés ;
- ne jamais écraser les modifications non liées de l’utilisateur ;
- ne pas supprimer un fichier ou une migration sans justification ;
- éviter les commandes destructrices (`reset --hard`, nettoyage massif, suppression de DB) ;
- ne pas modifier plusieurs modules sans nécessité ;
- conserver la compatibilité avec les données existantes ;
- privilégier les fonctions métier partagées plutôt que dupliquer les calculs ;
- lorsqu’une logique fiscale ou comptable est réutilisée entre écran, PDF, Excel et contrôles, chercher à disposer d’une source métier unique ;
- préférer les rapprochements exacts et déterministes aux heuristiques ;
- en cas d’ambiguïté de données, ne pas choisir arbitrairement : rendre l’ambiguïté visible à l’utilisateur.

Ne pas créer de commit Git ni pousser vers un remote sauf demande explicite.

## 14. Format de réponse attendu après une tâche Codex

Réponse courte, de la forme :

```text
Modifié
- ...
- ...

Tests automatisés
- ... : OK
- ... : OK

À valider sur PostgreSQL / navigateur
- ...

Prochaine étape
- ...

ZIP différentiel
- <fichier>
```

Pas de long compte rendu technique sauf demande explicite.

## 15. Première action lors de la reprise du projet

À chaque nouvelle session Codex :

1. lire `AGENTS.md` ;
2. inspecter `git status` ;
3. rechercher les derniers patches réellement présents ;
4. exécuter les tests ciblés de la zone active ;
5. identifier l’étape fonctionnelle exacte en cours ;
6. ne reprendre la roadmap qu’après validation de l’étape précédente.

À la date de rédaction de cette note, l’étape fonctionnelle active est la **recette ETIC B6/B7 de la liasse fiscale**, avec **Patch 112 à vérifier réellement côté B7** avant de continuer vers les autres rubriques ETIC ou les étapes 09B+.

## 16. Consignation active et reprise après interruption

Instruction de l'utilisateur : consigner chaque étape pendant son exécution
pour permettre une reprise d'une session à l'autre.

- Lire intégralement `CODEX_PROGRESS.md` au démarrage et consulter les étapes
  incomplètes avec `Test/journal_codex.py etat`. Les états récents du journal
  sont à vérifier dans le dépôt ; la note datée de la section 15 reste historique.
- Avant toute modification d'un lot, enregistrer son début avec un identifiant
  stable, l'objectif, les fichiers concernés et la prochaine action exacte.
- Après analyse, correction, commande de tests et préparation de livraison,
  enregistrer un point de reprise. Consigner le résultat de chaque commande
  de tests avant de passer au lot suivant. Avant une opération longue, noter
  sa commande et comment en vérifier l'achèvement.
- Utiliser `debut`, `point`, `interruption` et `fin` de `Test/journal_codex.py`.
  Le journal reste `CODEX_PROGRESS.md` ; ne pas remplacer son historique.
- Distinguer les tests exécutés ici des résultats historiques ou rapportés
  par un agent. Une commande interrompue n'est pas un test réussi.
- Terminer une étape seulement après vérification du ZIP différentiel.
  Le journal doit conserver les limites et la prochaine tâche même après fin.
- En cas d'interruption, quota ou blocage, sauvegarder le point exact si les
  outils restent disponibles. À la reprise, inspecter fichiers et processus
  concernés avant de relancer une commande ou de réappliquer une modification.
- Les travaux parallèles utilisent des identifiants distincts ; l'agent
  principal consigne leurs résultats et assure un seul rédacteur à la fois.
