# Clôture connectée CCA/PCA — lot599

Deux parcours Edge/API/PostgreSQL natif jetable exécutés : CCA1440px,
PCA390px. Calcul documentaire repris explicitement, aperçu, création,
validation depuis le Journal, clôture2025, AN2026, validation de la
contrepassation2026 et FEC des deux exercices. Aucun contournement métier.

Profil fiscal de laboratoire déjà livré dans l'oracle annuel : SARL exploitée
depuis2020, droit commun, aucune exonération CM/minimum. CM3000 comptabilisée
par la clôture. Il ne s'agit pas d'une qualification fiscale d'un dossier réel.
CCA : résultat avant impôt−6065,93, après impôt−9065,93 ; AN23000 équilibré.
PCA : résultat avant impôt6065,93, après impôt3065,93 ; AN32000 équilibré.
Contrepassations2026 de5934,07, comptes3491/4491 soldés, CPC−5934,07/+5934,07,
bilan équilibré. Suppression de l'ajustement après clôture refusée423.
Entêtes/lignes des sources et de l'ajustement définitif inchangées.

Commande `Test/run_unit_tests.py Test/test_e2e_cloture_prorata599_isole.py -q` :
2 réussis en45,943s, aucun échec/ignoré. Premier lancement : deux erreurs du test
sur un nom de table au pluriel, corrigées d'après models.py ; aucun bug produit
masqué. FEC réellement téléchargés sur le laboratoire, aucune donnée réelle.

Suite : exposer les contrepassations d'ouverture dans l'exercice de destination,
avec source, montant, date et statut ; validation ordinaire dans le Journal.
Pas de reprise automatique de provision présumée, ni recette humaine validée.
