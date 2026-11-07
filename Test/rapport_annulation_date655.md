# Annulation individuelle datée — lot 655

Le cahier RDO-008 demandait une date et un motif déjà acceptés par l’API,
alors que l’écran envoyait uniquement la date du jour après une confirmation.
Le formulaire de Règlements expose maintenant ces deux champs, dans le style
des autres fenêtres commerciales. Le motif reste facultatif ; aucune règle
comptable nouvelle ni migration n’est ajoutée.

Une requête en cours verrouille la soumission et la fermeture. Les réponses
ne rafraîchissent le contexte que si société/jeton, exercice et cycle restent
ceux du formulaire. Une erreur est affichée sans perdre les valeurs saisies.
Après succès, règlements et factures sont rechargés automatiquement.

## Vérifications réellement exécutées

9tests Edge/API/PostgreSQL isole reussis123.11s, puis2cibles apres correction couleur34.53s; zero echec/erreur/ignore. Builds4.97s et6.20s,exit0. Compilation des3tests Python livres. Campagnes recouvrantes non additionnees.

Les deux nouveaux parcours utilisent un vrai Edge en 1440 et 390 pixels,
une vraie API et PostgreSQL102 jetable sous LOGIN applicatif. Achat12000,
virement5250, capture750 : date future refusée422, données strictement
inchangées, puis date passée choisie et motif présents sur les deux
contrepassations équilibrées5250/750. Les trois écritures d’origine validées
restent identiques ; la facture retrouve un solde12000 et le statut se
rafraîchit sans F5. Les contrepassations restent brouillons à valider.
Captures du formulaire inspectées en ordinateur/mobile ; les pages3 et11
du PDF653 courant ont aussi été rendues et relues après sa correction finale.

Les sept autres cas couvrent notamment captures vente/achat, lettrage puis
délettrage, édition des règlements, consultation seule et absence de migration.
Les scénarios existants ont uniquement été adaptés au nouveau bouton de
confirmation. Les campagnes recouvrantes ne s’additionnent pas.

## Limites

La campagne ne qualifie pas toutes les courses possibles de changement de
contexte. Aucune base réelle, donnée comptable réelle ou ancienne migration
n’a été touchée. Annulation collective inchangée. Recette utilisateur,
installation sur PostgreSQL utilisateur et affichage dans son navigateur
restent à effectuer. RH/paie et point6 humain restent différés.

L’interruption technique de la revue automatique a empêché une lecture de
fichiers ; les tests ont terminé et leurs logs, code0 et XML ont été relus
à la reprise. Ce rejet ne concernait pas la sécurité de la modification.

[Mode d’emploi](../docs/ANNULATION_REGLEMENT_655.md).
