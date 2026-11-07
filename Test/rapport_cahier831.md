# HisabPro — annulation d'un règlement dans l'exercice suivant

Le cas PAY020 est exécuté sur ordinateur1440 etmobile390, dans deux sociétés fictives distinctes sur PostgreSQL natif isolé. Une facture de30000MAD du20/01/2025 est soldée par le virement10000 du25/01 puis un chèque20000 du26/01, réellement remis au01/02 et encaissé au05/02 via les transitions métier. Les cinq écritures de2025 sont validées avant la recette de l'annulation.

Dans Cycle commercial →Vente →Règlements, le virement VENTE-01-PAY est annulé avec une contrepassation datée du06/10/2026, conformément à la variante. Le formulaire existant permet déjà de choisir cette date ; sa valeur initiale reste le jour courant. Le motif fictif est enregistré. La date de l'opération comptable est distincte de l'horodatage réel de son enregistrement dans la piste d'audit.

Une seule écriture inverse apparaît dans2026 : BQ D3421=10000/C5141=10000, date comptable et date de pièce06/10/2026. Elle pointe vers l'écriture de virement d'origine et conserve le motif. Elle est d'abord brouillon, puis validée dans le Journal2026. La créance commerciale est réouverte pour10000 ; le règlement annulé et l'autre chèque restent dans l'historique. Les cinq écritures2025 sont strictement identiques à leurs réponses API d'avant l'annulation ; le bilan,CPC etESG2025 restent identiques.

Le rechargement retrouve la référence ANN-VENTE-01-PAY. Rejouer la demande d'annulation retourne l'opération existante sans nouvelle écriture. Les six écritures finales sont définitives et aucune écriture d'origine n'est supprimée ou réécrite. Aucun code produit ni migration n'est modifié dans ce lot.

Le premier essai de préparation échoue correctement : la liste des écritures étant affichée des plus récentes aux plus anciennes, le test avait tenté de valider une écritureAE du26/01 après celle du01/02. Le test est corrigé pour valider dans l'ordre date/id, sans changer les dates ni contourner le contrôle chronologique. Les deux parcours finaux réussissent ; durées, essais et preuves sont conservés dans PREUVE_CAHIER831.json.

Le suivi passe à136fiches réussies,5partielles,121nonqualifiées individuellement et10bloquées par les sources. Les70statuts fonctionnels restent inchangés. Aucun PostgreSQL utilisateur ni donnée comptable réelle n'a été utilisé. La recette utilisateur globale et la conformité réglementaire ne sont pas validées automatiquement.

Utilisation : ouvrir le règlement →Annuler par contrepassation, choisir une date dans un exercice ouvert et renseigner le motif. Vérifier le solde commercial et la présence des deux règlements historiques, puis passer dans l'exercice de la contrepassation et valider l'écriture après contrôle. Ne pas effacer le paiement ni modifier son écriture d'origine.

Prochaine étape : scénarios négatifs du cahier, en commençant par identité, exercices et saisies invalides. RH/paie et point6 restent différés.
