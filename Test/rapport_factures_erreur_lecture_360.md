# Factures : compteurs indisponibles et reprise — lot360

Une erreur de chargement ne signifie pas zéro facture. Les compteurs
En attente/En retard utilisent désormais la même garde que les montants.
La liste est indiquée indisponible, l'exportCSV désactivé et un bouton
Réessayer relance le contexte existant. Une liste vide correctement
chargée conserve ses zéros et son export. Aucun backend n'est modifié.
**LeGET500 historique359 reste noncorrigé et l'alerte reste visible.**

## Tests réellement exécutés

Commandes avec Python du venv, `-X utf8`, dotenv désactivé, runner isolé :

- Avant correction :nouveaux cas `-k 'nan or liste_vide'`,2réussis,
  2échoués,4désélectionnés,25avertissements,45,22s,code1. Les deux
  erreurs NaN affichaient des compteurs0 ; les deux listes vides étaient
  correctement à0.
- Première sélection après correction :16réussis,6échoués,25avertissements,
  142,21s,code1. La garde, les lignes rechargées et l'export étaient
  corrects ; le test attendait àtort0facture en attente au lieu des deux
  factures fictives créées avec ce statut. Oracle corrigé à2, avec
  vérification des deux statuts API ; les vrais zéros restent testés.
- Sélection finale :**22réussis,0échec/erreur/ignoré,25avertissements,
  109,16s,code0**. Préfixe `.codex-tests/compteurs360_livraison`.

```text
Test/run_unit_tests.py Test/test_e2e_factures_erreur_lecture_isole.py
Test/test_e2e_factures_ca_dates_isole.py Test/test_e2e_factures_retard_isole.py
Test/test_factures_periode.py -vv --tb=short
--junitxml=.codex-tests/compteurs360_livraison.xml
```

Onze cas Edge connectés :huit nouveaux (NaN/+inf/quantitéNULL×largeurs1365/390,
plus deux listes vides), puis dates/retards/agrégats connexes. Les onze
autres cas sont des contrôles Node de calendrier et période. Aucune API
n'est simulée. Chaque préparation, ycompris la remise d'une cellule
fictive àune valeur connue pour vérifier Réessayer, est gardée sur
PostgreSQL nonce ; aucune réparation produit ou base réelle utilisée.
Les photographies restent identiques après les lectures/rechargements.

Build réel `npm run build` :code0,6,25s ; avertissements de bundle/import
statique-dynamique conservés. Compilation du test et diagnostic359 :code0.
Les689sources figées360v2 sont identiques après tests ; seules six
différences depuis354, comprenant les lots357/359/360. La globale354
précède ces lots et n'est pas requalifiée comme validation ultérieure.

## Guide et limites

GuideWord/PDFv8 généré :390blocs,25pages,18fiches,17statuts Non testé.
Fiche04 décrit l'indisponibilité, Réessayer et le maintien du défaut359.
OOXML/XML/relations/CRC et toutes les pages PDF contrôlés ;11références
et oracles indépendants,8liens de procédure résolus, pieds11/10/2026
contrôlés ; page7 rendue et inspectée. Office et recette humaine nonfaits.

Le diagnostic359 conserve2réussis/6échoués,code1, hors collecte globale.
Prochaine correction :lecture API/UI qualifiée des factures historiques,
sans fausse valeur0, exclusion silencieuse ou modification des sources.
Développement global partiel et production nonvalidée.
