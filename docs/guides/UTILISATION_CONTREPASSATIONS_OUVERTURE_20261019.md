# Suivre les contrepassations d’ouverture

Dans **Comptabilité → Clôture**, sélectionner l’exercice de destination,
par exemple 2026 pour une CCA/PCA de 2025. Le bloc **Contrepassations d’ouverture**
présente les écritures déjà créées et liées aux ajustements d’inventaire.
Il reste consultable lorsque l’exercice source est clôturé.

Chaque fiche affiche la référence, la date et le journal de la contrepassation,
sa source, les débits/crédits et son statut réel. Le calendrier est celui
des pièces : sur un exercice décalé, l’ouverture peut être le 1er juillet.
Le compteur distingue **À valider** et **Validée**. Une source en brouillon
ou un déséquilibre reste signalé, sans correction automatique.

1. Comparer la source et les justificatifs conservés avec la pièce d’ouverture.
2. Cliquer **Ouvrir le Journal des contrepassations** ; retrouver la référence
   affichée et contrôler ses lignes. Le bouton ouvre le Journal de l’exercice
   sélectionné, sans filtrer automatiquement une seule pièce.
3. Utiliser la validation ordinaire du Journal si les droits le permettent.
4. Revenir à Clôture : le statut est rechargé. Cliquer **Actualiser les
   contrepassations** si une autre session a modifié le statut ou la source.
5. Au-delà de 20 pièces, utiliser **Suivantes** / **Précédentes**.

La consultation est accessible au rôle Lecture. Le bloc ne crée ni ne valide
d’écriture et n’impose aucune reprise de provision. Il recense les liens
techniques existants des ajustements, pas toutes les écritures manuelles
portant un libellé semblable. Une liste vide n’est donc pas une attestation
d’absence de régularisations à effectuer.

Recette suggérée, sur base isolée : créer une CCA 2025 avec contrepassation 2026,
vérifier le statut À valider dans 2026, valider au Journal puis constater
Validée. Vérifier qu’une autre société ne voit pas cette pièce et qu’un
lecteur ne peut pas la valider. Aucun résultat humain n’est prérempli ici.
