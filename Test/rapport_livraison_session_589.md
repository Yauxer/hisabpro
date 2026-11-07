# Livraison finale571–589 — contrôle du différentiel

Le dernier correctif rend explicite l'année civile du registre dans le cockpit
Liasse, avec choix des deux années pour un exercice décalé. Le service indique
le même périmètre dans ses données et les trois exports. Aucun calcul fiscal,
montant, ancien SQL ou schéma supplémentaire n'a été modifié.

## Tests et contrôles exécutés

- Consolidation589 :139réussis,1échec de préparation,29avertissements,352,17s.
  Le nouveau test appelait exercice2026 une période finissant en2027 ; l'API
  l'a correctement refusé. Le banc a été corrigé sans modifier le produit.
- Relance du seul cas décalé :1réussi,6non sélectionnés,29avertissements,38,66s.
  Exercice2027 du01/07/2026 au30/06/2027, sélection civile2026→2027→2026,
  trois captures puis aucune puis trois ; sociétés et écritures inchangées.
  Pas de relance globale après ce correctif de fixture. Les139autres cas ont
  réussi sur les mêmes sources produit, incluant les deux parcours587.
- Dernière restauration native :1réussie,29avertissements,79,56s.75tables,
  schéma/données/ACL/séquences, JSON/CSV/textePDF/valeursExcel/logo conservés,
  source de laboratoire préservée et cibles supprimées.
- Build final :réussi,10,44s ; avertissement existant sur les gros chunks.
- Compilation des28fichiers Python du cumulatif réussie ; guidePDF2pages,
  texte civil/SHA/images et bornes vérifiés. PDF réel du registre final ouvert,
  périmètre civil et empreinte présents, aucun débordement de texte détecté.

## Intégrité et archives

Référence de départ :4035empreintes, sans dépôt Git local. Aucune suppression
ou modification inexpliquée des fichiers suivis.98SQL préexistants, AGENTS,
main/models et anciens guides/recette préservés. L'ancien asset hero.png,
daté de mai2026 et hors champ de l'empreinte source, est laissé intact et exclu.

Les neuf ZIPs571–587 conservent leurs SHA-256 et leur contenu CRC valide.
L'ordre de certains anciens ZIPs diffère de l'ordre des listes de preuve :
les ensembles de fichiers sont identiques, sans doublon. Le contrôle ne
confond pas cet ordre sans effet avec une altération de contenu.

Deux archives sont fournies : différentiel589 de10fichiers et cumulatif571–589
de63fichiers, arborescence exacte et dernières versions du journal incluses.
Contrôle CRC, liste complète et comparaison octet par octet avec le dépôt.
Seul SQL nouveau :099_ras_tva_details.sql. Aucun cache, environnement, dump,
ZIP imbriqué ou fichier temporaire. Aucun PostgreSQL réel contacté.

La synthèse, les guides, les archives et les limites sont dans
[le rapport de session](../docs/audit/RAPPORT_SESSION_20261018_RAS_TVA.md).
Prochaine reprise : règles et modèles officiels de déclaration/imputation/
reversementTVA, puis autres lots hors RH indépendants du plan. Installation
cible099, recette humaine et production restent à effectuer. Développement
global partiel ; aucune certification officielle revendiquée.
