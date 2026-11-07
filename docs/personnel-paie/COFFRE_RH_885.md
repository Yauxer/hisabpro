# Coffre RH885 — socle API et exploitation

Cette étape livre le chiffrement,la déclaration de politique et les pièces privées. L’interface et les coordonnées bancaires approuvées suivent dans887 ;ne pas les présenter comme livrées par885.

## Configuration explicite,aucune clé automatique

Le coffre reste inutilisable pour la collecte si les clés manquent ou si la société n’a pas déclaré ses références de garde,conservation et rotation/sauvegarde. Les capacités Personnel,le module actif et la protection sont également exigés. Aucun rôle ni droit supplémentaire n’est accordé automatiquement.

Une seule variable de déploiement désigne un fichier privé **hors du dépôt**,hors base et hors archives métier :`PERSONNEL_COFFRE_CLES_FICHIER`. Le fichierJSON contient `version=1`,le nom de clé `active` et le dictionnaire `cles`. Aucune clé réelle ne doit être collée dans l’interface,une issue,le journalCodex ou un ZIP.

Le chiffrement authentifié utiliseFernet de `cryptography==50.0.1`,déjà présent et désormais dépendance explicite. La portée société/salarié/pièce et le type d’objet sont dans l’enveloppe authentifiée ;une substitution entre objets est refusée. Référence technique :[documentation officielleFernet](https://cryptography.io/en/latest/fernet/). Aucune formule cryptographique spécifique n’est inventée.

SousLinux,le lecteur refuse un fichier accessible au groupe/aux autres. SousWindows,préparer des répertoiresNTFS dont lesACL n’accordent l’accès qu’au service et aux opérateurs désignés ;le modeUnix ne prouve pas cesACL. La sauvegarde des clés doit avoir ses propres droits et son propre lieu de garde. L’hébergement et la durée réelle de conservation restent des paramètres du déploiement,aucune valeur légale par défaut n’est déduite.

## Utilitaire de clés livré,non exécuté sur production

`ops/personnel_coffre_cles.py` ne se connecte à aucune base. Il exige des chemins absolus privés préparés,dans des répertoires différents pour l’actif et la sauvegarde. Il refuse l’écrasement des sauvegardes,la réutilisation d’un identifiant et les chemins du dépôt. Il n’affiche jamais les clés.

```text
python ops/personnel_coffre_cles.py initialiser --fichier <chemin-prive-actif> --identifiant k2026 --sauvegarde <chemin-prive-sauvegarde-neuf>
python ops/personnel_coffre_cles.py rotation --fichier <chemin-prive-actif> --identifiant k2027 --sauvegarde <autre-sauvegarde-neuve>
```

La sauvegarde complète est créée **avant activation** ;la rotation remplace atomiquement le fichier actif et conserve les clés anciennes. Les nouvelles pièces utilisent la clé active,les anciennes continuent d’utiliser leur clé d’origine. Il s’agit d’une rotation pour les nouvelles écritures ;elle ne réchiffre pas les objets historiques et n’est pas une procédure de révocation après compromission. Ne jamais retirer une clé encore requise par des données ou sauvegardes. Un verrou `.lock` protège les opérations concurrentes ;après interruption,vérifier l’absence d’opération active avant toute intervention sur ce verrou.

## Migration et API

Déployer le code885,puis appliquer111 avec le rôle migrateur après105–110. Elle ajoute les politiques et pièces append-only,leurs clés étrangères,contrôles et droits runtime ;aucune donnée métier n’est créée. Les anciennes migrations restent intactes. Les références de politique sont des déclarations humaines,auditées avec l’administrateur ;elles ne certifient pas un contrôle réel des procédures.

-`GET /api/employes/personnel/coffre` :état minimal ;références complètes réservées à l’administrateur.
-`POST .../coffre/politique` :administrateur uniquement,références de garde des clés/conservation/rotation-sauvegarde,motif et confirmation explicite `DECLARER_POLITIQUE_COFFRE_RH`.
-`POST .../coffre/{salarié}/pieces?categorie=contrat|banque|autre` :corps binaire brut,borné à4Mio en mémoire,sans spool multipart en clair. PDF,PNG,JPEG détectés par signature ;aucun nom original conservé.
-`GET .../coffre/{salarié}/pieces` :métadonnées autorisées,sans chiffré ni nom personnel.
-`GET .../coffre/{salarié}/pieces/{pièce}` :téléchargement privé avec `no-store`,`attachment`,`nosniff` et événement d’audit. Dépôt ≠ contenu validé ;aucune analyse antivirus n’est revendiquée.

La collecte exige identité,identifiants sensibles et proposer. La consultation exige identité et identifiants sensibles. La révocation,le rôle local et le changement de société continuent d’être vérifiés côté serveur. Le profil Personnel seul peut déposer/lire sous capacités,mais ne peut déclarer la politique ni accéder aux autres modules.

Les fichiers sont chiffrés dansPostgreSQL avant persistance ;les clés ne sont pas stockées dans ces tables. Une clé absente produit503,une intégrité/portée incorrecte409,un type refusé400 et une pièce vide/trop grande413. Aucun contenu privé n’est renvoyé dans ces erreurs. Aucune URL publique ni suppression silencieuse n’est ajoutée. La politique d’effacement/purge de fin de conservation reste à traiter de manière contrôlée ;aucune purge automatique n’est inventée.

## Vérification réellement exécutée

45cas réussis :29unitaires/source/outillage et16API/SQLPGnatifsisolés. Ils couvrent chiffrement aléatoire,portée,corruption,perte/récupération des clés,rotation de la clé active,sauvegardes atomiques,configuration explicite,droits,profils,taille/type,isolation,immutabilité etabsence d’écriture comptable. 111 a été rejouée deux fois sans changer les tables antérieures. NeufPython compilés ;frontend inchangé,aucun nouveau build885 annoncé.

Un premier lancement a produit16réussites et2erreurs du harnaisWindows :le nom automatique du paramètre de4Mio dépassait la limite d’une variable d’environnement. Des identifiants de tests courts ont corrigé le harnais ;l’erreur n’était pas un succès du test de taille. La campagne suivante18cas puis la sélection finale45cas ont réellement tourné. Le XML initial publié est expurgé du dump d’environnement et du nom géant ;les compteurs d’erreur sont conservés,le brut privé n’est pas livré.

La récupération testée ici concerne les clés et les objets chiffrés de la base isolée ;elle ne remplace pas une restauration complète duPostgreSQL utilisateur. Aucun serveur réel,.env utilisateur,clé réelle ou procédure de production n’a été utilisé. LesACLWindows,l’installation cible,la politique réelle et la recette humaine restent à vérifier. Voir `Test/PREUVE_PERSONNEL_PAIE_885.json` pour les campagnes et identifiants exacts.
