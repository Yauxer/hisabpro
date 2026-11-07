# Comptabilité et facturation — état après923–929

Le correctif929 ferme une incohérence d’interface :les lecteurs voyaient des commandes interdites,et les comptables des corrections historiques réservées à administrateur. Les commandes affichées suivent maintenant les droits API déjà existants ;les consultations restent accessibles. Aucune règle métier ou fiscale ni donnée réelle n’a changé.

| État | Conclusion |
|---|---|
| Développement929 | Terminé pour les droits du registre,du plan et du diagnostic |
| Tests automatisés929 | Validés dans le laboratoire :69cas et build réel |
| Recette utilisateur | À effectuer :trois nouveaux cas929,six927 et autres cas antérieurs non renseignés |
| Prêt pour production | Non déclaré ;réserves métier et configuration cible restent ouvertes |

Les lots923–927 sont conservés :copie PDF interne figée,retour Journal sans alerte tardive bloquante,sessions liées au mot de passe,aperçu de sortie avant écriture. Le jeu927 précise le choix explicite4411 ;aucune contrepartie d’acquisition existante n’est changée. Les trois rôles conservent les restrictions du serveur ;l’administrateur ne contourne pas les contrôles d’exercice,période ou justificatifs.

La prochaine étape reste la recette pilote sur une copie restaurable de la cible avec le partenaire. Qualifier convention de prorata et TVA/régularisation de cession,délais contractuels,annexes et justificatifs/ventilations historiques FEC–ETIC. Les parties non justifiées restent visibles ;rien n’est fabriqué pour solder un contrôle. Vérifier sous responsabilité de l’exploitant les versions homogènes,rôle PostgreSQL limité,HTTPS/secrets,sauvegarde/restauration et fonctionnement navigateur de cette cible avant production. Aucune opération sur la base habituelle dans cette session.

Paie921 et les formats officiels de dépôt restent distincts et inchangés. Ces essais n’approuvent ni une paie définitive,ni un dépôt,ni un archivage légal certifié.

[Résultats929](RESULTATS_MVP_929.md) · [Guide](DROITS_IMMOBILISATIONS_929.md) · [Suivi](SUIVI_AUTOMATISATION_CAHIER_929.xlsx) · [État antérieur927](DECISION_FACTURATION_COMPTABILITE_927.md).
