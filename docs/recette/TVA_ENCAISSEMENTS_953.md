# Recette annuelle de la TVA sur encaissements — lot 953

Ce complément accompagne la fiche **HP-FIS-033**. Il s'utilise avec le cahier principal et une **nouvelle société fictive dans une base isolée**. Ne pas changer le régime des anciennes factures validées d'une société existante pour reproduire ce scénario.

Les données exactes de tous les formulaires, références, tiers, articles et écritures figurent dans le [classeur de saisie](JEU_RECETTE_ENCAISSEMENTS_953.xlsx) et dans [DONNEES_ENCAISSEMENTS_953.json](DONNEES_ENCAISSEMENTS_953.json). Le classeur comporte des colonnes vierges pour vos résultats, anomalies et preuves. Le [jeu principal](jeu_donnees_recette.json), en régime des débits, est conservé. Les résultats d'exécution sont consignés séparément dans [RESULTATS_MVP_953.md](RESULTATS_MVP_953.md).

## Préparation de la version

Le backend, le frontend et la migration **126_avoirs_compensations_tva.sql** constituent un même lot. La migration ajoute deux dates facultatives dans `utilisations_avoirs` et une contrainte de cohérence. Elle ne remplit aucune date historique et ne modifie ni facture ni écriture. Elle est idempotente.

Avant une installation sur une base existante : conserver une sauvegarde restaurable, appliquer la migration avec le rôle de migration sur une copie isolée, puis vérifier les écrans Avoirs et Déclaration TVA. L'application de cette migration sur votre PostgreSQL réel **n'a pas été exécutée par Codex**. La création de tables SQLAlchemy ne remplace pas cette migration pour une table déjà existante. Ne pas déployer le seul frontend ou le seul backend du lot.

## Déroulement du scénario

1. Créer une société fictive et sélectionner **TVA sur encaissements** avant la première facture. Garder la périodicité mensuelle, l'exercice 2025 et les autres paramètres du jeu principal.
2. Rejouer les référentiels, capital, acquisition d'immobilisation, achats et cycle commercial dans l'ordre chronologique du cahier.
3. Pour VENTE-01 : facture de 30 000 MAD TTC ; virement de 10 000 le 25 janvier ; chèque de 20 000 le 26 janvier, remis le 1er février, effectivement encaissé le 5 février. L'avoir de 3 000 MAD du 10 février produit un crédit client.
4. Sur cet avoir, choisir **Imputer sur une facture**, sélectionner VENTE-02, montant **3 000**, date **01/03/2025**. Dans ce scénario uniquement, l'accord fictif REC-COMP01 est signé ce jour par les deux parties : cocher **Accord de compensation signé par les parties à la date indiquée** et saisir **REC-COMP01** dans **Référence de l'accord signé**. La date doit être celle du document, et non celle à laquelle un opérateur saisit plus tard l'opération.
5. Compléter VENTE-02 : virement de 5 000 le 5 mars et effet de 10 000, remis le 15 mai, encaissé le 16 mai avec frais bancaires de 10. Les frais réduisent la banque reçue à 9 990 ; ils ne réduisent pas le règlement de la créance de 10 000.
6. Saisir l'acompte de 24 000 TTC le 1er juin, la facture de service de 144 000 TTC le 15 juin, son imputation de 24 000 et le règlement final de 120 000 le 30 juin. La TVA de l'acompte doit être comptée une fois.
7. Préparer manuellement les écritures mensuelles TVA du JSON. Les écritures TVA-01, TVA-02 et TVA-03 diffèrent du jeu des débits ; **TVA-05 est ajoutée**, et **TVA-12 n'est pas créée**. Le paiement TVA-06-PAY de 19 900 le 20 juillet est identique.
8. Terminer l'inventaire, amortissement, ajustements, IS, clôture et à-nouveaux du cahier. Consulter les douze déclarations TVA et leurs impressions de contrôle.
9. Conserver VENTE-IMPAYEE de 14 400 TTC impayée en 2025 : le chèque de 2 000 du 12 décembre est rejeté le 15 décembre et ne doit jamais être traité comme un encaissement effectif.
10. Pour prolonger la vérification en 2026 : afficher les factures de 2025, ouvrir l'encaissement de VENTE-IMPAYEE, saisir **14 400**, date **15/01/2026**, référence **REC953-IMPAYEE**, banque du jeu de recette. Passer à l'exercice 2026 pour valider l'écriture. Janvier 2026 devient taxable à hauteur de 2 400 ; décembre 2025 et le snapshot IS confirmé restent inchangés. Ne pas saisir l'ancien paiement TVA-12-PAY du scénario des débits : il n'existe aucune TVA due de décembre dans cette variante.

## Résultats indépendants attendus

| Mois 2025 | TVA collectée | TVA récupérable | Crédit d'ouverture | Crédit final | TVA due |
|---|---:|---:|---:|---:|---:|
| Janvier | 1 666,67 | 6 800,00 | 0,00 | 5 133,33 | 0,00 |
| Février | 2 833,33 | 2 400,00 | 5 133,33 | 4 700,00 | 0,00 |
| Mars | 1 333,33 | 2 400,00 | 4 700,00 | 5 766,67 | 0,00 |
| Avril | 0,00 | 0,00 | 5 766,67 | 5 766,67 | 0,00 |
| Mai | 1 666,67 | 0,00 | 5 766,67 | 4 100,00 | 0,00 |
| Juin | 24 000,00 | 0,00 | 4 100,00 | 0,00 | 19 900,00 |
| Juillet à décembre | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |

Total annuel collecté **31 500**, récupérable **11 600**, dû **19 900**, déjà payé en juillet. La facture impayée explique **2 400 au crédit de 4455**, non exigibles dans ce scénario ; **4456 est soldé**. Les 50 opérations / 118 lignes avant clôture, la banque de **287 730**, le bilan net de **337 010**, le résultat net de **106 409,75**, l'IS théorique de **23 420,25**, le solde IS de **23 220,25** et le total des à-nouveaux de **343 810** restent identiques au dossier principal. Les calculs mensuels figurent dans le JSON et sont contrôlés indépendamment du moteur applicatif.

## Anciennes imputations et annulations

Sans confirmation de l'accord signé, l'imputation commerciale reste possible. La déclaration signale **accord de compensation non confirmé** et ne crée pas une date fiscale supposée. Cette alerte appelle une qualification documentaire ; elle n'autorise pas à déposer une déclaration incomplète. La nouvelle confirmation n'est pas appliquée rétroactivement aux anciennes utilisations.

Une signature déclarée exige une référence non vide de 100 caractères au maximum. Dans ce flux, l'imputation est enregistrée à cette même date ; un accord antérieur nécessite de choisir sa vraie date dans le formulaire. L'API refuse une signature antérieure à la facture cible ou à l'avoir. La compensation ne génère pas un encaissement bancaire fictif ni une nouvelle écriture de règlement.

Une annulation conserve sa trace horaire et sa date d'effet distinctes. Une compensation de 600 TTC acceptée en mars et annulée au 1er avril reste dans le calcul de mars ; son effet est régularisé en avril. L'annulation ne peut précéder la signature. Les périodes clôturées restent soumises aux protections existantes.

Les justificatifs réels, la qualification d'autres formes de compensation, les cas historiques sans dates, la recette utilisateur et le dépôt DGI restent à examiner. Sources officielles et interprétation limitée du correctif : [note 953](../audit/SOURCES_COMPENSATIONS_TVA_953.md). Le produit n'est pas présenté comme certifié.
