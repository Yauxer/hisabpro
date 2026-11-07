# Consulter une préparation de balances dans l’application

Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
ouvrir une version de **Préparations conservées**, puis cliquer
**Consulter le bilan et les comptes sources**.

- **Côté du bilan** permet de consulter l’actif ou le passif. L’actif montre le
  brut N, les amortissements/provisions N, le net N et le net N-1 disponible.
  Les montants proviennent de la même présentation serveur que les exports677.
- Les lignes **Pour mémoire** détaillent les rubriques, notamment les
  immobilisations. Elles ne sont pas additionnées une deuxième fois. Une
  ventilation d’amortissement non déterminable reste **Indisponible**.
- **Balance source** sélectionne N ou N-1. **Rechercher un compte source**
  filtre par tout ou partie du numéro. Les comptes sont présentés par pages
  de 50 ; le filtre ou le changement N/N-1 ramène à la première page.
- Sur mobile, faire défiler horizontalement le seul tableau du bilan pour
  lire les colonnes de droite. Les commandes et comptes sources restent dans
  la largeur de la page.
- En cas de panne, l’erreur remplace le détail ; **Réessayer le détail** reprend
  la consultation sans F5. Le changement de version ou la fermeture écarte
  une réponse ancienne encore en cours de chargement.

Les comptes sources sont les données normalisées conservées à l’import.
Leur intitulé n’a pas été conservé par l’import historique ; aucun intitulé
actuel n’est donc présenté comme s’il avait été conservé avec cette version.
Une source absente est signalée, et non remplacée par une balance nulle.

Le rôle Lecture peut consulter ce détail. Les droits sont vérifiés sur le
serveur et limités à la société active. Une préparation dont l’empreinte ne
recoupe plus le contenu est refusée, y compris en consultation détaillée.

Cette consultation ne modifie aucune écriture, aucun compte, aucune version
ou archive fiscale. Le dossier fiscal autonome complet reste partiel ; les
résultats humains de recette restent à renseigner.

Voir aussi les [exports détaillés677](LIASSE_BALANCES_DETAIL_677.md).
