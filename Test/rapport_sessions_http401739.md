# Sessions HTTP401 — correctif739

## Modification

Seul src/services/api.js change côté produit. Le client n’efface plus la session
et ne recharge plus la page pour une connexion anonyme refusée : le message
réel du serveur s’affiche et l’email reste saisi. Pour une requête authentifiée,
le jeton courant est comparé à celui envoyé avant de déconnecter. Un refus
ancien rejette la promesse sans supprimer une nouvelle session. Une session
courante refusée reste déconnectée. JSON et téléchargement partagent la garde.
Aucune requête refusée n’est rejouée automatiquement. Aucun changement de droits,
de durée des jetons, de mot de passe côté serveur, de modèle ou de migration.
La confirmation incorrecte du mot de passe personnel reste HTTP400 préexistant.

## Tests exécutés

24 parcours connexes réussis en162,86s ;3 administration/mot de passe en43,09s ;2annuels réussis ;6ciblés en54,86s et13de reprise en48,54s. Zéro échec/erreur/ignoré dans les validations finales ;campagnes recouvrantes non additionnées. Build9,52s code0,1184SHA figés,témoins comptables/fiscaux/pièces/exports préservés,270sources backend inchangées. Avant1échec attendu44,36s ;premier banc8réussites/1échec de composition76,67s,assertion4comptes contre892,administration exécutée séparément ensuite. Guide Word/PDF5pages,Excel5feuilles,cinqcas humains Non testé.

Les6nouveauxcas utilisent Edge, une API native et PostgreSQL104 nonce : mauvais
secret puis connexion correcte sur1440/390 ; refus du jeton courant/ancien pour
JSON et téléchargement. Pour la course, le service réel est compilé dans la
page et une vraie réponse401 est retenue jusqu’au remplacement du jeton par un
jeton valide obtenu de l’API. Ce test ne qualifie pas le sélecteur multi-société.
Les données métier sont photographiées avant/après les refus.

La suite commune couvre aussi connexion avec ressource décorative retenue,
exports figés de balances et refus de rôle/isolation, vente/achat facturation,
validation/règlement/lettrage, sélecteur d’articles. Un dossier fiscal non vide,
ses pièces, ses rendus et une écriture définitive témoin sont préservés.
Administration est testée dans son banc original ; le verrou de mot de passe
relit réellement le secret courant sur PostgreSQL isolé. Les tests purs de
reprise ont leur banc unitaire distinct et ne remplacent pas PostgreSQL.
Le parcours annuel et son oracle sont séparés, preuve historique719 conservée.

La reproduction avant correction échoue réellement : message perdu après
navigation. L’échec de composition du premier banc est conservé ; aucune
assertion métier n’a été assouplie pour le rendre vert. Les30avertissements
historiques de la suite et ceux du build sur XLSX/chunks restent visibles.

## Livraison et limites

[Mode d’emploi](../docs/CONNEXION_SESSIONS_739.md),
[Word](../docs/recette/MODE_EMPLOI_SESSIONS_739.docx),
[PDF](../docs/recette/MODE_EMPLOI_SESSIONS_739.pdf),
[Excel](../docs/recette/MODE_EMPLOI_SESSIONS_739.xlsx).
Cinqcas humains restent Non testé, résultats réels/anomalies/preuves vierges.
Capture mobile et page du cahier inspectées ; Office non ouvert.

Le timeoutconnexion intermittent737 reste distinct et sous surveillance ;739
n’en établit pas la cause. Recette utilisateur/installation cible/production non
validées. Aucune base ou donnée réelle utilisée ; RH/paie etpoint6 différés.
Suite : vérification des sources fiscales officielles désormais récupérées
intégralement auprès du CRI Casablanca-Settat, puis calcul CM externe qualifié.
