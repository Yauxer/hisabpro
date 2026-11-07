# Personnel & Paie — API et approbations, livraison877

Lot1A.3 du 27 octobre2026. Les API décrites ici sont implémentées. Les écrans de saisie et le groupe de sidebar sont la prochaine étape1B. Aucun moteur de paie, virement ou déclaration n'est fourni par cette livraison.

## Installation et accès

Tester sur une copie autorisée avant toute installation cible. Les migrations passent par le rôle migrateur, séparément du démarrage : **105, puis106, puis107**. Ne pas rejouer105/106 après107 pour revenir à une ancienne politique de droits ; ne pas supprimer les nouvelles tables comme retour arrière. Rejouer107 est testé à vide et après opérations.

107 rend `employes.salaire_brut` nullable, ajoute les attestations du bénéficiaire, les propositions conservées et les capacités de mutation. Les valeurs historiques restent inchangées. Aucun salaire zéro, lien utilisateur, contrat, taux ou activation n'est créé automatiquement. Le modèle ORM nullable ne modifie pas à lui seul une ancienne base : la migration séparée reste nécessaire.

Le diagnostic existant reste disponible : `GET /api/employes/securite/preflight-dossiers`. Avant107, les nouvelles API et l'attribution des nouvelles capacités répondent503. Après installation, le workflow exige l'activation volontaire de la protection Personnel de la société. Sans activation :409 ; sans capacité requise :403.

L'administrateur attribue les habilitations via `POST /api/employes/securite/habilitations`, selon le [guide873](LOT1A1_HABILITATIONS_873.md). Il ne reçoit pas automatiquement le droit de lire une rémunération ou d'approuver.

| Fonction dans le pilote | Capacités nécessaires |
|---|---|
| Préparer un dossier et ses conditions | `personnel.lire_identite`, `personnel.proposer`, `personnel.soumettre` ; `personnel.lire_remuneration` pour les montants |
| Approuver ou rejeter | `personnel.lire_identite`, `personnel.approuver` ; `personnel.lire_remuneration` pour une rémunération |
| Consulter les événements | `personnel.lire_identite`, `personnel.audit_lire` ; les motifs des opérations de rémunération sont masqués sans lecture rémunération |
| Consulter les dossiers | `personnel.lire_identite` ; montant masqué sans lecture rémunération |

Les mutations du pilote exigent aussi un rôle existant **admin ou comptable** dans la société courante. Ne pas attribuer comptable à une personne chargée seulement du personnel pour contourner cette limite : le profil Personnel seul reste à construire. Un compte lecture ne peut pas muter, même avec une capacité de proposition.

Le module `paie_grh` doit être actif. Les droits sont relus en base, sans cache ; suppression/réinvitation ne reprend pas les anciens grants. Les API n'acceptent pas de `societe_id` dans les corps métier comme autorité.

## API disponibles

Préfixe : `/api/employes/personnel`. Authentification commune HisabPro ; réponses confidentielles sans cache.

| Méthode et chemin | Usage |
|---|---|
| GET `/` | Liste, recherche, statut, date de consultation, pagination ; derniers créés en premier |
| POST `/` | Nouveau brouillon sans rémunération, avec demande initiale d'identité |
| POST `/reprises` | Reprise explicite d'une identité historique, sans conversion de son salaire |
| GET `/demandes` | Demandes filtrables par statut et salarié, pagination |
| GET `/demandes/{id}` | Proposition et décision, avec masques serveur |
| POST `/demandes/{id}/soumettre` | Soumettre sa propre proposition |
| POST `/demandes/{id}/approuver` | Décision indépendante, révision contrôlée |
| POST `/demandes/{id}/rejeter` | Rejet tracé, y compris d'une proposition devenue périmée |
| GET `/{employe_id}` | Dossier et conditions approuvées applicables à la date demandée |
| POST `/{employe_id}/modifications` | Nouvelle proposition typée ; aucune modification directe d'une version approuvée |
| GET `/{employe_id}/historique` | Événements conservés, du plus récent au plus ancien |

Les chemins de liste s'utilisent sans slash final. Paramètres de liste : `recherche`, `statut`, `decalage`≥0 et `limite` de1 à100. Pour les demandes : `statut`, `employe_id`, `decalage`, `limite`. Dossier/liste acceptent `au=AAAA-MM-JJ`, date de consultation métier ; par défaut, date courante du serveur. La date n'est ni une échéance de facture ni une date de pièce comptable.

## Parcours de vérification sur données fictives

Utiliser `/api/docs` du backend de la copie, une session préparateur et une autre session approbateur, avec les capacités ci-dessus. Conserver les identifiants renvoyés : ils ne peuvent pas être prédéfinis sur une base existante.

### 1. Créer un brouillon

POST sur le préfixe, avec le préparateur :

```json
{
  "matricule": "FICTIF-001",
  "nom": "Salariée fictive de recette",
  "poste": "Poste fictif",
  "beneficiaire_sans_compte_confirme": true,
  "reference_beneficiaire": "ATTESTATION-FICTIVE-001",
  "motif": "Création du dossier fictif de recette"
}
```

Attendu :201, `statut=BROUILLON`, `revision=0`, `employe_id=E1` et `demande.id=D1`. La racine a `salaire_brut=NULL` et `actif=false`. Aucune écriture comptable n'est générée. Répéter avec `FICTIF-002` et `FICTIF-003` permet de vérifier trois dossiers et le tri. Réutiliser `FICTIF-001` dans cette société donne409 ; dans une autre société, le même matricule est autorisé.

Si le bénéficiaire possède réellement un compte HisabPro dans cette société, fournir plutôt `utilisateur_beneficiaire_id` et `beneficiaire_sans_compte_confirme=false`, avec référence. Ces deux choix sont exclusifs. Un compte étranger reçoit404. Une absence de compte doit être attestée explicitement ; elle n'est jamais déduite du nom ou de l'adresse e-mail.

### 2. Soumettre puis approuver l'identité

Préparateur : POST `/demandes/D1/soumettre` :

```json
{"revision_attendue":0,"motif":"Soumission fictive pour contrôle"}
```

Attendu :200, demande`SOUMIS`, dossier`A_VALIDER`. Avec l'approbateur distinct, POST `/demandes/D1/approuver` :

```json
{
  "revision_attendue": 0,
  "motif": "Identité contrôlée sur pièce fictive",
  "independance_confirmee": true,
  "reference_independance": "CONTROLE-INDEPENDANT-FICTIF-001"
}
```

Attendu : demande`APPROUVE`, dossier`ACTIF`, révision1. L'état ACTIF signifie ici identité approuvée : le dossier n'est pas encore complet pour ses conditions financières. `paie_definitive_autorisee` reste faux.

Le préparateur et le bénéficiaire relié à un compte sont refusés comme décideurs, même administrateurs. La confirmation d'indépendance est une attestation humaine enregistrée avec sa référence, pas une vérification automatique de la pièce. Un bénéficiaire sans compte n'est pas reconnu par une correspondance supposée.

### 3. Proposer et approuver un contrat

Préparateur : POST `/E1/modifications` :

```json
{
  "nature":"CONTRAT",
  "revision_attendue":1,
  "motif":"Contrat fictif de recette",
  "contenu":{
    "type_contrat":"CDI",
    "date_effet":"2026-01-01",
    "date_debut":"2026-01-01",
    "date_fin":null,
    "reference_justificatif":"CONTRAT-FICTIF-001"
  }
}
```

Reprendre l'identifiant de la demande dans la réponse. Soumettre avec révision1 puis approuver avec l'autre compte, révision1 et les confirmations/références. La révision passe à2. GET `/E1?au=2026-12-31` retourne le contrat approuvé et son identifiant `C1`.

### 4. Proposer et approuver le salaire de base

POST `/E1/modifications`, en remplaçant `C1` par l'entier renvoyé :

```json
{
  "nature":"REMUNERATION",
  "revision_attendue":2,
  "motif":"Rémunération fictive de recette",
  "contenu":{
    "contrat_version_id":123,
    "montant":"9000.10",
    "periodicite":"mensuelle",
    "devise":"MAD",
    "date_effet":"2026-01-01",
    "reference_justificatif":"REMUNERATION-FICTIVE-001"
  }
}
```

`123` est un exemple à remplacer par`C1`, jamais une référence à deviner. Soumettre puis approuver avec révision2. Attendu : révision3 ; consultation à date renvoie `montant="9000.10"` en texte exact et `dossier_complet_a_date=true`. Aucune paie définitive n'est autorisée pour autant : règles, variables et campagnes relèvent des lots suivants.

Montants en texte, sans arrondi implicite : les flottants JSON, booléens, NaN/infinis, montants négatifs ou à plus de deux décimales sont refusés. Le salaire doit référencer un contrat approuvé effectivement applicable à sa date. Les rubriques/primes ne sont pas encore ce composant `SALAIRE_BASE`.

### 5. Vérifier une hausse future

Nouvelle proposition de même nature et contrat, révision3, montant`"9876.54"`, date d'effet`2027-01-01`, référence`AVENANT-FICTIF-001`. Avant approbation, la consultation future garde`"9000.10"`. Après soumission/approbation : révision4 ; consultation au31/12/2026 :`"9000.10"`, au01/01/2027 :`"9876.54"`. La première version reste immuable.

La proposition et la décision sont consultables ; un lecteur sans `personnel.lire_remuneration` ne récupère pas le montant via la liste des demandes, les détails ou les motifs d'historique. Deux versions approuvées du même composant à la même date sont refusées. Un conflit SQL annule aussi la décision : la demande reste soumise, sans changement de révision ou de montant précédent.

### 6. Vérifier une sortie

POST `/E1/modifications` avec nature`SORTIE`, révision4 et contenu :

```json
{"date_sortie":"2027-06-30","reference_justificatif":"SORTIE-FICTIVE-001"}
```

Ajouter un motif au niveau de la proposition, soumettre puis approuver avec révision4. Attendu : révision5 ; consultation au29/06/2027 :ACTIF ; au30/06/2027 :SORTI. La date de sortie s'applique au statut à partir de ce jour inclus ; ce n'est pas une règle de calcul de jours payés. Le filtre de liste tient compte de la date de consultation. Les versions et événements restent présents. Une rémunération après la sortie ou une sortie antérieure à des conditions futures approuvées est refusée, sans suppression de ces conditions.

## Révisions, rejets et historique

Une proposition mémorise la révision du dossier. Chaque approbation ou rejet l'incrémente ; la simple création ou soumission d'une demande ne l'incrémente pas. Deux propositions à la même révision peuvent être préparées ; après la première décision, l'autre devient périmée pour approbation. Recharger et préparer une nouvelle proposition.

Une demande périmée peut être rejetée par un décideur indépendant avec la **révision courante** ; elle n'est pas effacée. Un rejet initial ramène le dossier au brouillon. Une modification d'identité approuvée applique seulement le nom/poste proposés ; une proposition de salaire ne modifie pas immédiatement la rémunération approuvée.

Il n'y a pas de PUT du contenu : corriger par nouvelle proposition. Les demandes soumises, décisions et versions approuvées sont conservées. Un double clic ou deux approbations concurrentes donnent un succès et un conflit409, avec un seul événement d'approbation. Seul le préparateur peut soumettre ; l'administrateur ne soumet pas à sa place.

Les conditions à date sont versionnées ; nom/poste restent l'identité courante. L'historique permet de consulter les propositions/décisions antérieures, mais n'est pas un moteur de reconstitution de toute l'identité à une date passée. Les futurs bulletins devront conserver leurs snapshots.

## Reprise et ancien écran

POST `/reprises` exige `employe_id`, le lien ou l'attestation d'absence de compte, sa référence et un motif. Il conserve la racine, le salaire flottant, les dates et l'ancien indicateur actif. La nouvelle extension commence au brouillon avec demande d'identité ; aucun salaire ni date d'effet approuvés ne sont déduits de l'historique. Matricule absent ou ambigu :409 et diagnostic, aucune réparation.

Sur un dossier repris, l'ancien GET ne présente plus le flottant historique comme salaire courant. Les anciens POST/PUT/DELETE restent bloqués après activation. La simulation historique répond409 lorsqu'elle rencontrerait des dossiers contrôlés ; elle ne doit pas mélanger anciennes valeurs et versions approuvées. Utiliser les nouvelles API ; les nouveaux formulaires suivent en1B.

## Limites de cette livraison

- Aucun PostgreSQL utilisateur contacté et aucune migration installée automatiquement pendant le développement.
- Références de pièces et attestations sont enregistrées ; leur contenu et l'indépendance réelle nécessitent un contrôle humain.
- Un dossier106 déjà créé manuellement sans attestation reste lisible mais ne reçoit pas une preuve inventée. Sa régularisation doit être explicite. Les liens bénéficiaire/matricule sont conservés ; leur rectification sensible n'est pas une modification libre du présent pilote.
- Une demande dont le préparateur a été désactivé peut nécessiter une intervention d'administration avant décision, du fait des contrôles de membre actif hérités de106. Aucun transfert d'auteur n'est effectué.
- Pas de RIB/CIN, changement bancaire, paie définitive, calcul de retenue, paiement ou déclaration. Pas de profil Personnel seul ni certification réglementaire.
- Frontend inchangé : l'intégration de la sidebar et des formulaires est la prochaine étape1B ; la recette d'ensemble1C suivra.

Installation cible, sauvegarde/restauration et recette humaine restent à valider sur copie. Voir les résultats877 pour les tests réellement exécutés.
