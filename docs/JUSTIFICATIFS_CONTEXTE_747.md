# MODE D’EMPLOI ET RECETTE — JUSTIFICATIFS ET CHANGEMENT DE SESSION

Version 1 du 22 octobre 2026. Complément 747 aux guides 739/745.

## Joindre et vérifier une pièce

Dans une société fictive et une préparation 2026 conservée, ouvrir Liasse fiscale
→ Import Balance / Liasse seule. Sélectionner la version souhaitée, puis ouvrir
Justificatifs complémentaires de cette version. Dans Fichier justificatif,
choisir JUSTIFICATIF_FICTIF747.pdf fourni avec ce guide. Saisir dans Référence
documentaire facultative : RECETTE-FICTIVE747. Cliquer Joindre et conserver le
justificatif. Le message de conservation, la pièce, sa taille et son empreinte
s’affichent sans F5. Son identifiant est attribué par le serveur.

Télécharger le justificatif avec le bouton portant cet identifiant, puis le
dossier ZIP de préparation. La pièce téléchargée doit conserver exactement
ses octets ; elle figure aussi dans justificatifs.json et dans le manifeste
du dossier. La préparation financière n’est pas remplacée par l’ajout d’une
pièce. Une consultation seule peut lire les pièces autorisées, pas en joindre.

## Ce qui est protégé

L’adaptateur d’envoi du fichier utilise maintenant les mêmes contrôles de
contexte que les requêtes JSON et les exports. Un ancien refus 401 ne supprime
pas une nouvelle session. Une ancienne réponse 201, ou sa lecture JSON terminée
après un changement de jeton, n’est pas restituée au nouveau contexte. Une
session courante réellement refusée reste déconnectée.

Une pièce déjà acceptée par le serveur reste dans la société et la version
d’origine. Ignorer sa réponse ne l’annule pas et ne relance pas son envoi.
Revenir dans l’ancienne société et vérifier la liste avant toute nouvelle
soumission. Le fichier n’est jamais supprimé pour masquer un refus de contexte.

## Données de recette et préparation

Bac isolé uniquement. Deux sociétés fictives Pièces A747 et Pièces B747, MAD,
exercice 2026. Même utilisateur administrateur dans A et invité en consultation
dans B. La préparation et la pièce sont créées dans A. Le fichier fourni est
explicitement fictif, sans valeur fiscale ; son SHA256 exact et sa taille sont
fournis dans DONNEES_PIECES747.json. Ne jamais l’utiliser dans un dossier réel.

Le responsable technique prépare les réponses natives retenues et le changement
de jeton dans le bac. Les tests de course portent sur le client réel compilé
sous Edge et une API native ; ils ne valent pas recette complète du sélecteur UI
ou de toutes les interactions entre onglets. Si le banc de latence est absent,
classer ces cas Bloqué, sans provoquer de panne en production.

## Cas de recette humaine à effectuer

Les résultats réels, anomalies et preuves restent à renseigner. Tous les cas
ci-dessous sont Non testé pour la recette humaine malgré les tests automatisés.
Aucune écriture, paiement ou déclaration fiscale attendu pour ces seuls essais.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|PIE747-01|Dans A, ouvrir les justificatifs de la préparation ; joindre JUSTIFICATIF_FICTIF747.pdf avec RECETTE-FICTIVE747 ; télécharger la pièce et le ZIP.|Une pièce, message de conservation, taille/SHA identiques auJSON de données ; octets téléchargés identiques, aucune nouvelle préparation financière ; captures et fichiers.|Non testé|
|PIE747-02|Responsable retient un vrai refus 401 d’un ancien envoi ; remplacer la session par celle deB, puis libérer le refus.|Session B et rôle Consultation conservés, ancienne réponse ignorée, aucune pièce créée pour ce refus ; trace 401 et capture.|Non testé|
|PIE747-03|Dans A, envoyer une pièce et retenir son succès 201 après conservation, ou la fin de lecture duJSON ; passer au contexte B puis libérer ; revenir vérifierA.|Ancienne réponse ignorée dans B, exactement une pièce conservée dans A avec ses octets, aucune relance ; B ne peut pas lire la pièce A ; captures, trace d’un seul POST et fichier.|Non testé|
|PIE747-04|Consulter les justificatifs comme utilisateur Lecture autorisé ; puis faire préparer par le responsable un jeton courant refusé dans le bac et demander un envoi.|Lecture et téléchargements autorisés selon droits, aucun bouton d’ajout ; vrai refus courant 401 ramène à Connexion, aucun fichier orphelin ni donnée créée ; captures et trace.|Non testé|

## Limites

Aucun backend, migration, calcul ou droit serveur changé dans 747. Les versions,
liens, fichiers et empreintes gardent leurs règles existantes. Les tests incluent
les uploads et téléchargements dans l’interface et les contrôles API/SQL natifs,
avec octets, rejouabilité et cloisonnement des sociétés.

Recette humaine, Office, installation cible et production restent à effectuer.
RH/paie etpoint 6 humain restent différés. Les qualifications fiscales et les
pièces réelles manquantes ne sont jamais remplacées par les fichiers de recette.
