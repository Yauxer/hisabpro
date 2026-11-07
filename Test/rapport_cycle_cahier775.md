# Cycle commercial du cahier775

Le premier sous-parcours commercial2025 fonctionne avec les valeurs exactes du cahier :acompte fournisseur6000,achat12000,imputation6000,solde6000,achat14400,devis/BC/BL/vente30000,virement client10000.7écritures définitives,17lignes, débits =crédits =84400MAD ;stock100unités auCMUP110,solde client20000. Le lettrage fournisseur à3lignes est conservé après reload. Les écritures sont produites par les vraies routes métier depuis Edge,pas injectées comme résultat attendu.

Corrections limitées àCommercial.jsx :notes facultatives du bon de commande désormais saisissables ;date de facture indépendante choisissable lors de la conversion d’un BL. Le défaut de note a été reproduit dansle navigateur. La date était déjàacceptée parAPI ;son exposition UI est une extension testée,la date proposée reste celle du jour à chaque ouverture,indépendante de la date du BL. La date du BL était déjàsaisissable et n’a pas été réimplémentée. Aucun backend/migration/règle fiscale modifié.

Résultats :2parcours complets réussis en86,72s ;après ajout du reload lettrage etcontrôles statut/lignes,13tests finaux réussis en266.46s (2nouveaux et11commerciaux connexes),aucun échec/erreur/ignoré final. Recouvrements non additionnés. Build Vite0 en6,02s,avec avertissement bundle. Deux Python compilés. Les3échecs initiaux restent conservés :2erreurs de helpertraitant des réponses récapitulatives comme des facturescomplètes et1champ de note absent ;les aides de test ontété corrigées sansaffaiblir lesmontants attendus.

Le classeur SUIVI_AUTOMATISATION_CAHIER_775.xlsx rapproche individuellement272fiches existantes :20réussies automatiquement,2partielles,240non qualifiées parfiche et10bloquées dansla source. Ces240ne sontpas déclarées dépourvues de tests techniques ;la correspondance exhaustive n’estpas attestée. Lesanciens classeurs humains sont inchangés. Les2cas partiels sont HP-ADM-003 (branche conditionnelle exercice) etHP-ADM-013 (comptes de stock3111/6114 àconfirmer dans l’inventaire).

Limites :capital etimmobilisation initiaux non rejoués dans ce sous-parcours ;banque préparée parAPI,formulaire testé771. Pas de prétention d’exercice annuel complet, de recette humaine oude production. Mentions client incomplètes laissées visibles. Aucun PostgreSQL réel ;RH/paie etpoint6 différés ;incident Lettrage769 ouvert,nonexpliqué même si les reloads de ce lot passent.

Suite :chèque client20000 puisavoir10unités etsecondevente50unités,pour atteindre lestock60/CMUP110 du cahier,avant inventaire etautres formulaires annuels.
