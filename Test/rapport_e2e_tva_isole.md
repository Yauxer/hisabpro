# Recette TVA connectée — 7 octobre 2026

Vraie interface React dans Edge, FastAPI et PostgreSQL éphémère marqué.
Les factures et règlements de préparation passent par les API métier ; aucun
appel métier n'est simulé. Aucun PostgreSQL réel, aucune déclaration déposée.

## Données et calcul indépendant

Société fictive au régime encaissement. Factures de mars : vente 1 000 HT +
200 TVA, achat 500 HT + 100 TVA. Le taux 20 % est un paramètre du laboratoire,
sans nouvelle qualification fiscale. Paiements partiels d'avril : 600 et 300 TTC.

Mars : TVA collectée et récupérable 0. Avril : base ventes 500, TVA collectée
100 ; base achats 250, récupérable 50 ; nette 50. Les vues T2 et annuelle
recoupent ces montants. Les quatre écritures définitives restent équilibrées,
total débit/crédit 2 700, TVA comptable facturée 200/récupérable 100.

Avec crédit d'ouverture fictif explicite 20 et prorata 80 %, la récupération
annuelle devient 40 et la TVA nette 100 − 40 − 20 = 40. Les paramètres
persistent après rechargement sans modifier les lignes comptables définitives.

## Corrections minimales

- Le bouton Imprimer déclenche désormais l'impression native de la vue.
  Le rendu papier conserve société, période, montants et mention de brouillon.
- L'identité de Préparation DGI provient des paramètres réels de la société.
  IF/ICE absents restent vides et indiqués à compléter dans l'impression.
- Le rôle lecture consulte et imprime ; les paramètres sont désactivés et
  le bouton Enregistrer est masqué. Une tentative PUT réelle est refusée 403.
- Les paramètres TVA refusent les booléens et les crédits NaN/Infinity avant
  mutation. Le prorata conserve sa plage existante 0–100.

## Exécutions réelles

Le premier parcours repris de l'agent a été exécuté par le principal après
correction impression/identité : **1 réussi, 0 échec/ignoré, 22,31 s**.
Le résultat de la commande interrompue de l'agent 97538 n'a pas été récupéré
et n'est pas présenté comme une réussite.

Avant correction des droits UI, le test lecteur a échoué : **1 échec,
1 désélectionné, 17,55 s**, bouton Enregistrer visible. Avant correction des
paramètres : **6 échecs, 2 réussis, 6 désélectionnés, 1,09 s**, NaN/Infinity
du crédit et booléens acceptés.

Après correction : **26 tests réussis, 0 échec/ignoré, 23,07 s**, dont deux
parcours connectés et tests connexes TVA/float8/exercices décalés.
Puis **14 tests réussis, 0 échec/ignoré, 19,43 s**, dont six requêtes PUT réelles
invalides : réponse 422 et paramètres persistés inchangés.

Compilation Python : OK. Build Vite : **131 modules, 4,15 s, code 0**.
Avertissements existants : dépréciations Pydantic/multipart, taille du bundle
et import XLSX partagé.

Le clic Imprimer est instrumenté uniquement pour compter l'appel natif ;
la vraie fonction est exécutée. Un PDF de la vraie page est généré et relu
avec pypdf : identité, période, mention sans dépôt DGI et montants présents.
Cela ne valide pas une imprimante physique ni un format officiel DGI.

## Limites

La TVA RAS, certaines exclusions automatiques, régularisations immobilisations
et gel d'une déclaration déposée restent documentés dans le module.
Pas de transmission DGI ni export officiel. Les vues trimestre/année servent
au contrôle et n'imposent aucune nouvelle périodicité déclarative.
Les clusters/serveurs/dossiers de cette recette sont arrêtés et nettoyés.
