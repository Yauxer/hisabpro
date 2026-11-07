# MODE D’EMPLOI ET RECETTE — CHANGEMENT DE SESSION ET RÉPONSES TARDIVES

Version 1 du 22 octobre 2026. Complément745 aux connexions739.

## Ce qui change

Une lecture ou un export demandé avec un ancien jeton ne doit plus restituer
son résultat après le remplacement de ce jeton. Le client vérifie le contexte
à la réception de la réponse puis après la lecture du JSON ou du fichier.
La synchronisation du rôle du profil vérifie également le jeton avant de
modifier le rôle local. Un message indique que la session a changé et que
l’ancienne réponse a été ignorée. La nouvelle session reste connectée.

Les accès serveur et les rôles ne changent pas. Une session courante refusée
reste déconnectée. Une erreur de connexion anonyme conserve le message du
serveur sans recharger la page, comme dans739. Les lectures et fichiers du
contexte courant continuent à fonctionner.

Une réponse ignorée n’annule pas une opération déjà exécutée par le serveur.
Si un enregistrement avait été envoyé avant le changement de société, revenir
dans l’ancienne société et vérifier sa présence avant de le ressaisir. Le
logiciel ne rejoue jamais automatiquement une mutation dans la nouvelle société.

## Données et préparation

Utiliser un bac isolé avec deux sociétés fictives Session A745 et Session B745.
Le même utilisateur est administrateur deA et invité en consultation seule
surB. Créer dansA une préparation fictive du petit CSV du guide741. Un export
PDF de cette préparation doit fonctionner dansA ; il reste inaccessible depuisB.
Aucune donnée comptable réelle n’est nécessaire.

Le responsable technique prépare la latence et la rétention des vraies réponses
sur le seul bac de recette. Il peut aussi retenir la fin de lecture d’un corps
JSON ou fichier, sans remplacer ses données. Le scénario automatisé vérifie le
clientHTTP réel dans Edge, avec les jetons d’un vrai basculement API. Il ne
constitue pas à lui seul une recette du sélecteur multi-société dans l’interface.

## Cas de recette humaine à effectuer

Les colonnes de résultat réel et de preuve du classeur restent vierges. Les
statuts ci-dessous restent Non testé. Si le banc de latence n’est pas disponible,
classer les cas concernés Bloqué ; ne pas simuler une panne en production.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|SES745-01|DansA, sans changement de session, consulter le profil et télécharger le PDF de sa préparation fictive.|ProfilA avec rôle Administrateur et fichierA corrects, aucune erreur de contexte ; captures et fichier.|Non testé|
|SES745-02|Responsable retient la vraie réponse de profilA ; basculer versB en Consultation, puis libérer la réponseA.|Ancienne réponse ignorée ; sessionB et rôle Consultation conservés, aucune commande Administrateur accordée dansB ; trace200 et captures.|Non testé|
|SES745-03|Demander le PDF dansA ; retenir sa réponse ou la fin de sa lecture, basculer versB puis libérer.|Aucun ancien fichier restitué par la demande tardive ; sessionB conservée et message de contexte, pas de relance automatique ; trace et capture.|Non testé|
|SES745-04|DansA, envoyer une nouvelle qualification CSS fictive puis retenir sa vraie réponse201 après création ; basculer versB et libérer ; revenir vérifierA.|Réponse ignorée dansB ; exactement une nouvelle version créée dansA, ancienne version intacte, aucun doublon ni écriture créée ; captures et trace d’un seulPOST.|Non testé|

## Vérifications et limites

Vérifier aussi la fermeture/réouverture de l’écran, la connexion refusée et les
exports normaux, avec les guides739/741/743. Le traitement des réponses ne
remplace pas les permissions serveur : une société non autorisée doit rester
refusée. Les requêtes déjà abouties doivent être vérifiées dans leur contexte
d’origine ; un message de changement de session ne prouve pas un échec serveur.

Aucun backend, migration, taux ou calcul fiscal modifié dans745. Les tests
utilisent PostgreSQL isolé, deux sociétés fictives et le client réel compilé
sous Edge. Des réponses natives200/201 sont retenues ; aucun corps métier
n’est inventé. La rétention du décodage n’en modifie ni le contenu ni le statut.
Recette humaine, Office, installation cible et production restent à vérifier.
Le timeout de connexion737 reste distinct, sans cause établie par ce correctif.
RH/paie etpoint6 humain restent différés.
