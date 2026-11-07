# Immobilisations : commandes selon le rôle

Le registre, les plans d’amortissement et le diagnostic de réconciliation restent consultables. Les commandes de l’écran suivent désormais les restrictions déjà imposées par l’API.

| Rôle | Comptabilité courante du registre | Réconciliation historique |
|---|---|---|
| Consultation seule | Création et dotations annuelles désactivées ; modification, paiement, sortie, encaissement, archivage et génération individuelle absents | Diagnostic lisible, champs de correction désactivés, commandes de correction absentes |
| Comptable | Commandes courantes conservées selon l’état du bien | Diagnostic lisible ; corrections réservées à administrateur |
| Administrateur | Commandes courantes conservées selon l’état du bien | Commandes de correction présentes, soumises au diagnostic et aux contrôles métier |

Pour consulter un plan, cliquer sur la ligne du bien. Pour lire les anomalies historiques, utiliser **Réconciliation historique**, puis **Fermer**. Ces consultations ne créent pas d’écriture. L’audit HTTP peut enregistrer la consultation. L’administrateur doit toujours confirmer les contreparties des reprises, contrôler les brouillons dans le Journal et respecter les exercices verrouillés.

Le correctif porte sur l’interface ; les restrictions API existaient déjà et restent appliquées. Il ne crée pas de nouveau rôle, ne donne pas des droits supplémentaires et ne change aucun calcul ou traitement fiscal. Il évite de proposer une action dont le serveur refuserait l’exécution.

Le jeu de recette927 est également précisé : choisir explicitement **4411** pour la dette fournisseur si l’on veut retrouver l’écriture d’acquisition annoncée. Le formulaire propose **4481** par défaut. Le code du formulaire et les acquisitions existantes restent inchangés ; aucune contrepartie n’est remplacée automatiquement.

[Trois cas humains PDF](RECETTE_DROITS_IMMOBILISATIONS_929.pdf) · [Excel à remplir](SUIVI_DROITS_IMMOBILISATIONS_929.xlsx) · [Données exactes](JEU_DROITS_IMMOBILISATIONS_929.json) · [Aperçu de sortie927](APERCU_SORTIES_IMMOBILISATIONS_927.md). Utiliser une copie de recette restaurable. Les tests automatiques et les résultats humains sont distincts ; convention et TVA de cession restent à qualifier.
