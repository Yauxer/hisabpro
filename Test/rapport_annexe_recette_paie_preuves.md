# Annexe de recette Paie/GRH — preuves documentaires — 8 octobre 2026

Sept cas RH-020 à RH-026 complètent les19cas existants sans renumérotation :
référentiel sans preuve, consignation partielle et dates non présumées,
historique, saisie invalide, lecture sans mutation, isolation société/année
et détection de péremption. Les données sont expressément fictives.

Les résultats de recette utilisateur restent vides. Les26cas comprennent
**23 Non testé et3 Bloqué**. RH-026 requiert un opérateur pour préparer puis
modifier une rubrique fictive sur une base isolée ; aucun écran de saisie de
ces taux n'est inventé. Ce blocage de préparation est distinct du scénario
développeur réellement exécuté dans228. Paie réglementaire/bulletins et CSV
avec référentiel vérifié conservent leurs blocages antérieurs.

Le cahier principal annuel218cas reste inchangé. La nouvelle annexe est un
complément, jamais une preuve de certification, recette utilisateur réussie
ou paie définitive activée.

## Exécutions du principal

```text
PYTHON_DOTENV_DISABLED=1 python -X utf8 Test/run_unit_tests.py Test/test_annexe_recette_grh.py --tb=short
python -X utf8 Test/generer_annexe_recette_grh.py
python -X utf8 -m py_compile Test/generer_annexe_recette_grh.py Test/test_annexe_recette_grh.py
```

Premier essai : 1réussi/1échoué3,75s, assertion sur un texte PDF coupé par un
retour à la ligne. Le test normalise ensuite les espaces extraits sans changer
le texte attendu ni le contenu généré. Relances : **2réussis0,82s**, puis
**2réussis0,85s** après précision du libellé Annuler la consignation, code0.
Génération :26cas, code0 ; compilation2fichiers :code0.

Les artefacts destinés à la livraison sont également ouverts réellement par
pypdf/openpyxl : **30pages PDF,7feuilles Excel**,26identifiants retrouvés,
23Non testé/3Bloqué, résultats et anomalies utilisateur vides. Le classeur
conserve les formules COUNTIF, filtres, validations de statuts et colonnes
résultat réel/anomalies/preuves. Aucun PostgreSQL utilisé par cette génération.
