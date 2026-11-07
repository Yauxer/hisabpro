# Reprise du lot3B — sources et choix techniques à vérifier

État du 28/10/2026. **Préparation du prochain développement, pas un moteur livré.** Les lots889,891 et 893 sont livrés ; les cotisations/IR/net restent non calculés dans les nouvelles campagnes. Aucun taux réel n'est activé par ce document.

## Sources primaires réellement consultées

| Source | Accès obtenu pendant cette exécution | Usage possible et limite |
|---|---|---|
| [CGI2026 officiel, MEF/DGI](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf) | Recherche primaire indexée, dont revenus salariaux ; ouverture directe en timeout | Références fiscales identifiées ; ne pas prétendre à une lecture intégrale ni à une validation des cas mensuels et particuliers. |
| [Arrêté1314-25, version consolidée sur Adala](https://adala.justice.gov.ma/api/uploads/2026/01/19/%D9%82%D8%B1%D8%A7%D8%B1%20%D9%84%D9%88%D8%B2%D9%8A%D8%B1%D8%A9%20%D8%A7%D9%84%D8%A7%D9%82%D8%AA%D8%B5%D8%A7%D8%AF%20%D9%88%D8%A7%D9%84%D9%85%D8%A7%D9%84%D9%8A%D8%A9%20%D8%B1%D9%82%D9%85%201314.25%20%20%D8%A7%D9%84%D9%85%D8%AA%D8%B9%D9%84%D9%82%20%D8%A8%D8%AA%D8%AD%D8%AF%D9%8A%D8%AF%20%D8%A7%D9%84%D8%AA%D8%B9%D9%88%D9%8A%D8%B6%D8%A7%D8%AA-1768818476331.pdf) | PDF officiel ouvert, 17 pages ; version mise à jour au 11/12/2025, mention du rectificatif BO7464 | Exclusions d'assiette sociale à qualifier rubrique par rubrique avec conditions et justificatifs ; aucun plafond détaillé automatiquement activé. |
| [Décret2-01-2723 publié par l'ACAPS](https://www.acaps.ma/sites/default/files/publication_documents/decret_ndeg_2-01-2723.pdf) | PDF officiel ouvert, 1 page, pagination imprimée71 ; texte citant des modifications jusqu'en 2008 | Source nouvelle obtenue ici pour les branches et leur plafond. Elle ne prouve pas, à elle seule, l'exhaustivité des modifications jusqu'en 2026. |
| [Fiche synthétique CNSS, ACAPS](https://www.acaps.ma/sites/default/files/fiche_synthetique_cnss.pdf) | PDF officiel ouvert, 3 pages, tableau des cotisations page2 | Point de comparaison institutionnel ; absence de millésime2026 et de dates d'effet complètes. Ne pas transformer un partage2/3–1/3 en parts arrondies légalement validées. |
| [AMO, ACAPS](https://www.acaps.ma/fr/grand-public/sante/couverture-medicale-de-base-amo) | Page officielle ouverte, section Secteur privé | Donne une présentation des contributions et distingue les populations. Vérifier le décret applicable et les particularités avant activation ; la page ne constitue pas une validation de tout dossier salarié. |
| [BO7054 du06/01/2022, SGG](https://www.sgg.gov.ma/BO/FR/2873/2022/BO_7054_Fr.pdf) | Passage officiel indexé, page imprimée48, rapport sur l'IPE | Document institutionnel utile sur le financement et les pistes de réforme ; ne pas confondre un rapport avec le texte normatif d'entrée en vigueur. |
| [BO7501 du20/04/2026, SGG](https://www.sgg.gov.ma/BO/AR/3111/2026/BO_7501_Ar.pdf) | Passage officiel indexé, page imprimée2263, analyse de la couverture AMO et références | Référence institutionnelle récente, mais ce passage n'est pas à lui seul un barème normatif à importer. |
| CNSS :taux et recueil des textes | Deux ouvertures directes ont échoué via l'outil web | Aucun taux issu d'une page privée n'est repris pour remplacer le document officiel indisponible. |

L'URL Adala doit être contrôlée à la reprise :le fichier ouvert provient bien du portail officiel ; le titre et la version consolidée, plutôt qu'une infographie, sont la référence de lecture. Aucun document intégral n'est copié ici et aucune date de crawl n'est interprétée comme date d'effet.

## Point précis à résoudre sur les branches

Le décret ACAPS obtenu présente le court terme à1%, tandis que la fiche institutionnelle synthétique présente1,57%. Un rapport officiel sur l'IPE mentionne0,57%. **L'égalité arithmétique1+0,57=1,57 est une piste de rapprochement, pas une preuve d'inclusion ni de validité pour 2026.** Il faut retrouver les textes normatifs et leurs modifications, documenter la composition des branches et éviter de compter deux fois un composant.

Le moteur doit distinguer les branches et payeurs, les assiettes et plafonds propres, ainsi que les régimes particuliers réellement confirmés. Une ligne globale « CNSS » sans composition vérifiable ne suffit pas pour qualifier des taux.

## Code existant inspecté, sans modification

- `hisabpro-backend/services/paie_service.py` contient la simulation fixe historique, les primitives décimales `nombre`/`montant`, la vérification de cinq codes et le calcul combiné social/IR. Cette voie garde son statut de simulation et ses avertissements. Elle calcule les branches sur une base commune et reçoit des plafonds annuels divisés par 12 ; ce contrat ne doit pas être appliqué silencieusement au nouveau modèle par branche et période.
- `hisabpro-backend/services/paie_referentiel_service.py` consigne des preuves annuelles et signale un référentiel périmé ; il ne qualifie pas une paie définitive et ne modifie pas de taux. Réutiliser les conventions de provenance/empreinte, préserver les anciennes versions.
- `paie_catalogue_*` conserve les règles par régime, leurs conditions/statuts et l'habilitation réglementaire dédiée. Les règles complexes de pourcentage, SMIG et cumul ne sont pas encore calculées.
- `paie_variables_*` conserve les montants, sources et versions approuvées. `paie_campagnes_*` conserve le brut simulé sans modifier les variables. Ces sources doivent être référencées par les futures simulations sociales.

Les taux historiques ne doivent pas être réécrits pour faire correspondre un exemple. Une ancienne valeur flottante ne devient pas un taux exact attesté simplement parce qu'elle peut être convertie en Decimal.

## Prochaine sous-étape exécutable :3B.1

1. Relire AGENTS, le master, le journal et les empreintes502 du candidat893 ; vérifier les ZIPs avant de reprendre. Aucune étape889/891/893 à réappliquer.
2. Compléter les preuves normatives des branches et dates d'effet ; conserver À vérifier tant que le champ d'application ou la composition n'est pas prouvé. L'indisponibilité d'un texte ne bloque pas les autres développements indépendants.
3. Concevoir puis livrer un référentiel social versionné **par société**, branche, payeur et période, avec taux décimaux exacts, plafond et unité explicites, assiette propre, composition, texte/article/URL/preuve, date et acteur de qualification. Préparation et approbation réglementaire restent distinctes ; aucun taux ni droit attribué implicitement.
4. Rendre ce référentiel accessible dans **04 · Charges sociales**, avec recherche, formulaires et historique. Ne pas ouvrir la rubrique comme une simple maquette. Les noms de tables et endpoints restent à vérifier avant leur création.
5. Produire un calcul social séparé de l'IR, sur snapshot du brut et sources courantes qualifiées. Appliquer les exclusions de rubrique avant le plafond propre de la branche. Une assiette, un taux ou une éligibilité inconnus restent bloquants ; aucun0 de secours.
6. Conserver les résultats par branche et payeur, les raisons de blocage et les empreintes. Le net à payer reste inconnu tant que l'IR et les autres éléments requis ne sont pas calculés. Ne pas présenter un net avant IR comme un net bancaire.
7. Ajouter les tests purs, API/SQL PostgreSQL natif, concurrence, multi-société, masques, révocation, Edge desktop/mobile et migration/restauration. Livrer un différentiel et actualiser la matrice avant 3B.2/3C.

## Dossier de référence purement fictif à écrire en tests

**Non exécuté :il s'agit des futurs cas3B, aucune fonctionnalité ci-dessous n'est annoncée livrée.** Les chiffres sont des hypothèses mathématiques, sans valeur réglementaire.

Base9000,10 et gain800,01 donnent un brut9800,11. Si l'hypothèse fictive exclut500 du gain pour IR, 300 pour CNSS et 0 pour AMO :assiettes9300,11 /9500,11 /9800,11. Branche fictiveB1 :plafond6000, taux salarié1%, employeur2% →60,00/120,00. Branche fictiveB2 sur 9800,11 :3%/4% →294,00/392,00 après arrondi documenté. Totaux fictifs354,00 et 512,00 ; **net à payer toujours inconnu faute d'IR calculé**.

Cas à écrire :frontières de plafond, plusieurs rubriques soumises/exclues différemment, cumul incomplet, périodes qui se chevauchent, source obsolète, branche en double, composition ambiguë, éligibilité inconnue, révocation de l'expert, concurrence et anciennes simulations stables après un nouveau taux. Ne pas remplacer une source manquante par un taux d'un site privé.

## Limite de cette consolidation

Ce document ne crée aucune migration116, aucune rubrique04 fonctionnelle et aucun moteur social/fiscal supplémentaire. Le produit reste exactement celui qualifié en 893. La suite est préparée pour une reprise directe, sans nouveau tour de confirmation technique.
