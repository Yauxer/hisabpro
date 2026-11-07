# Accueil et Grand livre — états de lecture explicites

Le bloc « Écritures à valider » de l'accueil ignorait les erreurs du contexte
et affichait une table vide après le refus 409 d'un brouillon historique
invalide. Il affiche désormais le diagnostic et « Réessayer », ou un état de
chargement. Le compteur et la table sont masqués dans ces deux états. Les
indicateurs obtenus indépendamment du Journal restent affichés.

Le Grand livre conservait un résumé « 0 comptes / 0 écritures » sous son erreur
de filtre. Son erreur est désormais une alerte, le rapport n'est pas affiché
et l'export est désactivé. Un filtre corrigé recharge et réaffiche le rapport.
Aucun calcul, filtre comptable ou comportement backend n'est modifié.

## Tests exécutés

Quatre nouveaux parcours Edge, en 1440 et 390 pixels, utilisent de véritables
API et PostgreSQL à nonce. Pour l'accueil, un brouillon fictif NaN est simulé
sans toucher l'autre écriture définitive ; alerte, relance 409, absence de table,
indicateur indépendant visible et originaux inchangés sont vérifiés. Le Grand
livre passe d'un rapport réel de deux comptes / une écriture à un filtre inversé,
puis retrouve le rapport réel et l'export après rétablissement des dates.
Aucune réponse API métier n'est interceptée ou remplacée.

Avant correction : quatre échecs en 74,81 s. Première relance : deux réussites
et deux échecs en 50,10 s ; les deux alertes de l'accueil étaient correctes,
mais le sélecteur exact du titre CA ignorait son enfant « détail ». Le test
contrôle désormais le libellé de l'indicateur indépendant « Résultat net ».
Il conserve toutes ses assertions de refus et d'intégrité.

Résultat final : **11 réussis, zéro échec/erreur/ignoré, 29 avertissements**,
en **113,31 s**, code 0. Ce total inclut les quatre nouveaux parcours, les cinq
cas négatifs de lecture 470 et les deux cas Journal lecteur 457.

```powershell
python -X utf8 Test/run_unit_tests.py Test/test_e2e_lectures_comptables_isole.py Test/test_lecture_ecritures_invalides_isole.py Test/test_e2e_journal_lecture_isole.py -ra
```

Build Vite : code 0, 7,39 s ; avertissement existant de taille de bundle.
Compilation du nouveau test exécutée avant livraison. Le contrôle de dates
inversées est un cas réel de validation frontend ; il ne qualifie pas toutes
les causes possibles d'indisponibilité serveur du Grand livre. Les écritures
historiques ne sont ni réparées ni omises silencieusement. PostgreSQL utilisateur,
autres navigateurs et recette humaine restent à vérifier ; point 6 en attente.
