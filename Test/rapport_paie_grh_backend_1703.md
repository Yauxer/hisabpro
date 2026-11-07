# Paie / GRH — dossier salarié et préparation indicative

## Périmètre livré

Dossier salarié enrichi : matricule, numéro CNSS, contrat CDI/CDD/autre, email,
téléphone, dates d'entrée/sortie et personnes à charge IR explicitement confirmées.
Les champs nouveaux sont optionnels. Le mariage et le nombre d'enfants ne
déterminent plus automatiquement une réduction fiscale dans la préparation.
Archivage logique et restauration, tri récent, isolation des sociétés et refus
des mutations pour le rôle lecture sont testés par API réelle.

La migration additive `080_dossiers_employes.sql` ajoute uniquement les colonnes
et contrôles, sans réécrire les salariés ou paramètres fiscaux historiques.
Les contraintes NOT VALID préservent l'historique ; leur validation historique
reste une intervention séparée. Les permissions UPDATE sont limitées aux
colonnes effectivement utilisées par la fiche et l'archivage. Aucun droit DELETE,
TRUNCATE ou modification de societe_id/id n'est ajouté.

`GET /api/employes/cotisations?annee=YYYY&mois=MM` exige une année explicite.
Il ne se replie jamais sur une autre année. La simulation utilise Decimal,
arrondit chaque cotisation au centime puis calcule les retenues, l'IR indicatif,
le net et les charges patronales à partir du référentiel stocké. Le nombre de
personnes à charge doit être confirmé, y compris la valeur zéro.

Un taux manquant, en doublon, non fini ou invalide, un barème absent/discontinu,
une réduction familiale absente, un salaire historique non fini ou une entrée/
sortie en milieu de mois bloque le calcul concerné. Les totaux sont null si une
ligne est bloquée, afin de ne pas afficher un total partiel comme complet.
Le mois sert au filtrage réel des dates du dossier. Aucun prorata n'est inventé.

## Limites et sources

La préparation est une **simulation indicative de salaire fixe sur mois complet**.
Elle ne produit ni bulletin figé, ni déclaration CNSS, ni écriture SA. Les primes,
indemnités, absences, heures supplémentaires, avances, CIMR, régimes particuliers,
régularisations annuelles et paiements ne sont pas couverts. Aucun taux AT de 1 %
n'est appliqué par défaut ; cette assurance contractuelle reste exclue.

Le référentiel historique de donnees_fiscales.sql est laissé intact. Il manque
notamment une participation AMO explicitement paramétrée ; le service bloque ce
jeu incomplet au lieu de livrer silencieusement un net présenté comme fiable.
Les paramètres sociaux doivent être vérifiés sur source CNSS puis configurés
dans un lot distinct. Aucun nouveau taux réglementaire n'a été inventé ni installé.

Références consultées le 7 octobre 2026 :

- [CGI 2026 — ministère des Finances](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf) : index officiel consultable, article 59 frais professionnels et article 74 réduction 600 MAD/personne, plafond 3 600 MAD retrouvés. Téléchargement direct en timeout pendant la session. Les règles générales de frais professionnels/annualisation existaient déjà ; ce lot ne prétend pas traiter toutes les catégories de salariés.
- [CNSS — paiement des cotisations sociales](https://www.cnss.ma/fr/content/paiement-de-vos-cotisations-sociales) : source directe indisponible, timeout. Plusieurs sources secondaires donnent des ventilations différentes ; elles ne sont pas utilisées pour installer des taux.

Le moteur paramétré vérifié avec un jeu de laboratoire ne constitue pas une
validation réglementaire de la paie marocaine. Les fonctions historiques de
routers/parametres.py restent présentes pour compatibilité, mais ne sont plus
appelées par le parcours employés. Aucun endpoint public ne les utilise.

## Tests exécutés

- Première suite ciblée : 40 réussis, aucun échec/ignoré, 18,90 s.
- Relancement incluant les quatre salaires historiques invalides : 45 réussis,
  aucun échec/ignoré, 28,17 s.
- Relecture : découplage du schéma de sortie pour lire les anciens dossiers
  sans leur imposer la validation d'une nouvelle saisie. Salaire non fini rendu
  null et simulation bloquée, sans réécriture de l'historique. Premier test
  ajouté : 45 réussis / 1 échec de fixture (ancien code trop long pour varchar20),
  29,23 s. Fixture corrigée, dernier relancement : **46 réussis**, aucun
  échec/ignoré, **29,77 s**.
- Suite ciblée et connexe (paie, documents numériques, règlements) : 170 réussis,
  aucun échec/ignoré, 63,53 s. Les quatre gardes supplémentaires sur le salaire
  historique sont vérifiées séparément par le relancement final ci-dessous.
- Compilation Python des modèles, schémas, route, service et deux fichiers de
  tests : exécutée après la suite connexe, sans erreur.
- PostgreSQL réel de l'utilisateur : jamais connecté. Les tests utilisent les
  clusters éphémères marqués sous .codex-tests, port distinct de 5432 et données
  fictives exclusivement. Arrêt et suppression contrôlée sont vérifiés.

L'oracle indépendant de laboratoire utilise un brut 10 000 MAD, retenues 494,80,
charges patronales 1 749,80, IR 601,56 sans personne à charge, net 8 903,64 et coût
11 749,80. Ces taux sont des **données de test explicitement non réglementaires**.
Le test API les range en année fictive 2088 pour les distinguer du référentiel réel.

Le test migration part d'une ancienne table de salariés, préserve toutes les
colonnes historiques du salarié fictif à 7 123,45 MAD et rejoue 080 deux fois.
Une connexion LOGIN hisabpro non propriétaire réalise SELECT/INSERT et UPDATE de
fiche ; changement de société/id, DELETE et TRUNCATE renvoient 42501, personne
à charge 7 renvoie 23514. Les assertions ne supposent pas la révocation des
permissions globales qu'une installation historique aurait déjà accordées.
