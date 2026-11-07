# Compléments auxiliaires : structure indépendante et immutabilité

Migration additive `075_complements_auxiliaires_structure.sql`, testée uniquement sur PostgreSQL éphémère local marqué. Aucun PostgreSQL réel, aucune donnée comptable réelle et aucun traitement historique 068/070 exécuté.

## Modification minimale

La migration reprend uniquement la structure située avant le premier `UPDATE tiers` de 068 : table, clés étrangères, deux index et garde append-only UPDATE/DELETE (SQLSTATE 23514). Elle ajoute une garde TRUNCATE de statement, révoque UPDATE/DELETE/TRUNCATE de PUBLIC et du rôle applicatif `hisabpro`, et conserve SELECT/INSERT ainsi que USAGE/SELECT sur la séquence. Elle ne change ni 068 ni 069.

Les trois CHECK du modèle ORM sont ajoutés seulement s'ils manquent sur cette table précise (`conrelid` et nom). `NOT VALID` préserve une éventuelle ligne ancienne non conforme sans la réparer ; les nouvelles insertions doivent présenter une nature client/fournisseur et un compte/libellé non vides. Les contraintes déjà présentes ne sont pas remplacées ni rétrogradées.

Aucune attribution de tiers, génération d'auxiliaire, mise à jour de ligne comptable ou réparation de données ne figure dans la migration.

## Tests réellement exécutés

```powershell
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m pytest Test/test_complements_structure_postgres.py -q
```

Résultat final : **5 réussis en 54,48 s**, aucun échec, aucun ignoré. Les 26 avertissements de dépréciation SQLAlchemy/Starlette/Pydantic proviennent des imports existants. Une première version du même test avait également réussi : 5 tests en 50,18 s ; le passage métier d'insertion a ensuite été renforcé et la suite entièrement réexécutée.

Scénarios et preuves :

- Rejeu deux fois avec ligne historique fictive invalide conservée strictement, et comparaison complète des tiers, codes auxiliaires, écritures et lignes avant/après.
- Trois origines d'anciennes permissions : directement `hisabpro`, PUBLIC, groupe hérité. ACL directes et PUBLIC supprimées ; l'héritage restant est effectivement bloqué par les triggers 23514. Les refus ACL sans héritage donnent 42501.
- UPDATE, DELETE et TRUNCATE refusés aussi au propriétaire sur les lignes présentes ; chaque tentative est suivie d'une comparaison des données.
- Connexion LOGIN réelle `hisabpro`, distincte du propriétaire, sans superutilisateur ni appartenance au rôle propriétaire.
- Insertion autorisée par la fonction métier existante `ajouter_auxiliaire_historique`, avec tiers explicitement sélectionné et code auxiliaire déjà renseigné. Ce test appelle la fonction Python avec une Session réellement connectée sous le rôle applicatif ; ce n'est pas un test HTTP ou navigateur.
- Nouvelles natures invalides, comptes blancs et libellés blancs rejetés 23514 malgré l'historique non validé.
- Table absente créée sans complément ni rattachement automatique ; rôle applicatif absent accepté et rejeu possible.
- Même nom de CHECK dans une autre table : il ne masque pas l'ajout du contrôle sur la table cible.
- Clusters créés via `cluster_isole`, garde nonce/répertoire/URL avant mutations et application SQL ; arrêt et suppression vérifiés à la sortie de chaque scénario.

```powershell
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m pytest Test/test_patch097_fec_complements_historiques.py Test/test_patch098_fec_corrections_historiques.py Test/test_patch099_fec_sources_factures_auto.py -q
```

Résultat : **16 réussis en 0,18 s**, aucun échec, aucun ignoré.

```powershell
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m py_compile Test/test_complements_structure_postgres.py
```

Résultat : code de sortie 0, compilation réussie après la dernière modification.

## Limites

Les anciennes lignes non conformes restent visibles et doivent être examinées séparément ; aucune validation globale des CHECK n'est exécutée. Les droits reçus d'un groupe ne sont pas silencieusement modifiés : les triggers apportent la protection contre UPDATE/DELETE/TRUNCATE. Un propriétaire ou superutilisateur reste capable d'administrer le schéma et désactiver des triggers ; le compte de production doit donc être un rôle applicatif non propriétaire avec droits maîtrisés.

Aucune application automatique de migration au PostgreSQL utilisateur ni validation navigateur/production n'a été effectuée. L'installation complète depuis une base vierge reste une recette distincte, à poursuivre avec les autres compléments structurels identifiés.
