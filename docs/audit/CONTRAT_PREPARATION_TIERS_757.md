# Contrat de préparation interne — rémunérations allouées aux tiers757

23 octobre2026. Cadrage de LIA-09F ; aucune fonctionnalité déclarative n’est livrée par ce document. L’audit640 du19octobre est conservé et n’est pas refait. La nouvelle valeur de ce lot est le rapprochement explicite avec les modèles et captures actuels, ainsi qu’une grille vierge de collecte.

## Texte et limite administrative

Le CGI2026 DGI, article151, pages imprimées283–284 (indicesPDF281–282), distingue identité des bénéficiaires, catégories de sommes comptabilisées et éléments soumis à retenue. Les états particuliers CPU/autoentrepreneurs et locations ont leurs propres modèles administratifs. Une estimation RAS ou une liste de règlements ne remplace donc pas la déclaration annuelle. Le texte a été relu sur l’exemplaire officiel déjà obtenu, SHA256 fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1.

[CGI intégral publié par le CRI](https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf), [notice](https://casainvest.ma/fr/node/719), [audit640 conservé](SOURCES_ANNEXE151_20261019.md). L’accès direct au PDF MEF a de nouveau rencontré un timeout le23octobre ; cette indisponibilité ne prouve pas l’absence du modèle. Aucun modèle applicable ou schéma EDI151 nouveau n’a été obtenu, et aucun n’est inventé. Les sites commerciaux repérés ne sont pas des preuves normatives et aucun fichier de leur outil n’est utilisé.

## Correspondance constatée dans le dépôt

| Domaine | Donnée à examiner | Source actuelle | Limite |
|---|---|---|---|
| Identité | Nom ou raison sociale | Tiers.nom | existant, à confirmer pour le bénéficiaire et la période |
| Identité | Adresse | Tiers.adresse | existant, peut être vide ou avoir changé |
| Identité | Identification fiscale | Tiers.identifiant_fiscal | existant, ne prouve pas le régime ni une identification TP |
| Identité | Activité/profession | aucun champ dédié Tiers | à compléter explicitement |
| Identité | Identification taxe professionnelle | aucun champ dédié Tiers | à compléter selon le cas ; pas RC/ICE substitué |
| Identité | CNSS du bénéficiaire | aucun champ dédié Tiers | à qualifier sur pièce ; ne pas utiliser CNSS société ou salarié |
| Régime | CPU / autoentrepreneur / autre | Tiers.categorie_fiscale | autoentrepreneur présent, CPU non distingué ; catégorie ne prouve pas le régime applicable |
| Comptabilité | Rattachement tiers | LigneEcriture.tiers_id | existant ; lien exact, historique manquant reste à qualifier |
| Comptabilité | Auxiliaire figé | LigneEcriture.libelle_auxiliaire_snapshot | existant ; identité fiscale complète non figée ici |
| Comptabilité | Montants comptabilisés par catégorie | Ecriture/LigneEcriture | montants présents ; catégorie151 non déterminable par compte seul |
| RAS | Capture et annulation | services/ras_reglement_service.py | registre existant SQL séparé du metadata ; ne pas le recréer |
| RAS | Estimation de facture | Facture.ras_taux | n’est ni une retenue effective ni une annexe151 complète |
| RAS | Date fiscale et montant soumis | qualification documentaire explicite | ne pas remplacer par date facture, échéance ou écriture bancaire |
| Annexe | Locations et CPU/AE | modèles administratifs applicables | états particuliers à obtenir ; ne pas réutiliser article154 non-résidents |

La CNSS mentionnée ici appartient au bénéficiaire tiers ; cela ne reprend pas la paie/GRH différée. Les montants créditables reçus d’un client dans749/755 ne doivent pas être recopiés comme rémunérations versées à un fournisseur. Le sens achat/vente et le bénéficiaire effectif doivent rester explicites.

## Lot d’implémentation proposé, encore à développer

Créer une préparation documentaire annuelle versionnée, distincte d’un dépôt officiel, dans l’architecture de sources/snapshots déjà utilisée. Le premier lot pourra conserver des identités et références fournies explicitement et des montants par catégorie, avec provenance et auteur ; il ne calculera pas de taux RAS et ne générera aucun Journal. La forme finale des données de dépôt reste réservée au modèle officiel applicable.

Pour le mode Liasse seule, les comptes importés n’identifient pas un bénéficiaire : saisie sourcée ou import explicite requis. Pour le mode comptable, proposer seulement des sources reliées exactement à un tiers, signaler les avoirs/contrepassations et conserver la décision humaine ; aucun classement juridique par simple compte6136 ou taux de facture. Ne pas agréger une capture annulée avec sa capture initiale. Les données historiques manquantes restent visibles.

Une donnée inconnue demeure vide/null. Un zéro doit être explicitement justifié ; il ne remplace pas une absence de pièce. Le changement ultérieur de fiche tiers ou d’un taux n’écrase pas l’identité/source conservée. Une préparation incomplète reste à compléter, même si ses totaux concordent. Les identifiants nécessaires à la déclaration ne deviennent pas obligatoires pour toute création de tiers dans l’application.

Dépendances d’une livraison : autorisations société/exercice et rôles ; champs et références validés ; invariants monétaires finis/2décimales ; exports de préparation logo/version/manifeste ; sources immuables ; sauvegarde/restauration ; refus de toute présentation prêt à déposer. Si une persistance dédiée devient nécessaire, migration additive distincte avec contrôle du schéma104 existant, sans toucher aux migrations passées. Aucune migration n’est ajoutée dans757.

## Recette technique requise pour ce futur lot

1. Deux sociétés et rôles admin/comptable/lecture, accès croisé refusé.
2. Identités incomplètes conservées comme inconnues ; aucun champ fiscal inventé.
3. Sommes comptabilisées, sommes soumises et retenues distinguées ; date fiscale indépendante de facture/échéance.
4. Source exacte, doublon de source, avoir, capture annulée et contrepassation, sans suppression comptable.
5. Zéro explicite, vide, NaN, infini, arrondi interdit, dépassement et montant négatif à qualifier selon la nature, sans règle fiscale improvisée.
6. Nouvelle version avec identité figée ; ancienne version/octets conservés, aucune réécriture du tiers ou du Journal.
7. Export PDF/Excel/ZIP avec logo et sources, restauration froide, témoins comptables inchangés.
8. Préparation incomplète ou modèle administratif absent : aucun statut de dépôt validé ni fichier EDI inventé.

Ces cas décrivent le développement futur et ne sont pas présentés comme exécutables dans l’interface actuelle. Leur statut est Bloqué — fonctionnalité non développée, pas une réussite automatisée.

## Grille de collecte fournie

[GRILLE_PREPARATION_TIERS757.xlsx](../recette/GRILLE_PREPARATION_TIERS757.xlsx) est une feuille de travail hors application :40lignes volontairement vierges pour préparer pièces, identités, catégories et montants. Elle ne s’importe pas dans HisabPro et n’est pas un formulaire DGI. Aucun montant ni bénéficiaire réel ou fictif n’y est prérempli. Les catégories et champs seront rapprochés du modèle administratif avant développement ; la grille ne prescrit pas de nouvelles obligations.

## Validation de ce lot

Contrôle AST du modèle Tiers et LigneEcriture, existence des services et empreintes des cinq sources vérifiés localement. Excel ouvert par openpyxl, quatre feuilles et40lignes de collecte vierges contrôlés, huit cas futurs Bloqué. Les1223sources/scripts de755 et117fichiers protégés restent inchangés. Aucun test API/PG/navigateur supplémentaire n’est revendiqué ; les réussites755 restent celles du lot755. Aucun build produit nécessaire : aucun code produit modifié.

Prochaine étape : développer le premier lot interne sourcé ci-dessus, sans attendre de pouvoir inventer un format officiel. En parallèle, obtenir depuis la DGI le modèle151/annexes applicables, leur version et date d’effet ; ne pas refaire les recherches640/757 sans nouvel élément. LIA-09F reste absent ; aucune déclaration complète n’est livrée. Les autres réserves FEC/ETIC/EDI et RH/paie/point6 demeurent.
