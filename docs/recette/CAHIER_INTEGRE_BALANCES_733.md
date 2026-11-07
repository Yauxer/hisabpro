# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Version 1 du 22 octobre 2026. Complément intégré : préparations depuis balances externes.

## Portée et organisation

Ce cahier complète le CAHIER_RECETTE_HISABPRO.pdf/.xlsx existant ; il ne le remplace pas et ne modifie aucun résultat humain déjà saisi. Il couvre les compléments B12/B13/B14/C3/N-2/extra livrés en725–731. Pour le parcours global depuis société vierge jusqu’au Journal, clôture et dossier annuel, suivre d’abord le cahier global ; les imports décrits ici restent indépendants du Journal et ne créent aucune archive annuelle.

Aucune recette humaine, conformité réglementaire ou production n’est validée automatiquement. Les huit cas ci-dessous restent Non testé. Les rapports techniques indiquent séparément les tests locaux réellement exécutés. RH/paie etpoint6 humain restent différés.

## Préparer la société fictive et les sources

Créer une société séparée nommée Atlas Recette733 SARL — simulation documentaire, deviseMAD, administrateur, comptable et lecteur. Ajouter un logo fictif PNG/JPEG. Créer explicitement les exercices2024,2025,2026 avec dates01/01–31/12 si absents. Vérifier le plan existant, notamment1161 Report à nouveau (solde créditeur). Aucun champ légal supplémentaire n’est imposé par ce scénario.

Utiliser uniquement les troisCSV BALANCE_FICTIVE_INTEGREE733_N2.csv (comme Balance N en 2024), _N.csv et _N1.csv (comme N/N-1 en 2026). Un compte par ligne, en-têtes compte,debit,credit, valeurs exactes dans DONNEES_INTEGREES733.json. N2 :4 comptes/12000MAD ; N1 :10 comptes/16500MAD ; N :13 comptes/25500MAD. Chaque côté non mouvementé présent vaut explicitement0.

Les fichiers et références sont fictifs. Le scénario vérifie les projections et leur cohérence arithmétique, pas un exercice réel complet ou une paie. Les décisions et effectifs déclarés ne constituent aucune validation juridique/sociale. Les pièces restent à leur version d’origine.

## Calculs indépendants et rapprochement des années

N2 :capital10000, ventes2000, charges1000 →net1000 et situation11000. Le bénéfice2024 est reporté en 2025 :RAN1000. N1 :capital10000+RAN1000+net3000−non-valeurs1000+amortissements200=situation13200. Le bénéfice2025 est3000 ; hypothèse déclarée de distribution1000 payée en 2026 :RAN N=1000+3000−1000=3000.

N :ventes10000−charges3000−rémunérations 6171 à400+produit non courant1000−impôt67 comptabilisé1580=net6020. Capitaux10000+RAN3000+net6020−non-valeurs2000+amortissements500=situation17520. Total actif/passif20020, contre14300 enN1 et11000 enN2. Les valeurs6171 et effectifs sont des hypothèses documentaires distinctes, aucun bulletin n’est supposé.

B12 :net6020+67 à1580=avant impôts7600 ; autres réintégrations500−déductions200 →7900. Déficit disponible0 explicitement déclaré →bénéfice7900 ; taux fictif déclaré20 →IS théorique1580. Ce résultat n’est pas l’IS exigible ou le solde à payer :CM/CSS/crédits/acomptes restent inconnus. Aucun régime ou avantage n’est déduit.

B13 :courant10000−3000−400=6600 ; base documentaire6600+500−200=6900 ; impôt théorique courant déclaré1380 ; courant après impôt déclaré6600−1380=5220. Le67 comptabilisé1580 ne remplace pas1380. Pour N1, courant3000, réintégrations/déductions0 explicites et impôt courant non fourni :après impôt reste inconnu.

B14 :4455 début300+opérations2000−déclarations1300=fin1000 ;34552 :100+800−400=500 ;34551 :50+300−150=200. Récupérable totale700 ; net documentaire300 ; écarts0. Les soldes N1 pour mémoire300/100/50 ne prouvent pas les flux ; ceux-ci sont déclarés avec leurs références.

Extra C3 :hypothèse explicitement documentée100 titres. N :net6020/100=60,20 et distribution2000/100=20 ; N1 :3000/100=30 et1000/100=10 ; N2 :1000/100=10 et0/100=0. Ces divisions sont l’oracle du jeu ; l’application reçoit les valeurs par titre déclarées. Effectifs déclarés3,50/3/2personnes. PV fictifs 2027 pour2026,2026 pour2025,2025 pour2024 :qualification à revoir, jamais dates inférées.

## Saisie exacte des compléments

Les données de DONNEES_INTEGREES733.json sont reprises dans la feuille Déclarations Excel. Pour chaque tableau, choisir Saisie documentée — à revoir, justification Synthèse intégrée fictive733, ajouter une seule ligne sauf B14 trois familles, puis saisir tous les champs fournis. Aucun identifiant de base ne doit être inventé :noter celui de la préparation source2024 effectivement conservée.

Pour N2, référence SOURCE INTEGREE733 N2. Pour B12, désignation Passage intégré733 N, référence SOURCE INTEGREE733 B12, autres réintégrations500, déductions200, déficit disponible 0, taux 20. Pour B13 N et N1, utiliser exactement les deux synthèses du JSON ; laisser l’impôt N1 vide. Pour B14, copier les troisflux et les références DECL FICTIVE733 suivies de4455/34552/34551. Pour extra C3, copier les trois périodes, les PV et SOURCE INTEGREE733 EXTRA suivie du code.

Après chaque conservation, la nouvelle version doit être sélectionnée sans F5. Les contrôles figés ne changent pas pendant un brouillon. Après rattachement N2 ou modification extra, conserver explicitement une nouvelle version des indicateurs C3 pour les inclure ; les anciens contrôles restent inchangés.

## Cas détaillés de recette


### I733-01 — Importer les trois sources

Module : Préparation

Prérequis : Société fictive MAD2026, exercices2024/2025/2026, plan existant avec1161, droits administrateur/comptable, aucune base réelle.

Données exactes : CSV N2 en 2024 puis N/N1 en 2026 ; en-têtes compte,debit,credit.

Actions dans l’interface : Importer puis Contrôler et préparer et Conserver une nouvelle version ; noter versions/empreintes, sans inventer un ID.

Résultat attendu : Totaux N25500,N1 16500,N2 12000 ; nets6020/3000/1000 ; sources conservées séparément par exercice.

Écritures attendues : Aucune :préparations documentaires uniquement.

Impacts fiscaux attendus : IS théorique1580 au taux déclaré ; CM/CSS/crédits/acomptes/solde inconnus. Aucune validation de dépôt ou de conformité.

Contrôles : Anciennes versions/empreintes et Journal inchangés ; sources explicites, inconnus distincts de0.

Statut humain : Non testé

Preuve attendue : Capture du formulaire/contrôle et export de la version, avec date et rôle.


### I733-02 — Rattacher explicitement N-2

Module : Comparatif N2

Prérequis : Société fictive MAD2026, exercices2024/2025/2026, plan existant avec1161, droits administrateur/comptable, aucune base réelle.

Données exactes : Préparation2024 et référence SOURCE INTEGREE733 N2.

Actions dans l’interface : En2026 choisir la source2024 dans Rattacher une source N-2 aux indicateurs C3 ; confirmer, conserver puis conserver les indicateurs C3.

Résultat attendu : N2 situation11000/net1000 ; provenance2024/version/SHA ; anciennes versions sans N2 inchangées.

Écritures attendues : Aucune :préparations documentaires uniquement.

Impacts fiscaux attendus : IS théorique1580 au taux déclaré ; CM/CSS/crédits/acomptes/solde inconnus. Aucune validation de dépôt ou de conformité.

Contrôles : Anciennes versions/empreintes et Journal inchangés ; sources explicites, inconnus distincts de0.

Statut humain : Non testé

Preuve attendue : Capture du formulaire/contrôle et export de la version, avec date et rôle.


### I733-03 — Passage fiscal documenté

Module : B12

Prérequis : Société fictive MAD2026, exercices2024/2025/2026, plan existant avec1161, droits administrateur/comptable, aucune base réelle.

Données exactes : RI500,déductions200,déficit disponible 0,taux déclaré20, référence SOURCE INTEGREE733 B12.

Actions dans l’interface : Choisir B12-N, saisir tous les champs du jeu JSON, confirmer et conserver. Vider ensuite le déficit dans une version de test :ne pas saisir0 implicitement.

Résultat attendu : Net6020+impôt67 à1580=7600 ; avant déficit7900, bénéfice7900, IS théorique1580. Déficit vide :bénéfice/IS inconnus ; rétablir0 explicitement.

Écritures attendues : Aucune :préparations documentaires uniquement.

Impacts fiscaux attendus : IS théorique1580 au taux déclaré ; CM/CSS/crédits/acomptes/solde inconnus. Aucune validation de dépôt ou de conformité.

Contrôles : Anciennes versions/empreintes et Journal inchangés ; sources explicites, inconnus distincts de0.

Statut humain : Non testé

Preuve attendue : Capture du formulaire/contrôle et export de la version, avec date et rôle.


### I733-04 — Distinguer courant et impôt comptabilisé

Module : B13

Prérequis : Société fictive MAD2026, exercices2024/2025/2026, plan existant avec1161, droits administrateur/comptable, aucune base réelle.

Données exactes : N RI500/déductions200/impôt courant déclaré1380 ; N1 RI0/déductions0/impôt inconnu ; références du JSON.

Actions dans l’interface : Remplir B13-N et B13-N1, conserver ; comparer au CPC figé sans copier automatiquement67 dans l’impôt courant.

Résultat attendu : Courant6600/base6900/après impôt déclaré5220 ;67 à1580 distinct de1380. N1 courant/base3000, après impôt inconnu.

Écritures attendues : Aucune :préparations documentaires uniquement.

Impacts fiscaux attendus : IS théorique1580 au taux déclaré ; CM/CSS/crédits/acomptes/solde inconnus. Aucune validation de dépôt ou de conformité.

Contrôles : Anciennes versions/empreintes et Journal inchangés ; sources explicites, inconnus distincts de0.

Statut humain : Non testé

Preuve attendue : Capture du formulaire/contrôle et export de la version, avec date et rôle.


### I733-05 — Rapprocher les flux TVA justifiés

Module : B14

Prérequis : Société fictive MAD2026, exercices2024/2025/2026, plan existant avec1161, droits administrateur/comptable, aucune base réelle.

Données exactes : 4455 :300+2000−1300 ;34552 :100+800−400 ;34551 :50+300−150, références du JSON.

Actions dans l’interface : Saisir trois familles B14, conserver ; comparer fins aux soldes sources. Modifier opérations4455 en1999,99, conserver et relever l’écart puis rétablir2000 et conserver à nouveau.

Résultat attendu : Fins1000/500/200, récupérable700, net documentaire300, écarts0. Variante fin999,99/écart−0,01 visible, aucun solde source corrigé.

Écritures attendues : Aucune :préparations documentaires uniquement.

Impacts fiscaux attendus : IS théorique1580 au taux déclaré ; CM/CSS/crédits/acomptes/solde inconnus. Aucune validation de dépôt ou de conformité.

Contrôles : Anciennes versions/empreintes et Journal inchangés ; sources explicites, inconnus distincts de0.

Statut humain : Non testé

Preuve attendue : Capture du formulaire/contrôle et export de la version, avec date et rôle.


### I733-06 — Intégrer les déclarations et conserver C3

Module : C3

Prérequis : Société fictive MAD2026, exercices2024/2025/2026, plan existant avec1161, droits administrateur/comptable, aucune base réelle.

Données exactes : N :3,50personnes/2000MAD/60,20MAD par titre/20MAD par titre ; N1 :3/1000/30/10 ; N2 :2/0/10/0 ; PV/références du JSON.

Actions dans l’interface : Saisir les trois synthèses extra-comptables, conserver ; constater C3 ancien inchangé et message d’actualisation. Conserver les indicateurs C3 puis choisir chaque période.

Résultat attendu : Situations17520/13200/11000, nets6020/3000/1000 ; déclarations avec bonnes unités, provenance et PV ; aucune lecture RH ou calcul par titre inféré.

Écritures attendues : Aucune :préparations documentaires uniquement.

Impacts fiscaux attendus : IS théorique1580 au taux déclaré ; CM/CSS/crédits/acomptes/solde inconnus. Aucune validation de dépôt ou de conformité.

Contrôles : Anciennes versions/empreintes et Journal inchangés ; sources explicites, inconnus distincts de0.

Statut humain : Non testé

Preuve attendue : Capture du formulaire/contrôle et export de la version, avec date et rôle.


### I733-07 — Vérifier dossier et logo

Module : Exports

Prérequis : Société fictive MAD2026, exercices2024/2025/2026, plan existant avec1161, droits administrateur/comptable, aucune base réelle.

Données exactes : Logo fictif PNG/JPEG ; préparation contenant N2,B12,B13,B14,C3 et extra.

Actions dans l’interface : Télécharger le dossier ZIP ; ouvrir PDF/Excel/JSON et troisCSV ; vérifier manifestes SHA256, logo, références et inconnus ; comparer Journal avant/après.

Résultat attendu : Même version et mêmes valeurs dans chaque format, N2 traçable, logo présent, CRC/SHA exacts ; aucune écriture, liquidation ou pièce déplacée.

Écritures attendues : Aucune :préparations documentaires uniquement.

Impacts fiscaux attendus : IS théorique1580 au taux déclaré ; CM/CSS/crédits/acomptes/solde inconnus. Aucune validation de dépôt ou de conformité.

Contrôles : Anciennes versions/empreintes et Journal inchangés ; sources explicites, inconnus distincts de0.

Statut humain : Non testé

Preuve attendue : Capture du formulaire/contrôle et export de la version, avec date et rôle.


### I733-08 — Refus et isolement

Module : Droits

Prérequis : Société fictive MAD2026, exercices2024/2025/2026, plan existant avec1161, droits administrateur/comptable, aucune base réelle.

Données exactes : Profils comptable/lecture et deuxième société fictive ; NaN, référence vide, empreinte incorrecte.

Actions dans l’interface : Tester saisie/export sur1440/390, lecteur sans conservation, autre société invisible ; rejets sans version ; brouillon conservé, anciennes versions inchangées.

Résultat attendu : Écriture403 pour lecteur, préparation404 autre société, refus422 ou conflit409 adaptés ; aucune mutation des écritures validées.

Écritures attendues : Aucune :préparations documentaires uniquement.

Impacts fiscaux attendus : IS théorique1580 au taux déclaré ; CM/CSS/crédits/acomptes/solde inconnus. Aucune validation de dépôt ou de conformité.

Contrôles : Anciennes versions/empreintes et Journal inchangés ; sources explicites, inconnus distincts de0.

Statut humain : Non testé

Preuve attendue : Capture du formulaire/contrôle et export de la version, avec date et rôle.


## Limites et documents complémentaires

Les exports ne prouvent ni dépôt, ni paiement, ni conformité. Les références justificatives et les qualifications fiscales/sociales restent humaines. Les données historiques FEC/ETIC incomplètes ne sont pas réparées. Le nouveau calcul automatique CM/CSS/crédits du mode externe reste conditionné à ses sources officielles applicables ; accès intégral CGI2026 MEF/DGI en échec pendant cette session. Aucun taux ou schéma EDI inventé.

Développement des quatre compléments livré ; validations automatisées détaillées dans les rapports725/727/729/731/733. Recette utilisateur à effectuer. Installation cible et prêt pour production nonvalidés. Les autres limites du cahier global et de REGISTRE_LIMITES_RECETTE.md restent applicables. Les guides détaillés par lot sont dans l’index de livraison733.
