# Paie — catalogue des éléments, livraison 889

La rubrique **02 · Éléments de paie** est maintenant accessible dans la sidebar, sur ordinateur et mobile, pour les profils autorisés. Ce lot livre le catalogue versionné et son interface ; les variables mensuelles, campagnes et bulletins sont les étapes suivantes.

## Installer sur copie

Après le socle Personnel jusqu'à 112, appliquer la migration additive `hisabpro-backend/113_paie_catalogue.sql` avec le rôle migrateur sur une copie isolée. Déployer le frontend et tous les backends actuels avant de déléguer le nouveau droit réglementaire. Aucun taux, plafond, rubrique ou droit n'est créé implicitement. Les anciens paramètres de paie restent inchangés.

La migration peut être rejouée : les anciennes données et les nouvelles habilitations sont préservées. Elle étend la contrainte de capacités existante, sans modifier le fichier d'une ancienne migration. Ne pas réexécuter une ancienne migration pour revenir à un ancien catalogue de droits.

## Habiliter

- Lecture du catalogue : protection Personnel active, module actif, capacités **identité et rémunération**.
- Préparation : profil autorisé à écrire le Personnel et capacité **Créer et proposer**.
- Décision : capacité **Approuver ou rejeter**, avec un décideur indépendant du préparateur pour l'approbation.
- Qualification des règles déclarées « Validé » : capacité supplémentaire **Qualifier les règles réglementaires de paie**, à déléguer explicitement à la personne compétente dans **Personnel > Habilitations**. Aucun administrateur ne la reçoit automatiquement. Sa révocation prend effet côté serveur.

## Créer et faire approuver une rubrique

Ouvrir **02 · Éléments de paie > Créer une rubrique**. Saisir un code stable en majuscules, libellé, nature, périodicité, mode de saisie et date de début connue. Le compte de charge est facultatif à ce stade ; s'il est renseigné, il doit exister et être actif dans le plan de la société. La validation de son imputabilité à la comptabilisation reste une étape ultérieure.

Les modes permis sont **Montant exact** et **Quantité × taux**. Ce sont les types destinés à la future saisie des variables ; aucune formule libre ni code utilisateur n'est exécuté. Les types de justificatifs et les codes incompatibles peuvent être renseignés séparément par virgules. Les incompatibilités doivent référencer des rubriques existantes de la même société ; une auto-incompatibilité est refusée.

Renseigner séparément **IR**, **CNSS** et **AMO**. Chaque régime possède son traitement, statut réglementaire, éventuel plafond, unité et conditions. Une inconnue reste **À vérifier** : elle n'est convertie ni en exonération ni en assujettissement présumé.

Pour déclarer une règle « Validé », il faut un traitement déterminé, un texte, un article, une URL HTTPS officielle et l'empreinte SHA-256 de la preuve. **Ces références sont déclarées par l'opérateur ; le serveur ne télécharge pas le texte et ne certifie pas son interprétation ni le contenu de la preuve.** Le décideur doit posséder le droit réglementaire dédié et confirmer le contrôle des textes, preuves et conditions. Une approbation du catalogue ne constitue pas une certification réglementaire.

Enregistrer crée une version **Proposée**. Le deuxième utilisateur ouvre **Consulter CODE**, examine le détail puis approuve ou rejette avec motif et référence du contrôle. Une décision est définitive pour cette version. Une version déjà décidée ou une demande concurrente produit un conflit explicite.

## Consulter les dates et versions

Le filtre **Règles applicables au** affiche la version approuvée correspondant à cette date ; la dernière proposition reste distincte. Une nouvelle version conserve les anciennes données et requiert une nouvelle date explicite. Après une première approbation, la suivante doit commencer dans le futur et après la dernière version approuvée. Une date de fin expirée ne réactive pas une version antérieure. Une révision périmée ne peut pas écraser une proposition concurrente.

Une erreur de proposition ne se corrige pas en modifiant l'historique : rejeter la version puis en proposer une nouvelle. Le code de rubrique reste stable. Aucune suppression de version n'est proposée.

## Recette chiffrée entièrement fictive

Sur copie de recette, créer `PRIME_FICTIVE889`, libellé `Prime FICTIVE889`, gain mensuel, montant exact, début `2026-01-01`. Déclarer les justificatifs `ATTESTATION_FICTIVE, MISSION_FICTIVE`. Pour chaque régime, saisir comme conditions : `Hypothèse FICTIVE889 ; aucune valeur réglementaire`.

Paramètres **pédagogiques, sans valeur légale** : IR plafonné à `500.00` par opération, CNSS plafonnée à `300.00` par opération et AMO soumise en totalité ; tous les statuts réglementaires restent **À vérifier**. Motif : `Exemple entièrement fictif889`. Faire approuver le catalogue par un deuxième utilisateur indépendant ; cela n'autorise pas une paie définitive.

Dans le détail, ouvrir **Aperçu pédagogique de ventilation**, saisir `800.01`. Résultats arithmétiques attendus :

| Régime fictif | Exonéré | Soumis |
|---|---:|---:|
| IR | 500,00 | 300,01 |
| CNSS | 300,00 | 500,01 |
| AMO | 0,00 | 800,01 |

L'aperçu n'évalue pas les conditions d'éligibilité ni les justificatifs. Pour un plafond mensuel, journalier ou annuel, il laisse les fractions non calculées plutôt qu'inventer un cumul. Il ne calcule ni cotisation, ni IR, ni net à payer.

Créer ensuite une version future au `2027-01-01`, si cette date est encore future lors de la recette, avec libellé `Prime FUTURE FICTIVE889`. La faire approuver. Au `2026-12-31`, l'ancienne reste applicable ; au `2027-01-01`, la nouvelle s'applique. Pour une recette ultérieure, choisir des dates futures correspondantes.

Essais négatifs : code dupliqué, mauvais compte, incompatibilité inconnue, auto-approbation, valeur NaN/non finie/flottante, montant négatif ou à plus de deux décimales, version périmée, règle « Validé » sans preuve, approbation réglementaire sans droit dédié ou après révocation, accès depuis une autre société. Aucun de ces essais ne doit générer d'écriture comptable.

## Sources consultées et limites

Le [CGI 2026 officiel](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf), notamment les dispositions relatives aux revenus salariaux, a été retrouvé dans l'index primaire ; son ouverture directe a rencontré un timeout. Le texte consolidé de l'arrêté 1314-25 a été ouvert sur le portail officiel Adala : 17 pages, version mise à jour au 11 décembre 2025, mentionnant le rectificatif du BO 7464. Cette consultation justifie de conserver les références et conditions par régime ; elle ne signifie pas que tous les plafonds ont été traduits en règles de calcul.

**Aucun chiffre réglementaire nouveau n'est activé dans cette livraison.** Les paramètres chiffrés de recette ci-dessus sont exclusivement fictifs. Les règles complexes de pourcentage, SMIG, cumul annuel, non-cumul entre variables, exonérations conditionnelles et calculs de cotisations/IR restent à développer et qualifier avant paie définitive. Le catalogue stocke les incompatibilités et types de preuves, mais leur contrôle sur les variables appartient au lot suivant.

La recette utilisateur et la production restent non validées. Aucune base PostgreSQL réelle n'a été contactée.
