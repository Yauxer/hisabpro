# HisabPro — livraison comptabilité et facturation, candidat865

Le périmètre traité est la facturation et la comptabilité intégrées. RH/paie, dépôt fiscal officiel et EDI restent différés. Le dépôt local et les preuves jointes identifient ce qui a été réellement testé ; aucune conformité officielle n'est affirmée.

## Changements concrets de cette session

- Message français lors d'une panne du transport API partagé, avec reprise par Réessayer ; les refus401/403/422 et les annulations gardent leur traitement propre.
- Factures et Cycle commercial : un chèque/effet non encaissé affiche Règlement en cours dans la liste et le détail. Le statut commercial et les écritures restent inchangés.
- Situation financière : le taux incluant les avoirs et imputations est nommé Taux de règlement commercial.
- Recettes connectées supplémentaires : unicité des dotations, refus d'une valeur résiduelle excessive, journaux/comptes disponibles et cache, caractères littéraux et logo du PDF facture, paiement partiel sansF5 ni POST doublé, changement de société avec brouillon abandonné et droits de lecture rechargés.
- Contrôle de navigation aux dimensions1366x768 et390x844 sur les principaux écrans, détails et deux formulaires. Absence de débordement global aux points mesurés ;appréciation humaine conservée.

Le produit comporte cinq fichiers ajoutés/modifiés dans cette session :client API,trois pages et une fonction partagée de présentation. Aucun fichier backend ni migration n'est modifié. Les autres fichiers livrés sont les tests, preuves, suivi et rapports. Le candidat865 contient463empreintes vérifiées.

## Statuts à distinguer

Développement du parcours principal : présent et mis à l'épreuve sur données fictives ;les variantes et réserves ci-dessous restent ouvertes. Tests automatisés : voir les campagnes réellement exécutées dans PREUVE_CAHIER867.json et les rapports853à865. Recette utilisateur : à effectuer avec le partenaire sur une copie isolée de l'environnement cible. Production : décision non validée, notamment configuration cible, migrations réellement installées, droits applicatifs, sauvegarde/restauration et réserves métier.

Le suivi comporte179fiches réussies automatiquement,6partielles,77nonqualifiées individuellement et10bloquées à la source. Les77fiches restantes attendent une qualification individuelle :une grande partie concerne Liasse seule, préparations fiscales/annexes et exploitation. Les statuts globaux des70domaines restent inchangés. Le classeur conserve les résultats humains séparés des preuves automatiques.

## Réserves précises à traiter avant les usages concernés

1. Navigation mobile : les arrêts de chargement historiques à15000ms sont conservés. Les parcours suivants réussis ne démontrent pas leur cause ;conserver les diagnostics et surveiller l'environnement cible. La géométrie contrôlée ne remplace pas la vérification visuelle des formulaires et tableaux réellement utilisés.
2. Archivage individuel de facture FAC013 :workflow non qualifié/bloqué dans la source. L'archive annuelle du livre d'inventaire est testée séparément. Décider le comportement attendu avant de revendiquer cette variante.
3. Cession d'immobilisation IMM004 :le prorata2026 produit un écart d'oracle13,33MAD ;méthode et traitement fiscal doivent être validés par le responsable comptable avant cet usage. Acquisition et dotation du cycle annuel sont contrôlées séparément.
4. Délais de paiement FAC017 :suivi/export opérationnels testés ;qualification fiscale et justificatifs contractuels restent partiels. Aucun calcul d'amende ni dépôt officiel validé.
5. Données historiques FEC/ETIC :les justificatifs et ventilations manquants restent visibles,notamment B6/B13. Une réparation éventuelle exige une source fiable et une trace ;aucune date ou donnée comptable ne sera inventée.
6. Sessions historiques :les anciens JWT sans version conservent leur durée de vie initiale. Prévoir une reconnexion générale lors de la préparation de production. Les jetons versionnés du changement de mot de passe sont testés séparément.

## Prochaine action concrète

Rejouer le cahier avec le partenaire sur une copie isolée de l'environnement cible et décider les réserves applicables à ses opérations. Commencer par société/exercice/tiers/articles,chaîne devis→commande→livraison→facture,validation,règlement partiel/complet,lettrage,puis balance/grand livre,bilan/CPC,immobilisations,clôture et à-nouveaux. Utiliser le jeu exact docs/recette/jeu_donnees_recette.json et le classeur867 ;renseigner résultat réel,anomalies et preuves sans préremplir de réussite humaine.

La préparation de production doit vérifier sur cette copie les migrations effectivement installées,le rôle PostgreSQL limité,les origines frontend,HTTPS et secrets,la conservation des justificatifs et logos,et une restauration froide vers une cible distincte. Les tests locaux isolés ne peuvent pas établir l'état de ce futur environnement. Aucune action sur la base réelle n'est autorisée dans cette session.


Campagnes867 exécutées :2parcours annuels265,84s et1restauration froide69,37s réussis ;83tables/8fichiers et463sources conservées. Prochaine vérification automatisée ciblée :NEG009,récupération ETIC des références02/002,avant recette partenaire.
