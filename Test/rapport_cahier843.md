# HisabPro — plafonds des règlements et acomptes

Deux scénarios négatifs du cahier sont exécutés sur ordinateur et mobile, avec API réelle et PostgreSQL natif éphémère. Les préconditions sont préparées par API sur une société fictive indépendante ; les refus dans le formulaire et la lecture des écrans sont réels. Aucune base utilisateur n'est utilisée.

NEG012 : la facture fournisseur portant la référence littérale02 est validée et comptabilisée pour200MAD HT +40MAD TVA, soit240MAD TTC non réglés. Saisir241MAD dans le formulaire Payer le fournisseur laisse le formulaire ouvert avec le message de dépassement. La tentative directeAPI est également refusée. Les écritures, règlements, acomptes et situation de la facture restent identiques. Le même formulaire accepte ensuite240MAD exactement et produit une seule pièce de règlement, débit4411/crédit5141 pour240MAD. La facture est soldée. Ce contrôle positif évite de considérer un formulaire entièrement bloqué comme une protection réussie.

NEG013 : AC-C01 reçoit24000MAD pour le client services et est entièrement imputé sur sa facture de144000MAD. Le solde de cette facture reste120000MAD : le refus n'est donc pas provoqué par une facture déjà soldée. Dans Acomptes, la commande Imputer sur une facture n'est plus disponible pour l'acompte épuisé. Une nouvelle tentativeAPI de1MAD reçoit409 avec le motif entièrement imputé. Les écritures, imputations, règlements et soldes restent conservés.

Les deux premiers passages ont révélé des erreurs dans le test, conservées dans les JUnit : la liste des règlements exige exercice2025, et le compte est la deuxième valeur du tuple de ligne comptable, la première étant l'identifiant. Les préconditions et assertions ont été corrigées après lecture du code, sans modifier le produit ni les montants attendus.

Les deux parcours finaux passent ainsi que39tests connexes des montants finis et permissions PostgreSQL acomptes/avoirs. Aucun changement produit, migration, règle fiscale ou build nouveau n'est revendiqué. Le suivi passe à160fiches automatiquement réussies,5partielles,97nonqualifiées individuellement et10bloquées à la source. Les70statuts fonctionnels globaux restent inchangés. Les réserves et preuves841 restent historiques et conservées ; ni recette humaine ni production validée.

Prochaine étape indépendante : mauvais tiers et dépassement de crédit d'avoir, puis retour supérieur à la quantité vendue. RH/paie, formats de dépôt et données historiques nécessitant justificatifs restent séparés.
