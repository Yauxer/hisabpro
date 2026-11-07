# Lot 482 — Registre des avances par salarié

## Fonction livrée

Paie & GRH → **Avances des salariés** rattache explicitement une ligne comptable
définitive du compte **3431 exact** à une fiche salariée de la même société.
Le registre affiche les versements, récupérations/remboursements, soldes des
mouvements affectés, mouvements non affectés et historique des annulations.
Il couvre tous les exercices, indépendamment du mois de simulation sélectionné.

Une ligne n'a qu'une affectation active. Le motif et l'auteur sont conservés.
L'annulation garde la ligne originale du registre, son motif initial, l'auteur
et la date de chaque opération. Une nouvelle affectation constitue une nouvelle
ligne ; aucune écriture ni ligne comptable n'est modifiée. Le FEC reste identique.
Les contrepassations apparaissent distinctement et restent à affecter.

La récupération ne peut dépasser les avances rattachées au salarié. Le contrôle
porte aussi sur le cumul historique, ordonné par date, identifiant d'écriture
puis identifiant de ligne. Pour deux écritures à la même date, cet ordre reste
déterministe ; ce n'est pas une reconstitution des heures de paiement.

## Installation et utilisation

1. Sauvegarder et vérifier la restauration selon la procédure d'exploitation.
2. Avec le rôle de migration, appliquer **095_registre_avances_salaries.sql**
   après les migrations précédentes jusqu'à 094. Ce script n'est pas exécuté
   automatiquement au démarrage. En son absence, l'onglet explique son indisponibilité.
3. Créer ou vérifier la fiche du salarié dans Paie & GRH → Équipe.
4. Saisir l'avance dans le Journal avec un des modèles personnel livrés en 092,
   vérifier ses justificatifs puis valider l'écriture.
5. Dans Avances des salariés, choisir **Affecter**, le bénéficiaire et le motif.
   Le montant provient intégralement de la ligne comptable ; aucun montant libre.
6. Faire de même pour une récupération ou un remboursement déjà comptabilisé.
   Une récupération sur rémunération suppose une dette justifiée ; ce registre
   n'établit aucun droit à retenue et ne génère aucun bulletin.
7. Corriger une erreur avec **Annuler le rattachement**, motiver puis réaffecter.
   Une avance déjà consommée ne peut être désaffectée tant que les récupérations
   dépendantes ne le sont pas. Un exercice clôturé reste en lecture.

Une fiche archivée ne peut recevoir un nouveau versement ; ses récupérations
peuvent encore être affectées. Aucun bénéficiaire historique n'est deviné depuis
un libellé et aucun compte auxiliaire client/fournisseur n'est détourné.

## Protection et périmètre

Migration additive : une table, une clé société/salarié, une unicité active,
deux fonctions invoker et trois triggers. Les suppressions/réécritures/TRUNCATE
sont refusés ; le LOGIN applicatif ne reçoit ni DELETE, ni TRUNCATE, ni UPDATE
des identités, ni SETVAL. Seules les colonnes d'annulation peuvent être mises à jour.
Les données et ACL des objets précédents sont conservées lors de l'installation.
Le rejeu conserve aussi le contenu du registre et les droits.

Le verrou de fiche salariée sérialise les affectations concurrentes pour ce
salarié ; l'unicité active protège une ligne même entre bénéficiaires distincts.
Les contrôles métier SQL refusent les sources étrangères, brouillons, mauvais
comptes, soldes négatifs et annulations incomplètes. Le contrôle de clôture vise
un état visible ; le calcul complet de clôture concurrent reste hors qualification.

Pas de taux social nouveau, de bulletin définitif, de paiement généré, de
retenue automatique ni de modification de rémunération. Les soldes sont ceux
des seuls mouvements affectés et peuvent être incomplets tant qu'il reste des
lignes non affectées. Les affectations sont des métadonnées : leur annulation
n'annule pas l'opération bancaire ni son écriture.

## Exécutions

- Premier passage : 14 réussis / 3 échoués en 61,21 s. Une donnée de test créait
  une écriture définitive antérieure à la dernière date validée du journal ;
  les deux autres échecs attendaient un séparateur de milliers différent de
  l'affichage MAD existant. Les prérequis et oracles ont été corrigés sans
  changer la règle de validation chronologique ni le format de l'application.
- Passage suivant : 72 réussis en 37,57 s, dont 55 validations pures existantes.
- Extension SQL/restauration : 81 réussis en 96,88 s. Ce passage précède
  l'ajout de la protection TRUNCATE ; la qualification finale figure ci-dessous.

Commandes isolées : `Test/run_unit_tests.py` avec `PYTHON_DOTENV_DISABLED=1`,
fixtures PostgreSQL nonce et LOGIN non propriétaire ; jamais la base utilisateur.
La restauration réutilise toutes les assertions du banc 452, source API arrêtée,
cible vide marquée, schéma/données/ACL/séquences identiques avant reprise.
Elle transporte 74 tables et quatre pièces, restitue trois affectations dont
une annulée, retrouve le solde 600 MAD, puis affecte une récupération existante
de 100 MAD sur la copie et obtient 500 MAD. Le FEC annuel et les sources sont
conservés. Les processus et répertoires créés sont nettoyés par leurs fixtures.

Qualification finale sur la version comprenant la protection TRUNCATE :
**86 réussis, 29 avertissements, 0 échec / erreur / ignoré en 144,97 s**.
Répartition : 25 cas registre (API, SQL natif, concurrence HTTP et SQL, deux
Edge1440/390), 55 validations pures existantes, une restauration froide095 et
cinq E2E existants de non-régression dossiers/simulation/congés. Les règles
sociales utilisées dans l'oracle de simulation existant sont fictives et
n'ont pas été déclarées applicables par ces tests.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_avances_salaries_isole.py Test/test_paie_grh_service.py Test/test_grh_absences_service.py Test/test_restauration_avances095_isole.py Test/test_e2e_paie_grh_isole.py Test/test_e2e_grh_absences_isole.py -ra
npm run build
```

Build final Vite réussi en **5,23 s** ; avertissement existant sur la taille du
bundle. Compilation Python des quatre fichiers ajoutés/modifiés réussie.
Journal et matrice actualisés ; aucun statut global ni résultat de recette
utilisateur n'est promu automatiquement.

## Limites de validation

Migration 095 non appliquée à la base réelle. Recette utilisateur, installation
et restauration de production restent à effectuer. La paie réglementaire
complète reste bloquée par la qualification documentaire du référentiel social.
Les 115 fichiers de guide/recette et le point 6 en attente sont conservés.
