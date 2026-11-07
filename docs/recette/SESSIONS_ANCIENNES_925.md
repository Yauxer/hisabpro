# Sessions de connexion — fin de transition925

Les anciennes sessions dépourvues de version de mot de passe sont désormais refusées avec **401 · Session ancienne : reconnectez-vous**. Le navigateur efface son jeton et son rôle local, puis présente la connexion. Après authentification, l’application reprend l’écran ouvert auparavant.

Une connexion normale suffit. Aucun changement de mot de passe n’est imposé, aucun compte n’est recréé et aucune donnée comptable n’est modifiée. Les sessions déjà versionnées restent utilisables tant que leur mot de passe, leur accès et leur durée de validité le permettent.

## Ce que le contrôle apporte

- Inscription, connexion et bascule de société émettent déjà une session liée au mot de passe courant.
- Après changement du mot de passe, les anciennes sessions versionnées sont invalidées dans toutes les sociétés du compte. Les jetons sans version ne permettent plus de contourner cette invalidation.
- Les droits actifs et le rôle dans chaque société continuent d’être vérifiés côté serveur. Un jeton ne remplace pas une habilitation révoquée.
- Un compte dont le mot de passe est encore stocké avec un ancien hash bcrypt peut se connecter normalement ; le hash n’est pas réécrit silencieusement par cette correction.

La version du mot de passe présente dans le jeton est une empreinte dédiée ; elle ne contient pas le mot de passe ni son hash de connexion.

## Installation et recette

Ce lot ne nécessite **aucune migration**. Déployer la même version du backend sur toutes les instances de la cible de recette avant de conclure que les anciens jetons sont refusés partout. Ne pas modifier les clés de signature ou les mots de passe pour appliquer ce changement. La configuration réelle de l’hébergement reste une vérification distincte.

Pour le cumul923–925, la conservation des PDF nécessite toujours la migration125 sur une copie isolée de l’installation. Le guide de [conservation et validation du Journal](CONSERVATION_FACTURES_923.md) reste applicable.

[Quatre cas de recettePDF](RECETTE_SESSIONS_925.pdf) · [SuiviExcel](SUIVI_SESSIONS_925.xlsx) · [Données de recette](JEU_SESSIONS_925.json).

Le cas d’une session ancienne exige un navigateur ou un banc de recette qui en possède réellement une. À défaut, le recettant le classe Bloqué et consigne le prérequis manquant ; il ne transforme pas un jeton courant pour simuler une session utilisateur réelle. Les tests automatisés préparent leurs propres anciens jetons avec une clé synthétique, exclusivement sur les laboratoires PostgreSQL éphémères à nonce. Aucun jeton ni clé de production n’est utilisé ou joint aux preuves.

Les résultats humains restent à renseigner. Ce durcissement ferme la réserve sur les sessions anciennes ; il ne constitue pas une validation globale de sécurité, de conformité ou de mise en production.
