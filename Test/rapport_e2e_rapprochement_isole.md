# Rapprochement bancaire connecté — 7 octobre 2026

## Résultat exécuté

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_rapprochement_isole.py -x
```

**1 réussi, 0 échec, 0 ignoré, 21,65 s**. Compilation du fichier par
`python -X utf8 -m py_compile` : **OK**, code retour 0.
25 avertissements existants de dépréciation Pydantic/multipart.

Le test utilise Microsoft Edge sans interface visible, l'application React
complète, FastAPI `main:app` et PostgreSQL éphémère. Aucun appel métier n'est
simulé. Il complète les acquis du patch 157 (parsing, navigateur avec API
synthétique et tests API PostgreSQL) par un parcours navigateur connecté.

## Données et contrôles

- Société fictive créée par API et connexion depuis l'UI.
- Prérequis par vraie API : écriture BQ définitive, D5141/C1111 = 1 200 MAD.
  Référence et libellé uniques, date du jour dans l'exercice ouvert.
- CSV fictif UTF-8 BOM : `Date;Libellé;Débit;Crédit`, crédit bancaire `1 200,00`.
  Ce crédit correspond au débit 5141 de l'écriture comptable.
- Import depuis l'UI : HTTP 201, une ligne créée, aucun doublon.
- Soldes saisis dans l'UI : initial 0 MAD et final déclaré 1 200 MAD,
  sauvegardés réellement par PUT lors de la perte de focus.
- Contrôles affichés : comptabilité/banque équilibrées et
  « Initial + mouvements = final ».
- Association depuis le sélecteur de la ligne de relevé : HTTP 200,
  statut Rapprochée et lien technique vers la bonne ligne comptable.
- PostgreSQL : montant 1 200, sens crédit, compte 5141, date et auteur du
  rapprochement présents ; une seule ligne de relevé et une seule écriture.
- Rechargement complet : lien, statut et soldes conservés dans l'UI.
- Réimportation du même fichier : zéro création, un doublon ignoré ;
  rapprochement conservé.
- Les identifiants, comptes, débits/crédits des lignes comptables définitives
  restent identiques avant/après import, pointage et réimportation.
- Aucun défaut produit rencontré dans ce parcours ; seul le fichier de test
  et ce rapport sont ajoutés pour ce lot.

## Isolation et limites

Aucun `.env`, PostgreSQL réel ou donnée réelle utilisé. Le banc contrôle
URL/rôle/marqueur/chemin du cluster avant ses DDL et arrête les processus et
supprime ses seuls dossiers temporaires au `finally`, avec assertions de
nettoyage. Les seules requêtes interrompues concernent les CDN décoratifs.

Ce cas ne valide pas un établissement bancaire réel, tous ses formats Excel/CSV,
la réconciliation historique, les règles après clôture, les soldes reportés
entre périodes ni la recette utilisateur annuelle. Les essais connexes existants
sont laissés à la consolidation globale de l'agent principal, sans leur attribuer
ici un résultat d'exécution nouveau.
