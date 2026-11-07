# Personnel & Paie — résultats 875 et reprise

27 octobre 2026. Fondation du lot 1A.2 ; pas recette du module Personnel & Paie complet.

**212 cas distincts réussis** dans la sélection finale : 93 unitaires/contrôles de sources, 115 API/SQL/bootstrap PostgreSQL natif isolé et 4 parcours Edge/API/PostgreSQL. Aucun échec, erreur ou cas ignoré dans cette sélection. Les répétitions ne sont pas additionnées au total.

| Campagne | Cas | Réussis | Échecs | Erreurs / ignorés | Durée pytest | Code |
|---|---:|---:|---:|---:|---:|---:|
| Reprise 873 | 2 | 2 | 0 | 0 / 0 | 26,00 s | 0 |
| Première cible 875 | 64 | 49 | 15 | 0 / 0 | 76,91 s | 1 |
| Diagnostic après correction | 2 | 2 | 0 | 0 / 0 | 36,03 s | 0 |
| Première passe complète | 69 | 69 | 0 | 0 / 0 | 103,94 s | 0 |
| Qualification du schéma final | 75 | 75 | 0 | 0 / 0 | 112,19 s | 0 |
| Non-régression | 137 | 137 | 0 | 0 / 0 | 403,91 s | 0 |

Les durées JUnit, légèrement différentes, figurent dans la [preuve JSON](../../Test/PREUVE_PERSONNEL_PAIE_875.json). Les six XML sont joints, y compris la première passe échouée. Les 15 échecs provenaient de l'utilitaire du test qui appelait `.scalar()` après un `INSERT` sans `RETURNING` ; la correction distingue les commandes avec ou sans résultat. Le trigger partagé a également été séparé par type de table pour ne pas résoudre un champ de rémunération sur une ligne de contrat. Aucun contrôle métier n'a été supprimé pour obtenir les succès.

La passe de 69 cas précède les dernières protections du contenu soumis et des privilèges publics. Elle n'est donc pas utilisée pour qualifier à elle seule le fichier SQL final. La sélection finale réunit uniquement `personnel875_qualification` et `personnel875_connexes`, sur des sources produit conservées identiques pendant l'exécution. Le [candidat 875](../../Test/CANDIDAT_PERSONNEL_PAIE_875.json) porte 468 empreintes : trois sources existantes modifiées et deux nouvelles depuis 873. Les anciennes migrations, l'authentification, les modèles ORM, les schémas historiques, le démarrage, la comptabilité, la fiscalité et le frontend sont conservés.

## Contrôles effectivement exécutés

- Montants décimaux exacts, sérialisation en texte, refus booléens/flottants/NaN/infinis/négatifs/précision excessive ; dates ISO connues, pas de timestamp coercitif.
- Normalisation matricule identique Python/SQL, zéros et casse préservés, collisions de bord détectées, aucune réparation.
- Installation sur schéma existant, rejeu à vide et avec versions/décisions/événements, empreintes historiques inchangées ; absence de105 refusée transactionnellement, installation partielle signalée.
- Diagnostic API authentifié, administrateur et capacités en mode protégé, module désactivé, société courante, listes plafonnées, absence de salaires/CNSS et de fuite inter-sociétés ; GET sans mutation des tables.
- FK composites, montant SQL fini, dates connues et finies, décision cohérente et indépendante, bénéficiaire relié refusé comme approbateur, contrat approuvé applicable avant rémunération approuvée.
- Versions approuvées immuables, contenu soumis figé, événements sans modification/suppression, refus de suppression/troncature ; rôle runtime LOGIN non propriétaire en lecture seule sur les nouvelles structures.
- Lecture technique à date : 9 000,10 MAD au 31/12/2026 puis 9 876,54 MAD au 01/01/2027, sans écraser la première version. Une proposition non approuvée n'interrompt pas la période courante.
- Deux insertions concurrentes de versions approuvées à la même date ne créent pas deux versions ; une création historique concurrente attend le rattachement du dossier puis reçoit409 ; même matricule autorisé dans une autre société.
- Compte référencé par un événement sans aucune habilitation105 : suppression409, désactivation200, historique conservé.
- Anciens dossiers, simulations indicatives, absences, référentiels, avances et bootstrap sur ancienne base ; quatre parcours Edge : masquage/révocation et avances, chacun exécuté aux largeurs1440 et390 pixels.

Ces parcours navigateur sont des non-régressions des écrans existants. Aucun nouvel écran ou formulaire1B n'est annoncé testé.

## Compilation et environnement

**Sept fichiers Python ajoutés/modifiés compilés : OK.** Une note intermédiaire du journal indiquait six ; l'inventaire et la preuve de compilation en comptent bien sept.

Frontend inchangé, empreintes conservées ; **build non relancé pour875**. Le résultat du build873 reste historique. Aucun PostgreSQL utilisateur contacté, aucun `.env` chargé pour les tests. Les clusters natifs temporaires portent un nonce et des ports locaux dédiés ; la collecte utilise une URL sentinelle injoignable. SQLite ne remplace aucun contrôle PostgreSQL de cette étape.

## À vérifier sur copie de l'environnement cible

Installation105/106, rôle migrateur distinct du runtime, préflight de chaque société, contraintes/droits réellement installés, sauvegarde restaurable et compatibilité du retrait applicatif. Les anomalies historiques restent à traiter par décision justifiée ; aucune donnée réelle n'a été examinée ou corrigée ici.

Le schéma est une fondation : les mutations runtime sont fermées, et les versions synthétiques des tests sont préparées par le propriétaire des clusters de test. Le circuit d'approbation API complet et l'activation de paie ne sont pas livrés. Le lien d'un bénéficiaire avec son compte doit être attesté avant l'approbation applicative ; son absence n'est pas une preuve d'indépendance. Aucun taux légal, règle fiscale, dépôt ou paiement réel n'est ajouté.

## Prochaine tâche exacte

Lot1A.3 : API de dossiers, propositions, soumissions, approbations/rejets et sorties ; capacités de mutation explicites, `revision_attendue`, verrouillage, refus des auto-approbations et doubles validations, historique et projections masquées à date.

Résoudre explicitement le brouillon sans salaire dans la racine historique où `salaire_brut` reste `NOT NULL` : aucune fausse valeur zéro. Prévoir une migration additive suivante si nécessaire ; ne pas réécrire105/106 après installation. Préserver les anciens liens et ne pas produire d'écriture comptable à la création. Ensuite seulement, lot1B pour les formulaires et la sidebar à neuf rubriques.

Référence : [guide de cette livraison](LOT1A2_DOSSIERS_VERSIONS_875.md). Développement de la fondation terminé ; tests automatisés de son périmètre validés ; recette utilisateur et production non validées.
