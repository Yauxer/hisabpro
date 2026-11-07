# Comptabilité et facturation — état après931/933

Le code du lot931 est conservé :lectures indisponibles distinctes de zéro,reprise sans F5,renommage après dotation avec verrou du plan préservé et indicateurs mobiles lisibles. Le lot933 complète la vérification du scénario de préparation fiscale depuis balances externes et rattache ses14fiches à des preuves exécutées. Il ne développe pas un nouveau moteur ou dépôt fiscal.

| État | Conclusion |
|---|---|
| Développement933 | Aucun changement produit nécessaire pour ces cas |
| Tests automatisés933 | Finale13cas réussis,correspondance explicite14fiches755 |
| Recette utilisateur | À effectuer ;14cas humains755 et anciens résultats non prévalidés |
| Prêt pour production | Non déclaré ;configuration cible et réserves métier restent ouvertes |

Les préparations755 sont internes :solde3650proposé selon le jeu fictif,CSS séparée,aucun paiement,liquidation confirmée,dépôt EDI ou archivage légal certifié. Les contrôles négatifs11–13 sont exécutés par API ;la méthode est explicite dans le suivi et ne remplace pas leurs gestes humains dans les formulaires.

Prochaine étape technique :rattacher de la même façon les8fiches de préparation des rémunérations de tiers759,avec vérifications réelles et limites explicites. En parallèle,la recette pilote sur copie cible doit qualifier les sorties,la convention/TVA,délais contractuels et justificatifs historiques FEC–ETIC. Avant production,contrôler versions homogènes,rôle PostgreSQL limité,HTTPS/secrets et sauvegarde/restauration de la cible. Aucune opération sur le dossier réel dans cette session. Paie921 et formats officiels restent distincts et inchangés.

[Résultats933](RESULTATS_MVP_933.md) · [Documents humains755](QUALIFICATION_FISCALE_933.md) · [Suivi](SUIVI_AUTOMATISATION_CAHIER_933.xlsx) · [Résultats931](RESULTATS_MVP_931.md).
