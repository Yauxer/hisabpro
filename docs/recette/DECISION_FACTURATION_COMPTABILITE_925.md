# Comptabilité et facturation — état après923–925

Trois points concrets sont fermés côté code :copie interne figée du PDF d’une facture de vente,alerte tardive bloquant la navigation après validation du Journal,et compatibilité des anciens jetons sans version de mot de passe. Les confirmations préalables et les contrôles comptables restent en place. Aucune donnée comptable réelle n’a été modifiée.

[Résultats923](RESULTATS_MVP_923.md) · [Résultats925](RESULTATS_MVP_925.md) · [Mode d’emploi copie/Journal](CONSERVATION_FACTURES_923.md) · [Sessions](SESSIONS_ANCIENNES_925.md) · [Suivi actuel](SUIVI_AUTOMATISATION_CAHIER_925.xlsx).

Le parcours principal est prêt pour recette pilote. Les automatismes n’approuvent pas la recette utilisateur ou la mise en production. Les huit cas humains923 et quatre925 restent Non testé,et les statuts humains historiques ne sont pas écrasés. Le suivi automatique par fiche reste181réussis,6partiels,76non qualifiés individuellement et9bloqués à la source ;les preuves de sécurité sont renforcées sans compter plusieurs fois les mêmes fiches.

Réserves encore applicables :convention de prorata de cession et qualification TVA d’immobilisation,délais contractuels et annexes fiscales,justificatifs/ventilations historiques FEC–ETIC,et configuration/exploitation du futur environnement. La cause d’alerte tardive reproduite est corrigée ;cela ne prouve pas l’origine de tous les anciens ralentissements. La conservation interne n’est pas un archivage légal certifié et ne remplace pas le document fournisseur original. Paie921 et formats de dépôt officiels restent distincts.

Prochaine action :installer le cumul sur une copie isolée de la cible,appliquer125 seulement si elle manque,et rejouer les parcours métier du partenaire. Vérifier déploiement homogène,versions effectivement installées,rôle PostgreSQL limité,configuration HTTPS/secrets et sauvegarde/restauration de la cible. Les anciens navigateurs sans version devront se reconnecter,les mots de passe ne changent pas. Toute décision comptable ou régularisation historique nécessite sa source ;aucune correction artificielle des soldes n’est autorisée.
