# HisabPro — plan comptable, journaux et sélection de compte

Les fiches ADM004 et SEC006 sont exécutées dans Edge sur ordinateur et mobile, avec API réelle et PostgreSQL natif éphémère. Une société fictive et un témoin BQ définitif de100MAD sont utilisés. Le contrôle compare les comptes disponibles aux numéros de toutes les lignes du jeu de recette existant ;il ne déclare pas le référentiel officiellement certifié ou exhaustif au sens réglementaire.

Tous les comptes nécessaires au scénario sont actifs. Les subdivisions51111,51112 et51132 sont recherchées dans la page Plan de comptes et leurs libellés affichés sont comparés à la lectureAPI. La suppression du compte5141 est refusée409 et ne change ni le plan ni le témoin comptable.

Le formulaire Nouvelle écriture propose AC,VT,AV,BQ,AE,OD,AM etAN. Le journalCL est une exception voulue :le modèle le réserve à la clôture,le sélecteur manuel ne le propose pas et le schéma d'entrée l'exclut. Une requête directe de création manuelleCL est effectivement refusée422, sans nouvelle écriture. Ce test conserve la règle existante au lieu d'ajouterCL aux choix manuels pour satisfaire une attente incorrecte.

Deux ouvertures successives du formulaire vérifient la recherche puis la sélection de3421 et2355. Les libellés Clients et Matériel informatique apparaissent automatiquement. Aucune nouvelle requête GET du plan n'est déclenchée pendant les quatre sélections ;les durées observées sont conservées en preuve sans devenir un seuil de performance de production. Les formulaires sont annulés et le journal ainsi que le plan restent identiques.

Les premières exécutions échouées sont conservées. Les attentes du banc ont été corrigées après inspection :CL ne doit pas figurer dans les choix ni dans le schéma de saisie manuelle,et le sélecteur Playwright has doit rester relatif à l'élément recherché. Les suggestions étaient visibles dans les traces ;aucun défaut produit de chargement n'est affirmé à partir de ces erreurs de test.

Résultats finaux :deux parcours connectés réussis et cinq tests connexes du cache et des droits réussis. Ces derniers comprennent des contrôles de source et du cacheJavaScript,ils ne sont pas présentés comme cinq tests PostgreSQL. Aucun fichier du produit ni migration n'est modifié ;les462empreintes de la candidate849 restent identiques et aucun nouveau build n'est revendiqué.

Le suivi atteint174fiches automatiquement réussies,5partielles,83nonqualifiées individuellement et10bloquées à la source. Les70statuts fonctionnels globaux restent inchangés. Prochaine étape :exportPDF avec la raison sociale littérale Atlas <SARL> & associés et logo fictif, puis chargement réseau et contexte multi-société. Recette humaine,réserves comptables et production restent à valider. Aucun PostgreSQL utilisateur ni donnée comptable réelle touché.
