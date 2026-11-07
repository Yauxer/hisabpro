# Lot493 — Génération concurrente de dotations

Défaut reproduit sur API réelle et PostgreSQL temporaire : deux demandes
simultanées sur la même immobilisation/exercice passaient le contrôle de référence
et créaient chacune une dotation de2000MAD. Avant correction :1échec en49,24s.

La fonction commune de création prend désormais un verrou transactionnel
PostgreSQL par société/immobilisation/exercice, sans attente. Elle revérifie
ensuite la référence AM avant de créer l'écriture. Un conflit renvoie409 et
invite à réessayer. Le verrou est libéré par commit/rollback ; aucune relance
automatique ne génère des écritures en arrière-plan.

Ce point commun est utilisé par la génération individuelle, le lot annuel,
le bouton de préparation de clôture et les dotations complémentaires de sortie.
Les références, montants, règles de calcul et statut brouillon restent inchangés.
Aucune migration, nouvelle règle fiscale ni réparation historique.

## Tests

Six courses initiales réussies en31,43s : unité/unité, unité/lot, lot/unité,
lot/lot, clôture/unité et unité/clôture. Le banc retient uniquement la table de
lignes du cluster nonce pour observer la première création non confirmée.
La seconde est refusée409, puis la première aboutit. Une seule référenceAM
subsiste avec61935D2000/28355C2000 pour un matériel fictif10000 amorti sur5ans.
Les écritures d'acquisition originales sont conservées à l'identique.

Après libération, rejouer l'unité renvoie409 « existe déjà » ; rejouer un lot
renvoie200,0créée/1ignorée. Deux cas additionnels vérifient l'indépendance des
sociétés/immobilisations/exercices et la libération après refus par le verrou
de clôture098, avec annulation complète de la tentative.

Commande finale :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_dotations493_isole.py Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py -ra
```

**32tests réussis,29avertissements en184.71s**,0échec/erreur/ignoré. Les8cas de
concurrence et d'isolation sont regroupés avec les parcours Edge d'acquisition,
dotations au centime, dégressif, cession/rebut, cession différée, vente/achat puis
validation/règlement/lettrage et clôture/à-nouveaux. Les tests unitaires du module
et de fin de plan sont exécutés. Les passages successifs ne sont pas additionnés.

Une restauration froide098 est rejouée sur le backend final :74tables,
quatre pièces, données/schéma/ACL/séquences et FEC conservés, fonctions et
refus409/reprise disponibles sur la copie ; source préservée et cibles nettoyées.
Les invariants comptables sont nuls :0pièce déséquilibrée,0montant non fini,
0définitive sans numéro/date. Sources/fonctions/ACL restent inchangées pendant
l'exécution. Trois fichiers Python compilés,98SQL antérieurs et115guides intacts.

## Installation et limites

Installer `hisabpro-backend/routers/immobilisations.py` et redémarrer l'API.
Aucune migration supplémentaire. Les protections Journal/clôture du lot490
nécessitent toujours098 après097, installées manuellement selon la procédure.
Les anciens scripts SQL et115fichiers de guide/recette sont conservés.

Cette correction protège la création commune des dotations par l'application,
pas une insertion SQL arbitraire ni toutes les mutations du registre. Les
changements concurrentiels du plan, les sorties simultanées une fois toutes les
dotations déjà présentes et la stabilité globale des immobilisations pendant
le calcul de clôture restent à qualifier. Aucun doublon historique n'est
supprimé ou corrigé silencieusement. Aucune base réelle n'a été utilisée.

Frontend inchangé : pas de nouveau build Vite annoncé. Les tests navigateur
automatisés ne remplacent pas la recette utilisateur. Production et point6
restent en attente.
