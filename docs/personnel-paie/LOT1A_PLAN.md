# Personnel & Paie — proposition exécutable de Lot 1A

Statut : prochaine sous-étape proposée, pas code livré. À examiner avec [architecture](LOT0_CONCEPTION.md), [matrice des droits](LOT0_RBAC.csv) et [migrations/recette](LOT0_MIGRATIONS_ET_RECETTE.md).

## Résultat attendu

Un socle backend de dossiers salariés rattachés aux identités existantes, avec montants décimaux et versions, droits explicites, création sans écriture comptable et transitions contrôlées. Aucun moteur de paie, calcul de taux, bulletin définitif, banque, déclaration ni nouveau formulaire dans cette sous-étape.

## 1A.1 — Choix et socle de sécurité

1. Examiner D01 : pilote pour utilisateurs déjà autorisés admin/comptable, avec capacités Personnel séparées ; ne pas donner un rôle comptable général à une personne chargée seulement du personnel. Le profil Personnel seul exige son confinement inter-modules avant usage.
2. Définir les capacités initiales : lire identité, lire rémunération, lire identifiants sensibles, créer/proposer, soumettre, approuver, consulter audit, administrer habilitations. Les habilitations de paiement/déclarations sont réservées aux lots suivants.
3. Faire appliquer les mêmes contrôles aux anciens `/api/employes`, aux détails et simulations qui exposent des salaires. Préparer un basculement explicite ; pas de nouvelle API protégée avec ancien GET/PUT contournable.
4. Interdire l'auto-approbation sensible par construction, y compris pour admin. La création de comptes ou de capacités ne doit pas suffire à déclarer sa propre paie approuvée.

**Acceptation :** autorisations backend et projections testées par appels directs et deux sociétés ; aucun changement de rôle ou d'accès comptable existant implicite. La compatibilité et le pilote choisi sont documentés avant activation.

## 1A.2 — Modèle et migrations

1. Préflight d'une copie isolée : schéma installé, doublons et matricules manquants, historique monétaire et clés composées ; zéro réparation automatique.
2. Conserver `employes.id` et son périmètre société ; ajouter extension de statut/révision/auteurs, contrats, rémunérations versionnées, demandes et événements append-only.
3. Montants `Numeric(18,2)`, dates d'effet connues, unicités/FK composites et absence de chevauchement approuvé. Les champs sensibles non nécessaires restent absents ; pas de RIB en clair ni de fausse valeur pour satisfaire une ancienne contrainte.
4. Reprise des historiques sans salaire ou date « attestés » inventés ; ne pas transformer un ancien `actif=True` en activation paie approuvée. Définir la normalisation textuelle du matricule et refuser les collisions sans les renommer.
5. Nouvelle migration après le dernier numéro réellement disponible ; ne pas modifier 080/081/082/095. Rejeu et rôle LOGIN non propriétaire. Le bootstrap de développement sur ancienne base reste testé.

**Acceptation :** schéma vierge et ancien + rejeu deux fois, contrôles SQL et droits, données historiques identiques hors ajouts explicitement documentés. Si des doublons réels empêchent une unicité, diagnostic et étape bloquée, sans sélection arbitraire d'une fiche.

## 1A.3 — API et transitions minimales

1. Services et schémas typés proposés sous `services/personnel_*` et `routers/personnel_*`, en conservant les conventions du dépôt et l'auth commune ; confirmer les noms à l'exécution.
2. Création brouillon et lectures masquées, recherche/pagination, modification proposée avec `revision_attendue`, soumission et approbation/rejet. Une demande périmée ou une double approbation doit produire un conflit propre.
3. Salaire approuvé historique immuable ; proposition future visible sans remplacement immédiat. Archivage/sortie sans suppression d'un dossier référencé.
4. Routes historiques adaptées au même service lors du basculement ; retirer les tests de caractérisation qui attendent un doublon/une exposition sensible et les remplacer par des refus/masques du nouveau contrat. Ne pas contourner ces refus pour garder les anciens tests verts.

**Acceptation :** trois salariés, doublon refusé dans A mais même matricule autorisé dans B, changement futur approuvé avec deuxième acteur, auteur et bénéficiaire interdits d'auto-approbation, aucune écriture créée par toutes ces actions.

## Fichiers potentiellement touchés au développement

- `hisabpro-backend/models.py`, `schemas.py`, nouvelles migrations additives ; routeurs/services Personnel et compatibilité `routers/employes.py`.
- Authentification/habilitations à intégrer explicitement selon D01, sans étendre implicitement `ROLES_ECRITURE` aux opérations des autres modules.
- Tests API/SQL/migration/concurrence/ancien chemin ; fixtures isolées existantes. Les fichiers de données comptables ne sont pas des fichiers de préparation de test.
- Aucune modification de sidebar en 1A : elle viendra en 1B avec les premiers écrans réellement livrés et les neuf rubriques cadrées dans Lot 0B.

## Tests à exécuter avant livraison 1A

- Unitaires : validation décimale, textes/dates, transitions, masques et révisions.
- API/PostgreSQL natif isolé : droits/sociétés, doublons, intégrité FK, immutabilité, concurrence, valeurs historiques, anciennes URL et absence d'écriture.
- Migrations : vierge/ancien/rejeu, permissions runtime, bootstrap et diagnostic sans réparation.
- Non-régression : dossiers/simulation historique explicitement adaptés au basculement, absences et registre d'avances, comptabilité/validation/journal SA conservés.
- Frontend/navigateur : seulement si des interfaces sont effectivement modifiées ; ne pas annoncer de nouveaux écrans en 1A.

La fin de 1A est un socle backend testé et livré par ZIP différentiel. 1B traitera liste, formulaires, fiche et navigation ; 1C consolidera le circuit, masquage et recette E2E. Les règles de paie légales restent hors de 1A.
