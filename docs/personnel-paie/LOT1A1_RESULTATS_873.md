# Lot 1A.1 — résultats et point de reprise

27/10/2026. Sous-étape de lecture/habilitations, pas validation du module complet.

**187 cas distincts qualifiés après résolution des échecs** :81unitaires/contrôles de sources,95API-SQL-bootstrap sur PostgreSQL natif isolé,11Edge/API/PG. Le nombre distinct ne recompte pas les mêmes contrôles relancés.

| Campagne | Cas | Échecs | Erreurs | Ignorés | Durée JUnit | Code |
|---|---:|---:|---:|---:|---:|---:|
| personnel873_cible | 23 | 4 | 0 | 0 | 61.86s | 1 |
| personnel873_reprise | 23 | 0 | 0 | 0 | 55.88s | 0 |
| personnel873_edge_reproduction | 2 | 2 | 0 | 0 | 49.87s | 1 |
| personnel873_edge_details | 2 | 2 | 0 | 0 | 47.9s | 1 |
| personnel873_final | 27 | 0 | 0 | 0 | 96.11s | 0 |
| personnel873_deploiement | 3 | 0 | 0 | 0 | 54.76s | 0 |
| personnel873_connexes | 141 | 1 | 0 | 0 | 296.22s | 1 |
| personnel873_ui_historiques | 7 | 0 | 0 | 0 | 123.79s | 0 |
| personnel873_scanner | 19 | 0 | 0 | 0 | 41.47s | 0 |
| personnel873_utilisateurs | 2 | 0 | 0 | 0 | 31.85s | 0 |
| personnel873_metadonnees | 2 | 0 | 0 | 0 | 25.93s | 0 |

Les premières passes échouées sont conservées. Les4premiers échecs proviennent du contexte d’ouverture d’un client HTTP du test ;les2suivants d’un mauvais libelléCNSS dans le sélecteur. La passe edge_details reproduit ensuite le vrai détail local conservé après révocation :corrigé en vidant les formulaires lors du changement des droits. La campagne connexe contient un échec du scanner statique sur un aperçu de clôture authentifié et sans mutation ;sa classification est corrigée avec assertions et7tests PostgreSQL dédiés de l’aperçu. La clôture produit est inchangée.

La sélection finale réunit personnel873_final,deploiement,connexes,ui_historiques,scanner etutilisateurs. Pour chaque identifiant de cas,le résultat final qualifié est conservé dans la preuveJSON ;l’échec du scanner est remplacé par sa réexécution réussie,les autres140succès de la campagne connexe sont conservés sans relancer inutilement les cas non modifiés.

**Build :OK**, Vite10,07s,commande13,98s ;avertissements existants de bundle/xlsx. **Compilation :OK**,10fichiersPython ajoutés/modifiés. Deux PNG de consultation protégée aux largeurs1440/390 sont joints.

## Ce qui est démontré

- Migration105 additive,rejouée à vide puis avec activation et habilitations actives/révoquées :données et droits conservés. RuntimeLOGIN non propriétaire,protections SQL testées aussi comme propriétaire.
- Sans105 :modehistorique conservé,administration indisponible503. Installation partielle :lecture/mutation refusées503 sans altérer le dossier.
- Après activation volontaire :pas de droit implicite admin,masquage API etUI,contrôle des simulations/PDF/registres,anciennes mutations409 etrévocation effective avec le même jeton.
- Invitation supprimée/recréée sans reprise des anciens grants ;compte historique non supprimable409 mais désactivable.
- Deux délégations concurrentes donnent201/409,une seule ligne ;activation attend l’opération historique déjà engagée.
- Le rafraîchissement après révocation purge un détail ouvert,ordinateur/mobile ;dossiers etécritures inchangés.
- Non-régression des dossiers,absences,référentiels,avances,démarrage etaccès utilisateurs existants.

## Limites et installation cible

Aucune donnée réelle ni PostgreSQL utilisateur contacté. Les fixtures utilisent des clusters natifs temporaires avec nonce et ports dédiés ;python-dotenv est désactivé et la collecte utilise une DATABASE_URL sentinelle injoignable. Aucun SQLite substitué aux contrôles natifs.

Les11parcours Edge sont des tests sur API/PG réellement connectés,dont2nouveaux de protection,2du registre d’avances et7historiques. Les95cas natifs n’ajoutent pas une deuxième fois ces11parcours. Les81unitaires incluent12contrôles de sources,qui ne sont pas présentés comme des tests API.

Le schéma,les habilitations effectives etl’activation de l’environnement cible restent à valider sur copie. Sans activation,les limites du modehistorique restent présentes. La protection de cette livraison est en consultation :pas encore création contrôlée de nouveaux dossiers ni versionnement salarial. Pas de profil Personnel seul,validation financière,dépôt ouproduction validés.

## Prochaine étape précise

Lot1A.2 :extensions de dossiers,contrats/rémunérations exacts avec dates connues,demandes etévénements,historique protégé etdiagnostic matricules. Puis1A.3 :API de propositions/soumissions/approbations. Ajouter une nouvelle migration au-delà de105 ;ne pas modifier105 après installation. Ne pas démarrer les calculs de paie etles neufécrans en bloc.

Références :[guide](LOT1A1_HABILITATIONS_873.md),[preuveJSON](../../Test/PREUVE_PERSONNEL_PAIE_873.json),[candidat](../../Test/CANDIDAT_PERSONNEL_PAIE_873.json).

Contrôle complémentaire :le statut réel du module est restitué même en mode historique ;deux cas de déploiement rejoués sans nouvel identifiant de test (187casdistincts conservés).
