# Lot625 — reprises et inverses sur exercices décalés

Le suivi affiche maintenant la date civile **et l’exercice comptable réel**
de chaque reprise et de chaque inverse. Les deux colonnes correspondantes
sont ajoutées en fin d’Excel (N/O), sans déplacer les13colonnes existantes.
Le PDF indique également les exercices réels. Ces valeurs viennent des
en-têtes comptables, pas de l’année extraite de la date ou de la source.
Aucune nouvelle migration, règle fiscale ou réparation historique.

## Parcours fictif réellement exécuté

| Étape | Calendrier et effet |
|---|---|
|Source2025|01/07/2024–30/06/2025 ; capital20000, dotation1000 au30/06/2025 validée puis exercice clôturé|
|Reprise2026|400au01/07/2025, exercice2026 (01/07/2025–30/06/2026), source2025déjà close|
|Fiscalité du banc|Déficit2025proposé1000explicitement enregistré ; clôture2026refusée avant confirmation d’imputation400, puis autorisée après confirmation réelle|
|Inverse2027|400au01/07/2026, exercice2027 ouvert (01/07/2026–30/06/2027), reprise2026déjà close|

Le profil fiscal fictif existant précise SARL exploitée depuis2020 et absence
d’exonération CM/minimum ; la CM3000 provient des paramètres déjà livrés.
Résultats comptables du banc après impôt :2025−4000,2026−2600 ;2027 avant impôt
−400. Aucune déductibilité d’un risque réel ni conformité réglementaire
n’est qualifiée par cette hypothèse de test.

L’inverse réserve encore400tant qu’il reste en brouillon, disponible600 ;
après validation : disponible1000. Le capital, la source définitive et la
reprise définitive sont comparés en octets avant/après. Le suivi, PDF/Excel,
FEC2026(date20250701) et2027(date20260701), CPC et bilan sont vérifiés. Le
bilan2027 reste équilibré à20000. Le contrôle de déficit n’est pas contourné.

## Tests et restauration

55cas réussis en134.685s, puis2parcours625renforcés en32.456s (recouvrent les2cas déjà présents, avec contrôle supplémentaire que source fiscale/déficits2026 restent inchangés après inverse2027), restauration1réussie en63.238s.0échec/ignoré final. Build Vite5,70s, Python compilé.

La restauration réutilise un vrai parcours625 dans une société séparée du
scénario civil du banc615. Après dump/restore natifs : mêmes suivis, SHA de
préparation, CPC/bilans et octetsFEC des trois exercices2025/2026/2027, schéma/
données/ACL/séquences des77tables identiques ; source préservée, cibles supprimées.
Les anciennes preuves de restauration615 restent intactes.

## Limites

Résultats automatisés de laboratoire uniquement. Installation réelle100,
qualification fiscale du dossier, recette humaine et Word/Excel interactifs
restent distincts. Aucune base réelle ou migration historique modifiée ; RH/
paie différées. Les mouvements manuels historiques non liés restent à analyser.
