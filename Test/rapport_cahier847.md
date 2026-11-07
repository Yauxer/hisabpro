# HisabPro — échéances, dates et frais bancaires

Les fiches NEG017 à NEG020 sont exécutées dans Edge aux largeurs1440/390 avec API réelle et PostgreSQL natif éphémère. Les copies reproduisent CHQ-01 de20000MAD et EFF-C01 de10000MAD émis le01/04/2025 avec échéance15/05/2025. Aucune donnée comptable réelle n'est utilisée.

NEG019 : après remise et encaissement du chèque, l'écran ne propose plus Déclarer impayé. Une requête directe de rejet reçoit400 pour statut incompatible. Aucune écriture de contrepassation ni réouverture arbitraire de créance n'est créée ; le journal et les règlements restent identiques.

NEG017 : l'effet est remis puis une date d'encaissement14/05/2025 est saisie. L'API répond400 et le formulaire affiche le motif d'échéance15/05/2025. Le statut reste en attente d'encaissement et aucune entrée en banque n'est générée. Ce contrôle du flux d'encaissement existant ne constitue pas un traitement d'escompte anticipé.

NEG018 : des frais10001MAD pour un effet10000MAD sont refusés par le formulaire. La requête directe est refusée422 avant mutation. Aucun débit bancaire négatif ni nouvelle charge n'est créé.

NEG020 : le formulaire soumet successivement une date future, calculée comme lendemain de la date réelle du laboratoire, et le31/03/2025, antérieur à l'émission01/04/2025. Les deux requêtes reçoivent400 avec leur motif distinct, affiché dans le formulaire. Les situations, dates, statuts et écritures restent identiques.

Contrôle positif : le même effet est finalement encaissé au16/05/2025 avec10MAD de frais. Une seule écriture est produite à cette date :5141 débité9990,61472 débité10 et51132 crédité10000. Les originaux restent conservés. Ces assertions empêchent de confondre un flux entièrement bloqué avec une protection valide.

Deux parcours finaux et16tests connexes natifs des frais au centime sont réussis. Les preuves enregistrent les dates réellement utilisées. Aucun correctif produit ni nouvelle migration/règle fiscale n'a été nécessaire ; aucun nouveau build n'est revendiqué. Le suivi atteint167fiches automatiquement réussies,5partielles,90nonqualifiées individuellement et10bloquées à la source. Les70statuts globaux et les réserves841 restent conservés. Cela ne valide ni recette humaine ni production.

Prochaine étape : double rapprochement bancaire puis stocks et dotations négatives. RH/paie, dépôts officiels et justificatifs historiques restent différés. Aucun PostgreSQL utilisateur utilisé.
