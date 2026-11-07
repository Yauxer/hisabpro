# Chargement des règlements : protection du contexte — lot390

## Analyse et reproduction

La liste lançait des GET parallèles sans invalider l'ancienne requête lors d'un changement d'exercice. Un GET2026 retenu puis libéré après le chargement2025 remplaçait les lignes de2025 par celles de2026. Preuve avant correction : **1échec réel**,33.043s, dans la copie isolée ; snapshot de l'interface conservé dans le JUnit local. Aucune donnée réelle consultée.

## Correction minimale

OngletReglements possède une génération indépendante pour les chargements. Exercice, sens achat/vente, jeton et génération doivent encore correspondre avant de mettre à jour liste, factures ou chargement. Nettoyage au changement de contexte et démontage. Les calculs, statuts et opérations comptables restent inchangés. Les gardes d'annulation388 restent distinctes.

## Tests réellement exécutés

- Copie isolée après correction :2réussites,0échec/erreur/ignoré,26avertissements,33.26s.
- Racine :42réussites,0échec/erreur/ignoré,26avertissements,276.989s :2nouveauxEdge1365/390,4contexteannulation,22annulationnative,10inter-exercices,4pagination.
- Après garde supplémentaire avant invalidation, racine finale :28réussites,0échec/erreur/ignoré,26avertissements,112.397s (chargement,contexteannulation,annulationnative). Les42précèdent cet ajustement ; suites non additionnées.
- Compilation Python du nouveau test :code0.
- Build frontend initial :code0,5.21s ; build de la version finale :code0,5.57s. Avertissements existants xlsx/chunk volumineux conservés.

Les tests utilisent PostgreSQL nonce et API locale isolée, Edge authentifié, requête API réellement obtenue puis retardée. Aucun faux résultat métier injecté. Photos comptables avant/après identiques. La consolidation389(232réussites) précède cette garde390 ; aucune nouvelle globale de tous modules exécutée après390.

## Limites et reprise

Recette navigateur de l'utilisateur à effectuer. Aucun PostgreSQL réel, donnée comptable réelle, modèle ou migration modifié. Point6 en attente utilisateur. Nouvelle globale des versions finales puis instrument bancaire unique/rapprochement d'une ventilation à une ligne bancaire et autres variantes annuelles.
