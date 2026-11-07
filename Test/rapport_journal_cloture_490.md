# Lot490 — Journal stable pendant la clôture

La migration additive098 fait participer les mutations des en-têtes et des
lignes comptables au verrou société/exercice097. L'API de clôture488 détient
le verrou exclusif dès son entrée ; les écritures prennent un verrou partagé
jusqu'à la fin de leur transaction. Un conflit refuse l'opération sans attendre
le verrou applicatif, avec le diagnostic40001 déjà traduit en HTTP409.
Le client peut réessayer après annulation complète de sa transaction.

Les déplacements protègent les anciens et nouveaux périmètres. Pour les lignes,
les parents sont verrouillés dans l'ordre de leurs identifiants avant de lire
leur société/exercice, afin d'éviter un changement concurrent du périmètre lu.
Une suppression en cascade reste protégée par le contrôle de l'en-tête.
Une trace de clôture confirmée bloque le Journal même sans ligne d'exercice.
Ce dernier refus utilise23514/ck_journal_exercice_ouvert, traduit précisément
en409 ; les autres erreurs SQL restent visibles.

Les protections des écritures définitives, de numérotation, d'équilibre, de
période, de comptes et d'auxiliaires restent installées. Aucun DML historique,
ancienne migration réécrite, exonération ni nouveau calcul fiscal. Les trois
nouvelles fonctions utilisent les droits de l'appelant et un search_path fixé.
Les droits antérieurs sont conservés, les droits EXECUTE du rôle applicatif
sont explicites ; TRUNCATE n'est pas accordé.

## Tests exécutés

- Avant correction :1 échec en28,22s, arrêt au premier défaut,11 cas désélectionnés.
  La modification native d'un en-tête restait autorisée sous verrou de clôture.
- Premier passage :24 réussis,29 avertissements en46,29s.
- Extension :29 réussis,29 avertissements en66,99s. Déplacements société/exercice
  sur les deux côtés, indépendance des périmètres, intangibilité des définitives,
  clôture sans exercice et droits. Deux cas supplémentaires d'insertion d'en-tête
  sont ajoutés à la consolidation finale.

Les transactions du laboratoire sont réelles : refus SQL40001, HTTP409 et reprise,
mutations du Journal en cours refusant une clôture, puis vraie clôture en attente
de la table d'immobilisations. Celle-ci aboutit après libération, avec conservation
des sources, FEC exportable et à-nouveaux. Le jeu fictif conserve la CM existante
de3000MAD (6705/4453), résultat net-3000 ; aucune règle fiscale n'est neutralisée.

Commande de qualification finale :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_journal098_isole.py Test/test_restauration_journal098_isole.py -ra
```

Résultat final : **155 réussis,29 avertissements en379.55s**, aucun échec,
erreur ou test ignoré. Les oracles TVA/avances existants sont conservés et rejoués
sous098, avec31cas Journal, vente/achat et clôture dans Edge, et une restauration
froide renseignée. Les passages successifs ne sont pas additionnés.

Après restauration :74tables, données/schéma/séquences/ACL et quatre pièces
conservés, FEC identique, trois fonctions098 et quatre fonctions097 identiques,
conflit HTTP409 puis reprise SQL autorisée/annulée sans mutation. Source au repos
préservée et cibles supprimées. Le registre d'avances conserve son historique et
reprend de600 à500MAD selon son scénario095. Cinq fichiers Python compilés.

Invariants finaux :0pièce déséquilibrée,0montant non fini,0définitive sans numéro
ou date de validation. Sources, fonctions et ACL inchangées pendant les tests.
Les97SQL antérieurs et115guides/recette sont conservés.

Anomalie indépendante constatée dans le laboratoire : année TVA0 peut renvoyer500.
Elle sera traitée dans le prochain lot, sans mêler sa correction à098.

## Installation et limites

098 reste une migration manuelle, à appliquer après097 avec le rôle propriétaire,
API arrêtée et sauvegarde/restauration préparée. Installer aussi database.py
de ce lot et conserver routers/cloture.py488. Le bootstrap et le CLI090 ne
l'appliquent pas automatiquement. Aucune base réelle n'a été utilisée.

La protection couvre les en-têtes/lignes du Journal et le point d'entrée de clôture
qui respecte ce protocole. Les écritures générées par les factures/règlements
passent aussi par ces tables, mais toutes leurs mutations préalables, les stocks,
immobilisations, paramètres fiscaux et rapprochements ne sont pas pour autant
qualifiés en concurrence globale. Une modification SQL qui désactive les triggers
ou clôture un dossier sans respecter le protocole n'est pas rendue sûre.

Frontend inchangé : pas de nouveau build annoncé. Les parcours navigateur restent
des tests automatisés de laboratoire ; recette utilisateur, production et point6
restent en attente. Les115 fichiers guide/recette restent inchangés.
