# Comptabilité et facturation — état après923

Le parcours principal reste prêt pour recette pilote. La navigation après validation du Journal a aussi été corrigée :le succès ne déclenche plus une alerte tardive pendant le passage à un autre écran. La réserve FAC013 dispose maintenant d’un parcours de conservation interne :PDF figé,logo inclus,date/auteur/motif,empreinte et retéléchargement exact. Aucun statut commercial « archivée » ou certification légale n’est ajouté. Les factures d’achat restent hors de ce nouveau parcours.

[Résultats et preuves](RESULTATS_MVP_923.md) · [Mode d’emploi](CONSERVATION_FACTURES_923.md) · [Suivi actualisé](SUIVI_AUTOMATISATION_CAHIER_923.xlsx).

Les réserves restantes demeurent :méthode de prorata de cession et qualification TVA d’immobilisation,délais de paiement et justificatifs contractuels,données historiques FEC/ETIC incomplètes,navigation intermittente historique,sessions JWT anciennes et configuration/exploitation du futur environnement. Les cas nécessitant une pièce ou décision métier ne sont pas corrigés artificiellement.

Prochaine action technique indépendante :fermer la transition des JWT anciens sans version de mot de passe,puis rejouer connexion,bascule de société,révocation et changement de mot de passe. Les utilisateurs concernés devront se reconnecter ;aucune donnée comptable ne doit changer. Les développements paie921 restent distincts et inchangés.

Recette utilisateur et production restent à valider sur copie. Ne pas utiliser ce rapport comme preuve de conformité officielle. L’état antérieur et ses réserves sont conservés dans la [décision869](DECISION_FACTURATION_COMPTABILITE_869.md).
