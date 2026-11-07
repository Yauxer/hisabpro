# HisabPro — échéancier contractuel et prochaine échéance impayée

Une facture de1200MAD du01/04/2025, répartie en deux échéances de600MAD au30/04 et au31/05, était correctement réglée partiellement dans le détail. La liste continuait pourtant d'afficher le30/04 déjà soldé comme date de retard. Cette incohérence est reproduite avant correction.

La lecture des factures expose maintenant date_prochaine_echeance, calculée à partir du service FIFO et de la situation réelle de paiement déjà utilisés par le produit. Le contrat conserve sa date initiale ; aucune facture ni écriture n'est réécrite par cette lecture. Le badge, le filtre et les indicateurs de la page Factures utilisent la prochaine échéance encore ouverte. Les jours de retard suivent les dates calendaires ; le jour d'échéance reste sans retard à toute heure. Un échéancier multiple dont la situation n'est pas qualifiée ne reçoit pas une date supposée.

La variante FAC015 est exécutée dans deux sociétés fictives distinctes, sur PostgreSQL natif isolé et Edge ordinateur/mobile. La facture de prestation1000HT+200TVA est créée dans le formulaire, avec le préréglage50/50 puis les deux dates exactes. La facture est validée/comptabilisée et un virement600MAD du30/04 est saisi. Les deux écritures définitives sont VT D3421=1200/C7124=1000/C4455=200 et BQ D5141=600/C3421=600.

L'API confirme600restants au31/05, sans retard au30/05 ni le31/05, puis un jour de retard au01/06. La liste affiche31/05 au lieu du30/04 réglé ; le détail conserve les deux échéances et la première réglée après rechargement. Le rapprochement intermodule ETIC B6 est contrôlé par API au31/12/2025 : solde600, ventilé en échues600, sans anomalie de source. Une modification de l'échéancier après paiement est refusée409. Aucune écriture ne change pendant les lectures et le refus.

Les premiers essais échoués sont conservés : un sélecteur de test imbriqué incorrect puis une attente de dates à quatre chiffres alors que l'interface utilise deux chiffres. Après correction de ces sélecteurs, un test distinct reproduit le véritable défaut de la liste. Les deux parcours finaux réussissent, ainsi que les cinq tests JavaScript des dates et les tests backend/UI connexes ; les nombres et durées exacts figurent dans PREUVE_CAHIER827.json. Build Vite réussi en11,48s, avec les avertissements existants de taille de bundle et d'import xlsx statique/dynamique.

Le suivi passe à134fiches réussies,5partielles,123nonqualifiées individuellement et10bloquées par les sources. La matrice70domaines garde ses statuts ; aucune recette humaine globale, conformité réglementaire ou mise en production n'est validée automatiquement. Aucun PostgreSQL utilisateur n'a été utilisé et aucune migration n'est nécessaire.

Utilisation : Factures →Nouvelle facture →Conditions de paiement →Échéancier →50/50, puis saisir les deux dates. Après règlement partiel, vérifier le détail et la prochaine échéance affichée dans la liste. La date contractuelle d'origine reste disponible dans le document ; les indicateurs de retard suivent la somme encore due. Redémarrer le backend et charger le frontend corrigés pour bénéficier du nouveau champ de lecture.

Prochaine étape : avoir intégral avec retour de stock et remboursement, puis annulation tracée d'un règlement. RH/paie et point6 restent différés.
