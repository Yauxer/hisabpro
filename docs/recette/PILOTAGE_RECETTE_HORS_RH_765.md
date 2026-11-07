# HISABPRO — PILOTER LA RECETTE HORS RH/PAIE

Version 1 du 24 octobre 2026. Lot 765. Point d’entrée et suivi des recettes existantes, sans nouvelle règle comptable ou fiscale.

## 1. Choisir le bon parcours

Ce dossier regroupe 272 cas de sept classeurs existants : 218 du scénario principal et 54 des compléments 749–761. Ce ne sont pas de nouveaux cas. État initial : 262 Non testé, 10 Bloqué, aucun succès utilisateur prérempli. Les autres annexes restent disponibles dans [l’index des recettes](INDEX_RECETTES_HISABPRO.md) ; elles ne sont pas toutes recopiées ici.

Pour une démonstration commerciale/comptable générale, choisir PRINCIPAL. Pour vérifier les derniers formulaires du mode Liasse seule, choisir F755, puis une copie indépendante pour TIERS759 et TP761. CR749/AP751/LIQ753 servent à isoler un composant ; leur jeu ne remplace pas le scénario annuel 755.

Ouvrir d’abord [le suivi unique Excel](PILOTAGE_RECETTE_HORS_RH_765.xlsx), feuille Campagnes, puis le guide de la campagne retenue. Lire ce guide avant la première saisie : les données exactes, prérequis et variantes restent ceux de la source. Les liens sont relatifs : installer ce différentiel dans le dépôt existant, conserver l’arborescence docs/recette et ouvrir les fichiers extraits du ZIP. Les guides et jeux antérieurs doivent déjà être présents.

## 2. Préparer la recette séparée

Utiliser une installation de recette avec sociétés fictives ; aucune opération décrite ici ne doit être lancée sur les données comptables réelles. Le point 6 et la recette humaine restent différés jusqu’à votre décision ; ce livrable prépare leur exécution, il ne l’autorise pas à votre place.

Faire préparer les services et le schéma par la personne technique selon [Exploitation](../EXPLOITATION_HISABPRO.md). Ne pas exécuter tous les SQL au hasard sur une base existante. La chaîne 104 et le stockage des pièces doivent être cohérents ; les procédures distinguent installation vierge et mise à jour. Aucun changement de base n’est appliqué par ce générateur.

Avant chaque parcours, noter dans une copie du suivi : date, version installée, société fictive, exercice, rôle et navigateur. Les variantes négatives se font sur les copies prévues, sans altérer le scénario principal. Ne pas changer l’horloge du poste pour simuler une échéance.

## 3. Parcours principal : entreprise complète

Ouvrir [le cahier principal PDF](CAHIER_RECETTE_HISABPRO.pdf) et conserver [le jeu chiffré principal](jeu_donnees_recette.json) avec ses pièces fictives. Le scénario utilise ATLAS RECETTE HISABPRO 2025, puis l’ouverture 2026. Suivre les 218 cas dans l’onglet Ordre de passage, filtré sur PRINCIPAL ; l’ordre chronologique prime sur l’ordre des onglets de domaine.

Le parcours couvre création et paramètres, tiers/articles, cycle commercial, paiements/lettrage, banque, stock, immobilisations, fiscalité, inventaire/clôture, états et exports, permissions et exploitation. Les cas Bloqué sont des limites explicites, pas des manipulations à deviner. Le détail des montants et écritures attendues est conservé dans chaque ligne et dans les fichiers sources.

Repères du scénario principal déjà calculés dans sa source : résultat avant IS 129 830, bénéfice fiscal 133 830, IS 2025 de 23 420,25, crédit documentaire 200, solde 23 220,25 ; bilan 337 010, banque 287 730, stock 6 600, CAF 112 709,75. Ces attentes pédagogiques ne sont ni les chiffres du dossier 755 ni des données réelles.

## 4. Dernières préparations annuelles et annexes internes

| Campagne | Guide à ouvrir | Repère indépendant | Frontière |
|---|---|---|---|
|F755|[Recette annuelle755](CAHIER_RECETTE_FISCALE_755.docx)|Solde proposé 3 650|Société neuve, balancesN/N-1, aucun Journal|
|TIERS759|[Guide tiers759](MODE_EMPLOI_TIERS759.docx)|1 400 comptabilisé / 740 soumis / 37 retenu|Jeu documentaire distinct des honoraires 21 500 de 755|
|TP761|[Guide TP761](MODE_EMPLOI_TP761.docx)|Brut 7 200 / avis 7 400 / écart −200|Bases/classes déclarées, aucun impôt dû confirmé|
|LIQ753|[Guide composant753](MODE_EMPLOI_LIQUIDATION_753.docx)|3 000 − 325 − 1 250 = 1 425|Variante indépendante, à ne pas additionner à 755|

755 contient 14 cas depuis une société neuve et les balances 2025/2026, jusqu’aux formulaires et exports. Utiliser [les données755](DONNEES_FISCALES755.json), [balanceN](BALANCE_FICTIVE_FISCALE755_N.csv), [balanceN-1](BALANCE_FICTIVE_FISCALE755_N1.csv), [logo](LOGO_FICTIF755.png) et [pièces fictives](JUSTIFICATIFS_FICTIFS755.pdf). Bénéfice 120 000, IS 24 000, crédits disponibles 350, acomptes 20 000, solde proposé 3 650, CSS 0 séparée. Ne pas saisir au Journal les opérations qui expliquent ces balances.

759 contient 8 cas, données et rubriques champ par champ dans son guide ; [jeu tiers](DONNEES_TIERS759.json).761 contient 8 cas, [jeu TP](DONNEES_TP761.json). Un zéro, une donnée inconnue et une absence d’applicabilité sont trois situations différentes. Aucun modèle administratif ou paiement ne se déduit des sommes documentaires.

Pour isoler les composants : [crédits749](MODE_EMPLOI_CREDITS_IS_749.docx), [acomptes751](MODE_EMPLOI_ACOMPTES_IS_751.docx), [proposition753](MODE_EMPLOI_LIQUIDATION_753.docx),8 cas chacun. Choisir une copie dédiée. Les oracles 1 425 et 3 650 répondent à des jeux différents et ne doivent jamais être additionnés.

## 5. Renseigner le suivi unique

Dans Ordre de passage, filtrer la campagne puis cliquer Lire la fiche. La feuille Fiches de lecture présente les champs verticalement : les longs textes sont répartis sans perte sur plusieurs lignes. Elle sert à la lecture ; les résultats se saisissent une seule fois dans l’onglet de domaine, via Renseigner le cas ou Renseigner le suivi. La colonne M contient le statut. N reçoit le résultat réel, O l’anomalie, R le chemin ou la référence de preuve, S les observations réelles. Ces cellules de saisie sont jaunes. P conserve les observations de la source ; ne pas effacer ces limites initiales.

Réaliser l’action puis comparer au résultat attendu et aux écritures attendues. Pour Réussi, conserver une preuve quand elle est demandée ; pour Échoué ou Bloqué, décrire le constat et la dépendance. Arrêter les étapes dépendantes d’une anomalie comptable et poursuivre uniquement les branches indépendantes prévues. Ne jamais modifier une écriture définitive pour faire correspondre un résultat.

La Synthèse recalcule les statuts des onglets de domaine. Son taux d’exécution compte Réussi + Échoué et exclut les Bloqué ; il ne signifie donc pas que la recette est réussie. Les formules doivent être recalculées à l’ouverture d’Excel ; le générateur ne prétend pas les avoir exécutées dans Office natif. Les feuilles sources et les anciens suivis ne sont pas synchronisés : renseigner cette copie unique, pas deux classeurs en parallèle.

Les colonnesT/U/V gardent le fichier, l’onglet et la ligne source ; W ouvre le guide. La feuille Campagnes conserve les empreintesSHA-256 des sept fichiers lus. Ces empreintes décrivent l’état initial, pas les modifications que vous consignerez ensuite. Le générateur refuse d’écraser ses sorties existantes : conserver une copie de travail par campagne et archiver les preuves à côté.

## 6. Blocages et verdict

Les 10 cas Bloqué du principal restent bloqués. Certaines préparations internes ont évolué depuis sa rédaction, mais cela ne valide pas leur variante déclarative officielle. Les compléments 759/761 testent des préparations disponibles ; ils ne débloquent pas les déclarations administratives complètes 09F/09G. Le référentiel 09B, les modèles et l’EDI exigent les [documents officiels listés](../audit/DEPENDANCES_OFFICIELLES_20261023_763.md).

Les justificatifs historiques manquants FEC/ETIC ne sont pas inventés. Les autres annexes de l’index sont des scénarios indépendants : ne pas les ajouter automatiquement au principal. RH/paie restent différées et aucun cas de leur annexe n’est importé dans ce suivi.

Distinguer quatre décisions : développement global partiel ; tests automatisés validés seulement sur les périmètres des rapports ; recette utilisateur à effectuer ; mise en production non validée. Une archive interne ou un export local ne prouve pas un dépôt accepté. Le partenaire doit décider du verdict à partir de résultats et preuves réels, pas du nombre de tests automatiques.
