# Installer et vérifier cette livraison sur une copie

Cette procédure concerne les lots897,899 et901. **Aucune migration n’a été exécutée sur la base réelle pendant cette session.** Les tests ont utilisé des PostgreSQL natifs éphémères, avec gardes de cible et données fictives.

## Préparation par le responsable technique

1. Préparer une copie isolée et restaurable de la base, avec les données de recette et une configuration d’application distincte. Identifier explicitement cette copie et le rôle utilisé ; ne pas reprendre automatiquement la connexion de l’environnement habituel.
2. Sauvegarder le code, la base et les éléments nécessaires au coffre RH selon les procédures existantes. Les fichiers et clés externes du coffre restent séparés de la seule sauvegarde SQL. Ne pas générer une nouvelle clé pour remplacer arbitrairement celle qui protège des documents existants.
3. Vérifier le socle déjà installé, notamment Personnel105–112, catalogue113, variables114 et campagnes115. Ne pas conclure à une installation complète uniquement parce qu’un fichier SQL existe ou qu’une table porte le bon nom. Les fonctions, contraintes, index et privilèges comptent aussi.
4. Utiliser le **ZIP cumulatif de cette session897–903** pour une base de code correspondant au début de session. Extraire les chemins relatifs depuis la racine du projet, pas depuis `hisabpro-backend` : les fichiers `src/...` et `hisabpro-backend/...` doivent rester à leur place. Le cumul contient les versions finales ; il n’est pas nécessaire de réappliquer successivement tous les petits ZIPs sur ce même état.

## Migrations sur la copie seulement

Le responsable technique exécute les SQL avec un outil configuré explicitement sur la copie et arrêt à la première erreur, avec un rôle autorisé à gérer le schéma. Ordre :

| Migration | Apport | Contrôle après installation |
|---|---|---|
| `hisabpro-backend/116_paie_referentiel_social.sql` | Branches/régimes et versions, qualification et double couverture | Tables vides sans taux préchargé ; accès au référentiel04 |
| `hisabpro-backend/117_paie_simulations_sociales.sql` | Snapshots sociaux, index d’intégrité et lien société du brut | Formulaire Simulations sociales, source du brut chargée |
| `hisabpro-backend/118_paie_controles_ir_annuels.sql` | Contrôles annuels IR2026 conservés | Écran05, sources et création d’un contrôle fictif |

Les migrations sont transactionnelles et rejouables ; elles n’effacent pas les données antérieures. Ne modifier aucune ancienne migration pour faire passer une installation. Si un prérequis manque, lire l’erreur et installer le prérequis sur la copie. Conserver le compte rendu et vérifier l’état avant de relancer.

Les grants livrés visent le rôle applicatif `hisabpro` lorsqu’il existe. Un déploiement utilisant un autre rôle doit faire vérifier ses privilèges équivalents par l’administrateur ; ne pas utiliser automatiquement un superutilisateur pour masquer une erreur de permissions. Aucune habilitation Personnel ou réglementaire n’est attribuée implicitement.

## Démarrage et recette

Redémarrer le backend de la copie et reconstruire/démarrer son frontend avec les dépendances du projet. Garder les deux versions de code cohérentes. Une réponse503 indiquant une migration requise est un diagnostic d’installation ; elle ne justifie pas de modifier des données comptables.

Activer le module et le mode protégé Personnel, puis attribuer explicitement les habilitations nécessaires à des comptes de recette séparés. Suivre le [mode d’emploi et les cahiers](MODE_EMPLOI_PERSONNEL_PAIE.md) : référentiel897, calcul social899 puis contrôle annuel901. Tous les statuts humains sont initialement **Non testé**. Les taux et montants des jeux sont fictifs.

Le vérificateur documentaire peut être lancé depuis la racine avec l’environnement Python du projet :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test\verifier_cahiers_paie903.py --vierge
```

Cette commande lit les PDF, classeurs et liens locaux ; elle n’utilise ni réseau, ni base, ni `.env`, et ne modifie pas les classeurs. Après saisie de résultats humains, omettre `--vierge` pour accepter les statuts renseignés. Elle ne vérifie pas le comportement de l’application à la place du recettant.

## Avant toute production

Les nouvelles fonctions sont des simulations et contrôles préparatoires. La qualification réglementaire, les cas complexes, l’assiette fiscale intégrée, les retenues mensuelles, le net, les bulletins, paiements et écritures de paie restent à poursuivre. Le déploiement réel, la restauration d’exploitation, les habilitations et la recette utilisateur nécessitent leurs validations propres. Aucun outil de cette session ne les a validés automatiquement.
