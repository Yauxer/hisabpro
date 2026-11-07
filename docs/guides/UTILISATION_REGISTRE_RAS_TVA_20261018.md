# Consulter le registre des retenues TVA guidées

Ce registre est un document interne. Il ne constitue ni une déclaration,
ni une preuve de reversement, ni un calcul de crédit fiscal imputable.

1. Choisir la société et l'exercice dans HisabPro.
2. Ouvrir **Fiscalité → Déclaration TVA**, puis **Registre des retenues TVA**.
   Le registre reste accessible si la déclaration affiche un calcul indisponible.
   Il est également accessible dans **Comptabilité → Liasse fiscale → Retenues TVA**.
   Dans ce cockpit, utiliser les boutons à l'intérieur du registre : les boutons
   Excel/PDF de la liasse exportent les états de la liasse. Ce suivi courant
   reste distinct de l'archive immuable et des tableaux internes T1–T25.
   Le registre couvre une année civile entière. Pour un exercice décalé,
   choisir l'année dans **Année civile du registre** : les deux années
   chevauchées par l'exercice sont disponibles, avec leurs dates civiles complètes.
3. Lire séparément les cartes **Achats : retenues opérées** et
   **Ventes : retenues subies**. Ne pas additionner ces catégories pour en
   déduire un solde fiscal. Les annulations de l'année sont présentées à part.
4. Consulter les pièces, de la plus récente à la plus ancienne. Déplier une
   pièce pour retrouver sa facture, le paiement, la quote-part TTC/TVA,
   la retenue, le net payé, les références, la justification et l'OD liée.
   Une OD non validée reste signalée comme telle.
5. Utiliser les pages suivantes si nécessaire. **CSV**, **Excel** et **PDF**
   téléchargent toutes les pièces de l'année, pas seulement la page visible.
   Le logo enregistré dans les paramètres société figure dans Excel et PDF.
   Les trois formats indiquent l'empreinte SHA-256 des données du registre,
   utile pour identifier l'état consulté ; ce n'est pas une signature officielle.
6. Si une source change après l'affichage, utiliser **Actualiser**, vérifier
   les nouvelles valeurs puis relancer le téléchargement.

Pour vérifier le résultat sur un environnement de recette, créer uniquement
des captures guidées fictives selon le guide
[RAS TVA guidée](UTILISATION_RAS_TVA_GUIDEE_20261018.md). Une capture annulée
doit rester visible avec son annulation. Valider une OD puis actualiser doit
modifier son état et le sous-total validé sans créer une nouvelle capture.
Les profils lecture seule peuvent consulter et exporter sans pouvoir créer.

Le registre couvre les captures TVA guidées de la migration099. Il n'inclut
pas les captures libres ou historiques non qualifiées. Si cette migration
manque, l'écran le signale ; aucun faux total nul n'est affiché. Son installation
doit suivre la procédure d'exploitation, avec sauvegarde et contrôle préalables.
Les tests de développement n'ont pas modifié votre base réelle.

Le mois de reversement indiqué provient du calcul conservé : il n'affirme
jamais que le versement a été réalisé. La déclaration TVA complète et les
justificatifs réglementaires demandent encore une qualification distincte.
