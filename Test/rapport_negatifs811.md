# HisabPro — contrôles négatifs des imports de balances

Les cinq fichiers négatifs originaux du cahier ont été utilisés dans Edge réel sur ordinateur et mobile, avec PostgreSQL natif temporaire : balance_desequilibree.csv, balance_compte_inconnu.csv, balance_compte_double.csv, balance_montant_nan.csv et balance_resultat_et_gestion.csv. Chaque fichier a réellement été envoyé au contrôle de l’API et refusé (422).

Les diagnostics visibles indiquent respectivement le déséquilibre, l’absence du compte dans le plan de la société, le doublon, le montant non fini et la présence simultanée du résultat technique 119 et des classes de gestion. Le message est une chaîne lisible, sans [object Object]. Le bouton de conservation est absent après chaque refus. Dix captures des erreurs sont jointes, avec les empreintes des fichiers sources.

Après chaque tentative, le journal, le plan comptable et les préparations conservées sont comparés à leur état initial : aucune écriture, aucun compte et aucune version n’ont été créés. Les fichiers du cahier restent inchangés. Le même formulaire accepte ensuite la balance valide fournie ; la première version est conservée avec le numéro 1. Aucune archive fiscale n’est créée. Ce contrôle vérifie aussi la récupération du formulaire après une erreur.

Les deux parcours ont réussi. Cinq fiches HP-NEG-046 à 050 passent à Réussi ; le suivi est de 122 réussies, 4 partielles, 136 non qualifiées individuellement et 10 bloquées par les sources. Les réponses humaines et les 70 statuts fonctionnels restent inchangés. Aucun défaut produit n’a été rencontré dans ce lot : les fichiers de tests et les preuves sont ajoutés, sans modifier le code métier ni les migrations.

Pour reproduire : ouvrir Liasse fiscale, Importer N / N-1, puis choisir chaque fichier du dossier docs/recette/negatifs. Cliquer Contrôler et préparer, lire le diagnostic et vérifier l’absence de version nouvelle. Choisir ensuite balance_attendue_2025.csv ; l’import doit réussir. Ces fichiers sont destinés à un laboratoire de recette.

Prochaine étape : importer le relevé bancaire du cahier, rapprocher ses 17 mouvements, vérifier les frais de 60 et le solde final 287 730, puis contrôler le réimport sans doublons. B6/B13 attendent toujours des justificatifs ou une méthode, sans données inventées ; RH/paie et point 6 restent différés. La recette humaine et la conformité réglementaire restent à valider.
