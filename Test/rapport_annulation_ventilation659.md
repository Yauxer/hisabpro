# Ventilation entière : date et motif — lot659

L’annulation collective imposait encore la date du jour dans une confirmation
native, alors que l’API atomique acceptait déjà une date et un motif. Le formulaire
commun du lot655 est maintenant utilisé après relecture du lot complet.
Il affiche le total, le nombre et chaque numéro de règlement concerné.

L’utilisateur choisit la date et un motif facultatif, puis confirme explicitement.
Les erreurs restent visibles sans perdre les champs. Les écritures d’origine
restent conservées et les contrepassations sont à valider dans le Journal.
Les listes de règlements et de factures se rafraîchissent après succès.
Les contrôles, verrous, transactions et droits du serveur ne sont pas modifiés.

## Résultats réellement exécutés

67tests reussis en227,03s, zero echec/erreur/ignore : API PostgreSQL nonce,Edge vente/achat et1365/390,refus/rollback/concurrence/permissions/contextes/lettrage et annulations individuelles. Build Vite reussi5,06s. Compilation Python des tests modifies. Ces campagnes recouvrent les precedentes et ne sont pas additionnees.

Les quatre parcours vente/achat en 1365/390 pixels passent par un vrai Edge,
une vraie API et PostgreSQL jetable. Deux paiements de120 donnent un lot240.
Une date future provoque422 et la photographie des données reste identique.
La date choisie, différente de celle du jour, et le motif sont ensuite présents
sur les deux contrepassations. Les originaux préalablement validés restent
identiques ; les statuts se rafraîchissent puis sont conservés après rechargement.
Le formulaire affiche les deux numéros et le montant total avant le POST.

Les tests connexes vérifient l’annulation API, le rollback intégral, l’idempotence,
la concurrence, les permissions, les paiements/lettrages et les annulations
individuelles. Les réponses tardives de preview ne doivent ouvrir aucune
confirmation ni envoyer de POST après changement d’exercice ou de jeton.

## Sources et limites

Aucun backend, calcul fiscal ou SQL modifié. Aucun PostgreSQL réel utilisé.
La recette utilisateur et le déploiement restent distincts ; RH/paie et point6
humain différés. Les protections côté serveur restent l’autorité en cas de
modification du lot entre sa prévisualisation et la confirmation.

La vérification ciblée du référentiel09B n’a pas obtenu de catalogue2026.
La recherche officielle retrouve le
[cahier EDI SIMPL-IS historique](https://www.finances.gov.ma/Publication/dgi/2010/9370_cahierdescharges.pdf),
déjà analysé au lot265. Son passage indexé décrit des modèles et périodes de
validité ; sa présence ne prouve pas le schéma applicable aujourd’hui.
Pas de nouveau code DGI ou export EDI déduit ; T1…T25 restent des repères internes.

[Mode d’emploi actualisé](../docs/ANNULATION_REGLEMENT_655.md).
