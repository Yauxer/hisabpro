# Lot621 — autres modules sous les protections100

35cas regroupés réellement exécutés, aucun échec/ignoré. Même application
FastAPI et PostgreSQL natif jetable sous LOGIN applicatif, avec100 installé et
un registre de provision témoin **non vide**. Aucune fonctionnalité ajoutée.

Parcours repris sans remplacer leurs règles ni oracles : facturation vente et
achat → validation → règlements → lettrage dans Edge ; exercice annuel connecté
stock/banque/TVA/immobilisation/clôture/à-nouveaux ; clôtures CCA/PCA décalées ;
captures RAS, refus/permissions/idempotence/concurrence et protections SQL099.

La source définitive et la reprise en brouillon du témoin appartiennent à une
société séparée ; leur suivi et les en-têtes/lignes sont comparés avant/après
toute la suite, sans mutation. Le nouveau registre ne doit pas bloquer les
pièces ordinaires ni contaminer les autres sociétés.

Commande réelle :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_intermodules621_isole.py -q
```

Durée78.632s, code retour0, JUnit `.codex-tests/intermodules621.xml`. Python compilé. Ces35cas réutilisent des
tests existants sous une nouvelle configuration SQL100 ; ils ne représentent
pas35nouvelles fonctionnalités ni un total unique à additionner à l’historique.

PostgreSQL utilisateur jamais connecté/modifié. Aucune migration historique,
écriture réelle ou fonctionnalité RH/paie changée. Recette humaine, installation
réelle100 et production restent non validées. Prochaine étape technique :
ajouter la chaîne d’installation vierge100 autonome et vérifier son rejeu.
