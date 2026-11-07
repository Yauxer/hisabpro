# HisabPro — correction du nom des exports téléchargés

L'API renvoyait déjà Content-Disposition avec le nom delais_paiement_2026_T1.csv. Sur une origine frontend distincte de l'API, CORS ne rendait pas cet en-tête accessible à JavaScript ; le client utilisait donc son repli export.bin. La correction ajoute uniquement Content-Disposition à expose_headers dans main.py. Les origines autorisées, les méthodes et l'authentification restent identiques. Aucune migration ni donnée comptable n'est modifiée.

L'échec est reproduit dans Edge avant correction. Après correction, les parcours complets ordinateur 1440 et mobile 390 téléchargent effectivement delais_paiement_2026_T1.csv. Les deux références 02/002, montants de 240 MAD et dates de service/échéance sont relus dans les fichiers ; les écritures restent identiques. Création, modification et annulation de relance restent également vérifiées. Un test sur le véritable serveur isolé confirme la prérequête autorisée, le refus CORS d'une origine étrangère et le refus 401 d'export sans authentification.

Tests réellement exécutés : campagne avant correction en échec attendu ; deux parcours navigateur après correction réussis ; contrôle CORS réussi ; compilation Python réussie. Aucun frontend modifié, donc aucun nouveau build nécessaire pour ce lot. Les fichiers de résultats JUnit et preuves brutes sont conservés.

Le suivi demeure à 131 fiches réussies, 6 partielles, 125 non qualifiées et 10 bloquées par les sources. FAC017 reste partielle : les factures dues le 31 décembre ne sont pas encore en retard à la fin du T4 ; leur présence et leurs compléments sont contrôlés au T1 suivant sans changer leurs dates. L'assujettissement et les montants indicatifs d'amende ne sont pas validés par ces tests.

Pour utiliser : redémarrer le backend corrigé, ouvrir Délais de paiement, choisir exercice/trimestre et Exporter CSV. Le navigateur doit proposer le nom de la période. Aucun accès à PostgreSQL utilisateur n'a été effectué. Prochaine étape : reprendre le diagnostic navigation/polices et la balance avant IS sur mobile. RH/paie et point 6 restent différés.
