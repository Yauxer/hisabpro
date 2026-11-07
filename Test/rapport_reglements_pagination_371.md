# Règlements au-delà de la première page — lot371

Le rapprochement de la liste des règlements avec seulement100factures masquait
les paiements plus anciens dans les volets Achat et Vente. Le formulaire de
règlement partageait cette limite. Ces deux chargements réutilisent maintenant
`facturesAPI.listerTout`, qui contrôle les pages répétées et les changements de société.
Aucun modèle, schéma SQL ou montant comptable n'est modifié.

Preuve sur PostgreSQL éphémère et Edge réel : une facture validée de120MAD,
un paiement de20MAD puis100brouillons plus récents. Le paiement doit apparaître
dans son sens uniquement, avec son numéro réel et la situation Partiel.
Les instantanés financiers avant/après consultation sont identiques.

- Avant :1échec,44,20s (`reglements371_avant.xml`).
- Première vérification :4échecs,75,68s ; paiements visibles mais assertion
  incorrecte «Partiellement» au lieu du libellé existant «Partiel». Corrigée.
- Vérification finale :28réussis,26avertissements,157,36s,code0 ;4nouveaux
  parcours achat/vente en1365/390px et24contrôles historiques du lot368.
- Build Vite :code0,4,91s ; avertissements existants xlsx/taille de bundle.
- Compilation du nouveau test :code0.

Commandes : `Test/run_unit_tests.py Test/test_reglements_pagination_isole.py
Test/test_lecture_reglements_historiques.py --tb=short
--junitxml=.codex-tests/reglements371_final.xml`, `npm run build`.
Les preuves XML sont conservées localement dans le cache de tests.

Base réelle non utilisée. Recette humaine encore à effectuer. Prochaine étape :
saisie ventilée par tiers en transaction atomique, sans modification des historiques.
