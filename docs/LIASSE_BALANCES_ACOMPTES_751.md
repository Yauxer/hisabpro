# MODE D’EMPLOI — ACOMPTES IS EXTERNES ET AFFECTATIONS JUSTIFIÉES

Version 1 du 23 octobre 2026. Complément 751 du mode Liasse seule.

## Ce qui est ajouté

La rubrique « Qualifier les acomptes IS — 2026 », dans Comptabilité → Liasse fiscale → Import Balance / Liasse seule, conserve les versements effectifs déclarés, les excédents antérieurs affectés et les retenues affectées. Chaque retenue désigne exactement son justificatif de crédits 749. Le calendrier et les états sont calculés sur une référence annuelle qualifiée et une date de contrôle explicitement saisie.

Ce formulaire ne réalise aucun paiement ni imputation effective. Il ne crée aucune écriture comptable et ne confirme aucune liquidation. Le disponible reste une proposition conditionnelle aux sources déclarées. La CSS est séparée. Une case vide reste inconnue ; les anciennes versions ne sont jamais recalculées.

## Prérequis et jeu de données

Utiliser exclusivement une société fictive MAD2026 et une préparation couvrant le 01/01/2026 au 31/12/2026. Préparer les deux crédits du guide 749 : CR749-A300 MAD dont 100 déjà utilisés sur acomptes et 25 autres utilisations ; CR749-B200 MAD dont 50 déjà utilisés et 0 autres utilisations. Le premier est PPRF ; le second est une rémunération de tiers allouée par un payeur public le 20/06/2026, retenue à cette même date et rattachée 2026. Le disponible crédits proposé est 325 MAD, avec un profil exhaustif explicitement confirmé.

Les documents `NOTES_FICTIVES_AP751.md` et `DONNEES_ACOMPTES751.json` contiennent les données exactes. Les notes sont sans valeur fiscale. Les services frontend/backend doivent être démarrés sur l’environnement de test ; les rôles admin/comptable peuvent conserver, lecture peut consulter et télécharger.

Pour ce scénario, la note de référence fictive retient un dernier exercice clos 2025 avec bénéfice fiscal 100000 MAD, régime déclaré de droit commun et taux applicable 2026 de 20% : référence ajustée 2026 =20000 MAD. Ce n’est pas une copie automatique de l’impôt 2025. Le solde d’excédent antérieur 170-IV2025 disponible avant affectations est 100 MAD et explicitement justifié. Il n’est pas déduit d’un solde comptable ni inventé depuis le Journal.

## Saisir le profil AP-PROFIL

1. Ouvrir « Qualifier les acomptes IS — 2026 ». Sélectionner AP-PROFIL, choisir « Saisie documentée — à revoir » et saisir la justification « Référence 2026 adaptée et solde antérieur fictifs justifiés, mouvements exhaustifs ». Ajouter une ligne.
2. Désignation : « Acomptes fictifs 2026 ». Périmètre : « Société relevant de l’IS ». Régime : « Quatre acomptes — exercice de douze mois ».
3. Référence annuelle ajustée 2026 justifiée :20000. Référence fiscalement qualifiée :oui. Exercice de référence :2025. Dernier exercice clos confirmé :oui.
4. Excédent antérieur disponible :100. Exercice d’origine :2025. Excédent 170-IV et solde disponible qualifiés :oui.
5. Mouvements et affectations exhaustifs :oui. Absence de tout mouvement confirmée :non. Date de contrôle :23/10/2026. Référence source : « NOTE-AP751-REF et état excédent 170-IV2025 ».

## Saisir les mouvements AP-LIGNES

Sélectionner AP-LIGNES. Déclaration documentée ; justification « Quittance fictive et affectations exactes des attestations CR749 ». Ajouter deux lignes.

Ligne 1 : désignation « Versement et affectations acompte 1 », numéro 1, date 31/03/2026, versement effectif 1000, excédent antérieur affecté 100, retenue affectée 100. Référence exacte du justificatif crédit :CR749-A. Rattachement et justificatif confirmés :oui. Référence de source :AP751-A.

Ligne 2 : désignation « Affectation retenue acompte 2 », numéro 2, date 30/06/2026, versement effectif 0, excédent antérieur affecté 0, retenue affectée 50. Référence crédit :CR749-B. Confirmation :oui. Référence de source :AP751-B. Cette ligne représente une affectation documentée, pas un versement bancaire de 50 MAD.

Cocher la confirmation puis « Conserver les acomptes IS dans une nouvelle version ». Le numéro de version doit changer sans F5. Réouvrir la rubrique pour consulter le contrôle figé. Les pièces restent attachées à leur version d’origine ; joindre les nouveaux justificatifs à la version souhaitée avec la fonction de pièces existante.

## Calculs attendus indépendants

Versements 1000 MAD ; excédent antérieur affecté 100 MAD ; retenues affectées 100+50=150 MAD. Total imputable proposé 1000+100+150=1250 MAD. Excédent antérieur restant 100−100=0 MAD. Rapprochement par justificatif :CR749-A100 affectés sur 100 déjà utilisés ; CR749-B50 sur 50. Écart global 0 MAD.

Référence 20000×25%=5000 MAD par acompte. Au 23/10/2026 :

- Acompte 1, échéance 31/03 : couverture 1000+100+100=1200 MAD ; reste 3800 MAD ; « Partiel — en retard ».
- Acompte 2, échéance 30/06 : couverture 50 MAD ; reste 4950 MAD ; « Partiel — en retard ».
- Acompte 3, échéance 30/09 : couverture 0 ; reste 5000 MAD ; « En retard ».
- Acompte 4, échéance 31/12 : couverture 0 ; reste 5000 MAD ; « À venir ».

Le total des échéances est 20000 MAD. Une référence avec centimes peut donner un écart d’arrondi entre quatre quarts et la référence : cet écart reste affiché, sans répartition inventée. Le calendrier est figé à la date de contrôle saisie ; il ne change pas tout seul le lendemain.

## Vérifier les cas négatifs

Inverser uniquement les références de crédits entre les deux mouvements conserve le total 150 MAD et l’écart global 0 MAD, mais crée des écarts individuels : le disponible proposé devient inconnu. Il faut revoir les justificatifs, pas remplacer l’égalité par un rapprochement approximatif.

Une valeur NaN, infinie, négative, trop précise, un numéro hors 1–4, une référence de mouvement dupliquée ou un excédent affecté supérieur au disponible déclaré est refusé sans nouvelle version. Le brouillon reste corrigeable. Une date après la date de contrôle, un rattachement non confirmé, un excédent d’origine antérieure à 2015 ou des justificatifs crédits incomplets laissent la qualification à revoir.

Laisser la référence annuelle vide conserve les versements et affectations justifiés : le total proposé peut rester 1250 MAD, mais aucun calendrier n’est fabriqué. L’exercice court ou un régime spécifique nécessite une qualification de calendrier distincte. Le mode minimum CM3000 couvre ici un exercice de douze mois et un versement unique au troisième mois, avec référence explicite 3000 ; les autres numéros ne sont pas reclassés automatiquement. Ce mode n’est pas une qualification automatique de l’éligibilité au minimum.

Une déclaration néant ne prouve pas à elle seule l’absence de mouvements. Une absence exhaustive doit être confirmée et justifiée, et rester cohérente avec les crédits déjà utilisés. Les retenues déjà utilisées ne sont jamais oubliées pour obtenir un zéro.

## Sources modifiées et exports

Modifier puis conserver les crédits dans une nouvelle version signale que le contrôle acomptes est ancien. Il reste figé ; relire les justificatifs et conserver une nouvelle qualification acomptes pour actualiser le rapprochement.

Le dossier ZIP contient `acomptes_is_documentaires.json`, le snapshot complet, les balances, PDF, Excel et le manifeste SHA256. Dans Excel, vérifier Origine acomptes IS, Contrôle acomptes IS, AP-PROFIL, AP-LIGNES, Rapprochement retenues IS et Échéancier acomptes IS. Le logo valide actuel est intégré aux rendus PDF/Excel. Les références commençant par = restent du texte. Télécharger ne crée aucune écriture ou version.

## Recette complémentaire à renseigner

Les cas humains restent Non testé. Les résultats automatisés ne remplacent pas la recette sur l’environnement cible ou l’ouverture réelle dans Word/Excel.

| ID | Actions détaillées | Résultat attendu et preuve | Statut |
|---|---|---|---|
|AP751-01|Saisir le profil et les deux mouvements exactement comme ci-dessus ; conserver puis rouvrir.|Nouvelle version sans F5 ; versements 1000, excédent 100, retenues 150, proposé 1250 MAD. Capturer rapprochement et quatre échéances 3800/4950/5000/5000.|Non testé|
|AP751-02|Modifier le versement de la ligne 1 sans conserver ; télécharger PDF/Excel/ZIP.|Contrôle et exports restent 1250 MAD ; brouillon non promu. Conserver le ZIP et la référence de version.|Non testé|
|AP751-03|Inverser uniquement les références CR749-A/B entre les deux mouvements puis conserver ; comparer les deux rapprochements.|Total retenues 150 et écart global 0, mais justificatifs individuels incohérents : aucun total imputable proposé. Capture et nouvelle version.|Non testé|
|AP751-04|Depuis une copie du jeu fictif, tenter NaN puis excédent 101 sur la ligne 1 ; tenter un doublon AP751-A.|Refus lisible sans nouvelle version ; brouillon conservé. Capturer les refus et le compteur de versions.|Non testé|
|AP751-05|Dans la rubrique crédits, changer seulement le total de CR749-A300 en 301 puis conserver ; rouvrir les acomptes, relire et conserver une nouvelle qualification.|Avertissement de source modifiée ; ancien contrôle 1250 figé ; après nouvelle qualification,1250 et rapprochements actualisés. Anciennes versions intactes.|Non testé|
|AP751-06|Laisser la référence annuelle vide dans le profil, conserver avec les deux mouvements valides.|Total justifié 1250 MAD conservé, calendrier indisponible ; aucune échéance nulle inventée. Capture du contrôle.|Non testé|
|AP751-07|Déclarer seulement AP-LIGNES néant avec justification, sans confirmer une absence exhaustive et en conservant les crédits déjà utilisés 150.|Aucun zéro ni total imputable proposé ; incohérence visible. Capturer profil et rapprochement des crédits.|Non testé|
|AP751-08|Avec rôles comptable puis lecture sur écran 390 px, consulter et télécharger les pièces ; comparer le logo et les montants aux contrôles.|Comptable peut conserver ; lecture ne peut pas modifier ; pas de débordement global. Logo valide et montants cohérents dans PDF/Excel/ZIP.|Non testé|

## Limites et suite

Aucune authentification de quittance ou qualification fiscale réelle n’est automatisée. Les régimes spécifiques, exercices courts et excédents anciens restent à qualifier pour leur calendrier. La liquidation externe conditionnelle est l’étape suivante ; aucun solde définitif n’est calculé ici. Les réserves historiques FEC/ETIC restent visibles. RH/paie et le point 6 humain restent différés.
