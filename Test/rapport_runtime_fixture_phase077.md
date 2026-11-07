# Fixture runtime — phase historique077, 8 octobre 2026

## Cause et correction

Le banc `test_permissions_cycle_facturation_postgres.py` vérifie le passage d'un
rôle PostgreSQL runtime sans droits sur `societes` aux droits accordés par077.
Il importait toutefois la liste `COMPLEMENTS` de la recette consolidée, désormais
étendue jusqu'à081, et appliquait077 avant de vérifier le refus initial du SELECT.
Le test ne pouvait donc plus observer sa phase initiale.

La fixture applique maintenant uniquement les compléments de préfixe inférieur
à77, soit074–076 actuellement. Le SELECT initial doit toujours échouer avec42501.
La migration077 reste appliquée deux fois ensuite pour vérifier son rejeu.
Les scénarios078 et079 continuent d'appliquer explicitement leurs migrations.

Le catalogue importé de la recette consolidée exigeait également les nouvelles
contraintes080/081, étrangères à cette phase. La fixture possède désormais un
catalogue local explicite des cinq contraintes historiques et six déclencheurs
074–076. Les noms attendus, l'activation `tgenabled='O'`, les définitions et les
états de validation sont conservés. L'égalité du catalogue avant/après chaque
rejeu077 reste exigée ; aucun contrôle historique n'a été retiré.

Seul ce fichier de test a été corrigé. Aucun SQL, GRANT, déclencheur ou helper
d'installation consolidée n'a changé. Aucune installation081 n'a été effectuée
dans ce banc historique.

## Commandes et résultats réellement exécutés ici

```text
PYTHON_DOTENV_DISABLED=1 python -X utf8 Test/run_unit_tests.py Test/test_permissions_cycle_facturation_postgres.py Test/test_factures_suppression_postgres.py Test/test_permissions_suppression_brouillons_postgres.py
```

- Premier lancement, après filtrage des migrations seulement : **1 réussi,
  31 erreurs de préparation, 45,64 s**. Le catalogue consolidé exigeait encore
  les contraintes `employes`080 absentes de la phase077. Ce résultat n'est pas
  présenté comme une validation.
- Après correction du catalogue local : **32 réussis, 48,88 s**, aucune erreur
  ni test ignoré. API avec vrais JWT et rôle PostgreSQL runtime non propriétaire,
  cycle facture/règlement, isolation des sociétés, immutabilité des définitives,
  ACL des archives/audits, droits ciblés de suppression des brouillons et rejeux.
- `python -X utf8 -m py_compile` sur les trois fichiers ci-dessus : **OK**,
  exécuté à nouveau après la dernière modification.

Les clusters PostgreSQL sont créés sous `.codex-tests`, gardés par URL loopback,
répertoire et nonce. Les fixtures arrêtent les serveurs et vérifient le nettoyage
de leurs répertoires. Aucun PostgreSQL réel ou donnée comptable réelle utilisé.

## Portée

La validation couvre la phase historique077 et ses scénarios connexes078/079.
Elle ne remplace pas la recette d'installation consolidée080/081. La suite globale
antérieure comportait d'autres échecs : le résultat ciblé ne constitue pas une
nouvelle validation globale. Livraison différentielle et consignation assurées
par l'agent principal.
