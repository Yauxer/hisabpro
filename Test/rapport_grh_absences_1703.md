# GRH — demandes de congés et absences

## Comportement

Le salarié possède un dossier existant dans la société active. Un opérateur
autorisé en écriture enregistre une demande datée de type congé, absence ou autre,
avec motif facultatif. Le service refuse les dates inversées, une période hors
des dates d'entrée/sortie renseignées et le chevauchement avec une demande active.
Les demandes archivées/refusées/annulées n'enlèvent aucun droit acquis.

Un administrateur approuve ou refuse une demande en attente. L'auteur ou un
administrateur peut annuler une demande en attente ou approuvée. Une demande
refusée ou annulée demeure consultable et ne revient pas à un état précédent.
Chaque création/décision ajoute un événement avec acteur, états, commentaire et
horodatage dans la même transaction. Le rechargement conserve l'historique.

API : GET/POST `/api/employes/conges`, PATCH `/api/employes/conges/{id}`.
Les indicateurs peut_decider et peut_annuler sont déterminés à partir du rôle,
de l'auteur et du statut courant, et les mêmes droits sont vérifiés côté serveur.

Le nombre affiché est **le nombre de jours calendaires inclusifs entre les deux
dates**. Il ne représente ni un solde de congés acquis, ni des jours ouvrables,
ni une retenue automatique. Aucun jour férié, prorata légal, salaire, cotisation
ou écriture comptable n'est calculé/modifié par ce module.

Il s'agit d'un outil de suivi administratif, sans portail salarié indépendant,
pièces médicales, planning avancé ou calcul de droit légal à congés. Ces étapes
restent distinctes et demandent leur propre analyse métier/réglementaire.

## Migration additive 081

Relecture de la première livraison locale 192 : le DEFAULT CDI de la colonne
nouvelle aurait qualifié arbitrairement les contrats historiques. Aucune migration
réelle n'ayant été appliquée ici, 080 est corrigée avant déploiement : colonne
nullable sans défaut, ORM sans défaut, et test ancien salarié conservé avec
contrat NULL. Le POST/PUT accepte également un contrat non renseigné (null),
sans reclasser le salarié lors de la modification d'un autre champ. L'interface
permet la saisie explicite du contrat. Utiliser la version cumulative comprenant ce correctif et 081,
plutôt que l'ancien ZIP 192 isolé.

Pour une éventuelle installation de la première version 080, 081 retire le
défaut CDI sans effacer aucune valeur existante : un CDI confirmé et un CDI
rempli automatiquement sont indiscernables sans justificatif. La vérification
humaine de ces anciens contrats reste nécessaire ; aucune requalification
automatique n'est exécutée.

La migration crée grh_absences et grh_absence_evenements. Les clés étrangères
composites empêchent le rattachement d'une demande à un salarié d'une autre
société, y compris par une insertion SQL directe. L'index unique additionnel
sur employes(id,societe_id) ne réécrit ni ne supprime les dossiers existants.

Le rôle applicatif reçoit SELECT/INSERT et UPDATE limité aux colonnes de décision.
Il ne reçoit aucun droit de suppression des demandes/historiques. Les événements
refusent UPDATE/DELETE/TRUNCATE par triggers, même pour le propriétaire ordinaire.
Un propriétaire capable de supprimer un trigger reste hors de ce modèle de
protection ; cette limite n'est pas présentée comme une inviolabilité absolue.
La traçabilité des décisions est assurée par le flux API ; aucune procédure
de modification SQL manuelle des demandes n'est proposée.

Les créations concurrentes verrouillent le dossier salarié avant le contrôle
de chevauchement. Deux décisions concurrentes verrouillent la même demande :
une seule transition gagne et produit un événement de décision.

## Tests réellement exécutés

- Première commande : 20 unitaires réussis, 5 erreurs de setup, 14,90 s.
  La compilation esbuild a rencontré CNSS.jsx pendant son édition parallèle ;
  les cinq tests API n'ont pas été exécutés par cette commande.
- Après stabilisation UI : 25 réussis, aucun échec/ignoré, 21,44 s.
- Suite élargie GRH + paie : 73 réussis, 1 échec de fixture, 55,84 s.
  L'INSERT SQL du test FK omettait le statut NONNULL. Ajout de statut=demande
  pour éprouver effectivement la clé étrangère ; aucune règle métier assouplie.
- Après correction fixture : 28 GRH réussis, aucun échec/ignoré, 31,26 s.
- Après correction contrat historique : 75 GRH + paie réussis, aucun
  échec/ignoré, 60,04 s.
- Dernier relancement, incluant contrat nullable et non-régression sécurité
  des routes : **87 réussis**, aucun échec/ignoré, **61,74 s**.

Tous les tests PostgreSQL emploient des clusters éphémères marqués dans le
workspace, ports distincts de 5432, vrais JWT et API FastAPI, données fictives.
Ils couvrent décisions, auteur/admin, refus lecture/comptable, multi-société,
dates, chevauchement, concurrence, absence d'écriture/salaire modifié, historique,
idempotence de migration, rôle applicatif absent et protections SQL des traces.
La base réelle de l'utilisateur n'a jamais été connectée.
