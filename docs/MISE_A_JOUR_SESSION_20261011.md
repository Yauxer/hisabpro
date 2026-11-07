# Mise à jour HisabPro — dates locales, 11 octobre2026

Différentiel à appliquer à une copie de recette déjà au niveau349 :
`HisabPro_Session_20261010_2129_Cumulatif_Verifie.zip`. Pour une installation
plus ancienne, appliquer ses prérequis selon la
[procédure précédente](MISE_A_JOUR_SESSION_20261010.md).
Le dépôt courant contient déjà les corrections : ne pas les réappliquer.

1. Préserver configuration, justificatifs et migrations. Comparer les
   fichiers avant remplacement et suivre les sauvegardes d'exploitation.
2. Appliquer le nouveau cumulatif `HisabPro_Session_20261011_0811_Cumulatif_Verifie.zip`
   à la copie isolée en conservant l'arborescence. Il ne remplace pas le projet.
3. Reconstruire le frontend avec `npm run build`, puis relancer uniquement
   les services de cette copie. Aucun SQL nouveau dans les corrections de
   cette reprise ; ne pas lancer une réparation historique pour les appliquer.
4. Règlements : contrôler la date de contrepassation d'une annulation et la
   conservation des écritures originales. Avec RAS, la date d'annulation
   doit être cohérente avec la capture ; les contrôles backend restent actifs.
5. Effets & Chèques : ouvrir une remise/rejet/encaissement/paiement, vérifier
   que la date proposée et la borne maximale sont le jour local. Saisir la
   vraie date bancaire ; conserver les refus de date future ou antérieure.
6. Rapprochement bancaire : vérifier la date proposée dans Saisie manuelle,
   saisir la vraie date du relevé et vérifier sa conservation au chargement
   du contexte. Dans un exercice passé ou futur, la proposition reste dans
   les bornes de l'exercice. Une saisie de relevé ne réécrit pas le journal.
7. En cas d'erreur sur la liste des factures, contrôler les compteurs « — »,
   l'export désactivé et le bouton Réessayer. Une erreur persistante de
   lecture historique est àtraiter par le technicien ; ne pas réparer
   une ancienne donnée comptable pour masquer l'alerte.
8. Consulter le [guideWordv8](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx)
   ou le [PDF](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.pdf), puis consigner
   les résultats réels et captures. Office et recette utilisateur restent à faire.

Le test d'effets352 calcule « demain » lors de l'exécution, pour préserver
son sens si une suite traverse minuit. Cela ne change aucune règle métier.
Le délai de connexion devis de346 n'a pas de cause prouvée ; le banc350
conserve davantage de diagnostics réseau sans retry ou délai assoupli.
Voir les rapports [350](../Test/rapport_diagnostic_sept_echecs_350.md),
[351](../Test/rapport_dates_locales_reglements_351.md) et
[352](../Test/rapport_effets_dates_minuit_352.md). Une réussite ciblée ne
requalifie pas la globale346 ; la consolidation354 est une preuve distincte.

La [consolidation354](../Test/rapport_non_regression_reprise_20261011_0811.md)
a réellement réussi3126tests, code0, avec686empreintes identiques. Elle
précède le lot bancaire357, vérifié par sa suite ciblée et son build propres.

Le [diagnostic359](../Test/rapport_lecture_factures_historiques_359.md)
confirme un défaut de lecture historique noncorrigé :2réussis/6échoués.
La garde d'affichage360 conserve cette erreur visible et ne qualifie pas
les anciens montants comme valides.

Aucune base réelle utilisée pour ces tests. Développement global partiel,
recette utilisateur non effectuée et préparation à la production non validée.
