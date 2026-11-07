# HisabPro — par où commencer la recette ?

## Point d’entrée actuel — 24 octobre 2026

Pour préparer la recette avec votre partenaire, ouvrir [le pilotage Word](PILOTAGE_RECETTE_HORS_RH_765.docx) ou [PDF](PILOTAGE_RECETTE_HORS_RH_765.pdf), puis [le suivi Excel unique](PILOTAGE_RECETTE_HORS_RH_765.xlsx). Il regroupe **272 cas existants** : 218 du cahier principal et 54 des compléments 749–761. État initial : **262 Non testé, 10 Bloqué**, aucun résultat humain prévalidé. Les autres annexes demeurent distinctes et ne sont pas toutes recopiées dans ce suivi.

Choisir une seule campagne et sa société fictive avant de saisir :

| Besoin | Campagne | Guide | Frontière du jeu |
|---|---|---|---|
| Cycle général, comptabilité et clôture | PRINCIPAL, 218 cas | [Cahier principal](CAHIER_RECETTE_HISABPRO.pdf) | ATLAS RECETTE 2025 ; ouverture 2026 ; suivre l’ordre de passage |
| Préparation annuelle depuis balances N/N-1 | F755, 14 cas | [Word755](CAHIER_RECETTE_FISCALE_755.docx) | Société neuve ; solde proposé 3 650 ; aucune écriture au Journal |
| Rémunérations des tiers | TIERS759, 8 cas | [Word759](MODE_EMPLOI_TIERS759.docx) | Jeu documentaire distinct ; 1 400 / 740 / 37 |
| Taxe professionnelle | TP761, 8 cas | [Word761](MODE_EMPLOI_TP761.docx) | Brut 7 200 / avis 7 400 / écart −200 ; pas un impôt dû confirmé |
| Composants à isoler | CR749/AP751/LIQ753, 24 cas | [Crédits](MODE_EMPLOI_CREDITS_IS_749.docx), [acomptes](MODE_EMPLOI_ACOMPTES_IS_751.docx), [proposition](MODE_EMPLOI_LIQUIDATION_753.docx) | Variantes dédiées ; l’oracle 1 425 de 753 ne s’ajoute pas aux 3 650 de 755 |

Dans le suivi unique, choisir l’onglet Ordre de passage et filtrer la campagne. Cliquer Lire la fiche pour la lecture verticale, puis Renseigner le cas pour saisir M statut, N résultat réel, O anomalie, R preuve et S observations réelles. Les colonnes de provenance permettent de retrouver exactement chaque ligne source. Ne pas renseigner parallèlement l’ancien classeur : aucune synchronisation automatique. Le guide détaille la préparation et les critères de verdict.

RH/paie et point 6 restent différés. Les anciennes références RH ci-dessous sont historiques, hors de ce parcours. Les documents765 préparent la recette humaine sans la lancer. Les cas déclaratifs bloqués du principal restent bloqués même lorsqu’une préparation interne existe désormais. Voir les [documents officiels manquants](../audit/DEPENDANCES_OFFICIELLES_20261023_763.md) et les [procédures techniques](../EXPLOITATION_HISABPRO.md).

Les fichiers765 sont un complément : installer le ZIP différentiel dans le dépôt existant, conserver l’arborescence et extraire les fichiers avant ouverture. Les anciens guides/données référencés doivent être présents. Les sections suivantes conservent l’orientation historique du 14 octobre ; le point d’entrée courant est celui-ci.

## Repères historiques du 14 octobre 2026


Point d’entrée du 14 octobre 2026. Les documents ci-dessous sont présents dans le dépôt. Cette page les relie ; elle ne remplace aucun jeu de données ni ne préremplit des résultats. Le point 6 reste en attente du retour utilisateur.

## Pour présenter les avancées à deux

1. Ouvrir le [mode d’emploi Word](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx), ou sa [version PDF](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.pdf). Le guide explique les actions et contrôles de chaque fiche. La démonstration nécessite une installation de recette séparée, avec données fictives.
2. Pour la préparation annuelle des ventes, utiliser ensuite le [complément Word](../guide/GUIDE_PREPARATION_VENTES.docx), ou son [PDF](../guide/GUIDE_PREPARATION_VENTES.pdf), et le [classeur de suivi ventes](ANNEXE_RECETTE_VENTES.xlsx). L’écran se trouve dans Comptabilité → Liasse fiscale → Préparation ventes. Les boutons CSV, Excel etPDF y sont décrits.
3. Consigner le résultat réellement observé et les captures lorsque la recette sera décidée. Une réussite automatisée n’est pas une validation de votre partenaire.

## Pour une recette annuelle complète

Le [cahier PDF](CAHIER_RECETTE_HISABPRO.pdf), le [classeur Excel](CAHIER_RECETTE_HISABPRO.xlsx) et le [mode d’emploi du scénario](README.md) forment le parcours principal : 218 cas, exercice 2025 puis ouverture 2026. Le classeur reste à 208 Non testé et 10 Bloqué ; les cas bloqués ne doivent pas être présentés comme exécutables. Utiliser le [jeu chiffré](jeu_donnees_recette.json), les justificatifs fictifs et les fichiers d’entrée indiqués dans le mode d’emploi.

Pour chaque test, saisir le statut, le résultat réel, l’anomalie éventuelle et la preuve obtenue. Conserver les résultats attendus pour comparaison. En cas d’échec, documenter etarrêter le parcours dépendant ; ne jamais modifier une écriture définitive pour obtenir le résultat attendu.

## Annexes à choisir selon le module

| Périmètre | Consignes | Suivi Excel |
|---|---|---|
| Cycle commercial | [Annexe](ANNEXE_RECETTE_COMMERCIALE.md) | [Classeur](ANNEXE_RECETTE_COMMERCIALE.xlsx) |
| Achats etréceptions partielles | [Annexe](ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.md) | [Classeur](ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.xlsx) |
| Bilan détaillé | [Annexe](ANNEXE_RECETTE_BILAN_DETAILLE.md) | [Classeur](ANNEXE_RECETTE_BILAN_DETAILLE.xlsx) |
| Corrections du 9 octobre | [Annexe](ANNEXE_RECETTE_CORRECTIONS_20261009.md) | [Classeur](ANNEXE_RECETTE_CORRECTIONS_20261009.xlsx) |
| Inventaire | [Annexe](ANNEXE_RECETTE_INVENTAIRE_20261010.md) | [Classeur](ANNEXE_RECETTE_INVENTAIRE_20261010.xlsx) |
| GRH et limites de paie | [PDF](ANNEXE_RECETTE_PAIE_GRH.pdf) | [Classeur](ANNEXE_RECETTE_PAIE_GRH.xlsx) |
| RAS : estimation | [Annexe](ANNEXE_RECETTE_RAS_ESTIMATION_20261009.md) | [Classeur](ANNEXE_RECETTE_RAS_ESTIMATION_20261009.xlsx) |
| RAS : attestation etcapture | [Annexe](ANNEXE_RECETTE_RAS_CAPTURE_20261010.md) | [Classeur](ANNEXE_RECETTE_RAS_CAPTURE_20261010.xlsx) |
| Rapprochement ventilé | [Guide, fiche dédiée](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.md) | [Classeur](ANNEXE_RECETTE_RAPPROCHEMENT_VENTILATIONS.xlsx) |
| Propositions etfrais bancaires | [Guide, fiche dédiée](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.md) | [Classeur](ANNEXE_RECETTE_PROPOSITIONS_FRAIS.xlsx) |
| Préparation des ventes | [Guide](../guide/GUIDE_PREPARATION_VENTES.md) | [Classeur](ANNEXE_RECETTE_VENTES.xlsx) |

Ces annexes comportent des scénarios distincts. Lire leurs prérequis et créer les sociétés/copies fictives indiquées ; ne pas cumuler leurs opérations avec le scénario principal. Exemple : les ventes du guide complémentaire utilisent leur propre société 2026, avec totaux documentaires 270 HT/54 TVA/324 TTC. La variante avec une pièce supplémentaire donne 370/74/444 et doit rester séparée. Les 7 cas de ce classeur sont Non testé.

## Limites etrésultats techniques

Les préparations etarchives internes ne sont pas un dépôt DGI. La paie réglementaire complète, les annexes déclaratives encore absentes et le schéma EDI applicable restent à finaliser. Consulter la [matrice actuelle](../audit/MATRICE_COUVERTURE_HISABPRO.md), le [registre des anomalies](../audit/REGISTRE_ANOMALIES_HISABPRO.md) et les [limites du scénario annuel](REGISTRE_LIMITES_RECETTE.md). Le cas annuel 09 Eofficiel reste bloqué ; le guide ventes couvre une préparation interne distincte, désormais disponible.

Les résultats automatisés sont dans le [rapport de session](../audit/RAPPORT_SESSION_20261012.md) et le journalCODEX_PROGRESS.md àla racine. Ils n’attribuent aucun statut « Réussi » aux classeurs utilisateur. Les procédures techniques se trouvent dans [Exploitation](../EXPLOITATION_HISABPRO.md). Aucun usage d’une base réelle n’est nécessaire àces recettes isolées.

Développement global : partiel. Tests automatisés : voir les périmètres réellement exécutés. Recette utilisateur : à effectuer après votre retour. Production : non validée. Aucune certification officielle annoncée.
