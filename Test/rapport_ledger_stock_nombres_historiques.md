# Lot334 — contrôle des mouvements et du CMUP historiques

## Défauts reproduits et correction

La vraie route `GET /api/inventaire/controle-mouvements` utilise
`stock_ledger_service`, distinct du schéma brut333. Avant correction,
NULL devenait0 et parfois « OK », NaN/Inf déclenchaient une exception Decimal
et un500. Une quantité invalide pouvait aussi mener à une division par zéro.
Après un CMUP inconnu, la chaîne conservait une ancienne valeur comme source
du mouvement suivant.

Le service reste en lecture seule. Chaque nombre nécessaire est qualifié ;
un contrôle s'exécute uniquement quand ses sources sont déterminables.
Les diagnostics identifient le champ et le mouvement. Une inconnue rompt sa
chaîne CMUP sans désactiver les contrôles de stock indépendants. Le CMUP avant
absent des mouvements legacy reste autorisé ; un nombre non fini effectivement
présent est signalé. Les tolérances et formules nominales sont conservées.
Les quantités invalides sont signalées sans calcul pondéré impossible.

Les valeurs courantes et totaux non représentables deviennent NULL avec
diagnostic. `audit_complet` distingue les sources historiques contrôlables ;
`valorisation_complete` distingue la valorisation courante disponible. Un
coût historique inconnu ne supprime pas une valeur courante connue ; une somme
débordante ne présente pas un sous-total comme total complet. Zéros et nombres
finis signés restent visibles.

L'onglet « Mouvements & CMUP » affiche « À vérifier » pour le stock inconnu
et un avertissement d'audit incomplet. Filtre, recontrôle et diagnostics
existants sont conservés. Aucun bouton de réparation ajouté.

## Tests réellement exécutés

Commandes via `Test/run_unit_tests.py`, `PYTHON_DOTENV_DISABLED=1` ; tests purs
sur les objets métier, HTTP et navigateurs sur PostgreSQL éphémère vérifié
par URL/dossier/nonce. Aucun `.env` ou PostgreSQL utilisateur lu.

- Baseline36cas : **36 échecs, code1**, XML23,479s. Faux0/OK, exceptions
  Decimal et500API reproduits. Les assertions sur les nouveaux indicateurs
  échouaient également avant leur ajout ; ces36échecs ne sont pas36bugs distincts.
- Premier ciblé+connexes : **71 réussis, code0**, XML23,198s.
- Deux Edge1365/390 : **2 réussis, code0**, XML46,193s.
- Run final enrichi : **95 réussis, aucun échec/erreur/ignoré**, code0,
  25 avertissements, XML52,287s.58nouveaux cas pure/API, deux nouveaux Edge,
  quatre tests06B et31tests d'intégrité des mouvements inchangés.

```text
python -X utf8 Test/run_unit_tests.py
 Test/test_stock_ledger_nombres_historique.py
 Test/test_patch06b_stock_ledger.py Test/test_stock_integrite_mouvements.py
 Test/test_e2e_stock_ledger_nombres_isole.py -q --tb=short
 --junitxml=.codex-tests/ledger_334_final.xml
```

Oracle sain : entrée10@100, sortie4@100 → stock6, CMUP100, valeur600,
statutOK. Contrôles : NULL/NaN/±Inf/booléens/texte, quantités invalides,
CMUP legacy, stock initial non nul, fractions, contrôle indépendant après
inconnue, produit/somme débordants, filtre et compteurs, services/archives
exclus, autre société vide. Photographies SQL articles/mouvements/écritures/
lignes identiques après les GET et les opérations de filtre/recontrôle UI.
Les deux navigateurs constatent aucun500, aucune erreurJavaScript et aucune
requête de mutation d'inventaire.

Compilation du service et des deux tests : code0. Build Vite :139modules,
7,89s, code0 ; avertissements de taille de bundle et importxlsx conservés.

## Limites et reprise

La préparation de l'agent frontend a rencontré une limite d'usage du contrôle
automatique ; aucune source ni test actif n'a été modifié par cet agent.
Le responsable a repris le cache, corrigé sa faute de syntaxe avant copie,
réalisé la correction et exécuté les preuves ci-dessus.

Aucune migration, donnée réelle ou historique comptable réparé. Les moteurs
de mutation de stock constituent un prochain lot distinct. La recette humaine
et la mise en production restent à effectuer. La globale325 concerne la
version antérieure ; une nouvelle preuve générale doit couvrir332–334.
