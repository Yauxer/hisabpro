# Lot520 — Régénération de stock et validation Journal simultanées

## Défaut reproduit et correction

La lecture d'un brouillon avant régénération ou validation pouvait devenir
ancienne pendant une opération concurrente. Quatre scénarios natifs ont
reproduit une erreur500 entre la régénération de l'écriture de stock et sa
validation, individuelle ou par lot. Les protections SQL d'intangibilité
existent et sont conservées ; aucune perte d'écriture définitive n'est
revendiquée comme démontrée par ces échecs.

La régénération et les deux endpoints de validation verrouillent désormais
l'en-tête avant la décision, avec relecture de l'état ORM. La validation d'un
lot verrouille les parents par identifiant croissant ; son traitement reste
trié par journal/date/identifiant pour conserver la chronologie comptable.

Si la validation finit en premier, la régénération constate la pièce
définitive et renvoie409, sans toucher ses lignes. Si le brouillon a déjà été
régénéré, la validation de l'ancien identifiant indique qu'il est introuvable
(404 seule, ou refus dans le lot) ; la nouvelle pièce doit être validée
explicitement. Il existe une attente transactionnelle pendant l'opération
concurrente ; ce lot ne promet pas un refus immédiat.

Aucune nouvelle migration, règle fiscale ou règle d'intangibilité. Aucun
numéro, date, ligne ou audit historique réécrit pour obtenir le résultat.

## Neuf scénarios API/PostgreSQL

- Quatre croisements : validation individuelle/par lot avant régénération et
  régénération avant validation individuelle/par lot. Une seule pièce courante
 3111D160/6114C160, numérotée et définitive ; audit antérieur conservé, une seule
  validation enregistrée, clôture−2840 et FEC effectifs.
- Quatre validations doubles, dans les combinaisons individuel/lot : une seule
  validation et un seul numéro réservé ; seconde demande refusée selon le
  comportement existant, aucune ligne modifiée.
- Deux lots se recoupant, avec identifiants demandés en ordre inverse : deux
  validations dans le premier lot, zéro dans le second, numéros distincts sans
  double réservation, ordre chronologique conservé, clôture/FEC.

Les chiffres sont fictifs : stock8×20=160, résultat160−CM3000=−2840 selon le
calcul déjà présent. Aucune qualification fiscale d'un dossier réel.

Avant correction : **4échecs,29avertissements,38,70s**, code1.
Premier passage corrigé : **14réussites,29avertissements,44,19s**, code0 :
quatre courses et dix régressions de stock/numérotation. Les cinq scénarios
supplémentaires sont ajoutés ensuite, sans déclarer une exécution avant
correction qui n'a pas eu lieu.

Qualification ciblée étendue : **19réussites,29avertissements,61,71s**, code0 :
neuf cas natifs PostgreSQL et dix régressions stock/numérotation. Les passages
successifs ne sont pas additionnés comme des cas distincts.

Qualification finale : **331réussites,29avertissements,603.03s**, code0,
aucun échec/erreur/ignoré :312oracles518,9cas520 et10régressions supplémentaires.
Scénarios du wrapper principal sous rôle LOGIN non propriétaire PostgreSQL18.3,
sources figées vérifiées ; Edge ordinateur/mobile, cycles vente/achat,
factures→règlements→lettrage, PDF/XLSX/impression, fiscalité et clôtures inclus.

Restauration098 :74tables, source préservée, cibles supprimées, trois fonctions
identiques et refus409/reprise conservés. Invariants comptables0 : pièces
déséquilibrées, montants non finis, définitives sans numéro/date.
Quatre Python du lot et28du cumulatif compilés ;98SQL/115guides,
main/models/AGENTS et moteur de mouvements518 intacts. Frontend inchangé.

Commande : liste de la consolidation518 avec
`Test/test_consolidation_stock520_isole.py` comme wrapper et ajout de
`Test/test_patch06_stock_cloture.py` et `Test/test_patch07c2_numero_validation.py`,
avec `-ra` via `Test/run_unit_tests.py`.


## Installation et limites

Installer ensemble `routers/ecritures.py` et `services/stock_service.py` à
jour520, puis redémarrer l'API. Aucune nouvelle migration ou intervention sur
les données réelles. Conserver les migrations existantes d'audit,
numérotation, intangibilité et verrouillage des exercices.

Ce lot qualifie validation individuelle/par lot et régénération de stock.
Les autres mutations directes du Journal, les autres générateurs automatiques,
les accès hors API et les dates d'exercices modifiées simultanément demandent
leurs propres contrôles. Recette utilisateur, production et point6 humain
restent distincts et en attente.
