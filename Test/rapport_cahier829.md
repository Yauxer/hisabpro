# HisabPro — avoir intégral et remboursement bancaire

La variante FAC016 est rejouée dans deux sociétés fictives indépendantes, sur PostgreSQL natif isolé et Edge1440/390. Les préconditions sont une vente du20/01/2025 de100unités à250MADHT, soit25000HT+5000TVA=30000TTC, entièrement réglée. L'article dispose de200unités avant vente ; il en reste100 avant le retour. Les opérations sont exclues des totaux du scénario annuel principal.

L'avoir intégral de retour/annulation est créé dans le formulaire au10/02/2025, avec100unités et retour physique confirmé. Sa seule création ne modifie ni le stock ni les écritures. La comptabilisation produit AV D7111=25000,D4455=5000,C3421=30000, puis l'écriture est validée au Journal. Le stock augmente de100 une seule fois et retrouve200unités.

Le crédit libre30000 est remboursé dans le formulaire par virement au11/02/2025, sur le compte bancaire5141, avec référence fictive REMBOURSEMENT-FAC016-829. L'écriture de remboursement D3421=30000/C5141=30000 est vérifiée puis validée. L'avoir devient remboursé, une seule utilisation active est enregistrée et son crédit disponible est nul. Après rechargement, la référence et l'historique demeurent visibles ; le bouton de remboursement n'est plus disponible. Une nouvelle tentative de remboursement1MAD est refusée409 sans mutation comptable ni stock supplémentaire.

Les quatre écritures finales sont définitives. Les deux écritures antérieures de facture et règlement sont conservées strictement, ainsi que le règlement commercial initial. Le retour de stock n'est pas répété lors du remboursement et aucun document d'origine n'est supprimé. Aucun code produit ni migration n'est modifié dans ce lot.

Le premier essai échoue correctement sur une préparation nonchronologique : un article créé aujourd'hui avec stock initial ne permet pas de saisir ensuite une vente de2025. La préparation est corrigée via les flux existants : article sans stock puis inventaire fictif daté01/01/2025 avant toutevente. Aucun mouvement existant n'est redaté et la règle CMUP reste active. Un essai intermédiaire échoue ensuite sur la lecture finale du test : le paramètre exercice requis avait été omis du GET des avoirs. Ce paramètre est ajouté, sans changement produit. Les résultats exacts, essais échoués, preuves et captures sont conservés dans PREUVE_CAHIER829.json.

Le suivi passe à135fiches réussies,5partielles,122nonqualifiées individuellement et10bloquées par les sources. Les70statuts fonctionnels restent inchangés. Aucun PostgreSQL utilisateur ni donnée comptable réelle n'a été touché ; la recette utilisateur et la conformité réglementaire ne sont pas validées automatiquement.

Utilisation : ouvrir la facture soldée →Créer un avoir →Retour/annulation, sélectionner toutes les quantités et confirmer le retour physique. Après comptabilisation et validation au Journal, ouvrir l'avoir →Rembourser, choisir date, banque et référence, puis valider l'écriture générée au Journal. Vérifier le crédit restant et l'historique après rechargement.

Prochaine étape : variante PAY020, annulation de règlement par contrepassation datée dans l'exercice suivant ouvert. RH/paie et point6 restent différés.
