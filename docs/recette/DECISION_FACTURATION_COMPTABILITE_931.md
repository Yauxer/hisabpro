# Comptabilité et facturation — état après923–931

Le lot931 corrige les lectures trompeuses du registre et du plan :une panne ne devient plus une liste vide ou un total nul ;les reprises relisent les données sans F5. Le formulaire permet un renommage après dotation en omettant les champs du plan inchangés ;un vrai changement de plan reste refusé par le backend. Sur mobile,les quatre indicateurs et les commandes restent dans la largeur.

| État | Conclusion |
|---|---|
| Développement931 | Terminé pour les défauts et reprises décrits |
| Tests automatisés931 | Validés dans le laboratoire :34cas et build réel |
| Recette utilisateur | À effectuer :quatre nouveaux cas931 et les cas antérieurs non renseignés |
| Prêt pour production | Non déclaré ;configuration cible et réserves métier ouvertes |

Les droits929 et les lots923–927 restent acquis dans leurs périmètres. Aucune modification de backend,migration,règle fiscale ou donnée réelle. Les injections de panne dans le navigateur éprouvent l’interface ;elles ne prouvent pas la disponibilité opérationnelle de la future cible. Aucun résultat humain n’est remplacé par un succès automatique.

Prochaine étape utile :recette pilote sur copie restaurable avec le partenaire,notamment les droits,sorties,renommages et reprises de lecture. Qualifier avec sources et pièces la convention de prorata,la TVA/régularisation de cession,les délais contractuels,annexes et justificatifs/ventilations historiques FEC–ETIC. Contrôler versions homogènes,HTTPS/secrets,rôle PostgreSQL limité,sauvegarde/restauration et navigateur sur cette cible avant production. Ne pas inventer des justificatifs ni modifier des écritures définitives pour solder un contrôle.

Paie921,formats officiels de dépôt et archivage légal certifié restent distincts et inchangés. [Résultats931](RESULTATS_MVP_931.md) · [Guide](LECTURE_IMMOBILISATIONS_931.md) · [Suivi](SUIVI_AUTOMATISATION_CAHIER_931.xlsx) · [État antérieur929](DECISION_FACTURATION_COMPTABILITE_929.md).
