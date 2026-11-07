# Personnel & Paie — Lot 0A : audit du dépôt

Date : 27 octobre 2026. Référence : [master version 1.0](../HISABPRO_PERSONNEL_PAIE_CODEX_MASTER.md). Lot documentaire ; aucune fonctionnalité nouvelle, migration, règle fiscale ou sociale activée.

L'inventaire reproductible [LOT0_INVENTAIRE.json](LOT0_INVENTAIRE.json) conserve les chemins, lignes des modèles et routes, colonnes, contraintes ORM et SHA-256 de 49 sources. Il est généré par `Test/audit_personnel_paie871.py`, sans importer l'application ni contacter une base. Il décrit 19 tables ORM utiles et 14 routes Personnel existantes ; la table SQL `grh_avances_affectations` est inventoriée séparément. Un fichier SQL présent ne prouve pas son installation chez l'utilisateur.

## 1. État de départ

Le dernier lot comptabilité/facturation consigné est 869, terminé ; aucun lot actif au démarrage. `CODEX_PROGRESS.md` a été lu dans son intégralité et ses 2 644 événements ont été analysés. Les anciens comptes rendus Paie/GRH servent à orienter les recherches ; les constats ci-dessous proviennent du code actuel. Aucun dépôt Git n'est disponible dans ce dossier (`git status` échoue), donc les empreintes de fichiers servent de référence de non-modification.

Le module actuel est une page `/cnss`, composant `src/pages/CNSS.jsx`, avec quatre onglets : Équipe, Préparation mensuelle, Congés & absences, Avances des salariés. La sidebar regroupe une seule entrée sous « Paie / GRH ». `ModulesContext` et le code de module `paie_grh` existent déjà. Les neuf futures rubriques ne sont pas encore neuf écrans livrés.

## 2. Couverture par rubrique du master

| Rubrique | Statut par rapport à la cible | Présence réelle et reste à construire |
|---|---|---|
| 01 Personnel | Partiel | CRUD `employes`, archivage logique et restauration, champs optionnels de dossier. Pas d'unicité du matricule par société, de statut d'approbation ni de salaire versionné à date d'effet. |
| 02 Éléments de paie | Absent | Pas de catalogue de rubriques/variables approuvées, justificatifs d'exonération ou ventilation IR/social par rubrique. Les paramètres annuels globaux sont un autre objet. |
| 03 Traitement de la paie | Partiel | Simulation de salaire fixe sur mois complet ; blocages et avertissements explicites. Pas de campagne persistée, bulletin approuvé, snapshot de calcul ni livre de paie définitif. |
| 04 Charges sociales | Partiel | Paramètres et calcul indicatif, sans déclaration sociale contrôlée ni preuve de dépôt. Validation des règles applicables encore nécessaire. |
| 05 Fiscalité salariale | Partiel | Barème/déductions et estimation IR dans la simulation. Pas de moteur complet versionné et validé par cas métier, ni déclaration salariale déposée. |
| 06 Avances & prêts | Partiel | Registre 095 d'affectation de lignes définitives 3431 à un salarié, annulation tracée, contrôle de solde. Pas de prêt, échéancier ou récupération automatique dans un net à virer. |
| 07 Paiements | Absent pour la paie | Banque et rapprochement communs disponibles ; API commerciale de règlement liée aux factures. Pas de dette salariale ou sociale et circuit de paiement salarial approuvé. |
| 08 Comptabilisation | Partiel | Journal `SA`, écritures et modèles d'avances existants. Pas de lien campagne/version → écriture, de comptabilisation de campagne ou d'OD de clôture Personnel intégrée. |
| 09 États & reporting | Partiel | CSV de simulation et registre interne PDF d'absences avec logo. Pas de reporting complet bulletin → campagne → dette → banque ni d'état des congés acquis à payer. |

Ces statuts portent sur le nouveau master. Ils ne modifient pas les qualifications historiques de comptabilité/facturation ni la matrice générale.

## 3. Carte des données existantes

| Objet | Source | Point d'attention |
|---|---|---|
| `employes` | `models.Employe`, routeur `routers/employes.py` | `salaire_brut` est un `Float` non nul ; `actif=True` par défaut. `PUT` remplace directement les valeurs. La contrainte unique existante porte sur `(id,societe_id)`, pas le matricule. |
| `grh_absences`, `grh_absence_evenements` | modèles et migration 081 | Clés composites société/salarié ; demande/décision et historique protégés. Durée calendaire informative, sans droit acquis ni retenue sur salaire. Ne pas étendre vers un SIRH hors périmètre. |
| `paie_referentiel_versions` | modèle, migration 082, `paie_referentiel_service.py` | Snapshots de preuves partielles par société/année ; empreinte et versions protégées. `paie_definitive_autorisee` reste explicitement faux. Ce n'est pas le catalogue versionné des règles légales du futur moteur. |
| `bareme_ir`, `taux_cotisations`, `deductions_ir` | modèles et `routers/parametres.py` | Paramètres globaux par année, montants/taux en `Float`, sans `societe_id`. Une édition ne constitue pas une règle légalement validée ni une date d'effet historisée. |
| `grh_avances_affectations` | SQL 095 et `routers/avances_salaries.py` | Registre distinct sans modèle ORM dédié ; rattachement de lignes 3431 validées, unicité de l'affectation active, transactions et protections SQL. Aucune nouvelle écriture créée par l'affectation. |
| `ecritures`, `lignes_ecriture` | modèles et `routers/ecritures.py` | Lignes monétaires en `Numeric(18,2)`, validation/numérotation/audit existants. Pas de clé métier de campagne de paie. |
| `reglements` | modèle et `routers/commercial.py` | `facture_id` nullable dans le modèle, mais l'API refuse actuellement un règlement sans facture : 422. Montant en `Float`. Ne pas confondre possibilité du schéma et contrat métier. |
| `utilisateurs`, `utilisateurs_societes` | modèles/auth | Trois rôles globaux : admin/comptable/lecture. Les sept fonctions du master ne sont pas sept rôles implémentés. |

## 4. Réutilisations et limites d'intégration

- **Identité et société** : conserver `employes.id`, `societe_id`, les FK composites existantes et `get_current_user`. Aucune seconde table racine de salariés ni nouvelle identité de connexion.
- **Journal** : `SA` existe dans `models.JournalEnum` et dans le contrat API actuel. Le code `PAI` du master est une possibilité à examiner, pas un journal disponible. Proposition : conserver `SA` avec un libellé utilisateur « Journal de paie », sauf décision contraire ; aucun enum ou ancien journal renommé dans ce lot.
- **Exercices et périodes** : réutiliser `verifier_date_ecriture`, `ensure_exercice`, les périodes existantes, le verrou transactionnel `verrouiller_saisie_exercice` et les protections SQL. Une période de paie civile est distincte de la clé d'exercice comptable ; un exercice décalé doit être résolu par les dates.
- **Écritures** : réutiliser contrôle de partie double, plan par société, numérotation, validation et contrepassation. La route de création appelle `commit()` ; elle n'est pas un service composable atomique pour une campagne. Prévoir au Lot 4 une primitive partagée sans commit, sous les mêmes contrôles, avec régression de la route historique.
- **Auxiliaires** : `auxiliaire_service.py` est construit autour de tiers clients/fournisseurs et de préfixes explicites. Un salarié ne doit pas devenir un faux client/fournisseur pour entrer dans ce mécanisme. Proposition : détail salarial restreint réconciliable avec une OD centralisée ; décision de granularité conservée au backlog.
- **Paiements** : réutiliser `comptes_bancaires`, les lignes d'écriture et le rapprochement. L'API `/api/reglements` n'accepte pas directement la paie. Étudier au Lot 5 un adaptateur de trésorerie hors facture partagé et transactionnel, sans détourner les règlements commerciaux ni créer de seconde banque.
- **Pièces et exports** : réutiliser les contrôles de chemins, tailles et stockage de `attachments.py`, et les helpers de logo. Sa liste `DOCUMENTS` n'inclut pas les salariés/bulletins : l'ajout exige une autorisation financière/documentaire backend spécifique. Les caches/downloads de paie doivent être privés.
- **Sauvegardes** : `ops/postgres_sauvegarde.py` et les bancs de restauration existent. Ajouter les futures tables et pièces au contrôle de restauration ; aucun dump ni test sur la base utilisateur dans ce lot.

## 5. Écarts prioritaires

| ID | Priorité avant mise en service du nouveau module | Constat | Traitement proposé |
|---|---|---|---|
| P01 | Bloquant Lot 1 | Matricules doublonnables, salarié immédiatement actif | Préflight doublons, identité stable, activation approuvée ; ne pas renuméroter les historiques. |
| P02 | Bloquant Lot 1 | Écrasement immédiat du salaire ; pas de date d'effet | Versions de rémunération et approbation, source historique non attestée conservée comme telle. |
| P03 | Bloquant Lot 1 | GET dossiers expose salaire et numéro CNSS à `lecture` | Habilitations distinctes, projections API et protection des anciennes routes. Le masquage frontend seul serait insuffisant. |
| P04 | Bloquant Lot 3 | Simulation fixe, formules partielles et paramètres globaux mutables | Catalogue versionné, moteur social/IR séparé, validation réglementaire sourcée ; ne pas rendre la simulation définitive. |
| P05 | Bloquant Lot 4 | Pas de lien unique campagne/OD ; création comptable commit interne | Adaptateur sans commit, FK et clé d'idempotence, concurrence et blocage clôture. |
| P06 | Bloquant Lot 5 | Règlement hors facture refusé ; flux de salaires absent | Adaptateur trésorerie et dette salariale ; pas de fausse facture. |
| P07 | Bloquant données sensibles | Pas d'identifiant bancaire salarié sécurisé/versionné, pièces non habilitées | Collecte minimale, chiffrement et clés à arrêter avant stockage de RIB, séparation des approbations. |
| P08 | À cadrer Lot 1 | Activation UI `paie_grh` distincte des droits API | Vérification backend de l'activation et des capacités ; ne pas utiliser la visibilité du menu comme contrôle de sécurité. |

Les trois tests de caractérisation 871 constatent volontairement des comportements actuels, y compris P01/P02/P03. Leur réussite ne signifie pas conformité au master ; les attentes devront être remplacées lors de l'activation de la nouvelle API.

## 6. Périmètre de la livraison

Documents d'architecture/RBAC/migrations/tests, outil d'inventaire sans accès SQL et caractérisations sur données fictives isolées. Aucun fichier de `src`, du backend produit, de `ops`, aucune migration et aucun barème ne sont modifiés. Les résultats réellement exécutés et leurs limites sont dans [LOT0_TESTS_ET_REPRISE.md](LOT0_TESTS_ET_REPRISE.md).

Suite : examiner les propositions [Lot 0B](LOT0_CONCEPTION.md), puis la sous-étape [Lot 1A](LOT1A_PLAN.md). Les choix ouverts sont explicités ; ce lot ne lance pas automatiquement le moteur de paie ou les neuf écrans.
