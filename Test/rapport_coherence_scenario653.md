# Révision2 du jeu de documents RAS —653

Le cahier649 initial était arithmétiquement cohérent, mais son scénario de
société vierge et facture1200TTC n'établissait pas l'absence d'exclusion pour
petites prestations. L'ajout de fichiers n'est pas remis en cause ; c'est
l'hypothèse du jeu humain qui devait être corrigée. Aucun cumul mensuel n'est
inventé pour la justifier. Voir les [sources et limites de lecture](../docs/audit/SOURCES_SCENARIO_RAS_20261019_653.md).

La **version2**, diffusée par le différentiel653, remplace les documents courants
649. Les anciens ZIPs restent intacts et leurs tests restent des preuves
historiques, sans être présentés comme une qualification fiscale du petit cas.
Les douze identifiants de cas sont conservés et tous les statuts humains restent
**Non testé**, avec résultats, anomalies et preuves vierges.

## Nouveau scénario principal

| Contrôle | Avant annulation | Après annulation |
|---|---:|---:|
|Capital|100000 MAD|100000 MAD|
|Achat|10000 HT + 2000 TVA = 12000 TTC|Facture conservée|
|Quote-part|6000 TTC dont1000 TVA|Capture annulée|
|Trésorerie du règlement|5250 MAD|Contrepassée|
|Capture TVA du jeu|750 MAD|Compte choisi soldé|
|Banque|94750 MAD|100000 MAD|
|Fournisseur|6000 MAD|12000 MAD|
|Résultat comptable avant impôt|−10000 MAD|−10000 MAD|
|Bilan|96750 MAD|102000 MAD|
|Pièces / lignes|4 /9|6 /13|
|Débit = crédit cumulés|118000 MAD|124000 MAD|

La facture et la quote-part dépassent le petit montant évoqué dans la source
consultée. Cela ne qualifie pas automatiquement les autres faits : parties,
nature de prestation, exclusions et attestation restent explicitement déclarés
pour le laboratoire, à contrôler pour tout dossier réel. Les autres traitements
fiscaux ne sont pas déterminés par cette annexe RAS TVA. Le compte4457 reste
une convention du scénario, pas une affectation imposée.

La révision porte uniquement sur les données fictives, le générateur, ses tests
et la documentation. Aucun calcul applicatif, taux, SQL, donnée réelle ou
écriture validée de l'utilisateur n'est modifié.

7cas ciblés réussis en26.010s, zéro échec/erreur/ignoré : six contrôles documentaires/données/consignes et oracle natif102 avec Journal/FEC/bilan/CPC et originaux. Word/PDF16pages/Excel8feuilles révisés,12cas humains Non testé. Données12000TTC/quote6000/cash5250/RAS750/capital100000 vérifiées ; pourcentages, dates et0,005 conservés. Python compilé. Aucun produit ni SQL modifié ;218tests651 antérieurs non requalifiés en exécution653.

Le contrôle des consignes vérifie chaque débit/crédit des étapes capital/achat,
règlement/capture et annulation contre les lignes de l'oracle indépendant.
Il contrôle aussi les soldes exprimés dans les résultats humains, les100% de
déduction/prorata conservés et le cas négatif0,005 inchangé. Le test de données
interdit de revenir à une facture ou quote-part sous le petit montant du cas,
ou d'ajouter un cumul mensuel externe supposé.

Mise au point : la première campagne révisée avait réussi6cas (25,929s), mais
la lecture visuelle a repéré des montants anciens dans certaines phrases,
malgré l'oracle et le Journal corrects. La révision du texte traitait mal
les valeurs avant un point final ou collées à un mot. Le générateur et les
contrôles des consignes ont été corrigés avant livraison. Le succès initial
ne suffisait donc pas à qualifier l'ensemble du document.

Commandes réellement exécutées, avec `PYTHON_DOTENV_DISABLED=1` :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/generer_annexe_ras_documents649.py
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_annexe_ras_documents649.py Test/test_oracle_ras_documents649_isole.py -q -x
```

Les218cas applicatifs651 ont réussi avant cette révision documentaire ; les
sources applicatives n'ont pas changé depuis. Ils ne sont pas présentés comme
une nouvelle exécution de la révision2. Les tests ciblés ci-dessus portent
effectivement sur les nouveaux fichiers et montants. Dernier build applicatif
647 :12,49s ; aucun frontend modifié en653.

Documents à utiliser : [Word](../docs/recette/ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.docx),
[PDF](../docs/recette/ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.pdf),
[Excel](../docs/recette/ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.xlsx),
[données révisées](../docs/recette/donnees_recette_documents_ras_20261019.json).
Le PDF fictif à joindre n'a pas changé et n'est pas une attestation.

Word/Excel interactifs, recette humaine, modèles administratifs applicables,
imputation/reversement et production restent à qualifier. RH/paie et point6
humains demeurent différés. Suite : audit final des sources/ZIPs/journal et
livraison cumulative655, sans réappliquer les étapes déjà terminées.
