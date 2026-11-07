# Qualification finale — logos, modèles et lectures

Le 16 octobre 2026 : **143 réussis, zéro échec/erreur/ignoré, 29 avertissements,
423,15 s, code 0**. Les **780 empreintes de sources** Python/SQL/frontend,
styles, assets et configurations sont identiques avant/après la commande,
puis ont été comparées aux fichiers courants après sa fin.

```powershell
python -X utf8 Test/run_unit_tests.py Test/test_consolidation_logos_modeles_20261016.py Test/test_lecture_ecritures_invalides_isole.py Test/test_e2e_lectures_comptables_isole.py Test/test_tva_verrou_exercice_isole.py -ra
```

Ce résultat remplace la qualification de 475 pour les sources finales après
le verrou TVA 477. Les 140 cas de 475 et les trois scénarios de concurrence
sont exécutés ensemble, pas additionnés depuis leurs comptes rendus.

Le périmètre comprend les logos PDF/XLSX et impressions, modèles et avances
personnel, recalcul HT/TVA, refus de téléchargement, facturation achat/vente
jusqu'aux règlements/lettrage/FEC, instruments, clôture, restauration native,
diagnostics de lecture et reprise des écrans, droits TVA et verrou d'exercice.
API réelle, Edge et PostgreSQL à nonce sous LOGIN limité ; fonctions pures
Python/Node exécutées dans le même lancement. Aucun PostgreSQL utilisateur.

Le jeu positif sous runtime 093 contient 58 sociétés fictives, 99 écritures,
249 lignes, deux clôtures, 26 lettrages, 64 modèles et 150 lignes de modèle.
Les compteurs de déséquilibres, montants non finis et écritures définitives sans
numéro/date sont à zéro ; ACL et 134 empreintes internes inchangées. Les trois
laboratoires négatifs de lecture/concurrence sont séparés de ce jeu positif.
Leurs anomalies volontaires ne sont pas effacées pour obtenir ces compteurs.

Le dernier build frontend est celui de 474 : code 0, 7,39 s. Aucun frontend
modifié depuis. Les 33 cas ciblés TVA/clôture de 477 ont également réellement
réussi en 122,86 s. Ces nombres recouvrants ne s'additionnent pas à 143.

Les pannes volontaires de certains scénarios sont contrôlées dans leurs
assertions ; cette campagne ne prétend pas qu'aucune réponse 500 n'a existé.
La suite globale historique 3426 n'est pas déclarée rejouée. Les résultats
intermédiaires échoués de 469 et 477 restent documentés dans leurs rapports.

Restent à qualifier : PostgreSQL réel, application manuelle 092/093, Excel et
boîte d'impression du partenaire, recette humaine et production. Le verrou TVA
porte sur une ligne d'exercice existante, pas le SQL direct ni tout le calcul
préalable de clôture. Les données et sources réglementaires manquantes restent
visibles ; point 6 en attente utilisateur. Aucun statut global promu ici.
