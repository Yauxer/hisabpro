# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Version 1 du 23 octobre 2026. Complément 755 : scénario annuel intégré du mode « Liasse seule ».

## Objet et périmètre

Ce parcours relie une société fictive neuve, le logo, les balances 2026/2025, le bilan/CPC, B12, CM, CSS, crédits, acomptes, proposition de solde et dossier PDF/Excel/ZIP. Il complète le cahier global HisabPro. Les opérations de travail ci-dessous expliquent les CSV ; l’import ne les comptabilise pas dans le Journal. Les parcours facturation, clôture, archivage définitif et dépôt conservent leurs recettes dédiées.

Résultat attendu : bénéfice fiscal 120000 MAD, IS24000 MAD, acomptes imputables 20000 MAD, crédits encore disponibles 350 MAD, solde IS/CM proposé 3650 MAD ; CSS0 affichée séparément. Aucun paiement, liquidation définitive ou dépôt confirmé.

Utiliser un environnement isolé et une société fictive. La recette humaine reste Non testé, même lorsque les parcours automatisés ont réussi. Les fichiers et attestations sont fictifs, sans valeur fiscale réelle. La date de contrôle 15/03/2027 appartient au scénario pour représenter un exercice 2026 achevé ; elle ne nécessite aucun changement de l’horloge du poste.

## Fichiers fournis

- `BALANCE_FICTIVE_FISCALE755_N.csv` : neuf comptes 2026, débit=crédit 258000 MAD.
- `BALANCE_FICTIVE_FISCALE755_N1.csv` : six comptes 2025, débit=crédit 127500 MAD.
- `DONNEES_FISCALES755.json` : opérations, ouverture, balances et montants attendus exacts.
- `JUSTIFICATIFS_FICTIFS755.pdf` : notes B12/CM/CSS, attestations CR755-A/B, affectations et quittances AP755-Q1 àQ4, PV fictif.
- `LOGO_FICTIF755.png` : logo bleu de test à utiliser dans les paramètres.
- `CAHIER_RECETTE_FISCALE_755.xlsx` : suivi humain, opérations, paramètres et calculs indépendants.

Les montants sont en MAD, avec point décimal dans les fichiers et deux décimales au maximum. Les libellés des comptes sont ceux du plan HisabPro existant. Ne pas remplacer un compte par un libellé libre pour faire disparaître un contrôle.

## Comprendre le jeu annuel

Société fictive : ATLAS CONSEIL RECETTE755 SARL, Casablanca, MAD, IS de droit commun ; activité antérieure aux périodes d’exonération CM, aucun régime particulier ou déficit dans ce scénario. Les prestations et honoraires sont supposés taxables à la TVA20%. L’État/organisme public qui verse les honoraires est explicitement qualifié ; les autres clients sont des sociétés privées hors nouvelle obligation de retenue de ce scénario.

En 2025, capital 10000, prestations 100000HT et TVA20000, intégralement encaissées. TVA20000 réglée. Acomptes IS17600, impôt 2025 de 17500 (100000×17,5%), résultat net 82500. La balance avant clôture technique porte banque 92400, acomptes 3453=17600 et dette IS4453=17500. Actif=passif 110000. La liquidation fictive 2025 laisse 100 d’excédent ; l’ouverture puis le PV AGO15/03/2026 affectent le résultat au report 1161. Aucun compte 119 technique dans les CSV à importer.

En 2026, les honoraires/services facturés totalisent 140000HT, dont 4000 à l’organisme public et 136000 à des clients privés. TVA collectée 28000. Le paiement public 4800TTC est reçu 4600 en banque et 200 en retenue IS5% ; autres encaissements 163200. Les charges d’honoraires fournisseur sont 21500HT, TVA récupérable 4300, règlement 25800. Les intérêts de placement sont 1500 brut, PPRF20%=300 et banque 1200. TVA Q1 créditrice 4300, imputée sur Q2, puis solde 23700 réglé le 15/07/2026.

Les versements d’acomptes 2026 sont 4800,4950,5000 et 5000, soit 19750cash. Ils sont complétés par 100 d’excédent antérieur et 150 de retenues affectées. La provision IS2026 est 24000. Les retenues et l’ancien excédent ne créent pas une deuxième écriture lors de leur affectation documentaire aux acomptes.

Au 31/12/2026 : banque 192150, actif fiscal 3453=20350, dette IS4453=24000, capital 10000, report 1161=82500. Produits 140000+1500, charges 21500+24000, résultat net 96000. Actif 212500=passif 212500. La différence dette IS24000−actif fiscal 20350 explique le solde 3650. Le paiement futur de ce solde n’est pas inclus dans les opérations 2026.

## Étape 1 — Société et logo

Depuis l’écran de connexion du laboratoire, cliquer « Créer un compte ». Saisir Votre nom = Admin recette fiscale 755, Raison sociale = ATLAS CONSEIL RECETTE755 SARL, Ville = Casablanca, email de test = recette 755@example.com, mot de passe de test = Recette 755!Local 2026 ; cliquer « Créer mon compte ». Utiliser une variante d’adresse si elle existe déjà dans le laboratoire. Aucune adresse réelle n’est nécessaire.

Ouvrir Paramètres. Dans « Logo de la société », choisir LOGO_FICTIF755.png, vérifier l’aperçu puis « Enregistrer ». Conserver la devise MAD. Le plan par défaut et l’exercice 2026 doivent être disponibles ; si un exercice doit être préparé, le faire sur cette société fictive avant la recette. Pour le rôle comptable, un admin prépare le compte puis lui confie ce parcours ; dans le banc automatisé, ce compte secondaire est créé par l’API de test, puis toutes les opérations fiscales sont réalisées dans le navigateur.

## Étape 2 — Importer N et N-1

Ouvrir Comptabilité → Liasse fiscale, sélectionner l’exercice 2026. Dans « Préparer depuis des balances externes », cliquer « Importer N / N-1 ». Balance N = fichier 755_N.csv ; Balance N-1 facultative = fichier 755_N1.csv. Cliquer « Contrôler et préparer », puis vérifier les chiffres avant « Conserver une nouvelle version ».

Attendus : neuf comptes N,258000 de chaque côté ; N-1,127500 ; bilan N212500 de chaque côté et résultat net CPC96000 ; N-1, bilan 110000 et résultat 82500. Version 1 conservée, aucun Journal créé. Les CSV sont avant clôture technique ; les résultats sont déterminés depuis les classes 6/7, sans compte 119 de transfert.

## Étape 3 — B12

Ouvrir « Préparer le passage fiscal B12 depuis la balance ». Déclaration = Saisie documentée — à revoir. Justification = « Jeu annuel fictif 755, opérations et balances vérifiées ». Ajouter une ligne.

Désignation = B12 annuel fictif 755 ; Autres réintégrations hors 67 =0 ; Déductions fiscales =0 ; Déficit disponible déclaré et justifié =0 ; Taux IS déclaré =20. Régime = « Droit commun 2026, aucun avantage, retraitement ou déficit pour ce scénario ». Référence = NOTE755-B12. Confirmer puis conserver.

Attendus : net 96000 + impôts comptabilisés 24000 = résultat avant IS120000 ; bénéfice fiscal 120000 ; IS théorique 24000. L’impôt comptabilisé est réintégré une fois, sans ajouter une deuxième réintégration 24000 dans le champ hors 67.

## Étape 4 — CM et CSS séparée

CM : ouvrir « Calculer la cotisation minimale — 2026 », déclaration documentée et justification « NOTE755-CM, régime et absence d’exonération vérifiés ». Ajouter une ligne : désignation CM755 ; régime IS hors forfait non-résident ; base exclue 0 ; base réduite 0 ; exonération totale non ; minimum exonéré non ; référence NOTE755-CM. Confirmer et conserver. Base 141500, calcul 353,75, minimum 3000, CM proposée 3000, maximum IS/CM24000.

CSS : ouvrir « Calculer la CSS — 2026 ». Déclaration documentée, justification NOTE755-CSS. Ajouter une ligne : désignation CSS755 ; périmètre Société relevant de l’IS ; exercice fiscal de référence 2025 ; bénéfice net fiscal 100000 ; dernier exercice clos confirmé oui ; exonération permanente non ; référence NOTE755-CSS. Conserver : CSS0, sur une base explicitement fournie, distincte de l’IS. Aucun calendrier CSS n’est inventé depuis la seule année.

## Étape 5 — Crédits

Ouvrir « Qualifier les crédits IS — 2026 ». CR-PROFIL documenté, justification NOTE755-CR. Ligne : désignation Crédits 755 ; périmètre Société IS hors exonération totale ; période confirmée oui ; liste exhaustive oui ; absence de crédit non ; référence NOTE755-CR.

Sélectionner CR-LIGNES, documenté, justification « Attestations fictives CR755-A/B ».

Ligne 1 : désignation PPRF bancaire 755 ; type PPRF — CGI159 ; exercice 2026 ; date retenue 20/03/2026 ; date allocation et payeur article 157 laissés vides pour ce PPRF ; éligibilité oui ; montant 300 ; déjà sur acomptes 100 ; autres utilisations 0 ; référence CR755-A.

Ligne 2 : désignation Conseil organisme public 755 ; type Rémunérations de tiers — CGI157 ; exercice 2026 ; retenue 20/06/2026 ; allocation 20/06/2026 ; payeur Public ou filiale publique ; éligibilité oui ; montant 200 ; déjà sur acomptes 50 ; autres utilisations 0 ; référence CR755-B. Confirmer et conserver les deux tableaux ensemble : total 500, déjà utilisé 150, disponible 350.

## Étape 6 — Acomptes

Ouvrir « Qualifier les acomptes IS — 2026 ». AP-PROFIL documenté, justification NOTE755-REF. Désignation Acomptes 755 ; périmètre Société relevant de l’IS ; régime Quatre acomptes — exercice de douze mois ; référence annuelle ajustée 2026 =20000 ; référence fiscalement qualifiée oui ; exercice référence 2025 ; dernier clos confirmé oui ; excédent antérieur disponible 100 ; origine 2025 ; solde d’excédent 170-IV qualifié oui ; mouvements exhaustifs oui ; absence non ; date contrôle 15/03/2027 ; référence NOTE755-REF.

Référence 20000 = bénéfice 2025 de 100000×taux applicable 2026 de 20%, et non l’impôt 2025 de 17500 recopié.

Dans AP-LIGNES documenté, justification « Quittances fictives AP755-Q1 àQ4 », ajouter quatre lignes :

- Ligne 1 : désignation Acompte 1 ; numéro 1 ; date 31/03/2026 ; versement 4800 ; excédent antérieur 100 ; retenue 100 ; référence crédit CR755-A ; rattachement confirmé oui ; référence source AP755-Q1.
- Ligne 2 : désignation Acompte 2 ; numéro 2 ; date 30/06/2026 ; versement 4950 ; excédent 0 ; retenue 50 ; crédit CR755-B ; confirmation oui ; source AP755-Q2.
- Ligne 3 : désignation Acompte 3 ; numéro 3 ; date 30/09/2026 ; versement 5000 ; excédent 0 ; retenue 0 ; référence crédit vide ; confirmation oui ; source AP755-Q3.
- Ligne 4 : désignation Acompte 4 ; numéro 4 ; date 31/12/2026 ; versement 5000 ; excédent 0 ; retenue 0 ; référence crédit vide ; confirmation oui ; source AP755-Q4.

Confirmer et conserver : cash 19750 ; ancien 100 ; retenues 150 ; total 20000 ; quatre échéances 5000 couvertes selon déclarations ; chaque reste 0. Le rapprochement par justificatif recoupe 100 pour CR755-A et 50 pour CR755-B. Excédent antérieur restant 0.

## Étape 7 — Proposition du solde

Ouvrir « Proposer le solde IS/CM — 2026 ». LIQ-N documenté ; justification « REVUE755, calculs indépendants et justificatifs fictifs ». Ajouter une ligne : désignation Revue annuelle 755 ; oui pour taux/régime/déficits B12 vérifiés, qualification CM vérifiée, crédits/acomptes exhaustifs vérifiés, solde antérieur vérifié et ordre de simulation examiné et justifié. Excédent antérieur à utiliser annuellement 0 ; référence REVUE755.

Confirmer et conserver : proposition conditionnelle disponible, maximum 24000−crédits disponibles 350−acomptes 20000=3650 MAD. CSS0 séparée ; excédent arithmétique 0 ; version 7 si aucune version intermédiaire n’a été créée. L’ordre de simulation doit être examiné pour le dossier ; ce cas ne prouve pas une priorité légale universelle ou un droit à restitution.

## Étape 8 — Dossier et preuves

Télécharger le dossier de préparation ZIP. Ouvrir PDF et Excel : logo valide, banque 192150, bilan 212500, CPC96000, IS24000, acomptes 20000, crédits 350 et solde 3650. Le fichier liquidation_is_documentaire.json reprend les contrôles et sources ; total global IS+CSS reste nul au sens JSON null, pas égal à un montant 0 inventé. Les confirmations de paiement/liquidation/prêt à déposer restent fausses.

Si souhaité, joindre JUSTIFICATIFS_FICTIFS755.pdf à la version 7 depuis « Justificatifs complémentaires de cette version » → Fichier justificatif → Référence documentaire = Dossier annuel fictif 755 → « Joindre et conserver le justificatif ». Le document conserve ses octets et sa trace ; ce dossier fictif ne constitue pas des quittances fiscales réelles. Ce complément est vérifié dans la restauration automatisée ; la recette humaine du dépôt dans cette version reste à effectuer.

Le manifeste SHA256 donne taille et empreinte de chaque autre fichier du ZIP. Les CSV exportés sont normalisés, les libellés facultatifs des fichiers d’entrée ne sont pas une réécriture du plan. Revenir à la première version : elle reste inchangée et sans les compléments ajoutés ensuite. Aucun F5 n’est nécessaire après chaque conservation.

## Contrôles négatifs

Sur des versions de travail distinctes, une balance dupliquant 1111 ou un montant NaN doit être refusé sans nouvelle préparation. Pour la retenue de juin, choisir volontairement Banque ou assurance au lieu de Public laisse l’éligibilité à qualifier avant l’entrée en vigueur de juillet ; les nouveaux acomptes puis la proposition deviennent indisponibles. Corriger les faits uniquement d’après les justificatifs du jeu, puis conserver de nouveau crédits, acomptes et revue.

Inverser seulement les références des deux retenues peut laisser l’écart global 150−150=0, mais le rapprochement individuel échoue. Modifier B12 laisse l’ancienne CM et l’ancienne proposition figées pour mémoire ; actualiser les contrôles dépendants avant une nouvelle simulation. Une case vide reste inconnue. Les états historiques ne sont pas réparés pour obtenir un contrôle vert.

## Cas humains et suivi

Renseigner le résultat réel, les anomalies et les preuves dans le classeur. Les quatorze cas restent Non testé jusqu’à leur exécution humaine. Les écritures de travail sont disponibles dans les feuilles Opérations ; aucune écriture n’est attendue dans le Journal du seul fait de ce mode.

| ID | Actions à effectuer | Résultat attendu et preuve | Statut |
|---|---|---|---|
|F755-01|Créer le compte/société fictive puis enregistrer LOGO_FICTIF755.png selon étape 1.|Société neuve MAD, logo visible ; aucun Journal. Capture identité et paramètres.|Non testé|
|F755-02|Importer les deux CSV, contrôler puis conserver selon étape 2.|N258000/N1 127500, bilans 212500/110000, résultats 96000/82500 ; version 1. Capture comparatif.|Non testé|
|F755-03|Saisir B12 avec hors 67=0, déductions 0, déficit 0 et taux 20 ; conserver.|Avant IS et bénéfice 120000 ; IS24000 ; pas de double réintégration des 24000 déjà comptabilisés. Capture B12.|Non testé|
|F755-04|Saisir la qualification CM normale, exclusions/réduction 0 et exonérations non.|Base 141500, CM calculée 353,75, exigible 3000, maximum 24000. Capture source/calcul.|Non testé|
|F755-05|Saisir CSS2026 sur dernier clos 2025 et bénéfice fiscal 100000 justifié.|CSS0 explicitement calculée ; aucun résultat comptable ou calendrier supposé. Capture CSS et référence.|Non testé|
|F755-06|Saisir profil crédits et deux attestations 300/200, déjà utilisées 100/50, autres 0.|Total 500, déjà 150, disponible 350. Allocation/public juin qualifiés. Captures des deux lignes.|Non testé|
|F755-07|Saisir profil référence 20000 et quatre mouvements 4800/4950/5000/5000 avec affectations exactes.|Cash 19750+ancien 100+retenues 150=20000 ; quatre échéances couvertes, restes 0. Capture rapprochements et échéancier.|Non testé|
|F755-08|Saisir revue annuelle, cinq confirmations et excédent annuel 0 ; conserver.|Solde 3650, CSS0 séparée, aucun paiement/liquidation confirmé. Capture finale et numéro de version.|Non testé|
|F755-09|Télécharger ZIP/PDF/Excel, contrôler logo, montants, manifeste et anciens snapshots ; joindre le PDF fictif si souhaité.|Exports de même version ; JSON solde 3650 ; fichier joint traçable ; première version intacte. Conserver les fichiers et SHA.|Non testé|
|F755-10|Refaire avec comptable sur 390 px puis consulter avec un lecteur préparé par l’admin.|Comptable peut conserver ; lecture ne peut pas modifier ; pas de débordement global. Captures rôles et viewport.|Non testé|
|F755-11|Sur copie de travail, changer le payeur de CR755-B en Banque ou assurance avec allocation 20/06 ; conserver puis actualiser AP et revue.|Disponible inconnu pour les nouvelles versions ; aucune date d’effet inventée. Corriger Public d’après la pièce fictive puis actualiser pour retrouver 3650. Captures des deux états.|Non testé|
|F755-12|Sur copie, inverser seulement les références de crédits des deux affectations ; conserver.|Écart global 0 possible, rapprochements individuels incohérents, aucun total imputable proposé. Capture des deux références.|Non testé|
|F755-13|Changer B12 et conserver ; consulter l’ancienne proposition puis tenter une nouvelle avant actualisation CM.|Ancien 3650 figé et averti ; nouveau solde indisponible tant que les sources ne sont pas synchronisées. Capturer le parcours.|Non testé|
|F755-14|Dans une copie des CSV, dupliquer 1111 puis tester un montant NaN ; tenter les deux imports.|Refus sans préparation supplémentaire et sans écriture ; message lisible. Conserver CSV erroné et capture du refus.|Non testé|

## Limites et critères d’acceptation

Les calculs indépendants doivent recouper les six contrôles, le bilan/CPC et les exports. Les versions et justificatifs doivent rester intègres ; aucune écriture comptable réelle n’est créée. La liste des cas humains et les preuves réelles restent à compléter. Les tableaux ETIC/annexes non documentés restent à compléter ; le dossier n’est pas présenté comme une liasse complète prête à déposer. Le schéma officiel XML/EDI, le calendrier CSS et les qualifications réelles restent distincts de cette recette. RH/paie et le point 6 humain restent différés.
