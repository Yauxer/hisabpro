# Factures — filtres et liste vide

Complément767 du24octobre2026. Installer le différentiel dans le dépôt existant et reconstruire le frontend ; aucune migration SQL. Les règles et les calculs restent ceux du produit existant.

Dans Facturation → Factures :

1. Saisir un numéro ou un tiers dans la recherche, puis choisir type, statut et dates si nécessaire.
2. La croix Effacer la recherche efface uniquement le texte et replace le curseur dans ce champ.
3. Réinitialiser les filtres efface en une fois recherche, type, statut et dates. L’exercice reste sélectionné ; les indicateurs retrouvent leur période complète, selon les règles habituelles.
4. Si aucun résultat ne correspond, le message précise les critères possibles et le bouton Afficher toutes les factures de cet exercice donne le même retour à la liste complète. Le message est lisible sans déplacer horizontalement le tableau.
5. Si l’exercice ne contient aucune facture, le message le précise. Un utilisateur autorisé peut ouvrir Créer une première facture ; en consultation seule, cette action n’est pas proposée. Ouvrir le formulaire ne crée pas de facture tant qu’il n’est pas enregistré.

Les boutons de type/statut indiquent leur sélection aux technologies d’assistance ; le champ et sa croix sont nommés, et les contrôles peuvent être utilisés au clavier. Cela ne constitue pas un audit d’accessibilité complet.

Les filtres servent àla consultation et ne modifient aucune facture. Les indicateurs conservent leur périmètre existant, basé sur la période ; la recherche/le type/le statut filtrent la liste. Une lecture en erreur ou un montant historique inconnu ne devient pas une facture absente.

[Capture mobile](recette/PREUVE_UX_FACTURES_767_MOBILE.png), [bureau](recette/PREUVE_UX_FACTURES_767_BUREAU.png), [rapport des14tests](../Test/rapport_ux_factures767.md). Contrôles automatisés réellement exécutés sur données fictives, pas sur la base utilisateur. La recette UX avec vous reste à effectuer ;RH/paie etpoint6 différés.
