# Qualification consolidée des retenues TVA — lot581

## Résultats exécutés le18octobre2026

La commande avec le venv du dépôt a réellement terminé : **130 tests réussis,
29 avertissements,264,94s, code0**. Elle regroupe les tests de capture guidée,
des anciennes captures libres, des interfaces et du lettrage, la simulation,
les taux HT de grande précision, les API et l'interface du registre, les
calculs TVA purs et les formats CSV/Excel/PDF, dont le contrôle multipage.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_ras_tva581_isole.py Test/test_ras_tva_simulation.py Test/test_patch02_tva_service.py Test/test_patch02b_tva_service.py Test/test_montant_decimal_exact_frontend.py Test/test_ras_tva_registre_precision.py -ra
```

Le premier lancement de cette consolidation utilisait par erreur le Python
global, sans playwright/openpyxl :2 erreurs de collecte,1 avertissement,7,00s,
code2 ; aucun test exécuté. La commande ci-dessus utilise les dépendances
déjà présentes dans le venv ; aucun paquet n'a été installé.

La restauration native a ensuite réussi : **1 test,29 avertissements,76,65s,
code0**, fichier `Test/test_restauration_registre_ras_tva_isole.py`.
Deux clusters PostgreSQL jetables, sauvegarde/restauration via les outils
natifs ;75 tables, schéma, données, ACL et séquences identiques avant
redémarrage. Source conservée et cibles de test supprimées à la fin.

Après restauration, pour une capture active/validée et une capture annulée :

- JSON et empreinte du registre identiques ; aucune mutation métier ;
- CSV identique, texte PDF et valeurs des feuilles Excel identiques ;
- logo restitué dans PDF et Excel ;
- montant actif validé75,00 MAD et annulé75,00 MAD, sans compensation ;
- dossiers, rejeu idempotent, garde TVA et immutabilité SQL conservés.

Ce test réutilise les contrôles natifs575 sans modifier le fichier575 ni ses
preuves historiques. Les preuves de laboratoire581 sont enregistrées
séparément dans `.codex-tests/restauration581_preuve.json`.

Les2 tests Edge d'absence099 ont également été exécutés pour579 :30,10s,
code0. Le build frontend final579 a réussi en5,76s. Ces résultats distincts
ne sont pas présentés comme inclus dans les130 tests.

## Portée de la qualification

Aucun correctif produit supplémentaire dans581 : consolidation, contrôle de
reprise et documentation du plan/registre d'anomalies. Pas de PostgreSQL réel,
pas de modification d'écritures existantes, de SQL ancien ou de migration
exécutée chez l'utilisateur. Les avertissements Pydantic/anyio existants et
celui des gros chunks frontend restent présents.

La couverture globale demeure16 terminé,47 partiel,3 absent,4 bloqué.
RAS TVA reste partielle : déclaration complète, crédit imputable et reversement
ne sont pas automatisés. L'installation cible099, la qualification comptable
sur pièces, la recette humaine et la production restent des étapes distinctes.
RH/paie restent différées. Prochaine action : qualification des règles et
modèles officiels manquants, sans lever la garde de déclaration par hypothèse.
