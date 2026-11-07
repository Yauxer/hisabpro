# Rapport de reprise autonome — HisabPro — 7 octobre 2026

Session commencée à 06:21 UTC, interrompue par quota. L'utilisateur a demandé
la reprise à 11:34 UTC ; nouvelle limite d'exécution à 13:34 UTC.
Après interruption du quota, nouvelle demande et reprise à17:03UTC, limite19:03UTC.
Une nouvelle interruption du quota a laissé les lots tri, RAS et lisibilité en cours.
Reprise demandée à21:58UTC (7octobre23:58Paris), limite23:58UTC ; aucun processus Python
de test encore actif. Les services PostgreSQL existants de l'utilisateur sont laissés intacts.
Nouvelle interruption vers22:40UTC, reprise utilisateur le8octobre04:54UTC,
limite06:54UTC. Aucun Python de tests encore actif ; connexes du lot217 repris.
Le dépôt courant, les migrations, les tests et les ZIPs ont été examinés avant
modification. Le dossier ne contient pas de dépôt Git. Aucun commit créé.

Reprise suivante le8octobre11:16UTC, limite13:16UTC (15:16Paris), après
correction du démarrage229. Le backend et Vite de l'utilisateur tournent déjà
et sont laissés intacts. Cette exécution termine les preuves de paie, étend
les recettes commerciales et de restauration, puis consolide les livraisons.

## Livraisons et résultats exécutés

| ZIP | Périmètre | Résultat réel |
|---|---|---|
| 160 | Mot de passe personnel et révocation JWT versionné | Principal : 14 tests API/Edge/PG isolé, build et compilation réussis |
| 161 | NaN/Infinity/bool dans les écritures, réponse JSON 422 sérialisable | Principal : 99 tests ciblés et connexes, compilation réussie |
| 162 | Vente/achat → validation → règlements 400/800 → lettrage | Agent : 6 tests connexes dont 2 UI connectés, réussis |
| 163 | Clôture réelle UI → à-nouveaux → FEC et verrouillage | Agent : 3 tests, réussis ; 9 comptes AN équilibrés à 14 320 MAD |
| 164 | Filtres, droits et suivi des relances, montants et historique | Principal : 24 tests ; agent : 8 tests connectés ; build et compilation réussis |
| 165 | Cahier PDF/Excel, oracle, jeu fictif et procédures exploitation | Agent : 24 tests réussis ; PDF 105 pages, Excel 27 feuilles réellement ouverts |
| 166 | Scanner RBAC et route personnelle authentifiée | Principal : 23 tests hardening/mot de passe réussis |
| 167 | Permissions SQL effectives du rôle runtime non administrateur | Agent : 52 tests runtime/bootstrap/hardening réussis |
| 168 | Import CSV et rapprochement bancaire connectés | Agent : 1 test UI réussi ; écriture définitive inchangée et réimport dédoublonné |
| 169 | Montants des règlements : création et modification | Principal : 29 tests dont8API PostgreSQL, puis49connexes réussis ; pas de mutation sur saisie invalide |
| 170 | Nettoyage des dossiers E2E sous Windows | Principal : 3 régressions incluses dans49connexes réussis ; retry borné et garde de chemin |
| 171 | Migration073 : permissions et TRUNCATE des archives fiscales | Agent : 5 tests PostgreSQL réussis ; droits directs/PUBLIC/hérités, propriétaire et rôle absent |
| 172 | Finalisation et relecture d'une archive fiscale | Agent : 1 Edge connecté et16connexes réussis ; PDF/XLSX réels, snapshot etSHA vérifiés |
| 173 | TVA connectée, impression, identité et permissions | Principal : 26 tests puis14paramètres réussis ; 2UI connectées, PDF de page relu ; build etcompilation OK |
| 174 | Valeurs finies des lignes devis/BC/BL/factures | Principal : 100 tests dont8API PostgreSQL, puis71connexes réussis ; prix zéro/fraction conservés |
| 175 | Acquisition et amortissement sur trois exercices | Agent : 1UI et13unitaires réussis ; 6 scénarios patch03 réellement lancés ; API_BASE corrigé etbuildOK |
| 176 | Audit de l'installation vierge | Principal : 64SQL appliqués sur socle ORM,18tables métier vides,27.92s ; anomalies de structure identifiées |
| 177 | Migration074 : archives comptables immuables | Principal : 13PostgreSQL et33connexes réussis ; livre d'inventaire etpréparationsbalances protégés y comprisTRUNCATE |
| 178 | Migration075 : compléments auxiliaires de structure seuls | Agent : 5PostgreSQL et16connexes réussis ; fonction métier runtime, aucunbackfill historique |
| 179 | Migration076 : CHECK ETIC etempreinte manquants | Principal : 8PostgreSQL et24connexes réussis ; anciennes lignes fictives invalides préservées NOT VALID |
| 180 | Installation consolidée vierge | Agent : 67SQL+3rejeux réussis11.14s ; catalogue stable, tables vides, rôleLOGIN nonowner ; ACL core insuffisantes documentées |
| 181 | Version et empreinte archive dans Excel | Principal : 17E2E/connexes réussis21.65s ; téléchargementXLSX vérifié ; build131modules5.04s etcompilationOK |
| 182 | Devis → BC → BL → facture etstock | Agent : 1Edge19.91s et50connexes2.35s réussis ; stock10→8, liens4documents etécriture1200définitive |
| 183 | Avoir, retour et annulation | Agent : 1Edge21.95s et43connexes2.32s ; écritures originales préservées |
| 184 | Permissions runtime commerciales077 | Agent : 18API/PG22.95s et7connexes ; LOGIN non propriétaire |
| 185 | Échéanciers : valeurs finies | Principal : 28tests18.14s et44connexes31.60s |
| 186–187 | Facture validée non supprimable078, droits commerciaux079 | Principal : 36tests PostgreSQL etconnexes26.10s |
| 188 | Acomptes : valeurs finies | Principal : 49tests0.81s ; agent9API/PG18.34s |
| 189 | Acompte → imputation → solde → lettrage | Principal : 28tests26.85s ; corrections échéance vide et actions accessibles |
| 190 | IS connecté, contrôle comptable et snapshot | Agent : 1Edge18.56s et29connexes0.23s ; oracle fiscal fictif explicite |
| 191 | Minimum trois lettres pour nouveaux codes lettrage | Principal : 18tests42.52s etcompilation réussis ; historiques préservés |
| 192 | Dossiers salariés et simulation mensuelle paramétrée | Agent : 46tests29.77s et170connexes63.53s ; compilation, migration080rejouée etruntime vérifiés |
| 193/196 | Couverture et checklist | Audit73points et75références locales ; ZIPs sources vérifiés |
| 194/199 | Interface Paie/GRH et congés/absences | Agent3E2Epaie et5E2Econsolidés48.76s, build etcompilationOK |
| 195 | Numérotation interne T1…T25 | Agent24ciblés et1E2Earchive20.11s réussis, codes etSHA conservés |
| 197 | Retards sur paiements partiels | Principal19tests48.18s, alerte/filtre/soldage réels |
| 198 | Workflow GRH et contrat inconnu préservé | Agent87backend61.74s, concurrence etpermissions ;080corrigée et081additive |
| 200 | Logo société | Agent20ciblés et1E2E20.01s, image dans vrai PDF facture |
| 201 | Annexe recette Paie/GRH | Principal2tests0.71s, PDF etExcel réellement ouverts,19cas utilisateur non prévalidés |
| 202 | Navigation états depuis liasse | Principal1E2E17.07s ; anciens liens compatibles, éditeur ETIC conservé |
| 203 | Contrat salarié facultatif | Agent3E2E23.74s ; NULLconservé après édition/restauration |
| 204 | Lisibilité et fuiteCSS corrigée | Reprise principal5E2E72.44s,13connexes0.51s ; desktop/mobile ettable étrangère au module ; build135modules5.64s |
| 205 | Listes commerciales par création récente | Reprise agent6E2E54.19s,29connexes2.27s,3E2E69.31s ;NULLhistoriques préservés |
| 206 | Pourcentages RAS finis | Agent42ciblés33.82s dont11API et165connexes67.63s ; aucun taux légal ajouté |
| 207 | Conservation RAS et diagnostic historique | Agent89tests67.12s dont7nouveauxAPI/PG etéditionEdge réelle ; valeurs historiques invalides intactes etPDF409 |
| 208 | Audit RAS et limites fiscales | Sources primaires indexées et expériences isolées ; RAS HT partielle, TVA absente ; aucun régime nouveau codé |
| 209 | Installation vierge jusqu'à081 | Principal72SQL et8rejeux17.83s,21tables métier vides, catalogue/runtimeGRH etnettoyage contrôlés |
| 210 | Périodes factures et totaux documentaires | Agent3ciblés36.91s et4E2Econnexes66.16s ;100/101pièces, avoirs dates propres, HT457/TTC548,40 ; build138modules6.57s |
| 211 | Excel/PDF balances générale auxiliaire âgée | Agent10tests36.71s dont2API/Edge PGisolé ;10téléchargements réellement relus, filtres/totaux/droits/nonmutation ; build138modules5.22s |
| 212 | Diagnostic RAS dans les formulaires | Agent3E2E33.28s et7lectureconnexes réussis ; aucunPATCHsans choix, taux7conservé, historique définitif protégé ; build139modules5.96s |
| 213 | Libellés société dans la balance générale | Agent11tests41.21s ;25subdivisions, comptes renommés/inactifs etPDFmultipages ; sourceAPI commune sans mutation ; build139modules5.90s |
| 214 | Activité tiers et reliquats | Agent8Node113ms et2E2E28.59s ; identités réelles, homonymes,201tiers, reliquat800/1200, créances/dettes distinctes etdiagnostics ; build139modules4.62s |
| 215 | Délai modifié et échéance | Agent2E2E32.83s et5connexes67.29s ; création/édition et finsmois60/30/0, datesmanuelles préservées ; build139modules4.69s |
| 216 | Excel/PDF balances résultat et comparative | Agent12tests44.97s ;16téléchargements, mouvementsN/N-1/variations,29février etlabels textes ; build139modules4.54s |
| 217 | Comptes historiques désactivés en journal/grandlivre | Principal13pytest34.37s et5Node138.54ms, compilation2OK ; vraiEdge A→B→A,6CSV etécritures/snapshots intacts ; buildagent139modules5.40s |
| 218 | Consolidation globale avant nouveaux lots de paie | Principal2060réussis,0échec/erreur/ignoré en1233,35s,29avertissements ; premièreglobale échouée etcauses conservées |
| 220 | Sources primaires de paie2026 | Audit officiel documenté, référentiel social2026 encore incomplet ; aucun nouveau taux activé |
| 221 | Fixture historique des permissions077 | Agent32tests48,88s etcompilation3OK ; phases074–076/077 distinctes,5checks6triggers conservés, SQL/GRANT inchangés |
| 222 | Chargement concurrent du lettrage | Agent1test strict17,41s et2cycles26,59s, build139modules5,88s ; défaut reproduit avant correction17,84s |
| 223 | Bancs des évolutions livrées | Agent37tests1,37s etcompilation5OK ; sept anciens échecs corrigés sans modifier application ou règles |
| 224 | Exercice annuel connecté réduit | Agent2tests23,95s, oracle figé inchangé ; stock, TVA, immo, clôture, AN, FEC et5exports réels |
| 225 | Notes de devis vente | Agent2Edge desktop/mobile23,73s etcompilationOK ; consultation clavier, édition/reload/PDF réel, zéro écriture, aucune modification applicative |
| 226 | Paramètres paie finis et diagnostics historiques | Agent148tests43,26s, compilation4fichiers ; refus avant mutation, anciennes valeurs intactes ; aucune activation fiscale |
| 229 | Démarrage GRH sur base existante | Principal54casdistincts dont import main/HTTP200, compilation etbuild ; scripts080/081 inchangés, données fictives historiques conservées |
| 227 | Référentiel annuel : preuves versionnées et immuables | Agent24ciblés15,20s et172avecconnexes64,13s ; API/PG, scopes/concurrence/replay/runtime. Aucun taux activé ; [rapport](../../Test/rapport_paie_referentiel_trace.md) |
| 228 | Interface des preuves paie société/année | Agent2Edge25,41s et5connexes51,50s ; GET/POST tardifs protégés, datesnull conservées, build139modules4,47s ; [rapport](../../Test/rapport_e2e_paie_referentiel_isole.md) |
| 230 | Protections082 installées au démarrage | Principal15tests54,52s, vrai import main/health200, versions historiques intactes et triggers082 ; [rapport](../../Test/rapport_demarrage_paie_082.md) |
| 231 | Installation consolidée jusqu'à082 | Agent73SQL+9rejeux=82applications12,75s,22tables vides ;20tests32,90s puis2renforcés10,57s ; [rapport](../../Test/rapport_installation_vierge_082.md) |
| 232 | Annexe recette paie étendue aux preuves | Principal2tests0,85s ;26cas,23Non testé/3Bloqué ;30pages PDF/7feuilles Excel réellement ouverts ; [rapport](../../Test/rapport_annexe_recette_paie_preuves.md) |
| 233 | Édition des règlements | Agent39tests43,57s dont2Edge et25connexes0,35s ; montant/date/mode/notes, originaux validés préservés ; [rapport](../../Test/rapport_e2e_reglement_edition_isole.md) |
| 234 | Consolidation globale historique avant BR/stock | Principal2199réussis1422,89s32avertissements,0échec/erreur/ignoré ; XML relu et sources figées ; [rapport](../../Test/rapport_non_regression_globale_20261008_1135.md) |
| 237 | Messages d'erreurs des écritures | Agent2Edge22,58s et55connexes28,44s, erreurs422/400 lisibles et aucune écriture persistée ; [rapport](../../Test/rapport_e2e_ecriture_erreurs_isole.md) |
| 238 | Revue loi9-88/Avis24/CGNC | Audit11points,9partiels/2bloqués ; accès officiel complet403/timeouts, aucune norme inventée ; [revue](REVUE_LOI_9_88_HISABPRO.md) |
| 239 | Sauvegarde/restauration GRH082 | Agent1test22,90s et5connexes ;8tables toutescolonnes,2clusters, dump/restore, triggers/ACL082replay ; [rapport](../../Test/rapport_sauvegarde_paie_grh_082.md) |
| 240 | Documents reçus du client | Agent26tests49,34s dont2Edge1365/390 ; fichiers/SHA, stockage nonce privé, droits et invariants métier ; [rapport](../../Test/rapport_e2e_reception_client_documents_isole.md) |
| 241 | Diagnostic indicatif de stock des devis | Agent76tests16,71s dont22nouveaux ; cumulDecimal/fraîcheur/services/inconnus, devisrupture201 sansréservation ; UI242 distincte ; [rapport](../../Test/rapport_devis_stock_diagnostic.md) |
| 243 | Cession immédiate et rebut connectés | Agent2Edge25,20s et13connexes0,24s ; oracle VNC/lignes exactes, validation et originaux conservés ; [rapport](../../Test/rapport_e2e_immobilisations_sortie_isole.md) |
| 242 | Alerte de stock en création et édition de devis | Agent2Edge26,62s puis10finaux28,26s ;34connexes après retrait d'une seule assertion statique obsolète ; build138modules4,84s ; [rapport](../../Test/rapport_e2e_devis_stock_alerte_isole.md) |
| 245/250 | Procédures082, dossier pièces et restauration | Principal liens locaux/UTF8 et16blocs PowerShell analysés ; commandes production non exécutées ; [procédure](../EXPLOITATION_HISABPRO.md) |
| 246 | Sauvegarde conjointe DB et pièces | Agent1test28,32s et13connexes11,11s ; neuf tables, trois fichiers, six téléchargements SHA et droits authentifiés, deux clusters nonce ; [rapport](../../Test/rapport_sauvegarde_pieces_documents_isole.md) |
| 247 | Annexe de recette commerciale | Agent4tests2,07s ; cinq cas4Non testé/1Bloqué, PDF12pages/Excel6feuilles ouverts, oracles84/36 MAD ; [rapport](../../Test/rapport_annexe_recette_commerciale.md) |
| 248 | Lecture API des articles au stock inconnu | Principal76tests31,35s dont9nouveaux, contrats sortie NULL/diagnostic et instantanés SQL inchangés ; [rapport](../../Test/rapport_articles_stock_historique_lecture.md) |
| 249 | Stock inconnu dans la page Articles | Agent10tests33,47s dont1Edge, tableau/valeur/champ/tri sans faux zéro ; build5,47s et compilation OK ; [rapport](../../Test/rapport_e2e_articles_stock_inconnu_isole.md) |
| 251 | Quantités hors représentation du diagnostic | Agent35tests API/PG,13nouveaux/22connexes ; cas prouvé500 devenu422, cumulDecimal conservé ; [rapport](../../Test/rapport_devis_stock_limites_numeriques.md) |
| 244 | Globale historique suivante | Principal2255passes,1echec documentaire,0erreur,0ignore1615.64s ; corrige255 et24tests cahier passes, aucune fausse globale verte. |
| 253 | Scroll factures mobile | Agent3Edge troisviewports24.39s,13connexes72.43s,build138modules4.42s ; validation native et zeroecriture. |
| 254 | Totaux devis non finis | Agent127connexes79.26s puis15finaux19.66s ; avantfixPOST/PATCH500 aprescommit reproduits, apres422sansmutation. |
| 255 | Procedure chemin complet pieces | Principal24tests cahier passes, analyse syntaxique PowerShell sans execution. |
| 258 | Cession differee immobilisation | Agent1nouveauEdge puis3finaux61.85s ; creance3481de9000en2025 encaissee2026,6ecritures equilibrees validees, refus400423409404sourcesintactes. |
| 252 | Acompte fournisseur complet | Agent2Edge desktop/mobile jusquAAA,4ecritures9lignesD=C2800,13tests regroupes106.24s. |
| 256 | Bilan detaille cockpit etexports | Agent3nouveauxpasses25.15s,16connexes et1archiveconnectee31.51s ;build9.67s,oracle45000/300/44700. |
| 257 | Scroll lettrage mobile apresselection | Agent3Edge passes33.76s,13connexes106.24s,build5.65s ;clics natifs originaux preserves. |
| 260 | Montants calcules BC/BL | Agent148passes77.34s puis1complement1.09s,compile2OK ;avantfix persistances/GET500reproduits. |
| 261 | Factures calculs avantmutation | Principal30passes18.62s puis10finaux20.27s,compileOK ;notes historiques seulespreservees,aucun plafond arbitraire. |
| 262 | Annexe recette bilan detaille | Agent6testsdocumentairespasses1.59s,PDF9pagesExcel6feuilles ouverts,4casNonTeste avecoracles. |
| 259 | Consolidation des sources jusqu'au lot 262 | Principal : 2 328 réussis, aucun échec, erreur ou test ignoré ; 32 avertissements, 2 330,74 s. 3 304 empreintes conservées ; [rapport](../../Test/rapport_non_regression_globale_20261008_finale.md). Lot 263 absent de cette collecte. |
| 263 | PDF devis/BC aux grands montants | Agent : 24 réussis en 27,57 s (16 nouveaux et 8 FACT9), compilation de trois fichiers OK. PDF réellement ouverts, aucune mutation source, diagnostic explicite si les lettres sont indisponibles ; [rapport](../../Test/rapport_documents_pdf_limites_numeriques.md). |
| 265 | Recherche du catalogue et du schéma DGI actuels | Vérification documentaire : publication officielle de 2010 identifiée, accès actuel indisponible, aucun schéma 2026 présumé ; [sources et limites](SOURCES_DGI_MILLESIME_20261008.md). |
| 264 | Consolidation finale post263 | Principal2343passes,1echec,0erreur,0ignore ; `1 failed, 2343 passed, 32 warnings in 2504.64s (0:41:44)` ; 3305empreintes conservees,16nouveaux PDF collectes ; [rapport](../../Test/rapport_non_regression_globale_20261008_post263.md). |


Les suites se recouvrent : leurs nombres ne sont pas additionnés pour annoncer
un total unique. Les résultats des agents sont distingués des commandes lancées
par le principal. Les échecs intermédiaires et corrections des fixtures ou
sélecteurs sont consignés dans le journal et les rapports de chaque parcours.

Première exécution globale par le principal : **1 552 réussis, 1 échec,
0 ignoré, 393,02 secondes**. Son unique échec était l'ancien scanner RBAC,
collecté avant la correction du ZIP166. Les suites ciblées après correction
ont réussi. Deuxième globale : **1 638 réussis, aucun échec ni ignoré,
738,49 secondes**, collectée avant les lots174 etsuivants. Les nouveaux lots
ont leurs tests ciblés réellement exécutés. La consolidation259 des sources
jusque262 a reussi ; la consolidation264 post263 a termine :2343passes,1echec,0erreur,0ignore.

## Cahier et couverture

Le cahier couvre 218 cas, avec données exactes, étapes utilisateur, impacts,
contrôles et preuves attendues. L'oracle indépendant comporte 50 écritures
fictives ; les fichiers de balances, journaux, banque et justificatifs sont
livrés. Les **208 cas Non testé et 10 Bloqué** représentent la recette
utilisateur à effectuer : aucune réussite utilisateur n'est préremplie.

L'annexe Paie/GRH232 comporte26cas,23Non testé et3Bloqué ; ses30pages PDF et
7feuilles Excel ont été ouvertes. Elle complète le cahier principal sans
transformer une simulation documentaire en paie définitive ou recette réussie.

L'annexe commerciale247 comporte cinq cas, quatre Non testé et un Bloqué
nécessitant un opérateur pour préparer un historique NULL dans un laboratoire.
Ses12pages PDF et6feuilles Excel ont été ouvertes. Les données exactes donnent
84MAD puis36MAD TTC ; aucun résultat utilisateur n'est prérempli.

L'annexe bilan262 ajoute quatre cas Non teste avec oracles independants,
neuf pages PDF et six feuilles Excel ouvertes. L'absence de N-1, sa presence,
les exports et la preservation d'une archive anterieure sont distingues ;
aucune acquisition ou dotation fiscale n'est deduite des OD de presentation.

La matrice distingue terminé, partiel, absent et bloqué. La recette connectée
exécutée cette session utilise des scénarios réduits ; elle ne remplace pas
le scénario annuel intégral du cahier. Les procédures d'installation,
sauvegarde, restauration et déploiement sont fournies avec leurs limites.

Comptage historique alors constaté : matrice **70 fonctions : 15 terminé, 46 partiel, 5 absent,
4 bloqué** ; checklist **73 demandes : 38 terminé, 32 partiel, 2 absent,
1 bloqué**. Ces périmètres ne sont pas additionnés. JUN-07 et AUG20-13 sont
terminés dans leurs scénarios précis ; JUN-03 est livré et testé en UI242
selon la décision d'autoriser les devis à approvisionner avec alerte.

## Protection des données et limites

Aucune connexion au PostgreSQL réel ni mutation de données comptables réelles.
Les PostgreSQL utilisés sont des clusters éphémères avec chemin, marqueur,
nonce, rôle, base et port vérifiés, puis arrêtés et nettoyés par leurs fixtures.
Le vieux banc pouvant muter une cible non isolée est exclu du runner.

Les archives différentielles sont listées et leur CRC contrôlé. Elles excluent
environnements, caches, secrets et dumps. Les anciennes migrations sont
conservées ; aucune réparation historique n'est lancée.

Restent notamment : catalogue exhaustif DGI et schéma EDI officiels du millésime,
annexes ventes/rémunérations/taxe professionnelle, fiscalité autonome du mode
Liasse seule, TVA RAS et recette annuelle complète. Installation expérimentale001–082 vérifiée231 :73SQL uniques,9rejeux et22tables vides ; catalogue stable, droits082 et séquence testés. Privilèges runtime exhaustifs et déploiement restent partiels. Sauvegarde239 conserve huit tables dont GRH/provenance et comptabilité validée ; --no-privileges exclut rôles/ACL. Reprovisionnement minimal082 testé, autres ACL de production restent a verifier. Restauration conjointe246 testee avec9tables et3pieces,6telechargements controles apres arret de la source ; sauvegarde a chaud non validee.
Les pièces historiques FEC/ETIC ne sont pas reconstituées arbitrairement.
La réouverture d'un exercice définitivement clôturé exige une décision métier.

**Développement global : partiel. Tests automatisés : validés sur les périmètres
exécutés. Recette utilisateur : à effectuer. Mise en production : non prête.**
L'archivage interne n'est pas un dépôt fiscal ; aucune certification annoncée.

## Point de reprise

Reprise du8octobre17:52UTC, budget jusqu19:52UTC. La priorite utilisateur256 est livree : bilan detaille dans la liasse, Excel et PDF, totaux preserves et anciennes archives non recalculees. Fournisseur252 et cession differee258 sont testes, scroll253/257 corrige ; montants254/260/261 controles avantmutation. La globale259 a termine2328passes en2330.74s, sources jusque262. PDF263 livre apres24tests ciblés ; consolidation264 post263 terminee :2343passes,1echec,0erreur,0ignore, code1, XML/log complets relus et3305empreintes conservees ;16cas PDF263 inclus. Couverture235 et cumulatif236 actualises apres cette preuve.

La globale234 historique compte2199reussis. La suivante244 compte reellement2255passes,1echec documentaire,0erreur,0ignore en1615.64s. Le chemin complet par defaut des pieces est retabli255 ;24tests cahier reussis ensuite. Cette relance ciblee ne transforme pas244 en globale verte. La consolidation259 a ensuite reussi sur les sources jusque262 ; aucun cumul arithmetique des suites qui se recouvrent.
L'état exact figure dans `CODEX_PROGRESS.md`, via `Test/journal_codex.py etat`.

Prochain parcours independant, analyse en lecture seule et NON execute :
achat fournisseur de deux unites stockables a500HT, TVA20% explicitement
deductible, puis avoir avec retour physique d'une unite et paiement du
reliquat600TTC. Oracle propose : AC debit6111=1000/34552=200,
credit4411=1200 ; AV debit4411=600,credits6111=500/34552=100 ;
banque debit4411=600/credit5141=600. Trois ecritures,huit lignes,
debit=credit2400 ; stock1,4411solde,lettrageAAA attendu. Sans RAS,
acompte ni escompte ; ne pas annoncer ce parcours reussi avant execution.
Fichiers a creer : Test/test_e2e_avoir_fournisseur_isole.py et rapport associe.

## Archives différentielles de cette reprise

Les noms et contenus exacts sont consignés dans
[le manifeste des livraisons](LIVRAISONS_SESSION_20261006_2012.json).
Le ZIP cumulatif contient les dernières versions des seuls fichiers modifiés
de cette reprise, avec arborescence exacte ; il n'inclut pas les ZIPs eux-mêmes.

## Diagnostic prioritaire de reprise

Diagnostic global : XLSX comparative ligne285 porte2026-01-01/12-31 et2025-01-01/12-31 au lieu de mars. Cause racine non prouvee. Cible1passe30.51s etmodule4passes47.93s sans modification ; ne pas contourner assertion. Prochaine action : reproduire reinitialisation tardive des filtres/instantane export puis correction minimale et tests.
Budget17:52-19:52UTC atteint ; prochains changements applicatifs non commences.

## Reprise du 9 octobre 14:04 UTC

Interruption du quota après23:36UTC le8octobre ; reprises274/275/277 uniquement à partir des fichiers présents. AGENTS relu, journal intégral1060422caractères chargé, état actif consulté ; aucun test encore actif, services utilisateur laissés intacts.113archives375versions CRC vérifiées, divergence applicative unique Factures275 attendue. Aucun dépôt Git local.

- **266 — Dates balances et contexte** : 7tests finaux65,47s ;3nouveaux Edge,4exports existants ; cause comparative264 reproduite.
- **267 — Avoir fournisseur retour paiement lettrage** : 5tests96,40s ;3écritures8lignes D=C2400, stock1 etAAA.
- **268 — Articles nombres finis** : 207ciblés19,83s puis38connexes40,47s ; avantmutation, historiques préservés.
- **269 — Frais optionnels article** : 2Edge25,75s +11connexes26,35s ; valeurs persistées, report documentaire manuel.
- **270 — Grand livre contexte tardif** : 3Edge28,41s +26connexes25,27s ; CSV1000/200/800.
- **271 — Achat BC réception facture** : 5tests96,79s ; stock entrée unique à validation facture, liens etunicité.
- **272 — Journal AV recette** : 2Edge28,10s +3connexes54,74s ; doublon actuel non reproduit, sources intactes.
- **273 — Aperçu et sauvegarde libellés** : 1Edge22,85s +49connexes2,37s ; modèles/numéros distincts, historique inchangé.
- **274 — Rapprochement contexte** : 77tests83,75s incluant4nouveaux Edge ; supports synthétiques explicitement distingués, build partagé2757,07s.
- **275 — Édition qualification TVA achats** : 6tests106,47s ;80→1040/160/1200, inconnus préservés etverrouillage409.
- **277 — Annexe corrections utilisateur** : 9tests1,72s ;18pages PDF,7feuilles Excel et8Non testé, rendus réellement vus.
- **279 — Filtre délai tiers** : 4Edge46,08s et9Node115,39ms ;202tiers,NULL etfrontières, aucune mutation.
- **280 — Achats partiels avec stock auBR** : 6 tests finaux en 96,79 s ; deux Edge et oracle 2000/400/2400, stock4 et deux entrées BR.
- **278 — Première globale, échec conservé** : 2575 réussis,4 échecs,0 erreur,0 ignoré,32 avertissements,2079,35s ;623 empreintes identiques.
- **281 — Guide de mise à jour** : 9 liens locaux et3 blocs PowerShell contrôlés, sans déploiement ni accès base.
- **282 — Accès aux preuves CNSS** : Sources primaires ciblées ; preuve CT/LT encore insuffisante, aucun taux installé.
- **283 — Achats partiels payés et lettrés** : 8 tests finaux118,89s ;4 écritures10 lignes D=C4800,4411 soldé,stock4,deuxBR ; cause ancien échec mobile non établie.
- **284 — Annexe achats partiels** : 6 tests documentaires1,02s ; PDF6pages,Excel3feuilles,deux cas Non testé et oracles indépendants.
- **285 — Support simulé de l’édition** : 20 tests1,59s ; dépendances TVA déclarées, assertions et application inchangées.
- **286 — Suite globale finale sources figées** : 2582 réussis, 0 échec, 0 erreur, 0 ignoré ; code retour 0.

Matrice70fonctions : {'terminé': 15, 'partiel': 46, 'bloqué': 4, 'absent': 5} ; checklist73demandes : {'partiel': 30, 'terminé': 40, 'bloqué': 1, 'absent': 2}. Aucun cumul arithmétique des suites superposées. La globale264 reste un échec historique ; sa réussite ciblée ne l’a jamais transformée en globale verte. La nouvelle preuve286 figure dans [son rapport](../../Test/rapport_non_regression_globale_20261009_finale.md).

Le cahier annuel218cas et les annexes restent à exécuter par l’utilisateur ; l’annexe277 apporte huit cas sans prévalidation. Développement global partiel, recette utilisateur à effectuer, mise en production non validée. Référentiels sociaux et EDI applicables, pièces FEC/ETIC et autres limites du registre restent visibles. Aucune migration ni donnée comptable réelle modifiée dans ces lots.

La globale finale a duré **2 024,18 secondes (33 min 44 s)** et conserve 32
avertissements existants. Le XML, le code retour 0 et les 625 empreintes ont été
vérifiés par le principal. Les annexes 277 et 284 complètent le cahier annuel
avec respectivement huit et deux cas utilisateur « Non testé ».

À reprendre : RAS sur règlements partiels, en repartant de l'audit 208 et des
implémentations actuelles. Reproduire d'abord l'imputation au premier paiement
sur une société fictive isolée ; vérifier les qualifications IR/IS/TVA et les
justificatifs requis auprès des sources officielles avant toute règle nouvelle.
Ne pas convertir une estimation documentaire en retenue réellement acquittée.
Les références CNSS et XML/EDI encore insuffisantes restent des blocages distincts.

## Reprise du 9 octobre à 19:44 UTC — RAS

Interruption précédente par limite d'usage ; nouvelle exécution jusqu'à21:44UTC.
Journal actif et processus inspectés, 156 archives/487 versions comparées à16:55
sans divergence applicative ; aucune réapplication. Baseline ancienne récupérée
à19:45 :59tests réussis59,79s, distincte des nouvelles commandes.

- **291** : estimation RAS ne réduit plus le dû sans comptabilisation ; OD entière
  automatique supprimée des nouveaux paiements. Agent44tests55,06s,
  33connexes4,23s et16contrôles22,49s ; principal10tests purs0,22s.
- **292** : estimation/imputation historique et solde autoritaire affichés ; statut
  partiel commercial corrigé. Agent7Edge53,22s+22connexes93,96s, build réussi.
- **294** : preuves BO primaires ciblées et limites CGI consolidé documentées.
  Contrôle principal rectifié :7 occurrences de liens HTTPS,6 URL distinctes ;
  la première assertion sur7URLdistinctes a échoué et reste au journal.
- **295** : recouvrement inconnu visible et CSV diagnostiqué ; agent34tests76,95s.
- **296** : dashboard API conserve NULL, PDF âgé conserve les inconnus et indique
  totaux À vérifier ; agent12tests68,58s, originaux validés inchangés.
- **297** : interfaces dashboard et balance âgée,4Edge45,82s et13connexes78,69s ;
  exports CSV/Excel/PDF ouverts, nombres inconnus vides et diagnostiqués.
- **298** : annexe RAS estimation, deux cas utilisateur Non testé ; PDF6pages,
  Excel3feuilles et9tests documentaires1,56s. Aucun parcours avec capture dans
  cette annexe ; preuve304 référencée séparément.
- **304** : principal4Edge49,81s vente/achat1365/390, paiement1100+100, validation
  journal puisAAA ;3écritures7lignes D=C2400, banque+1200/−1200, collectif0.

Les suites se superposent : leurs nombres ne sont pas additionnés en un total
global. Les échecs avant correction et erreurs de préparation restent dans les
rapports et le journal. Aucun PostgreSQL réel utilisé. Les lots restants et la
nouvelle globale seront consignés à leur achèvement, sans présumer leur succès.

## Reprise du 10 octobre à 00:58 UTC

Budget jusqu'à02:58UTC. Journal actif et processus vérifiés avant reprise ;
services utilisateur conservés, aucune connexion au PostgreSQL réel.
Les lots déjà livrés291/292/294–298/304 ont été contrôlés et conservés.

- **293** : capture déclarative par règlement, OD brouillon, auxiliaire réel,
  contrôles et annulation atomique.42passes100,72s puis29connexes50,66s ;
  dernier test de migration final1pass19,79s après toutes les modifications,
  compilation12Python0. La première commande comptait sept modules, comme
  dans le rapport ; l'annonce intermédiaire de huit est rectifiée308.
- **303** : cinq Edge finaux81,20s, dont vente/achat aux largeurs1365/390 et
  absence de migration sansPOST/DDL.19connexes96,11s, compilation0 et
  build138modules9,88s. Quatre OD/cash validés, cinq lignes AAA délettrées
  avant annulation ; sept écritures/quinze lignes D=C3170, originaux conservés.
- **305** : sauvegarde/restauration réelle sur deux clusters nonce, onze
  tables et huit triggers.1pass35,20s+5connexes14,70s ; rôles/ACL horsdump,
  droits083 reprovisionnés et vérifiés sous une vraie connexion LOGIN.
- **306** : annexe capture PDF9pages et Excel3onglets, deux cas Non testé ;
  9tests documentaires1,40s, compilation0. Pages1/4/5 inspectées par agent,
  page5 également vue par principal ; oracles indépendants2400puis3170.
- **307** : deux Edge40,02s chèque/remise/rejet/virement/validation/lettrage,
  30connexes46,34s. Cinq écritures/onze lignes D=C6000, banque1200 et
  attente/collectif soldés, originaux et refuspermissions contrôlés.
- **308** : deux annulations historiques injustifiées200 reproduites, puis
  résolution exacte unique et refus409 sansmutation si la piste est incertaine.
  7tests20,25s et30connexes71,90s, compilation3Python0 ; cas positifs
  vente/achat et autre règlement actif conservés.

Les résultats ciblés ci-dessus proviennent des agents et ont été relus par
le principal. La nouvelle globale300 est exécutée par le principal sur
645empreintes figées ; son résultat doit être lu séparément à son achèvement.
Les suites qui se recouvrent ne sont pas additionnées.

Les mentions d'absence de changement après build dans les rapports303/307
décrivent l'état au moment de ces livraisons. Le lot308 a ensuite modifié
uniquement le backend et son test ; les sources frontend restent identiques
à celles du build303. La globale300 est encore en cours à ce point de reprise.

Point intermédiaire à01:37UTC : la globale300 signale un échec dans le parcours
navigateur de clôture. Le principal conserve la commande et les sources figées,
puis examinera le traceback final. Résultat global et cause non encore établis.

## Reprise du10octobre à08:14UTC après quota

Nouvelle exécution jusqu'à10:14UTC ; les processus et le delta du journal sont
inspectés avant toute relance. Aucun pytest encore actif ; les services
utilisateur sont conservés. La globale300 a terminé vers02:04UTC pendant
l'interruption : **2627réussis,12échecs,0erreur,0ignoré,32avertissements**,
code1,2386,05s. XML, log et code retour récupérés par le principal ;
**645empreintes identiques**. Son échec est livré séparément et conservé.

Les traces prouvent `NameError: societe_id` dans le calcul du crédit disponible
de l'avoir. Les tests clôture échouent lors de leur préparation d'avoir, avant
le contrôle de clôture ; les hypothèses de synchronisation UI ne sont pas
établies. Le lot309 corrige le rattachement à la société de l'avoir et ajoute
une non-régression RAS. Tests et livraison à consigner après exécution réelle.

Le lot309 a depuis été livré :33tests finaux58,90s après les deux corrections
(société et verrou PostgreSQL ciblé). Les huit Edge du principal166,68s
portent sur la version après correction de société, avant correction du verrou ;
la prochaine globale est une preuve distincte sur la version complète.

## Livraison demandée — reprise du10octobre à09:36UTC

La limite de quota a interrompu l'agent frontend. Son dernier résultat92900
n'a pas été récupéré et n'est pas déclaré réussi. Le principal reprend les
processus et le journal puis limite cette exécution à la finalisation des lots
en cours, à leur consolidation et au cumulatif ; aucun autre chantier ouvert.

Lot310 : sept nombres historiques projetés sousNULL avec diagnostics ;
prix/TVA inconnus vides, PATCH limité aux champs modifiés, création/édition
commerciale bloquée jusqu'aux valeurs explicites. Deux mises à jour de taux
et qualification perdaient le choixTVA : correction atomique, tests conservés.
Les résumés HT échappant au diagnostic sont également corrigés.

Preuves backend de l'agent :92réussis23,44s et230connexes40,80s. Preuves finales
du principal :3tests47,20s dont2Edge,5connexes88,95s, compilation4Python0,
build139modules12,72s0. Les erreurs de fixture et les défauts réels rencontrés
restent détaillés dans [le rapport310](../../Test/rapport_articles_historique_nombres_lecture.md).
Le ZIP310 a été listé et ses CRC vérifiés, onze fichiers dont journal/manifeste.

La nouvelle globale311 a été lancée vers09:40UTC sur649empreintes figées.
Résultat principal relu après fin : **2 734 réussis, 4 échecs, 0 erreur,
0 ignoré, 32 avertissements, code1 en3 150,16s**. Les649empreintes restent
identiques. Deux échecs articles sont des lecturesPOST du stock comptées
à tort comme modifications ; le lot312 corrige cette mesure exacte en
gardant les refus métier et ajoute une relecture des documents inchangés.
Les deux autres échecs sont des délais navigateur avant navigation/login ;
leur cause n'est pas établie. La globale311 demeure une preuve d'échec.
Les relances finales du lot312 donnent **13réussites140,11s**, code0,
25avertissements : articles, achats partiels et recouvrement. Les quatre
cas échoués311 passent. La première relance312 avait11réussites2échecs
124,92s : le contrôle supplémentaire omettait le paramètre exercice duGET,
corrigé depuis le document source. Compilation du test0, aucun code produit
modifié. Voir [rapport312](../../Test/rapport_e2e_articles_diagnostic_stock_mesure.md).
Aucune addition des suites ni transformation rétrospective en succès.
La couverture reste70fonctions15terminé/46partiel/5absent/4bloqué et
73demandes40terminé/30partiel/2absent/1bloqué. Limites inventaire, familles,
coûts historiques, fiscalité complète, CNSS et EDI maintenues ; recette humaine
et production non validées. Aucun PostgreSQL réel ni aucune donnée réelle utilisés.

Développement global partiel ; RAS réglementaire complète, référentiels
sociaux et XML/EDI applicables restent soumis aux limites documentées.
Recette utilisateur à effectuer et production non validée. Voir
[la note de reprise RAS](../REPRISE_RAS_SESSION_20261009.md) et
[le guide d'activation isolée](../MISE_A_JOUR_RAS_20261009.md).

## Reprise du 10 octobre, 10:45 UTC — lots313–315

313 livré : inventaire/clôture/livre/PDF inconnus diagnostiqués, refus avant mutation, UI bureau/mobile et valeurs zéro connues préservées. Principal148réussites60,73s, agent4Edge46,66s, build139modules4,93s et compilations0. Le ZIP17fichiers est vérifié. [Rapport et échecs intermédiaires](../../Test/rapport_inventaire_nombres_historiques.md).

314 actualise la couverture sans changer les totaux70fonctions/73demandes.
La globale315 termine avec2742réussites49échecs5erreurs0ignoré,32avertissements
3410,26s ;653sources identiques, fichier exit du wrapper non récupéré.
L’échec est établi par XML/log et reste historique.52incidents concernent
les processus Node/driver, deux sont des délais navigateur.

## Reprise du 10 octobre,14:34 UTC

- 318 : périodes effectivement insérées avant trigger de l’écriture sur
  exercice implicite ; calendriers partiels/verrous conservés.60tests passent,
  dont8nouveaux,41,79s. [Rapport318](../../Test/rapport_exercice_implicite_periodes.md).
- 320 : polices Inter/Tabler locales, licences/empreintes et vrai service des
  assets dans le banc ; deux Edge avec CDN muets42,17s, build139modules6,93s.
- 324 : familles inconnues projetées NULL et choix TVA explicite article ;
 347backend79,79s,4nouveaux Edge29,99s puis6connexes85,04s, historiques intacts.
  [Rapport324](../../Test/rapport_familles_tva_historique.md).
- 326 :4962glyphes décoratifs gardent leur affichage et n’altèrent plus les noms
  accessibles ; quatre Edge chargement/accessibilité48,62s. [Rapport326](../../Test/rapport_icones_accessibles.md).
- 327 : retests et diagnostics distincts,54réussites pendant intégration puis
  53réussites/1échec101,73s sur670empreintes identiques. L’alerte de succèsBR
  survenant après début de navigation est effectivement capturée ; les causes
  système des incidents historiques Node/driver ne sont pas démontrées.
  [Preuves327](../../Test/rapport_retests_globale315.md).
- 330 : retourBR immédiat non bloquant, quatre Edge60,01s dont cycles achats
  jusqu’au règlement/lettrage ; build final139modules4,75s. [Rapport330](../../Test/rapport_facturation_br_retour_non_bloquant.md).
- 317/323/329 : annexe inventaire19cas et guide utilisateur Word/PDF22pages,
  18fiches17statuts Non testé. OOXML/PDF/chemins/oracles vérifiés, aucun résultat
  de recette humaine prérempli. [Word actualisé](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx).

La [globale325](../../Test/rapport_non_regression_reprise_20261010_1434.md)
a terminé le 10 octobre à 15:54:50 UTC : 2 853 réussis, aucun échec, erreur
ou ignoré, 32 avertissements, 2 973,36 s, code retour 0. Les 675 empreintes
des sources/SQL/tests/configurations/assets publics restent identiques à la
reprise de 19:39 UTC. Les suites ciblées superposées ne sont pas additionnées.
Tous les clusters de tests sont nonce ; aucun PostgreSQL utilisateur ni
donnée comptable réelle modifié. Les anciens échecs restent historiques.

Les statuts restent70fonctions15terminé/46partiel/5absent/4bloqué et
73demandes40terminé/30partiel/2absent/1bloqué. Les alertes stock et autres
moteurs historiques sont des consommateurs distincts encore à sécuriser.
Recette utilisateur à effectuer, conformité réglementaire non certifiée,
mise en production non validée.

## Reprise du 10 octobre, 19:39 UTC

Le résultat325 a été récupéré après quota, confirmé par log/XML/code effectif
et675empreintes identiques ; ZIP325/328 puis cumulatif1434 livrés et vérifiés.
Les lots332–334 ont ensuite leurs propres preuves, distinctes de325 :

- 332 alertes brutes : agent5échecs reproduits puis19réussites36,29s.
- 333 schéma de sortie des mouvements : principal45réussites, XML40,328s.
  Les deux cas de préparation invalides ont été remplacés par des contrôles
  de refus PostgreSQL, sans lever les contraintes ; anciennes preuves conservées.
- 334 auditCMUP/UI : principal36échecs baseline,71réussites puis deux Edge
  réussis ; run final95réussites, XML52,287s. Nombres absents/non finis,
  booléens/texte, débordements produit/somme, chaîneCMUP, contrôles indépendants,
  filtre, sociétés et conservation SQL réellement contrôlés. Build139modules7,89s0.
- 337 mode d'emploi version3 : Word contrôlé en OOXML, PDF23pages et11références
  locales, oracles indépendants vérifiés ;17statuts utilisateur Non testé.
- 335 moteur stock et gardes articles : agent106réussites98,28s, dont52cas
  nouveaux ; les sources de toutes les compensations sont qualifiées avant
  leur première mutation. Origines, coûts explicites, fractions, idempotence,
  sociétés et périodes fermées contrôlés ; baselines historiques conservées.
  [Preuves335](../../Test/rapport_mutations_stock_historique.md).
- 339 procédure de mise à jour actualisée et livrée :11liens locaux existants,
  quatre ZIPs stock sans SQL vérifiés ; aucun déploiement réel exécuté.

La limite d'usage de l'agent334 n'a modifié aucune source. Le principal a
repris ce lot et exécuté ses tests. Aucune base réelle ou migration modifiée.

La consolidation336 a terminé à21:15:28UTC : **3009réussis,0échec,0erreur,
0ignoré,32avertissements,4072,44s,code0**. Le principal a relu le XML,
le code de sortie et les680empreintes figées avant/après. Les cycles connectés
facturation→validation→règlement→lettrage ont réellement été exécutés sur
les bancs isolés, ainsi que les tests connexes de clôture/exports/GRH.
L’ancien banc PostgreSQL non isolé reste exclu. [Rapport336](../../Test/rapport_non_regression_reprise_20261010_1939.md).

Après cette consolidation, le lot341 reproduit neuf erreurs500 au BR,
avec quatre témoins réussis. Trois lignes de calcul du coût sont déplacées
dans le `try` existant : refus409 avec rollback intégral, même si une première
ligne saine avait commencé son entrée. Les **122tests ciblés/connexes**
passent227,75s,25avertissements,code0, dont trois Edge achats/vente ;
compilation2fichiers OK. Le principal relit le XML et contrôle681empreintes
stables, avec exactement deux changements source/test depuis336. Aucune
globale nouvelle après341 n’est revendiquée. [Rapport341](../../Test/rapport_br_cout_historique.md).

Le guide342 version4 Word/PDF est régénéré :23pages,18fiches,17statuts
Non testé,385blocs. Il précise le déclencheur d’entrée de stock à la réception,
les dates2025, le paramétrage des préfixes et le dépannage BR. OOXML/CRC,
11références, oracles indépendants et pages11/12/23 sont contrôlés ; la
procédure a11liens et cinq ZIPs sans SQL vérifiés. Une ébauche24pages avec
paragraphe isolé a été corrigée avant livraison. [Preuves342](../../Test/rapport_guide_stock_br_342.md).

Développement global : **partiel**. Tests automatisés : preuves336 avant341
et ciblés341 distinctes. Recette utilisateur : **à effectuer**. Mise en
production : **non validée**. Les70fonctions et73demandes gardent leurs
statuts. Le cumulatif final de cette fenêtre est préparé après livraison338 ;
le budget de reprise se termine à21:39UTC. Prochaine reprise : suivre les
contrôles du guidev4 et qualifier les autres consommateurs historiques de
stock/commercial sans inventer de prix, de justificatifs ou de règles fiscales.

## Reprise du 10 octobre, 21:29 UTC

Les archives et le reçu final1939 ont été vérifiés avant les nouveaux
changements ; processus utilisateur préservés. Le workspace n’a pas de
dépôtGit. Les nouvelles corrections sont isolées de la livraison précédente.

- 343 : prix nécessaireNULL transformé en0 et réponse500 après commit de
  montants non représentables réellement reproduits. Photos SQL nonce
  conservées. Prix et totaux contrôlés avant commit,409 avec rollback.
  Finale69réussites240,15s,25avertissements,code0, dont sept Edge ;683hashes
  stables et compilation3fichiers OK. Les préparations E2E corrigées
  (exercice requis, BR reçu) restent documentées avec leurs échecs initiaux.
  [Rapport343](../../Test/rapport_conversion_bon_prix_historique.md).
- 344 : dix validations invalides persistaient réellement facture/lignes/
  numéro dans la baseline nonce. La garde partagée qualifie les sources
  monétaires avant le calcul, puis protège validation normale/proforma
  avant réservation et snapshots. Finale91réussites170,78s,25avertissements,
  code0, dont58nouveauxAPI et quatre Edge ;684hashes stables, compilation2OK.
  Les baselines16échecs/12réussites et30échecs sont conservées.
  [Rapport344](../../Test/rapport_validation_facture_montants_historiques.md).
- 345 : guideversion5 Word/PDF23pages,18fiches17statuts Non testé,
 387blocs ; contrôlesOOXML/CRC/11références/oracles/pages7et23 réussis.
 Procédure11liens et deux ZIPs343/344 sansSQL vérifiés, prérequis342 explicite.
 [Preuves345](../../Test/rapport_guide_montants_345.md).
- 346 : nouvelle globale lancée21:53:38UTC,3112cas collectés,
 684sources/tests/SQL/assets figés. Exécution en cours ; résultat non
 revendiqué avant code/XML/empreintes finaux. [Suivi346](../../Test/rapport_non_regression_reprise_20261010_2129.md).

Aucune base réelle, environnement utilisateur ou écriture comptable réelle
modifié. Aucune migration, taux ou formule fiscale nouveau. Les statuts
70fonctions et73demandes restent inchangés ; recette humaine, justificatifs
historiques et production restent des validations distinctes. Le budget de
la reprise est23:29UTC ; les livraisons343–345 sont vérifiées avant poursuite.

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

## Reprise11octobre11:05UTC — correction de lecture363

Reprise réelle du journal et des processus. Le cumulatif précédent33fichiers
était intègre et identique au dépôt. Aucun Git local ; services utilisateur
préservés. Aucun ancien correctif réappliqué.

363corrige le défaut359 :JSON200 qualifié, pièces et identifiants conservés,
inconnus explicitement nullable, détail en lecture seule et actions/CSV protégés.
Le calcul financier partagé refuse une source inconnue ; les taux etrègles
fiscales existants sont conservés. Aucun montant historique remplacé par zéro.
Les refus etlectures sont photographiés sur le seul PostgreSQL nonce.

Tests :40ciblés réussis,6sources globales/avoirs liés réussis,8Edge finaux
réussis ; diagnostic original8réussis. Les erreurs initiales d'import etde
précondition de photographie sont consignées etleurs oracles conservés.
Compilation0 etbuild4,79s0. Aucun succès n'est présumé pour la consolidation365.
[Rapport363](../../Test/rapport_lecture_factures_historiques_363.md).

Guide364v9 :26pages398blocs ;18fiches17Non testé. CRC/XMLrelations ettexte
de chaque page vérifiés ;page7 inspectée. Contrôle visuel complémentaire réel
sur1365/390 :modals698/698 et388/388,aucun débordement horizontal ni erreurJS/API,
photographies conservées. Office etrecettehumaine restent à effectuer.
[Rapport364](../../Test/rapport_guide_lecture_364.md).

Couverture70fonctions :15terminé,46partiel,5absent,4bloqué. Les statuts ne
sont pas promus arbitrairement. Développement global partiel, production
nonvalidée. Aucun PostgreSQL réel,migration ou écriture comptable réelle touché.


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
