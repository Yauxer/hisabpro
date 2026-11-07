# Lecture qualifiée des règlements historiques — lot368

**Correction exécutée et testée ; recette humaine distincte.**

## Défaut reproduit

La liste GET `/api/reglements` utilise le modèle de saisie `ReglementCreate`
via `ReglementOut`. Un montant historique NaN, +infini, -infini ou nul fait
échouer la validation de réponse entière et masque le règlement sain.
Le montant nul est déjà interdit à la saisie ; il reste un zéro explicite
dans la source et ne doit pas être transformé en montant inconnu.

Le banc fictif crée une facture HT100, TVA20, TTC120, la valide normalement
et crée deux règlements non comptabilisés de20 et10. Seul le deuxième
règlement fictif est préparé comme source défaillante. Aucune écriture
définitive ni trigger d'intégrité n'est modifié pour préparer ce cas.

## Preuves avant correction

- Observation `.codex-tests/diagnostic_reglements368.py` : quatre GET500 ;
  photographies des tables identiques avant/après chaque lecture.
  Son code0 signifie seulement que l'observation a été enregistrée.
- Oracle200 `.codex-tests/test_oracle_reglements368.py` :4tests échoués,
  0erreur,0ignoré,22,710s. JUnit `reglements368_avant.xml` conserve
  les quatre réponses500. Ce résultat n'est pas déclaré réussi.

## Correction

Projection de lecture distincte de la validation de saisie ; nonfinis nullable,
zéro et négatif finis explicites mais signalés, identifiants et autres champs
conservés. La lecture conserve filtrage exercice/facture/société et ordre.
Les actions financières et mutations normales d'une source monétaire
défaillante sont refusées422 avant toute écriture ou suppression.
La situation d'une facture liée reste également indéterminable ; le calcul
réutilise la règle positive déjà présente dans le modèle de saisie.

Commercial et Effets/Chèques conservent les deux lignes, signalent les
totaux à vérifier et rendent les actions de la ligne défaillante
indisponibles. Commercial évite un statut Soldée inventé. Le détail Factures
utilise sa lecture seule si la situation liée n'est pas qualifiée.
La qualification reste monétaire ; elle ne
constitue pas un audit exhaustif des modes, dates ou justificatifs historiques.

## Tests réellement exécutés

- `Test/test_lecture_reglements_historiques.py` :24réussis,0échec/erreur/ignoré,
  26avertissements,92,09s,code0 ; JUnit92,083s.
  Dixcas API vente/achat :NaN,+infini,-infini,zéro et négatif. Ordre,
  filtres exercice/facture, séparation entre sociétés, situations liées,
  cinqactions refusées et photographies des sources inchangées.
  QuatorzeEdge réels :8Commercial et6Effets,1365/390.
- Connexes :125réussis,0échec/erreur/ignoré,26avertissements,326,85s,code0.
  Modules montants, modes/dates d'effets, édition des règlements,
  facturation→validation→règlement→lettrage, RAS/solde/lettrage,
  chèque impayé, captures RAS et lecture des factures historiques.
- Compilation des3fichiers backend et du nouveau test :code0.
- BuildVite :code0,5,09s ; avertissements connus sur xlsx et taille du bundle.
- Empreintes :691sources avant/après les suites ciblées,aucune modification.

Les quatre captures Commercial/Effets1365/390 ont été inspectées.
Desktop lisible ; le mobile révèle une navigation fixe qui comprime le
contenu. Les14testsEdge valident les comportements et gardes, sans prouver
une lisibilité mobile complète. Ce défaut est reproduit par un oracle
distinct370 :largeur utile170 sur390,un test échoué avant correction.
Il est traité dans un lot séparé, sans masquer cette observation.

## Limites

Aucune migration ou réparation historique. Tests uniquement sur PostgreSQL
éphémère nonce gardé et navigateur Edge automatisé. Base utilisateur,
recette humaine et préparation de production restent distinctes.
La consolidation365 précède cette correction ; ses résultats ne peuvent
être présentés comme validation des sources368.

Prochaine étape :corriger/tester la navigation mobile370, actualiser le guide,
la couverture et le cumulatif. Paiement multi-factures et réparation
historique restent des périmètres distincts.
