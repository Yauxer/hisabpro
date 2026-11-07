# Personnel seul — confinement et utilisation (881)

Cette livraison complète879 : le profil **Personnel seul** est désormais disponible. Les restrictions de879 au pilote admin/comptable restent historiques ; elles ne doivent plus conduire à donner un rôle comptable à un gestionnaire RH.

## Activation sur une copie

1. Installer105–108 selon les guides précédents. Déployer **le code881 sur toutes les instances backend**, puis la migration109 avec le rôle migrateur. Aucun compte ne reçoit ce rôle pendant la migration. Ne pas attribuer `personnel` tant qu’une ancienne instance capable de traiter ce rôle comme une simple lecture générale reste en service.
2. Avec un administrateur existant, ouvrir **Paramètres → Utilisateurs**, créer un compte ou choisir **Personnel seul** dans sa liste de rôles. Pour un compte d’une autre société, l’invitation propose également ce rôle local.
3. Accorder les capacités utiles dans **Personnel & Paie → Habilitations**. Le profil global ne donne aucun droit de consultation, de préparation ou d’approbation implicitement. Prévoir deux personnes distinctes pour les décisions sensibles.
4. Activer la protection si ce n’est pas déjà fait. Se connecter avec le nouveau compte : arrivée directe au Personnel, sans tableau de bord financier, journal, factures, paramètres ou espace historique.
5. Suivre les cas du [cahier879](CAHIER_RECETTE_PERSONNEL_HISABPRO_879.pdf) et les huit cas supplémentaires du [classeur881](SUIVI_RECETTE_PERSONNEL_881.xlsx). Les étapes d’administration s’effectuent avec le compte administrateur, jamais avec le gestionnaire Personnel.

Les mutations demeurent conditionnées au rôle local actuel, au module actif, à la protection, aux capacités et aux contrôles d’indépendance/révision. Le changement de rôle, la désactivation d’un accès et la révocation des capacités sont relus côté serveur sans attendre l’expiration du JWT. Une société où le même compte possède un autre rôle conserve ses propres droits ; changer de société ne transporte pas les capacités RH de la précédente.

## Limites techniques de l’accès

Le serveur applique une liste **fermée** de chemins et méthodes après résolution du rôle principal ou invité en base. Les nouvelles routes sont refusées par défaut à ce profil. Les seuls accès communs sont le profil personnel, son changement de mot de passe, la liste de ses sociétés et leur sélection. Le contexte RH n’expose que l’identifiant/nom de la société et l’activation du module ; ni RIB société ni paramètres comptables ne sont nécessaires.

La navigation dédiée ne monte pas les fournisseurs de données du journal, des factures, du plan comptable ou des exercices. Falsifier le rôle local ne donne aucun droit serveur. Les rôles administrateur, comptable et lecture conservent leurs règles précédentes.

La restriction est applicative ; elle ne remplace pas les droits du rôle PostgreSQL runtime, ni la protection du compte migrateur. Le rôle `personnel` ne doit pas être utilisé comme accès SQL direct à la base.

## Migration, retour arrière et production

109 élargit deux contraintes de rôles, sans modifier de compte, de capacité ou de donnée métier. Elle est transactionnelle et rejouable. Les migrations antérieures restent inchangées. Une installation partielle doit être corrigée avant attribution du profil.

**Ne pas revenir à un backend antérieur à881 en laissant des comptes `personnel` actifs** : les anciennes versions ne connaissent pas ce confinement. En cas de retour arrière, garder le code de garde, ou désactiver explicitement les accès concernés sous contrôle administratif avant le retour. Ne jamais convertir automatiquement ces comptes en comptable ou en lecture générale.

Aucun déploiement ni migration n’a été exécuté sur la base utilisateur. Le test de conservation après deux applications de109 a été fait sur PostgreSQL natif isolé. Recette humaine et production restent à valider sur copie.

## Reste du Lot1

Le profil exclusivement Personnel est traité par881. Restent la collecte sécurisée des coordonnées bancaires/pièces et la gestion des clés/conservation (décisionD05 du Lot0), ainsi que la déclaration des régimes sociaux utiles avant usage paie. Aucune clé réelle ni durée de conservation n’a été inventée. Les références de contrôle restent des attestations à vérifier humainement. Les lots de calcul et paiement de paie restent distincts.
