# Checklist utilisateur — audit du dépôt HisabPro

Mise à jour du19octobre2026 : les associations déclarées et la préparation
d’un achat correspondant à une vente validée existent (lots633/635), avec
deux comptabilités distinctes. SEP20-01 passe de absent à partiel ; aucune
réplication générale ni consolidation fiscale présumée. Les annulations datées,
lectures fiables, permissions des règlements et entrée réception sont complétées
par les lots655–669. Les statuts de recette humaine restent à renseigner.

Complément du 16 octobre 2026 : les nouvelles demandes d'alimentation du
catalogue et de logos sur les pièces générées sont couvertes par les lots
[462](../../Test/rapport_logos_exports_462.md),
[463](../../Test/rapport_logos_xlsx_463.md),
[464](../../Test/rapport_modeles_avances_464.md),
[465](../../Test/rapport_modeles_taux_465.md) et
[466](../../Test/rapport_logos_impression_466.md).
Cinq modèles d'avances personnel sont ajoutés au Journal ; leur récupération
reste une saisie explicite, sans nouveau calcul de bulletin. PDF/XLSX et
impressions reprennent le logo intégré. Les pièces jointes originales, les
formats texte et les anciennes archives sans logo sont conservés.
Les [effets](../../Test/rapport_effets_date_locale_471.md),
[paramètres TVA](../../Test/rapport_tva_parametres_runtime_472.md) et
[erreurs de lecture du Journal](../../Test/rapport_lecture_journal_historique_470.md)
ont reçu des corrections vérifiées. Ces références du16octobre sont historiques ; l’actualisation du19octobre ci-dessous conserve les résultats humains à renseigner.

Audit du 7 octobre 2026, repris le 8 octobre à 11:16 UTC (13:16 Paris). Périmètre : toutes les demandes datées de juin à septembre, acomptes, RAS, numérotation de la liasse et Paie/GRH. Les lignes ci-dessous sont actualisées après les corrections livrées ; les limites restantes sont conservées.

AGENTS.md et le journal de continuité ont été consultés. Aucun dépôt Git local. Aucun PostgreSQL réel ouvert et aucune donnée comptable réelle modifiée. Les différentiels sont listés dans le manifeste de livraisons et leurs CRC sont vérifiés par le principal. Le présent lot est un audit documentaire ; aucun test métier n'a été réexécuté par cet audit. Les résultats ci-dessous sont les exécutions consignées dans CODEX_PROGRESS.md, avec les tests correspondants réellement présents dans le dépôt.

Les quatre statuts sont **terminé**, **partiel**, **absent**, **bloqué**. « Terminé » concerne le besoin précis et son périmètre testé ; la recette utilisateur reste à effectuer. « Partiel » inclut une fonction présente mais insuffisamment couverte ou présentant un écart. « Bloqué » désigne une pièce, une norme applicable ou une décision manquante. Une mention de test existant n'annonce pas une nouvelle exécution réussie.

Comptage des **73 demandes** actualisé le19octobre2026 : **40 terminé, 31 partiel, 1 absent, 1 bloqué**. Les statuts concernent le besoin précis ; aucun résultat de recette utilisateur prévalidé.

## Demandes prioritaires ajoutées

| ID | Demande | Statut | Présence et preuves | Écart / suite exacte |
|---|---|---|---|---|
| PRI-01 | Paie / GRH marocaine et direction artistique cohérente | partiel | CNSS.jsx, employes.py, grh.py, paie_service.py ; ZIP192/194/198/199/203/204/226–232 | Dossiers, congés, simulation conditionnelle, preuves versionnées et péremption livrés ; API, Edge desktop/mobile et installation082 exécutés. Annexe26cas à effectuer par l'utilisateur. Références de calcul globales, taux officiels incomplets ; variables, bulletins figés, CNSS et écritureSA automatique restent à traiter. |
| PRI-02 | Acomptes à pousser | partiel | acomptes.py, Acomptes.jsx ; ZIP188/189/252 ettest_e2e_acompte_imputation_isole.py | Parcours acompte400 + règlement800 sur facture1200, quatre écritures validées etlettrage testés etlivrés189 ; 28tests par principal. Fournisseur252 etendu : deuxEdge desktop/mobile400/1200/800,4ecritures9lignesD=C2800,lettrageAAA ;13tests regroupes passes. Retours etcycle annuel restent a etendre. Acompte commercial etacompteIS restent distincts. |
| PRI-03 | Liasse T1…T25 incluant bilan et CPC | terminé | Source canonique liasse_numerotation_interne.json, UI/Excel/PDF ; ZIP195 | T1 bilan, T2 CPC, T3–T25 sections ETIC, codes d'origine conservés. 24tests et1E2E archive réussis par agent ; SHA etsnapshot intacts. Numérotation interne clairement identifiée, sans prétendre correspondre à une codification officielle DGI. |
| PRI-04 | RAS à revoir | partiel | factures.py, commercial.py, fiscalite_credits_service.py ; ZIP206/207/208/212/291–298/303–306/308/309 | Estimation sans effet de paiement, nouveaux règlements sans OD automatique et historiques conservés291/292. Dû1200, paiements1100puis100, validation/AAA vérifiés dans quatre Edge304. Inconnus diagnostiqués dans recouvrement/dashboard/balances/exports295–297. Capture manuelle293/303 sur virement ou espèces comptabilisés : compte/date/référence/montant explicites, cinqEdge réussis, annulation traçable et backup305. Annexe306 deuxcas Non testé. Ancienne OD absente/ambiguë : annulation refusée409sansmutation308. Lot309 couvre le crédit d'avoir avec/sans capture et le verrou PostgreSQL, sans modifier les sources définitives. RAS TVA, qualification IR/IS/TVA, attestations et pont créditsIS restent incomplets ; preuves294 ne justifient aucune règle universelle. |

## 06/06/2026

| ID | Demande | Statut | Présence et preuves | Écart / suite exacte |
|---|---|---|---|---|
| JUN-01 | Visualiser les notes du devis ou rendre le devis cliquable | terminé | `src/pages/Commercial.jsx`, `Test/test_e2e_devis_notes_isole.py` ; ZIP225 | Deux Edge1365/390 réussis23,73s : création/édition, consultation clavier, actualisation sansF5, reload, acceptation etPDF réel avecnotes exactes ; snapshots persistés, zéro écriture. Devis Vente uniquement ; cycleAchat commence parBC. Aucune fonction existante recréée. |
| JUN-02 | Bons de commande acheteur et vendeur | terminé | Commercial.jsx, commercial.py ; ZIP182/271/280 | Vente déjà testée182 ; achat connecté271 puis partiels280 sur deux largeurs, liens et stock uniques contrôlés. Recette utilisateur distincte à effectuer. |
| JUN-03 | Devis et alerte de stock | terminé | Décision utilisateur8octobre ; ZIP241/242/248/249 ; [recette navigateur](../../Test/rapport_e2e_devis_stock_alerte_isole.md) | Cumul par article, fraîcheur réelle5→0, services exclus, stocks inconnus et quantités extrêmes Decimal en texte. Deux Edge1365/390 vérifient création et édition malgré rupture, actualisation et réponse réelle tardive ignorée. Backend76tests puis10UI/connexes finaux ; aucune réservation. Liste des articles au stock inconnu corrigée248/249 sans réparation historique. Stock physique actuel, sans engagement futur ni reconstitution à la date du devis. |
| JUN-04 | Factures visibles dans le cycle commercial | terminé | `OngletFactures`, onglets vente/achat `src/pages/Commercial.jsx` ; `Test/test_e2e_cycle_commercial_isole.py`, ZIP182 ; [673](../../Test/rapport_listes_commerciales673.md) | Liste existante conservée ;673 corrige le mélange achat/vente et la limite100, avec102factures réelles. Chargement, erreur, reprise et vrai vide distincts ; aucune nouvelle liste indépendante. |
| JUN-05 | Éléments nouvellement créés en tête de liste | terminé | commercial.py, factures.py, Commercial.jsx ; ZIP205 | Tri par création puisID, UIrespectantordreAPI ;6E2E ciblés54,19s,29connexes et3E2E connectés réussis après reprise. Dates de création historiquesNULL conservées, aucune date comptable changée. |
| JUN-06 | Segmenter tout le cycle achat / vente | terminé | `ONGLETS_VENTE`, `ONGLETS_ACHAT`, `typeForce` dans `src/pages/Commercial.jsx` ; tests fact2/fact3/factC ; ZIP162/182 ; [673](../../Test/rapport_listes_commerciales673.md) | Régression de la liste Factures reproduite et corrigée673 :typeForce est maintenant réellement appliqué. Vente/Achat et pagination au-delà100 vérifiées ; les factures restent intactes. Les données de tiers mixtes réelles restent à vérifier en recette utilisateur. |
| JUN-07 | Conserver les bons de réception du client côté vente | terminé | PiecesJointes reliées au BL dans Réception client ; ZIP240 ; [rapport](../../Test/rapport_e2e_reception_client_documents_isole.md) |26tests dont2Edge1365/390 : dépôtPDF/PNG, homonymes conservés, téléchargementSHA/reload, lecteur403et autre société404. Aucun stock/écriture/statutBL modifié ; aucune signature authentique présumée. Pièces locales à sauvegarder séparément de PostgreSQL. |
| JUN-08 | Statut payé/non payé/partiellement payé | terminé | `hisabpro-backend/routers/factures.py` calcule la situation, `src/pages/Factures.jsx` affiche les badges ; ZIP162 | UI réelle vente/achat : règlement 400 puis 800, solde 800 puis 0, trois écritures et lettrage. Paiement en portefeuille reste distinct d'un encaissement définitif. |
| JUN-09 | Règlement modifiable | terminé | Commercial.jsx, commercial.py ; ZIP169/233 ; test_e2e_reglement_edition_isole.py | Deux vrais Edge vente/achat, 39 ciblés/connexes et 25 autres connexes réussis. Date seule, montant400→600→1200, changement de mode différé/immédiat, commentaire et statut/solde actualisés. Finances comptabilisées ou bancaires engagées figées409 ; annulation UI conserve l'original validé et rouvre le solde. Notes seules restent éditables via API, sans formulaire financier sur paiement comptabilisé.  Annulation collective native381 testée, transaction unique et contrepassations conservées ; individuelle toujours disponible. |
| JUN-10 | Filtrer le CA de la page factures par dates | terminé | Factures.jsx, facturesPeriod.js, collecterPages.js ; ZIP210 | Bornes inclusives liste/export/indicateurs, avoirs à leur propre date et pagination100/101 réellement testés :3ciblés et4E2Econnexes. Libellés facturation nette HT et ventes nettes TTC : montants documentaires, avant escompte pourHT, consignations séparées dans détail ; aucun CA comptable certifié. |
| JUN-11 | Facture en retard et compteur zéro | terminé | echeancesFactures.js, Factures.jsx, Dashboard.jsx ; ZIP197 | 19tests Node/Edge/API par principal ; échéance enregistrée prioritaire, délai0respecté, paiementpartiel inclus, facture dujour nonéchue. Alertes etfiltre disparaissent après solde. |
| JUN-12 | Immobilisations : brut, amortissement actuel et VNC | terminé | `src/pages/Immobilisations.jsx` affiche brut, cumul et VNC ; `Test/test_e2e_immobilisations_isole.py`, ZIP175 | Acquisition 10 000 HT + 2 000 TVA ; dotations 3 333,33 / 3 333,33 / 3 333,34 ; VNC finale zéro réellement vérifiées. |
| JUN-13 | Écriture à acquisition et amortissement annuel | partiel | `hisabpro-backend/routers/immobilisations.py`, `src/pages/Immobilisations.jsx`, contrôles de `hisabpro-backend/routers/cloture.py` ; ZIP175 | Écriture d'acquisition et génération explicite des dotations présentes et testées. Aucune tâche planifiée annuelle automatique démontrée ; ne pas comptabiliser des dotations futures automatiquement. |
| JUN-14 | Dégressif coefficients 1,5 / 2 / 3 | terminé | `coefficient_degressif` dans `hisabpro-backend/services/immobilisations_service.py`, `Test/test_patch03_immobilisations.py` ; source CGI2026 art.10, p.40 | Code actuel : 3–4 ans → 1,5 ; 5–6 → 2 ; strictement plus de 6 → 3. La formulation « 6+ » est ambiguë : 6 ans relève de 2. L'éligibilité du bien doit rester distincte de la seule durée.  Variante connectée382 :60000HT sur5ans,annuités24000/14400/8640/6480/6480,VNC0 et aucun doublon ; autres variantes distinctes. |
| JUN-15 | Écriture associée aux règlements clients/fournisseurs | terminé | `hisabpro-backend/routers/commercial.py`, `Test/test_e2e_facturation_isole.py`, ZIP162 | Vraies API/UI PG isolées : facture et deux paiements, écritures équilibrées conservant tiers et compte collectif. |
| JUN-16 | Règlement par client/fournisseur partiel/total et lettrage | partiel | ReglementParTiers.jsx, /api/reglements/par-tiers ; [392](../../Test/rapport_rapprochement_ventilation_392.md), [393](../../Test/rapport_annee_rapprochement_393.md) ; [659](../../Test/rapport_annulation_ventilation659.md), [663](../../Test/rapport_reglements_lecture663.md), [665](../../Test/rapport_reglements_consultation665.md) | Ventilation native atomique, inter-exercices, annulation collective et lettrage vérifiés. Une ligne du relevé peut rapprocher le lot immédiat; règles débit/crédit et soldes inchangées. Instruments uniques chèques/effets et historiques ambigus restent partiels. Date/motif individuels et collectifs, reprise de lecture sans faux vide et commandes masquées en consultation seule qualifiés sur bacs natifs/Edge. |
| JUN-17 | Balances Excel et PDF | terminé | Balances.jsx, exportBalances.js, balance_pdf_service.py ; ZIP211/213/216 | Cinq balances générale/auxiliaire/âgée/résultat/comparative :12tests dont4API/Edge et16téléchargementsXLSX/PDF relus. Filtres, soldes, libellés du plan société même inactifs, datesN/N-1 et variations N/A vérifiés. Comparative reprend les mouvements de la période, sans qualification de bilan officiel. |
| JUN-18 | Article stockable ou service | terminé | `models.Article.is_stockable`, `src/pages/Articles.jsx`, `hisabpro-backend/routers/articles.py`, `Test/test_articles_archivage_stock.py`, ZIP147 | Déjà présent. Conversion en service refusée tant que le stock n'est pas nul ; services sans mouvement de stock. |
| JUN-19 | Emballage et transport facultatifs sur article | terminé | Articles.jsx, schemas.py ; ZIP268/269 | Création/édition des frais HT par unité réellement testées desktop/mobile, valeurs2,50/7,25 puis3,75/8,50 relues sansF5, vide→défaut0 explicite. NaN/non finis/bool et négatifs refusés avant mutation. Report vers document manuel et qualification accessoires/perdu/consigné restent explicites, aucune TVA automatique inventée. |

## 19/07/2026

| ID | Demande | Statut | Présence et preuves | Écart / suite exacte |
|---|---|---|---|---|
| JUL19-01 | Effet encaissable à échéance, net réduit avant échéance | partiel | `src/pages/Effets.jsx`, `hisabpro-backend/routers/commercial.py`, `Test/test_effets_dates_operations.py`, `Test/test_effets_dates_navigateur.py`, ZIP140 | Encaissement avant échéance refusé ; frais bancaires explicites déduits du crédit banque. L'escompte anticipé est un mécanisme distinct, absent du cycle observé : ne pas abaisser arbitrairement le nominal. |
| JUL19-02 | Dashboard factures/paiements/créances/dettes | partiel | Dashboard.jsx, SituationFinanciere.jsx ; ZIP164/197 | Indicateurs et recouvrement présents, écart de retard corrigé et testé197 ; cohérence annuelle avec comptes définitifs à compléter. |
| JUL19-03 | Changer le style du journal | partiel | `src/pages/Journal.jsx`, `src/pages/Journal.module.css`, `Test/test_patch054_journal_conformite_finale.py` | Journal déjà structuré avec colonnes, lignes et entêtes fusionnées ; appréciation visuelle finale utilisateur à effectuer. |
| JUL19-04 | Erreur [Object][Object] à création d'écriture | terminé | FormulaireEcriture.jsx, formatErreurAPI ; ZIP161/237 | Deux vrais Edge/API/PG et 55 connexes : deux erreurs422 imbriquées avec chemins et message lisible ; compte privé d'une autre société rejeté400 ; déséquilibre bloqué avant POST. Aucune écriture persistée même avec validation immédiate demandée. Correction existante confirmée, sans réapplication. |
| JUL19-05 | Respecter les noms exacts du plan dans le journal | terminé | Journal.jsx, GrandLivre.jsx, planComptableCache.js ; ZIP217 | Actifs déjà chargés depuis le plan société ; inactifs désormais conservés en lecture. Principal13pytest et5Node verts, réelEdge A→B→A et6CSV ; libellés exacts et snapshots auxiliaires inchangés. Sélection d'un nouveau compte reste limitée aux actifs. |
| JUL19-06 | Avoir en double et date près du titre | partiel | Journal.jsx ; ZIP272 | Deux sources avoirs clients distinctes : un badge/date par écriture, six mouvements et totalAV360, snapshots intacts. Doublon ancien non reproduit dans version courante. Placement esthétique demandé reste à valider par utilisateur. |

## 26/07/2026

| ID | Demande | Statut | Présence et preuves | Écart / suite exacte |
|---|---|---|---|---|
| JUL26-01 | Famille d'article : garder seulement le nom | terminé | `FormulaireFamille` dans `src/pages/Articles.jsx` : nom seul, code dérivé, paramètres comptables internes par défaut | UI déjà simplifiée. Conserver les attributs techniques requis par le mapping, sans migration destructrice des familles. |
| JUL26-02 | UX articles | partiel | `src/pages/Articles.jsx`, `Test/test_articles_archivage_navigateur.py`, ZIP147 | Code stable, messages d'erreur et rechargement après archivage testés ; appréciation globale et cas services/transport à étendre. |
| JUL26-03 | Présentation des écritures conforme à image.png | bloqué | `src/pages/Journal.jsx`, commentaire de référence historique | Le dernier message contient seulement le nom image.png, aucune image exploitable jointe. Ne pas inventer ses dimensions, colonnes ou mise en page. |
| JUL26-04 | BC → BL → facture, vérifier les liens existants | terminé | `hisabpro-backend/routers/commercial.py` suit quantités par lignes et factures actives, `Test/test_form22_conversion_guards.py`, `Test/test_fact3_partiels_ligne_par_ligne.py`, ZIP182 | Vraie UI reliée aux quatre documents, stock 10 → 8 une seule fois à la validation ; tests connexes de conversion et résiduels présents. |
| JUL26-05 | Filtrer tiers par délai/ancienneté/fréquence | partiel | Tiers.jsx, tiersActivite.js ; ZIP214/279 | Délai fiche ajouté : comptant0,1–30,31–60,plus60 etÀ vérifier, combiné aux rôles/recherche/activité.4Edge finaux et9Node réussis,202tiers/pagination et scope société/année, snapshots intacts. Activité limitée à exercice courant et historiques non rattachés visibles ; pas de date d’échéance déduite. |
| JUL26-06 | Préfixe modifié mais titre reste FA° FA… | terminé | Parametres.jsx, factures.py ; ZIP273 | Défaut d’aperçu figé FA-2026-014 reproduit, corrigé selon préfixe/exercice. Sauvegarde Fiscalité accessible.1Edge réel+49connexes passent : numérosVTE etmodèle distinct,3pièces définitives et2CSV intacts. Un FA° littéral se modifie dans le modèle ; aucun ancien titre réécrit. |

## 02/08/2026

| ID | Demande | Statut | Présence et preuves | Écart / suite exacte |
|---|---|---|---|---|
| AUG02-01 | BC → BL puis facture | terminé | Même périmètre que JUL26-04 ; ZIP182 | Ne pas réappliquer cette conversion déjà présente et testée. |
| AUG02-02 | Exploiter plancomptable.ma pour les écritures | partiel | Site consulté en lecture seule ; `hisabpro-backend/routers/modeles.py`, `Test/test_compta2_modeles_ecritures.py`, référentiel CGNC du dépôt | Revue ciblée possible pour enrichir les modèles. Ne pas recopier tout le site, ni traiter ses exemples pédagogiques comme règles officielles. Comparer les situations et comptes aux textes CNC et vérifier chaque règle nouvelle. |
| AUG02-03 | Améliorer la détection automatique des modèles | partiel | `src/components/FormulaireEcriture.jsx` détecte le compte ; `hisabpro-backend/routers/modeles.py` recherche préfixes 4/3/2 caractères | Détection existante, choix assisté et calcul des lignes. Une correspondance de compte n'identifie pas à elle seule l'intention : conserver le choix de l'utilisateur pour éviter une écriture erronée. |
| AUG02-04 | Immobilisations manquantes dans la clôture | terminé | `hisabpro-backend/routers/cloture.py` et `src/pages/Cloture.jsx` exposent dotations manquantes, génération et rapprochement registre/comptabilité ; ZIP163/175 | Déjà intégré ; étendre le scénario annuel avec mise en service tardive et cession, sans forcer une correction historique. |

## 20/08/2026

| ID | Demande | Statut | Présence et preuves | Écart / suite exacte |
|---|---|---|---|---|
| AUG20-01 | Page listant tous les règlements | terminé | `OngletReglements` dans `src/pages/Commercial.jsx`, filtrage et détail ; ZIP162/169 | Liste déjà disponible dans chaque segment ; une route autonome supplémentaire relève de navigation/UX. |
| AUG20-02 | Améliorer le grand livre | partiel | `src/pages/GrandLivre.jsx`, `Test/test_balance_grand_livre_final.py` | Soldes et CSV présents ; définir les améliorations visuelles attendues et tester export/filtre de la période. |
| AUG20-03 | Remplacer échéance par délai de paiement | partiel | `src/pages/Factures.jsx` affiche les deux champs ; `Test/test_factF_delais_paiement.py` | Délai est une durée, échéance est une date : préserver cette distinction. Le dernier besoin demande précisément de renommer « Échéance contractuelle » en « Échéance ». |
| AUG20-04 | Vérifier la loi 9-88 | partiel | REVUE_LOI_9_88_HISABPRO.md ; ZIP238 ; manuels et contrôles existants | Onze points rapprochés aux preuves techniques : neuf partiels, deux bloqués. Textes officiels complets non obtenus (403/timeouts) ; articles non lus non attribués par mémoire. Comparaison réglementaire exhaustive reste à terminer ; aucune certification. |
| AUG20-05 | Devise, régime fiscal, régime TVA, secteur société | terminé | `src/pages/Parametres.jsx` lignes 862–902, `hisabpro-backend/models.py`, `hisabpro-backend/routers/societe.py`, ZIP153 | Champs déjà présents ; ne pas les concaténer au nom légal stocké. |
| AUG20-06 | Exercice clos verrouillé, intervention admin | partiel | `hisabpro-backend/routers/cloture.py`, `hisabpro-backend/services/exercices_service.py`, `Test/test_e2e_cloture_isole.py`, ZIP163 | Verrouillage et refus 423 testés. Réouverture d'un exercice définitivement clos renvoie 409 ; procédure exceptionnelle admin à définir sans effacer la piste d'audit. |
| AUG20-07 | Bilan plus detaille | terminé | liasse_service.py, bilan_presentation.py, LiasseFiscale.jsx, liasse_pdf.py ; ZIP256/262 | Cockpit ancien agrege corrige256 : six postes immobilisations, stocks, clients et banque, sous-totaux et general ; UI/Excel/PDF memes valeurs45000brut300amort44700net.3nouveaux tests +16connexes +1archiveconnectee passes. Nets des sous-postes non ventiles restent absents ; anciens snapshots inchanges. Annexe262 :4casNonTeste PDF9pages Excel6feuilles. |
| AUG20-08 | Deux journaux AV — Avoirs | partiel | Référentiel journaux, Journal/FormulaireEcriture ; ZIP272 | Version courante testée desktop/mobile : un codeAV dans filtre et sélecteur, autres codes conservés. Ancien doublon utilisateur non reproduit ; vérifier version/contexte sans supprimer ni fusionner arbitrairement les sources. |
| AUG20-09 | Journal salaires | partiel | Journal SA dans `src/components/FormulaireEcriture.jsx` : « Rémunérations du personnel », modèles comptables | Journal manuel présent ; intégration bulletin → écriture → paiement à qualifier dans le nouveau lot Paie/GRH. |
| AUG20-10 | Acquisition immobilisation | terminé | `hisabpro-backend/routers/immobilisations.py`, ZIP175 | Acquisition et écriture réelles exécutées sur cluster isolé. |
| AUG20-11 | Mise en service immobilisation | partiel | Date distincte dans `src/pages/Immobilisations.jsx`, moteur d'amortissement | Champ présent et moteur linéaire utilise la mise en service ; événement traçable autonome à vérifier. |
| AUG20-12 | Amortissement immobilisation | terminé | `hisabpro-backend/services/immobilisations_service.py`, `Test/test_immobilisations_fin_plan.py`, ZIP175 | Dernier centime, date d'arrêt et VNC vérifiés ; éligibilité fiscale dépend du bien. |
| AUG20-13 | Cession / sortie immobilisation | terminé | FormSortie et route/sortie existants ; ZIP243 ; [recette cession/rebut](../../Test/rapport_e2e_immobilisations_sortie_isole.md) | Deux Edge25,20s et13connexes : cession immédiateHT7500/VNC6000/résultat1500, rebutVNC7000/perte7000, écritures exactes validées et originaux intacts. Doublons/droits/sociétés testés. Périmètre linéaire uniquement ; encaissement différé, cession partielle, dégressif et réévaluation restent à traiter distinctement. |
| AUG20-14 | Réévaluation si applicable | absent | Aucune opération dédiée retrouvée dans registre, moteur ou UI immobilisations | Ne pas remplacer la valeur d'acquisition silencieusement ; règles, choix et écritures séparées nécessaires. |
| AUG20-15 | Inventaire immobilisations | partiel | Registre, contrôles de clôture et livre d'inventaire | Dossier existant ; rapprochement physique des biens à documenter séparément de l'inventaire de stocks. |
| AUG20-16 | Historique immobilisations | partiel | Tableaux de dotations, écritures et réconciliation historique dans `src/pages/Immobilisations.jsx` | Pas de chronologie exhaustive de chaque événement démontrée. Réconciliation historique reste opération contrôlée, jamais recette automatique sur données réelles. |
| AUG20-17 | Facture non réglée | terminé | Situation financière, factures ouvertes, relances, `Test/test_e2e_recouvrement_isole.py`, ZIP164 | Déjà couvert ; préserver le reliquat et distinguer retard commercial de créance douteuse. |
| AUG20-18 | Écart de conversion | partiel | Comptes du plan et écritures manuelles disponibles, devises société/banques | Pas de moteur documenté de réévaluation des créances/dettes en devises retrouvé. Ne pas calculer sans devise, montant d'origine, taux datés et source du cours. |
| AUG20-19 | Valider l'écriture et case de validation dans les formulaires | partiel | `src/components/FormulaireEcriture.jsx` : `validerDirect`, `src/pages/Journal.jsx` : validation ; ZIP161/162/148 | Validation manuelle et SQL définitif présents. Générateurs de documents produisent des brouillons selon contrat existant ; option uniforme à étudier sans contourner les contrôles. |
| AUG20-20 | Dashboard : écritures à valider | terminé | `src/pages/Dashboard.jsx` affiche « Écritures à valider » vers ligne 578 | Déjà présent. |
| AUG20-21 | Progression de clôture annuelle | partiel | `src/pages/Cloture.jsx` : contrôles, dotations, FEC et rapprochements ; ZIP163 | Assistant présent, mais indicateur de progression exhaustif/versionné non démontré. Ne pas déclarer « prêt » tant que les contrôles bloquants subsistent. |
| AUG20-22 | Rapprochement automatique journal banque / relevé | partiel | [405](../../Test/rapport_rapprochement_propositions_405.md), [406](../../Test/rapport_encaissement_frais_406.md) | Propositions automatiques exactes et uniques, confirmation explicite et atomique, simple/lot natif immédiat. Ambiguïtés non attribuées ;aucun frais absorbé ou date devinée. Rapprochement approximatif exhaustif et instruments groupés restent hors de ce lot. |

## 19/09/2026

| ID | Demande | Statut | Présence et preuves | Écart / suite exacte |
|---|---|---|---|---|
| SEP19-01 | Auto-entrepreneur client/fournisseur | terminé | `src/pages/Tiers.jsx`, `hisabpro-backend/routers/tiers.py` : `autoentrepreneur` accepté et affiché | Déjà présent ; statut juridique n'est pas une preuve suffisante du traitement RAS/TVA. |
| SEP19-02 | Cohérence des libellés, notamment capital | partiel | `src/components/FormulaireEcriture.jsx` distingue souscription, libération bancaire, espèces et apport en nature | L'affirmation « apport uniquement bancaire » n'est pas une règle à imposer : vérifier les pièces et le mode réel. Exemple pédagogique plancomptable.ma traite aussi l'apport en nature. |
| SEP19-03 | Retirer les explications grises du formulaire | partiel | `src/components/FormulaireEcriture.jsx` conserve des indications et l'aide aux modèles | Besoin UX à traiter en conservant les erreurs, contrôles obligatoires et avertissements utiles ; ne pas supprimer indistinctement les explications métier. |
| SEP19-04 | Revoir les écritures possibles via plancomptable.ma | partiel | Même audit que AUG02-02 ; modèles préfixes et bibliothèque existants | Revue ciblée sourcée ; aucune importation intégrale automatique autorisée par ce lot documentaire. |
| SEP19-05 | Salaires → Rémunération dans journal | terminé | `src/components/FormulaireEcriture.jsx` SA : « Rémunérations du personnel » | Libellé métier déjà présent ; vérifier également la liste de journaux provenant des paramètres. |

## 20/09/2026

| ID | Demande | Statut | Présence et preuves | Écart / suite exacte |
|---|---|---|---|---|
| SEP20-01 | Facturation réciproque entre sociétés d'un groupe | partiel | [633](../../Test/rapport_societes_liees633.md), [635](../../Test/rapport_factures_liees635.md), [consolidation661](../../Test/rapport_consolidation_portable661.md) ; migrations101/102 | Association explicite avec tiers et droits dans les deux sociétés ; vente validée → achat brouillon correspondant, validation/comptabilisation séparées et deux Journaux testés. Pas de réplication des paiements, avoirs ou livraisons ni de consolidation fiscale. Recette utilisateur à effectuer. |
| SEP20-02 | Logo société dans paramètres | terminé | LogoSociete.jsx, logo_societe_service.py ; ZIP200 | ImportPNG/JPEGoptionnel borné, aperçu etretrait admin ;20ciblés et1E2E téléchargementvraiPDF avecimage réussis. Anciennes références conservées ; aucune requête serveur vers URL saisie. |
| SEP20-03 | Bilan, CPC et ETIC visibles seulement dans Liasse | partiel | Sidebar.jsx, LiasseFiscale.jsx ; ZIP202 | Accès du menu regroupés dans la liasse,1E2E réel17,07s réussi. ÉditeurETIC accessible depuiscockpit etanciennes routes conservées pourcompatibilité ; intégration stricte de tousécrans de saisie dans cockpit reste à faire. |
| SEP20-04 | « Échéance contractuelle » → « Échéance » et recalcul par délai | terminé | Factures.jsx ; ZIP210/215 ; test_e2e_factures_delai_echeance_isole.py | Libellé renommé et changement explicite de délai recalculant création/édition :2E2E et5connexes réussis, finsjanvier/février,60/30/0. Date manuelle préservée si seul autre champ/date/tiers change ; pièce validée verrouillée. |
| SEP20-05 | Lettrage logique débit/crédit | terminé | `hisabpro-backend/lettrage.py` exige même compte, exercice, tiers, sélection non lettrée et total débit=crédit ; ZIP162/222/224 | Trois lignes vente/achat et rechargement testés ; réponse tardive client/fournisseur corrigée ettestée222. Annuel224 contrôle deux auxiliaires soldés, code3lettres etsnapshots inchangés ; aucune modification du montant définitif pour atteindre l'équilibre. |
| SEP20-06 | Afficher Clients/Fournisseurs dans lettrage | terminé | `src/pages/Lettrage.jsx` : « Clients (3421) », « Fournisseurs (4411) » | Déjà présent au sélecteur de compte ; vérifier libellé du tiers sélectionné en recette visuelle. |
| SEP20-07 | Code de lettrage : trois lettres minimum | terminé | lettrage.py ; ZIP191 ettest_lettrage_codes_trois_lettres.py | NouveauxcodesautomatiquesAAA, saisie3à10lettres ;18tests réels, anciennes valeurs préservées etécritures définitives inchangées. |

## Sources et limites réglementaires

La numérotation **T1…T25** doit être distinguée des codes des rubriques **ETIC CGNC** et des codes d'un schéma **EDI SIMPL-IS**. Le dépôt n'a pas de catalogue officiel exhaustif versionné. Le [cahier EDI du MEF de 2010](https://www.finances.gov.ma/Publication/dgi/2010/9370_cahierdescharges.pdf) est ancien et ne prouve pas le format 2026. Une présentation interne peut être construite sans changer les clés persistées ; sa numérotation doit être explicitement définie et ne doit pas se présenter comme une homologation DGI.

Le [CGI 2026 publié par le MEF](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf), article 10, page 40, confirme les coefficients dégressifs **1,5 pour trois/quatre ans, 2 pour cinq/six ans, 3 au-delà de six ans**. Le moteur existant suit ces bornes. Le même passage exclut certains biens et prévoit une option irrévocable : une durée de trois ans ne suffit pas à rendre tout bien éligible. Le PDF direct a échoué au chargement pendant cette consultation ; son passage de l'article 10 a été obtenu par la recherche indexée officielle, pas par une copie tierce.

Le CGI distingue RAS IS, RAS IR et RAS TVA. La [loi de finances 2026 publiée au Bulletin officiel](https://www.finances.gov.ma/Publication/db/2025/BO_7465-bis_fr.pdf), pages 3834 et 3841, traite notamment l'article 117 et les dates progressives d'application. Le [rappel DGI du 23 août 2024](https://www.finances.gov.ma/fr/pages/detail-actualite.aspx?fiche=6947) décrit déjà des retenues de TVA sur la taxe, l'attestation et les relevés. Une RAS manuelle calculée sur le HT dans la facture ne remplace donc pas ce dispositif. L'extension doit être qualifiée selon payeur, bénéficiaire, opération, date et justificatifs avant automatisation ; le module de crédits IS n'est pas une déclaration de RAS.

Le [site officiel CNC/MEF](https://www.finances.gov.ma/fr/Nos-metiers/Pages/cnc-normes.aspx) référence CGNC tomes I/II, loi 9-88 et avis relatifs aux liasses. Son ouverture directe a rencontré un timeout ; le catalogue officiel a été consulté via son résultat indexé. Cela ne remplace pas une comparaison ligne par ligne du CGNC complet.

À la demande explicite de l'utilisateur, [plancomptable.ma](https://www.plancomptable.ma/) a été parcouru en lecture seule. Les pages [1111 — Capital social](https://www.plancomptable.ma/capital-social/) et [3461 — Comptes d'apport](https://www.plancomptable.ma/3461-associes-comptes-dapport-en-societe/) contiennent des exemples de souscription et de libération, y compris par biens apportés. Elles sont utiles à la revue de la bibliothèque ; elles ne constituent pas une source officielle. Aucun contenu complet n'a été copié dans l'application. Comparer les comptes et justifications avec le CGNC officiel avant de transformer un exemple en règle automatique.

## Ordre de correction proposé

1. Ne pas reprendre les lots déjà livrés : acomptes189, IS190, retard197, lettrage191/222, T1…T25 interne195, tri205, filtres210, logo200 et balances211/213/216.
2. Effectuer la recette utilisateur sur dossier fictif avec le cahier annuel et les annexes GRH/commerciale ; les succès automatisés n'en remplissent pas les résultats.
3. Étendre les variantes connectées encore partielles : effets/escompte, variantes annuelles et exercice complet ; acomptes fournisseurs252, cession différée258 et achats partiels280 déjà testés, sans réapplication.
4. Qualifier RAS HT/TVA selon opération, acteurs, date et justificatifs avant tout calcul automatique supplémentaire ; conserver les historiques.
5. Compléter les références officielles de paie et DGI avant bulletins, déclarations ou EDI ; définir les droits runtime et le déploiement sans certification présumée.

La disponibilité d'une fonction ne signifie pas que les données historiques de l'utilisateur ont été vérifiées. Les anomalies FEC/ETIC, reliquats, justificatifs absents et migrations non appliquées restent visibles. Recette utilisateur et mise en production demeurent non validées.

## Complément inventaire313 — 10 octobre 2026

Les contrôles de clôture ne convertissent plus un coût ou stock historique inconnu en zéro. Lecture, CSV et livre/PDF signalent « À vérifier » ; comptabilisation, clôture et archivage refusés sans mutation. [Preuves313](../../Test/rapport_inventaire_nombres_historiques.md) :148tests intégrés et4parcours Edge, bureau/mobile. Les demandes de progression annuelle et inventaire physique des immobilisations restent partielles ; ce lot porte sur les stocks. Globale315 terminée avec2742réussites49échecs5erreurs, preuve conservée ; recette utilisateur à effectuer.

## Compléments de la reprise14:34

Les familles historiques à TVA inconnue sont lisibles avec diagnostic ; la
fiche article et la création rapide demandent un choix explicite, sans20
inventé ni réparation. [Lot324](../../Test/rapport_familles_tva_historique.md) :
347backend,4Edge nouveaux et6Edge connexes réussis. Les prix/frais dans les
autres moteurs restent une limite distincte. Les polices locales320 et leurs
icônes décoratives326 restaurent chargement et noms accessibles ; quatre
Edge stricts réussis, sans modifier les délais ou sélecteurs.

La conversionBR330 confirme la facture sans dialogue tardif : quatre Edge
réussis60,01s, dont les cycles achats existants bureau/mobile jusqu’au lettrage.
Le [rapport330](../../Test/rapport_facturation_br_retour_non_bloquant.md)
conserve la baseline et la limite des erreurs absorbées par certains chargeurs.

Le calendrier implicite est sécurisé318 ; un calendrier partiel ne crée pas
silencieusement ses périodes manquantes et les verrous restent appliqués.
Ces corrections de fiabilité ne changent pas les73statuts des demandes.
Le [guide Word](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx) donne les
chemins et contrôles à suivre avec un partenaire ; tous les résultats de la
recette humaine restent à renseigner.

Reprise19:39UTC : alertes stock332, projection des mouvements bruts333 et
auditCMUP334 sécurisent les sources historiques inconnues sans réparation.
19tests agent,45tests principal puis95tests principal avec deux Edge bureau/mobile
passent sur leurs périmètres. Les suites superposées ne sont pas additionnées.
Dans Mouvements & CMUP, le stock inconnu affiche À vérifier, le diagnostic
indique le champ/mouvement et le filtre conserve les compteurs globaux.
Le guide337 Word/PDF23pages donne les contrôles ; les73statuts restent inchangés.

Le lot335 protège les corrections et annulations qui nécessitent des sources
historiques inconnues, ainsi que l’archivage/conversion d’un stock inconnu.
106tests exécutés par agent passent98,28s ; aucune réparation des anciennes
valeurs. La [procédure de mise à jour339](../MISE_A_JOUR_SESSION_20261010.md)
explique les contrôles sur une copie isolée et conserve les limites de recette.

La consolidation336 a réellement terminé :3009réussis,aucun échec/erreur/
ignoré,32avertissements4072,44s,code0,680empreintes stables. Elle couvre
332–335 et précède le refus BR341. Ce dernier possède122tests ciblés et
connexes réussis227,75s, dont3Edge achats/vente ; aucun cumul des suites.
[Preuves336](../../Test/rapport_non_regression_reprise_20261010_1939.md) et
[preuves341](../../Test/rapport_br_cout_historique.md).

Le guide livré est maintenant en version4 :23pages,18fiches17statuts
**Non testé**, paramètre d’entrée de stock au BR, dates exactes et
dépannage des coûts inconnus. [Contrôles342](../../Test/rapport_guide_stock_br_342.md).
Les73statuts de la checklist ne changent pas ; la recette partenaire reste
à effectuer et les résultats réels doivent être renseignés par son exécutant.

## Compléments de la reprise21:29UTC

Les conversions BL/BR343 refusent un prix nécessaire absent/non fini et
des totaux non représentables avant la création durable d’un brouillon ou
de son lien au bon.69tests réellement réussis240,15s, dont sept Edge.
La sélection d’une ligne saine seule reste autorisée même si une autre
ligne historique non sélectionnée est invalide. [Preuves343](../../Test/rapport_conversion_bon_prix_historique.md).

La validation définitive normale/proforma344 réutilise la garde de montants
avant numéro définitif, snapshots ou mouvements :91tests réussis170,78s,
dont58nouveauxAPI et quatre Edge de facturation/éditionTVA. Les anciens
documents définitifs ne sont pas réécrits. [Preuves344](../../Test/rapport_validation_facture_montants_historiques.md).

Le guide est en version5,23pages,18fiches et17statuts **Non testé**.
La procédure de mise à jour exige le niveau342 avant le nouveau cumulatif
2129. [Contrôles345](../../Test/rapport_guide_montants_345.md).
La consolidation346 est en cours et suivie séparément. Les73statuts de
cette checklist restent inchangés ; recette utilisateur et production
ne sont pas déclarées validées.

## Résultat définitif de consolidation346 — 11 octobre 2026

Cette mise à jour remplace l'état « en cours » de la reprise21:29 ci-dessus.
**3 105 réussis, 7 échoués, 0 erreur/ignoré**,32 avertissements,
4 000,94s,code1 ;684 empreintes identiques avant/après. La globale346
est **échouée**, sans promotion des statuts de couverture.
[Rapport et sept échecs](../../Test/rapport_non_regression_reprise_20261010_2129.md).
Un délai de connexion devis, quatre annulations RAS refusées422 et deux
attentes de rejet de date future restent à diagnostiquer. Le passage de
minuit peut affecter les dates calculées à l'import ; hypothèse à vérifier.
Les preuves ciblées343/344 restent distinctes, sans effacer cet échec.
Les contrôles négatifs344 sont API ; les quatre Edge344 sont des parcours
positifs connexes. La lecture UI des anciens montants invalides reste à
qualifier. GuideWord/PDFv5 livré, recette utilisateur et Office à effectuer.
Budget23:29UTC dépassé lors du suivi final : arrêter le développement,
livrer le cumulatif puis reprendre par le diagnostic isolé des sept cas.
Aucun PostgreSQL réel, donnée comptable réelle ou nouvelle migration touché.

## Reprise du11octobre08:11UTC — corrections de dates

-350 : diagnostic des sept échecs346,27cas passent àheurecourante avant
 correction ; diagnostic réseau du devis enrichi sansretry ni délai
 assoupli. Cause du délai de connexion nonétablie.
 [Rapport350](../../Test/rapport_diagnostic_sept_echecs_350.md).
-351 : quatre annulationsRAS reproduites422 à00h30locale et huit modales
 d'effets datées UTCveille/lendemain. Trois expressions utilisent désormais
 dateLocaleISO. Sélection finale63réussis25avertissements201,80s,code0,
 dont11Edgeconnectés et16composantsAPI simulée distincts. BuildVite5,85s
 code0, avertissementtaille conservé.
 [Rapport351](../../Test/rapport_dates_locales_reglements_351.md).
-352 : date future du banc calculée àl'import devenue courante après
 minuit. Deux reproductions échouées puis24tests ORM/structure réussis
 1,67s,code0. Dates calculées àl'exécution, assertions et backend conservés.
 [Rapport352](../../Test/rapport_effets_dates_minuit_352.md).
-353 : guideWord/PDFv6,23pages18fiches17statuts Non testé ; pieddate
 dérivé du titre11/10, sixliens procédure et11référencesguide/oracles
 contrôlés. WordOffice et recettehumaine àeffectuer.
 [Rapport353](../../Test/rapport_guide_dates_353.md).
-354 : consolidation achevée,3126réussis,0échec/erreur/ignoré,32avertissements,
 3866,88s,code0 ;686sources avant/après identiques. Cette globale précède357.
 [Rapport354](../../Test/rapport_non_regression_reprise_20261011_0811.md).
-357 : formulaire bancaire :date locale, saisie conservée au chargement
 et cartes non comprimées.45réussis dont13Edgeconnectés,112,18s,code0 ;
 build6,80s,code0 ;687sources finales stables, seules trois différences
 depuis354. Échecs intermédiaires conservés ;aucun clic forcé.
 [Rapport357](../../Test/rapport_rapprochement_date_locale_357.md).
-358 : guideWord/PDFv7 actuel,25pages,18fiches et17statuts Non testé ;
 fiche bancaire avec alternative manuelle400/800MAD, septliens procédure
 et11références/oracles contrôlés, page13 inspectée. Office àeffectuer.
 [Rapport358](../../Test/rapport_guide_banque_358.md).

La globale346 reste3105réussis/7échoués ; les suites ciblées ne sont pas
additionnées ni substituées àsa preuve. Couverture70fonctions et73demandes
inchangée. Aucun PostgreSQL réel, migration nouvelle ou écriture réelle
modifié. Prochaine tâche : lecture API/UI des anciens montants invalides
àqualifier ; règles fiscales/sociales et recettehumaine restent distinctes.

## Diagnostic de lecture historique et garde d'affichage — lots359/360

Recontrôle Edge après360 :1échec,7désélectionnés,25avertissements,
29,74s,code1. La facture saine reste invisible lorsque la lecture échoue ;
la garde UI ne corrige pas ce défaut. Les689sources restent identiques.

-359 : défaut noncorrigé. Deux contrôles sains/zéro réussis, cinqGET500
 etunEdge facture saine invisible :2réussis/6échoués,38,06s,code1.
 Diagnostic explicite hors collecte test_*.py ; oracle200 conservé ;
 photographies inchangées. Les chiffres invalides ne sont pas réparés.
 [Diagnostic359](../../Test/rapport_lecture_factures_historiques_359.md).
-360 : garde d'affichage uniquement. Compteurs « — », liste indisponible,
 CSVdésactivé etRéessayer réel sansF5.22réussis,25avertissements,109,16s,
 code0,dont11Edgeconnectés. Build6,25s0,compilation0,689sources stables.
 Les listes vides connues gardent leurs zéros. LeGET500 de359 reste visible.
 [Rapport360](../../Test/rapport_factures_erreur_lecture_360.md).
-GuideWord/PDFv8 actuel :25pages18fiches17statuts Non testé,390blocs,
 fiche04 décrit indisponibilité etRéessayer ; huitliens procédure,
 onze références/oracles,OOXMLCRC etPDF contrôlés,page7 inspectée.
 Office et recettehumaine nonfaits.

La globale354 couvre686sources avant357/359/360. Les45ciblés357,
22ciblés360 et diagnostic359 ne sont pas additionnés aux3126réussis354.
Les six échecs diagnostiques359 ne sont ni supprimés ni présentés comme
réussis. Couverture70fonctions et73demandes :statuts inchangés ;FAC03
reste partiel. Aucun PostgreSQL réel,migration ou donnée comptable réelle
touché. Production nonvalidée.

Prochaine tâche :reprendre diagnostic_lecture_factures_historiques.py,
qualifier la lecture API/UI avec montants inconnus explicites, conserver
factures saines et identités/lignes historiques. Couvrir règlements,RAS,
avoirs,échéanciers etexports sans faux0 ni exclusion silencieuse.

## Reprise11octobre11:05UTC — lecture qualifiée363 etguide364

Les constats359/360 ci-dessus sont les preuves antérieures à363.
La liste rétablit désormais une réponse200 qualifiée : chaque pièce et ses lignes
restent présentes, les montants inconnus sont explicites et la pièce saine reste
visible. Le détail défaillant est en lecture seule ; actions financières et CSV
concernés sont protégés. Les calculs de règlement/échéancier et le PDF défaillant
refusent explicitement la source inconnue. Aucune réparation historique.

40ciblés réussis,6sources globales/avoirs liés réussis,8Edge finaux réussis,
build4,79s0. Le diagnostic original passe désormais8cas ; ses anciens échecs
restent conservés. Les suites ne s'additionnent pas. Consolidation365 distincte.
[Correction363](../../Test/rapport_lecture_factures_historiques_363.md).

GuideWord/PDFv9 :26pages398blocs,18fiches17statuts Non testé,relationsXML/CRC
etPDF vérifiés,page7 inspectée. Office etrecette partenaire restent à effectuer.
[Guide364](../../Test/rapport_guide_lecture_364.md).

Les73demandes gardent leurs statuts globaux :40terminé,30partiel,2absent,1bloqué.
Les variations annuelles,règlement multi-factures etlimites réglementaires
ne deviennent pas terminées à partir d'une correction de lecture.


## Actualisation finale — session du11octobre2026 commencée à11h05UTC

Consolidation365 réellement exécutée :3170réussis,0échec/erreur/ignoré,
32avertissements,3998,11s,code0,690empreintes stables.
Elle précède les correctifs368 et370 ; ses résultats ne les valident pas
par anticipation. [Rapport365](../../Test/rapport_non_regression_lecture_factures_365.md).

368 :lecture des règlements qualifiée, montants nuls/négatifs explicites mais
inadmissibles, inconnus nullable, actions financières protégées et sources
conservées.24ciblés dont14Edge puis125connexes réussis ; aucune réparation.
[Rapport368](../../Test/rapport_lecture_reglements_historiques_368.md).

370 :navigation mobile repliable, clavier/focus, largeur utile complète,
filtre Effets contenu.40connexes puis18finaux après la dernière correction
réussis ;692empreintes stables. Les échecs d'avant et de précondition login
restent consignés. [Rapport370](../../Test/rapport_navigation_mobile_370.md).

Guidev10 :27pages,408blocs,18fiches et17statuts Non testé conservés.
Word/PDF réellement générés,CRC/XML/relations et pages vérifiés ; Office
et recette partenaire à effectuer. [Rapport369](../../Test/rapport_guide_reglements_mobile_369.md).

Couverture70fonctions :15terminé,46partiel,5absent,4bloqué.
Demandes73 :40terminé,30partiel,2absent,1bloqué. Aucun statut global promu
à partir de ces corrections. Aucune migration ou base comptable réelle
modifiée. Développement global partiel ; production non validée.

Prochaine reprise :recette annuelle intégrée, extension des règlements
multi-factures et qualification des historiques encore ambigus. Les schémas
officiels, justificatifs et validations réglementaires restent nécessaires.

## Session du11octobre2026 — reprise13h06UTC — lots371 à377

- 371 :liste de règlements complète au-delà des100premières factures ;28tests réussis. [Rapport371](../../Test/rapport_reglements_pagination_371.md).
- 372 :paiement immédiat ventilé par client/fournisseur natif, transaction atomique, centimes exacts, UUID de reprise, référence commune, gardes des soldes, avoirs, acomptes et RAS.108ciblés connexes puis4Edge finaux réussis, sans additionner ces suites. [Rapport372](../../Test/rapport_reglements_par_tiers_372.md).
- 373 :globale réelle3235réussis et4échecs,0erreur/ignoré,4419,71s,code1 ;696empreintes stables. Cette preuve échouée est conservée. [Rapport373](../../Test/rapport_non_regression_reglements_373.md).
- 374 :guideWord/PDFv11,28pages,419blocs,18fiches et17statuts Non testé. Variante2026 distincte :factures120/240TTC,240ventilés120/120 puis120 ;5écritures, débit/crédit720,tiers360/360 et lettrage. [Rapport374](../../Test/rapport_guide_ventilation_374.md).
- 377 :course de clôture reproduite puis corrigée, réponses d'ancien exercice ignorées ; bancs admin/menu mobile adaptés.3E2E clôture en60,01s,8bancs en78,97s et9connexes en0,35s réussis ; build0 en9,29s. Les échecs intermédiaires restent consignés. [Rapport377](../../Test/rapport_regression_recette_377.md).

Couverture inchangée :70fonctions,15terminé/46partiel/5absent/4bloqué ;73demandes,40terminé/30partiel/2absent/1bloqué. Les règlements ventilés sont des règlements individuels, pas un instrument bancaire groupé. Aucune migration, donnée ou base PostgreSQL réelle touchée. Tests connectés sur bases jetables protégées uniquement. Développement global partiel ; tests ciblés validés, dernière globale échouée ; recette utilisateur à effectuer ; production non validée.

Prochaine action :relancer la consolidation globale après377, puis étendre la recette annuelle intégrée et le rapprochement bancaire des paiements ventilés. Préserver les limites documentaires/réglementaires et les historiques ambigus.

## Session du 11 octobre 2026 — reprise 16h05 UTC — lots 378 à 390

- Consolidation378 : **3241 réussites**, zéro échec/erreur/ignoré, 3877.960s, code0 ; 697 empreintes stables. Elle couvre l'état après377, avant379/381. La preuve échouée373 est conservée. [Rapport378](../../Test/rapport_consolidation_globale_378.md).
- 379 : règlements d'une facture N-1 visibles en N dans le bon cycle ; projection native isolée par société, statut et diagnostics partagés. [Rapport379](../../Test/rapport_reglements_inter_exercices_379.md).
- 380 : variante annuelle ventilations2025, clôture, reports clients/fournisseurs120, compléments2026, validation, lettrage et exports. Avant impôt9écritures/22lignes/D=C2200, AN4180, balance2026 nette4060. [Rapport380](../../Test/rapport_annee_ventilation_380.md).
- 381 : annulation collective native en transaction unique, contrepassations et capturesRAS tracées ; refus/rollback et concurrence testés, quatreEdge. Instrument bancaire unique et rapprochement à une ligne restent à traiter. [Rapport381](../../Test/rapport_annulation_ventilation_381.md).
- 382 : acquisition60000HT/72000TTC et cinq dotations dégressives24000/14400/8640/6480/6480 ;6écritures définitives,D=C132000,VNC0,aucun doublon. [Rapport382](../../Test/rapport_immobilisations_degressif_382.md).
- 383 : mode d'emploiWord/PDFv12,30pages,439blocs,18fiches et17statutsNon testé ; trois variantes chiffrées ajoutées. [Rapport383](../../Test/rapport_guide_ventilation_degressif_383.md).
- 384 : preuve primaire supplémentaire des partsLT, mais consolidation sociale applicable et schémaEDI toujours non qualifiés ; aucun taux/schema installé. [Rapport384](../../Test/rapport_sources_paie_edi_384.md).
- 385 : consolidation des consommateurs règlement/RAS après379/381, avant388 : **228 réussites**, zéro échec/erreur/ignoré, 691.620s, code0 ; 701 empreintes stables. [Rapport385](../../Test/rapport_consolidation_reglements_ras_385.md).
- 388 : preview tardive de l'annulation reproduite et corrigée ; une ancienne réponse après changement d'exercice/cycle/jeton ne peut plus confirmer, poster ou rafraîchir le nouveau contexte. QuatreEdge bureau/mobile et22connexes exécutés. [Rapport388](../../Test/rapport_annulation_contexte_388.md).
- 389 : consolidation après388, avant390 : **232 réussites**, zéro échec/erreur/ignoré, 705.560s, code0 ; 702 empreintes stables. Ces suites connexes ne valent pas une nouvelle globale de tout le dépôt. [Rapport389](../../Test/rapport_consolidation_reglements_contexte_389.md).

- 390 : réponse GET retardée de2026 remplaçant la liste2025 reproduite puis corrigée ; génération, exercice, cycle et jeton vérifiés avant chaque mise à jour. **42tests racine réussis**, zéro échec/erreur/ignoré, 276.989s, puis28connexes(112.397s) sur la garde finale avant invalidation, compilation0 et buildfinal0. [Rapport390](../../Test/rapport_reglements_chargement_390.md).

Les suites se recoupent et ne sont pas additionnées. 70fonctions :15terminé/46partiel/5absent/4bloqué ;73demandes :40terminé/30partiel/2absent/1bloqué. Développement global partiel ; validations automatisées limitées à leurs périmètres ; recette utilisateur à effectuer. **Point6 en attente à la demande de l'utilisateur** : aucune préparation de mise en production engagée. Aucun PostgreSQL réel, donnée comptable réelle, modèle,main ou migration modifié.

Prochaine reprise : nouvelle globale couvrant379/381 et tous modules, puis instrument bancaire unique/rapprochement des paiements ventilés et variantes annuelles restantes. Paie définitive/EDI seulement après qualification des textes/schémas officiels applicables. Attendre le retour utilisateur pour le point6.

## Session du 11 octobre 2026 — reprise 18h12 UTC — lots391 à398

- [Globale391](../../Test/rapport_consolidation_globale_391.md) :3282 réussites et **un échec** de délai de connexion Edge sur3283cas,4251,60s;703empreintes stables. Reprise isolée du fichier :8réussites39,345s sans changement. La preuve globale en échec est conservée; cause du délai non démontrée.
- [Rapprochement392](../../Test/rapport_rapprochement_ventilation_392.md) :une ligne réelle du relevé pour plusieurs lignes bancaires d'une ventilation native immédiate, choix explicite, dépointage atomique, gardesSQL/permissions/concurrence/clôture. Migration084 additive et manuelle; modèles/main et migrations antérieures inchangés. Sans084 les rapprochements simples restent disponibles.
- [Année393](../../Test/rapport_annee_rapprochement_393.md) :facturation→validation→règlement→lettrage→clôture→à-nouveaux;relevé2025 trois opérations pour cinq lignes,solde1000/flux1480;en2026 deux compléments120,solde1000/flux240;comptabilité originale préservée.
- [Guide394](../../Test/rapport_guide_rapprochement_394.md) :Word/PDFv13,31pages,18fiches/17Non testé;annexeExcel3feuilles/8casNon testé. Contrôles techniques des fichiers réussis, MicrosoftWord/Excel non ouverts.
- [Restauration398](../../Test/rapport_sauvegarde_ventilation_398.md) :deuxPGnonce distincts,pg_dump/pg_restore,huit tables comparées,liens et gardes restaurés,rôleLOGIN application et cible non vide vérifiés. Aucun dump livré.
- [Consolidation397](../../Test/rapport_consolidation_bancaire_397.md) :**92réussites**,zéroéchec/erreur/ignoré,298.918s,sources finales figées;compilation et build0. Elle couvre les modules bancaires connexes, l'année et la restauration, et ne constitue pas une nouvelle globale de tous les modules. Les suites se recoupent et ne sont pas additionnées.

Couverture conservée :70fonctions,15terminé/46partiel/5absent/4bloqué;73demandes,40terminé/30partiel/2absent/1bloqué. Le rapprochement à une ligne est désormais disponible pour les ventilations natives immédiates. Instrument unique chèque/effet,escompte/frais,moteur automatique exhaustif et historiques ambigus restent partiels. Paie définitive/EDI toujours bloqués par qualification officielle.

Aucun PostgreSQL réel ni données comptables réelles utilisés. **084 non appliquée sur installation réelle. Point6 en attente utilisateur.** Développement global partiel;tests automatisés validés sur leurs périmètres;globale391 en échec malgré reprise isolée réussie;recette utilisateur à effectuer;mise en production non validée.

Prochaine reprise :nouvelle globale sur les sources après392, surveiller le délai de connexion observé en391,puis variantes annuelles et instruments/frais bancaires restant au périmètre. Ne pas réappliquer392/393/398. Attendre le retour utilisateur pour le point6.

Complément399 :[annulation après rapprochement](../../Test/rapport_annulation_rapprochement_399.md),deux vraisEdge vente bureau/achat mobile réussis en racine. Origines,contrepassations et relevé préservés;dépointage explicite possible,lot annulé non reproposable. Aucun changement produit après397.

Complément400 :[RAS et banque](../../Test/rapport_ras_rapprochement_400.md),deux casAPI/PGnonce vente/achat réussis en racine. Banque210 ventilée90/120,retenue10 indépendante conservée;aucune règle fiscale nouvelle. Code produit inchangé après397.


## Complément401 — protection du numéro technique

[Rapport401](../../Test/rapport_namespace_ventilations_401.md) :saisie manuelle du numéro natif reproduite201 puis refusée422 au POST public;flux natif et numéros commerciaux préservés. 89tests racine réussis,202.546s,zéroéchec/erreur/ignoré;compilation0. Avant correction:2échecs et1réussite,créations201du format technique reproduites. La suite397 précède cette correction du seulcommercial.py;autres sources397 identiques. Historiques non modifiés,aucune migration supplémentaire,statuts de couverture conservés. Nouvelle globale des sources finales restant à exécuter.

## Session du 11 octobre 2026 — reprise 20h09 UTC — lots403 à410

- [Globale403](../../Test/rapport_consolidation_globale_403.md) :3320 tests, 0 échec, 0 erreur, 0 ignoré, 4071.765 s, 713 sources stables. Exécution des sources finales401, avant les nouveautés404/405/406. L’échec historique391 et sa reprise isolée restent conservés dans leur rapport.
- [Frais404](../../Test/rapport_effets_frais_precision_404.md) :six défauts API reproduits puis corrigés ;refus des booléens, fractions de centime et frais ignorés ;calculs Decimal et erreurs lisibles. Encaissement120 = banque109,99 + frais10,01. Aucun changement d’historique.
- [Propositions405](../../Test/rapport_rapprochement_propositions_405.md) :correspondances exactes et uniques, sélection explicite, confirmation atomique, refus d’aperçu obsolète et de doublons. Simple et lot natif immédiat ;gardes de contexte, dates, clôture, permissions et concurrence. Course initiale du chargement société reproduite puis corrigée. Aucune écriture créée par le pointage.
- [Parcours406](../../Test/rapport_encaissement_frais_406.md) :chèque bureau et effet mobile, remise/encaissement, validation du Journal, pointage du net, lettrage et FEC réel. Quatre pièces, dix lignes, D=C480 ;client/attente0, banque109,99, frais10,01. Annulation après cycle bancaire refusée409 sans mutation. Facture initiale préparée viaAPI fictive ;ce cas n’est pas une année complète.
- [Guide407](../../Test/rapport_guide_propositions_frais_407.md) :Word/PDFv14,32pages,18fiches/17Non testé ;nouvelle annexeExcel3feuilles/9Non testé. Contrôles techniques réussis,MicrosoftOffice non ouvert.
- [Consolidation410](../../Test/rapport_consolidation_propositions_frais_410.md) :185 réussis, zéro échec/erreur/ignoré, 456.818 s, sources finales figées et identiques, compilation/build code0. Dix-neuf fichiers couvrant les nouveaux lots, les opérations bancaires existantes, annulation/RAS, sauvegarde/restauration et année2025→2026. Suite connexe distincte de403 ;les résultats ne sont pas additionnés.

Couverture conservée :70fonctions,15terminé/46partiel/5absent/4bloqué ;73demandes,40terminé/30partiel/2absent/1bloqué. Propositions exactes et frais individuels développés/testés ;rapprochement approximatif exhaustif, instruments chèque/effet groupés et escompte restent partiels. Les références du relevé réel ne sont pas supposées égales au Journal. Paie définitive, XML/EDI et qualifications fiscales/documents historiques restent limités ou bloqués selon la matrice.

Développement global partiel ;tests automatisés validés sur les périmètres exécutés ;recette utilisateur à effectuer ;mise en production non validée. Aucun PostgreSQL réel ni données comptables réelles. Aucune nouvelle migration ;084 reste une activation manuelle distincte sur recette isolée. Point6 en attente utilisateur.

Parcours annuel réduit406 également exécuté :2025→2026, résultat89,99 avant impôt de laboratoire3000, perte2910,01 ;clôture etAN2026 validés,quatre lignesD=C3020 ;FEC des deux exercices équilibrés etpointage2025 conservé/verrouillé. Le scénario annuel utilisateur exhaustif reste distinct. Relevés historiques non finis ou non positifs405 :montants et totaux concernés signalés inconnus,pointage interdit,sources conservées ;les correspondances certaines restent confirmables.

Nouvelle globale411 déjà en cours sur les sources finales :3390 cas collectés,721 empreintes figées. Aucun résultat final annoncé. Lire .codex-tests/consolidation411_globale.exit et.xml puis vérifier les empreintes avant toute validation ;ne pas relancer une commande encore active ni modifier les sources pendant l’exécution. La suite connexe410 est réussie et ne remplace pas cette nouvelle preuve exhaustive.

[Recherche ciblée412](../../Test/rapport_source_modification_cnss_412.md) :texte de modificationCNSS non obtenu ;aucune nouvelle qualification réglementaire ni calcul modifié. Limite sociale maintenue,ainsi que la dépendance distincte au schéma officielEDI.

Prochaine reprise :ne pas réappliquer les lots livrés. Vérifier l’achèvement de la globale411 déjà lancée,puis instruire les instruments bancaires groupés,escompte et variantes annuelles exhaustives ;conserver les anomalies FEC/ETIC et ne pas débloquer paie/EDI sans sources officielles qualifiées. Point6 en attente utilisateur.
