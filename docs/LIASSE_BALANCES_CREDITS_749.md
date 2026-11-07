# Mode d’emploi — Crédits IS externes qualifiés 2026

Version 1 du 22 octobre 2026. Complément 749 du mode Liasse seule.


## Ce que permet cette avancée

Dans Comptabilité → Liasse fiscale → Import Balance / Liasse seule, ouvrir une préparation conservée. La rubrique « Qualifier les crédits IS — 2026 » distingue désormais les justificatifs de retenues, leur exercice, leur date et leurs utilisations antérieures. La rubrique ajoute une nouvelle version ; elle ne modifie aucune écriture ou déclaration fiscale existante.

Les montants proposés dépendent des qualifications explicitement saisies. Ils ne constituent pas une confirmation par un fiscaliste, un dépôt, une restitution ou un paiement. La CSS reste séparée. Une qualification vide reste inconnue. Le calcul couvre 2026 uniquement.

## Préparer une recette sans données réelles

Utiliser une société de test MAD et une préparation 2026 couvrant le 01/01/2026 au 31/12/2026. Le fichier existant `BALANCE_FICTIVE_CM741_N.csv` peut servir à l’import. Ne pas sélectionner une société comptable réelle. Les services frontend/backend de test doivent être démarrés ; les scénarios de panne et de réponse différée nécessitent le banc automatisé isolé, pas une manipulation de production.

Les données ci-dessous sont exclusivement fictives. Le document `ATTESTATIONS_FICTIVES_CR749.md` décrit les références ; ce ne sont pas des attestations utilisables fiscalement. Le rôle admin ou comptable peut conserver ; le rôle lecture peut consulter et télécharger.

## Saisir le profil et les deux justificatifs

1. Ouvrir la rubrique « Qualifier les crédits IS — 2026 ». Sélectionner « CR-PROFIL · Profil et exhaustivité des crédits ». Choisir « Saisie documentée — à revoir » ; saisir la justification « Profil fictif et liste exhaustive revus » puis ajouter une ligne.
2. Saisir la désignation « Crédits fictifs 2026 », le périmètre « Société IS hors exonération totale », période source confirmée = oui, liste exhaustive = oui, absence de tout crédit = non. Référence : `NOTE-CR749`.
3. Sélectionner « CR-LIGNES · Justificatifs des crédits IS ». Déclaration documentée ; justification « Attestations fictives et historique des utilisations ». Ajouter deux lignes.
4. Ligne 1 : désignation « Attestation banque fictive », type « PPRF — CGI159 », exercice 2026, date de retenue 20/03/2026, date d’allocation et catégorie du payeur laissées vides pour ce PPRF, éligibilité IS = oui, montant 300, part déjà imputée sur acomptes 100, autres utilisations ou restitutions 25. Référence `CR749-A`.
5. Ligne 2 : désignation « Attestation client fictive », type « Rémunérations de tiers — CGI157 », exercice 2026, date de retenue 20/06/2026, date d’allocation 20/06/2026, catégorie du payeur « Public ou filiale publique », éligibilité IS = oui, montant 200, déjà imputé 50, autres utilisations 0. Référence `CR749-B`.
6. Cocher la confirmation puis « Conserver les crédits IS dans une nouvelle version ». Le numéro de version doit changer sans F5. Réouvrir la rubrique pour consulter les contrôles conservés.

Chaque référence de ligne doit identifier distinctement son justificatif. Si un même document contient plusieurs retenues, préciser un numéro de ligne distinct dans la référence. Pour les rémunérations de tiers et locations, la date d’allocation justifiée et la catégorie du payeur sont nécessaires. Les produits de location alloués avant le 01/07/2026 restent à qualifier. Pour les banques/assurances et entreprises privées de CA au moins 500 millions MAD, la nouvelle retenue ne commence que le 01/07/2026. Une retenue effectuée en juillet ne prouve pas que le produit a été alloué en juillet. Une allocation inconnue ou postérieure à la retenue laisse la qualification incomplète.

Les types Sukuk et Location sont distingués dans les déclarations. Le moteur existant regroupe respectivement PPRF/Sukuk et tiers/location pour l’arithmétique, sans imposer un ordre juridique d’imputation.

## Vérifier les résultats indépendants

Le total vaut 300+200=500 MAD. La part déjà imputée sur acomptes vaut 100+50=150 MAD. Les autres utilisations valent 25 MAD. Le reliquat arithmétique est 500−150−25=325 MAD ; avec ce profil et ces deux lignes qualifiées, le disponible proposé vaut 325 MAD.

Si le contexte fiscal 735 fictif d’origine est conservé, son total crédits est 600 MAD et sa part déjà utilisée 150 MAD. Les écarts sont donc−100 MAD et 0 MAD. Le module les montre sans modifier le contexte. Si aucun contexte n’existe, les écarts restent indisponibles.

Modifier une ligne sans conserver laisse le contrôle et l’export à 325 MAD : le formulaire est un brouillon. Marquer ensuite l’éligibilité de la ligne 1 = non et conserver donne 150 MAD proposés ; le reliquat arithmétique des deux justificatifs reste 325 MAD, car la première ligne est visible mais exclue de la proposition.

## Inconnus, absence de crédits et contrôles négatifs

Laisser « autres utilisations » vide, choisir un autre type à qualifier, indiquer un crédit 2025 ou une date hors période : la disponibilité globale devient inconnue. Le module ne recycle pas automatiquement un crédit antérieur. Une ligne explicitement non éligible reste exclue et visible.

Pour une absence exhaustive de crédits, créer une nouvelle version de recette : profil documenté et confirmé, absence = oui, tableau CR-LIGNES « Néant — déclaré et justifié », sans lignes et avec justification. Le disponible proposé est explicitement 0 MAD. « Néant » seul, sans confirmation du profil, laisse le montant inconnu. Une absence déclarée avec des lignes est refusée.

Une valeur NaN, infinie, négative, trop précise, une date invalide, un doublon de référence ou une somme des utilisations supérieure au justificatif est refusée sans créer de version. La saisie est conservée à l’écran pour correction. Un lecteur ne dispose pas du bouton de conservation ; une autre société ne peut pas consulter cette préparation.

## Télécharger et contrôler les preuves

« Télécharger le dossier de préparation ZIP » fournit le snapshot JSON, le complément `credits_is_documentaires.json`, les balances conservées et les rendus PDF/Excel. Le logo actuel de la société est intégré aux rendus lorsqu’il est valide. Le manifeste vérifie les tailles et SHA256 de chaque autre fichier.

Dans Excel, contrôler « Origine crédits IS », « Contrôle crédits IS », CR-PROFIL, CR-LIGNES et « Qualification crédits IS ». Les références commençant par = restent du texte. Le PDF reprend les sources, qualifications et montants. Une modification ultérieure du contexte fiscal signale que la comparaison conservée est ancienne ; il faut relire puis conserver une nouvelle qualification. Le contrôle historique reste figé.

## Cahier de recette complémentaire

Tous les cas humains restent Non testé, même si leurs parcours automatisés sont réussis. Renseigner le résultat réel, les anomalies et les preuves dans le classeur, après exécution sur une société fictive.

| ID | Actions détaillées | Résultat attendu et preuve | Statut |
|---|---|---|---|
|CR749-01|Suivre les six étapes de saisie du profil et des deux justificatifs ci-dessus.|Nouvelle version sans F5 ; total 500, déjà utilisé 150, autres 25, disponible 325 MAD. Capture du contrôle et numéro de version.|Non testé|
|CR749-02|Modifier le montant de la ligne 1 sans conserver puis télécharger le dossier ZIP.|Contrôle et exports conservés à 325 MAD ; aucune nouvelle version. Garder le ZIP et sa référence.|Non testé|
|CR749-03|Marquer l’éligibilité de la ligne 1 non puis conserver.|Disponible proposé 150 MAD, reliquat arithmétique 325 MAD, ligne 1 exclue visible. Capture et snapshot.|Non testé|
|CR749-04|Depuis une version de base, laisser autres utilisations de la ligne 1 vide ; conserver. Refaire avec exercice 2025 ou type Autre. Pour le type Location : date de retenue 01/07/2026, allocation 30/06/2026, payeur public ; conserver, puis corriger allocation au 01/07/2026 et conserver.|Disponible global indisponible si qualification manquante ou location allouée avant juillet ; corrigée au 01/07 avec ce profil, disponible325MAD. Aucun report automatique. Capturer les deux versions et sources.|Non testé|
|CR749-05|Saisir NaN puis autres utilisations 201 sur la ligne 1, ou dupliquer la référence CR749-A sur la seconde ligne ; tenter de conserver après chaque cas.|Refus lisible, aucune nouvelle version ou écriture ; brouillon corrigeable. Captures des refus.|Non testé|
|CR749-06|Confirmer absence oui dans le profil ; retirer explicitement toutes les lignes ; déclarer CR-LIGNES néant avec justification ; conserver. Comparer au même néant sans profil exhaustif confirmé.|Absence confirmée donne 0 MAD ; néant seul reste indisponible. Deux numéros de version et captures.|Non testé|
|CR749-07|Avec les rôles comptable puis lecture, consulter la préparation sur écran 390 px ; télécharger PDF/Excel/ZIP.|Comptable peut conserver ; lecteur ne peut pas modifier ; pas de débordement horizontal global. Logo et montants visibles dans les rendus.|Non testé|
|CR749-08|Avec le contexte 735 initial 600/150, conserver les crédits ; modifier son premier crédit 300 en 200 dans une nouvelle version ; relire les crédits puis conserver une nouvelle qualification.|Ancien écart−100/0 figé et avertissement de source modifiée ; nouvelle comparaison 0/0. Anciennes versions et pièces préservées.|Non testé|

## Limites et suite

Le contrôle ne prouve pas l’authenticité d’une attestation ni l’éligibilité réelle déclarée. Le cas totalement exonéré est hors périmètre de ce profil. Autres crédits et reports antérieurs restent à qualifier. Les acomptes et la liquidation externe conditionnelle sont les étapes suivantes ; aucun solde définitif n’est présenté ici. La recette utilisateur, Office et l’environnement cible restent à vérifier. RH/paie et le point 6 humain restent différés.
