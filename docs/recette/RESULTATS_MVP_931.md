# Résultats — lecture et reprise des immobilisations931

La finale unique a réellement terminé avec **34tests réussis,aucun échec ni ignoré**,en584.79s (durée XML),code0 :{'Edge_API_PostgreSQL_natif_isole': 26, 'API_SQL_PostgreSQL_natif_isole': 7, 'unitaires': 1}. [Identifiants,rapports et historique](../../Test/PREUVE_MVP_931.json). Les répétitions ciblées ne sont pas ajoutées à ce total.

La reproduction initiale a6tests de droits réussis et1échec attendu :un GET interrompu était présenté comme Aucune immobilisation et quatre zéros. Les six premiers cas dédiés ont ensuite réussi. L’ajout du test après modification a révélé un refus réel du renommage après dotation :le formulaire renvoyait les champs inchangés du plan. Deux campagnes intermédiaires ont6succès/2échecs ;la première comparaison stricte ne traitait pas les Decimal sérialisés en chaînes. Ces échecs restent dans les rapports et ne sont pas qualifiés comme verts. Après correction,les8cas enrichis ont réellement réussi avant la finale.

Les pannes sont des **interruptions explicites de transport de GET dans Edge** ;aucun montant ou JSON financier n’est substitué. Après retrait du blocage,les reprises utilisent les vraies réponses HTTP de l’API sur PostgreSQL natif jetable. Lecteur et administrateur1440/390 :erreurs du registre/plan visibles,indicateurs inconnus au lieu de zéro,reprise sans F5,droits conservés et absence de mutation du Journal,des biens,du calendrier ou de cinq séquences métier. L’audit HTTP reste distinct.

Deux essais supplémentaires vérifient une vraie liste vide reçue200[] et ses zéros justifiés. Deux autres enregistrent réellement une désignation,puis interrompent la lecture de rafraîchissement :les valeurs anciennes sont masquées,la reprise relit le nouveau nom sans renvoyer le PATCH. Une tentative distincte de durée5→6 est réellement transmise et refusée409 ;la durée et toutes les écritures restent intactes. Le correctif UI omet les champs inchangés en tenant compte de la représentation numérique ;il ne supprime aucun verrou du serveur.

À390px,les quatre indicateurs et les commandes tiennent dans la largeur ;positions vérifiées et capture inspectée. Non-régression :droits929 et reconstitution administrative,aperçu927,acquisition par interface,sorties/rebut,encaissement différé,cinq annuités dégressives et deux cycles annuels d’intégrité. Ces essais ne qualifient pas toute la roadmap.

Build final214modules/5,55s,code0,avec avertissement de taille du bundle ;compilation Python des fichiers livrés et empreintes des anciennes migrations préservées. Backend et schéma inchangés,aucune base réelle utilisée. Aucune nouvelle restauration931 ;la preuve84tables925 reste antérieure et distincte.

Quatre nouveaux cas humains restent Non testé ;les anciens classeurs de recette humaine ne sont pas modifiés. Suivi par fiche inchangé181Réussi/6Partiel/76Non qualifié individuellement/9Bloqué à la source. Convention de prorata et TVA/régularisation de cession restent à qualifier ;IMM004 demeure Partiel. Paie et production non validées par ce lot.

[Guide](LECTURE_IMMOBILISATIONS_931.md) · [PDF humain](RECETTE_LECTURE_IMMOBILISATIONS_931.pdf) · [Excel humain](SUIVI_LECTURE_IMMOBILISATIONS_931.xlsx) · [Suivi global](SUIVI_AUTOMATISATION_CAHIER_931.xlsx) · [Décision](DECISION_FACTURATION_COMPTABILITE_931.md).
