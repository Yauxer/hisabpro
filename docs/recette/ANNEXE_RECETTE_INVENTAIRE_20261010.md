# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

## Annexe inventaire — 10 octobre2026 — lot317

Cette annexe complète le cahier annuel218cas. Elle ne remplace ni sa recette de clôture ni une liquidation fiscale. Les19cas utilisateur commencent Non testé (16) ou Bloqué (3), jamais Réussi. Les148tests et4Edge313 ont été exécutés sur leurs propres fixtures ; le scénario entier achat→paiement→inventaire de cette annexe n’a pas été exécuté ici. Aucune conformité réglementaire, recette humaine ou production automatiquement validée. Ne jamais modifier une écriture définitive pour masquer un écart ; préparer les historiques inconnus uniquement dans un cluster isolé vérifié. Le technicien ouvre la base de recette, le testeur suit les actions interface. Ne jamais saisir les valeurs NaN/Inf via SQL réel.

## Données exactes

- **Société** : RECETTE INVENTAIRE 313 SARL — fictive, société distincte du dossier annuel
- **Utilisateur** : Administrateur recette ; email inventaire313@example.com ; mot de passe choisi par le testeur
- **Exercice** : 2025 ; début01/01/2025, fin31/12/2025 ; ouvert, sélectionné avant toute opération
- **Devise** : MAD ; régime fiscal/TVA à qualifier pour le laboratoire, aucun identifiant légal inventé
- **Fournisseur** : FOURNISSEUR FICTIF INV313 ; délai30jours ; compte collectif4411
- **Article principal** : INV313-M ; Marchandise recette ; stockable ; unitéunité ; stock initial0 ; achatHT20 ; venteHT30 ; TVA20 ; frais0 ; seuil0
- **Article zéro** : INV313-Z ; Zéro connu ; stockable ; stock initial0 ; achatHT0 ; venteHT0 ; TVA0 ; frais0 ; seuil0
- **Comptes** : 1111 capital ; 5141 banque ; 6111 achat ; 34552 TVA récupérable sur charges ; 4411 fournisseur ; 3111 stock ; 6114 variation. Choisir les libellés exacts du plan chargé.
- **Hypothèse TVA** : Taux20% et récupération100% explicitement choisis uniquement pour cet oracle fictif ; aucune qualification fiscale réelle
- **Dates/références** : Capital02/01/2025 CAP-INV313 ; achat10/01/2025 ACH-INV313 ; paiement20/01/2025 REG-INV313 ; inventaire31/12/2025 INV-STOCK-2025
- **Achat et paiement** : 10unités ×20HT =200HT +40TVA =240TTC ; paiement unique240 ; aucun avoir/acompte/RAS
- **Comptage** : ArticleINV313-M :8unités ; articleINV313-Z :0 ; écart principal−2 ; CMUP20 ; perte40 ; valeur160

## Oracle indépendant (MAD)

- achat_ht : 200
- tva_laboratoire : 40.00
- achat_ttc : 240.00
- stock_avant : 200
- stock_final : 160
- perte_physique : 40
- banque : 760.00
- solde_fournisseur : 0
- resultat_avant_impot : -40
- actif : 960.00
- passif : 960
- total_debits : 1640
- total_credits : 1640

Quatre écritures, neuf lignes. Les40MAD de perte physique ne créent pas une OD supplémentaire : achat200 et variation crédit160 produisent déjà la charge nette40.

## INV313-01 — Créer le dossier fictif et son exercice passé.

- **Module** : Administration
- **Prérequis** : Base de recette isolée vierge préparée par le technicien ; aucune connexion au dossier réel.
- **Données exactes** : Société et administrateur ci-dessus ; exercice2025,01/01–31/12.
- **Actions interface** : S'inscrire ; ouvrir la gestion des exercices ; créer2025 explicitement ; choisir2025 dans Exercice actif ; vérifier les dates et le statut ouvert.
- **Résultat attendu** : Société distincte, plan chargé, exercice2025 ouvert et actif. Ne pas saisir un capital2025 avant cette création.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Identité du dossier de test et exercice affichés avant chaque opération.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Capture société/exercice et URL du dossier isolé.

## INV313-02 — Financer la banque fictive.

- **Module** : Administration
- **Prérequis** : INV313-01 réussi.
- **Données exactes** : 02/01/2025 ; CAP-INV313 ; capital1000MAD.
- **Actions interface** : Journal : créer une écriture bancaire, débit5141=1000/crédit1111=1000 ; enregistrer puis valider.
- **Résultat attendu** : Une écriture définitive équilibrée ; banque1000, capital1000.
- **Écritures attendues** : 5141D1000 /1111C1000.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Référence et deux lignes ; validation effective, aucune duplication.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Écriture et grand livre5141.

## INV313-03 — Créer les deux articles sans stock initial.

- **Module** : Articles
- **Prérequis** : INV313-01 réussi.
- **Données exactes** : INV313-M et INV313-Z ; valeurs exactes du tableau de données.
- **Actions interface** : Articles : créer les deux fiches ; cocher Stockable ; saisir prix, TVA et frais explicitement ; stock initial0 ; enregistrer et rouvrir.
- **Résultat attendu** : Deux articles distincts ; stock0 et coût0 connus, aucun zéro utilisé pour masquer une donnée inconnue.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Codes, prix, TVA, stockable et absence de mouvement initial non nul.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Fiches et liste articles.

## INV313-04 — Acheter10unités et alimenter le stock.

- **Module** : Facturation
- **Prérequis** : INV313-01/03 réussis ; fournisseur fictif créé avec compte4411.
- **Données exactes** : Facture fournisseur10/01/2025 ; ACH-INV313 ; INV313-M quantité10, prixHT20, TVA20%, récupération100%.
- **Actions interface** : Factures : Nouvelle facture, type achat ; choisir le fournisseur ; saisir référence externeACH-INV313 et article ; enregistrer puis valider ; générer son écriture comptable. Ne pas créer de BR dans cette variante directe.
- **Résultat attendu** : Facture200HT/40TVA/240TTC ; stock10 et CMUP20, une seule entrée ; écriture brouillon conforme.
- **Écritures attendues** : 6111D200 /34552D40 /4411C240.
- **Impact fiscal** : TVA laboratoire40 récupérable sous hypothèse explicite ; dette fournisseur240.
- **Contrôles** : Comparer les trois montants et le mouvement10×20 ; stopper et noter anomalie si la TVA ou le stock diffère.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Facture, historique article et écriture liée.

## INV313-05 — Payer le fournisseur intégralement.

- **Module** : Règlements
- **Prérequis** : INV313-02/04 réussis.
- **Données exactes** : 20/01/2025 ;240MAD ; banque5141 ; virement ; REG-INV313.
- **Actions interface** : Depuis la facture, Payer le fournisseur ; saisir240, date20/01 et compte banque5141 ; enregistrer ; générer le règlement comptable si demandé par le flux.
- **Résultat attendu** : Facture payée, reste0 ; banque760 ; paiement et écriture liés.
- **Écritures attendues** : 4411D240 /5141C240.
- **Impact fiscal** : Pas de seconde TVA ni de retenue fictive.
- **Contrôles** : Comparer montant enregistré, statut payé, dette et banque ; aucune seconde sortie.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Facture et règlement lié.

## INV313-06 — Valider et lettrer achat/règlement.

- **Module** : Journal
- **Prérequis** : INV313-04/05 réussis.
- **Données exactes** : Deux brouillons achat/paiement ; tiers fournisseur ; codeAAA.
- **Actions interface** : Journal : valider les brouillons ; Lettrage : choisir Fournisseurs puis le fournisseur ; sélectionner240crédit de facture et240débit du règlement ; lettrerAAA.
- **Résultat attendu** : Trois écritures définitives en comptant le capital ; fournisseur soldé ; deux lignes lettréesAAA.
- **Écritures attendues** : Aucune écriture de lettrage nouvelle ; écritures sources conservées.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Solde auxiliaire et collectif0 ; banque760 ; total débits=crédits1480 avant inventaire.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Journal validé et lettrageAAA.

## INV313-07 — Vérifier les sources avant comptage.

- **Module** : Inventaire
- **Prérequis** : INV313-03/04 réussis.
- **Données exactes** : INV313-M : stock10, CMUP20, valeur200 ; INV313-Z :0/0/0.
- **Actions interface** : Inventaire : ouvrir Comptage physique puis Valeur du stock ; rechercher chaque article ; vérifier les quantités préremplies et les montants.
- **Résultat attendu** : Total200 ; réel proposé10 et0 ; aucun diagnostic de source inconnue.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Le zéro connu reste0 ; ne pas confondre préremplissage et comptage physique réel.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Feuille et valorisation200.

## INV313-08 — Simuler un comptage complet de fin2025.

- **Module** : Inventaire
- **Prérequis** : INV313-07 réussi.
- **Données exactes** : 31/12/2025 ; INV-STOCK-2025 ; M=8 ; Z=0 ; note Comptage fictif313.
- **Actions interface** : Comptage physique : conserver la date31/12/2025 ; saisir8 sur M et0 sur Z ; cliquer Vérifier ; lire aperçu et perte.
- **Résultat attendu** : ÉcartM−2, perte40, excédent0, impact−40, stock compté160. Simulation sans mutation.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Rouvrir Valeur du stock avant validation : stock toujours10, valeur200 ; aucun mouvement ni snapshot ajouté.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Aperçu et historique avant validation.

## INV313-09 — Valider le comptage et sa photographie.

- **Module** : Inventaire
- **Prérequis** : INV313-08 réussi.
- **Données exactes** : Même date, référence et quantités ; confirmation explicite.
- **Actions interface** : Cliquer Valider l’inventaire ; confirmer ; rouvrir les deux articles et l'historique sans F5.
- **Résultat attendu** : M stock8/CMUP20/valeur160 ; Z0 ; photographie2lignes, total160/perte40 ; une correction supplémentaire de2unités en sortie.
- **Écritures attendues** : Pas encore de nouvelle écriture comptable tant que la génération stock n’a pas été demandée.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Deux mouvements au total pour M : achat10 puis correction2 ; aucune nouvelle entrée après validation.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Confirmation, historique et photographie.

## INV313-10 — Comptabiliser le stock final.

- **Module** : Inventaire
- **Prérequis** : INV313-06/09 réussis ; aucun autre stock ou stock initial comptable dans cette société.
- **Données exactes** : Exercice2025 ; photographie160 ; comptes3111/6114.
- **Actions interface** : Inventaire : Rapprochement comptable ; cliquer Générer l’écriture de stock ; ouvrir le brouillon créé.
- **Résultat attendu** : Brouillon160/160 lié à2025 ; stock comptable devient160 après validation. Ne pas créer en plus une OD de perte40 : elle compterait deux fois la charge.
- **Écritures attendues** : 3111D160 /6114C160.
- **Impact fiscal** : Achat200 et variation crédit160 donnent charge nette40 avant impôt ; aucune TVA supplémentaire.
- **Contrôles** : Deux lignes exactes, date31/12/2025, référenceSTOCK-CLOTURE-2025.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Brouillon stock.

## INV313-11 — Valider et rapprocher le stock.

- **Module** : Journal
- **Prérequis** : INV313-10 réussi.
- **Données exactes** : Le seul nouveau brouillon stock160/160.
- **Actions interface** : Journal : valider le brouillon ; retour Inventaire/Rapprochement comptable ; vérifier la mention Stock rapproché.
- **Résultat attendu** : Physique160 =comptable brut160 ; dépréciation0 ; écart0 ; écriture stock validée ; quantité8inchangée.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Quatre écritures définitives ; neuf lignes ; D=C1640 ; fournisseur0, banque760, stock160, TVA40.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Écriture définitive et rapprochement.

## INV313-12 — Comparer les états aux calculs indépendants.

- **Module** : États
- **Prérequis** : INV313-11 réussi ; aucune autre opération et aucun impôt ajouté.
- **Données exactes** : Banque760 ; stock160 ; TVA40 ; capital1000 ; résultat avant impôt−40.
- **Actions interface** : Lire balance/grand livre ; ouvrir bilan et CPC dans Liasse fiscale ; comparer les comptes aux feuilles Oracle et Écritures attendues.
- **Résultat attendu** : Actif960 =passif960 ; charges nettes40 ; résultat−40 avant toute écriture fiscale ; aucune créance/dette fournisseur.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucune liquidation IS/CM/CSS revendiquée. Hypothèses fiscales à qualifier dans le cahier annuel.
- **Contrôles** : Actif :760+160+40 ; passif :1000−40. Total mouvements1640dechaque côté.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Balance, bilan et CPC.

## INV313-13 — Contrôler CSV et PDF du livre.

- **Module** : Exports
- **Prérequis** : INV313-11 réussi, exercice2025 encore ouvert.
- **Données exactes** : ArticleM8/20/160, articleZ0/0/0 ; total160.
- **Actions interface** : Inventaire/Valeur du stock : Exporter ; ouvrir CSV ; Livre d’inventaire : choisir2025 et Exporter PDF ; lire toutes les lignes stock.
- **Résultat attendu** : Valeurs160 et0 lisibles dans fichiers ; PDF ouvrable ; stock rapproché. Archive définitive reste indisponible puisque l’exercice est ouvert.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Présence des deux articles, dates, montants et quantités ; aucun NaN/Infinity ; ne pas déclarer dossier prêt à déposer.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : CSV/PDF téléchargés et captures.

## INV313-14 — Vérifier le lecteur.

- **Module** : Sécurité
- **Prérequis** : Créer un utilisateur Lecture sur la société fictive ; INV313-11 réussi.
- **Données exactes** : lecture-inv313@example.com ; rôleLecture.
- **Actions interface** : Se connecter avec le lecteur ; consulter inventaire/livre ; vérifier que validation et génération ne sont pas accessibles ; revenir comme administrateur.
- **Résultat attendu** : Lecture autorisée ; aucune mutation autorisée, aucune nouvelle écriture ni photographie.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Technique :tentativesPOST avec jeton lecteur403 ; contrôle complémentaire réservé au technicien.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Écrans lecteur et journal inchangé.

## INV313-15 — Refuser une quantité négative ou non numérique.

- **Module** : Inventaire négatif
- **Prérequis** : Copie isolée de la société ; aucun comptage à valider pour ce cas.
- **Données exactes** : Quantité−1 puis texteabc ; aucune valeur finale valide envoyée.
- **Actions interface** : Comptage : tenter−1 puisabc ; Vérifier ; relever le refus ; remettre8 uniquement pour quitter sans valider.
- **Résultat attendu** : Saisie invalide refusée ; aucune mutation ; stock conserve8. API booléen/NULL/texte refusés422 par tests techniques.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Stock, mouvement et photographie identiques avant/après.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Message de refus et historique.

## INV313-16 — Refuser une photographie annuelle incomplète.

- **Module** : Inventaire négatif
- **Prérequis** : Copie isolée ; feuille avec les deux articles stockables.
- **Données exactes** : 31/12/2025 ; M=8 ; caseZvide.
- **Actions interface** : Vider la quantité de Z ; tenter Vérifier/Valider ; lire erreur sans confirmer une mutation.
- **Résultat attendu** : Comptage de clôture incomplet explicitement refusé ; la case vide ne devient pas0.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Renseigner0 rend la ligne connue, mais ne valider aucun nouveau comptage pour terminer ce cas.
- **Statut utilisateur** : Non testé
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Refus articleZ et photographie inchangée.

## INV313-17 — Rendre visibles les nombres historiques inconnus.

- **Module** : Inventaire historique
- **Prérequis** : Technicien : société fictive distincte et cluster nonce vérifié ; préparer article stockNULL, coûtNULL/NaN/Inf/négatif et valeur débordante. Jamais dans le dossier utilisateur.
- **Données exactes** : Jeu technique313 fourni par les tests isolés ; aucun NaN saisi dans un formulaire normal.
- **Actions interface** : Après préparation technique : Inventaire/Comptage puis Valeur du stock ; rechercher les articles signalés ; lire les diagnostics ; exporterCSV.
- **Résultat attendu** : Sources inconnues et total affichés À vérifier ; quantitéNULL vide ; coût invalide ne devient pas0 ; CSV contient diagnostic et valeur inconnue.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Aucun changement de prix/quantité historique ; garder ces anomalies visibles.
- **Statut utilisateur** : Bloqué
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Captures, CSV et photographie technique avant/après.

## INV313-18 — Refuser sans mutation comptage/clôture/archivage.

- **Module** : Inventaire historique
- **Prérequis** : INV313-17 préparé ; exercice2025 ouvert ; capital validé1000 dans la variante technique.
- **Données exactes** : Compter toutes les lignes à0 ; conserver un article source inconnu.
- **Actions interface** : Comptage : observer Vérifier et Valider désactivés ; Rapprochement : génération désactivée ; Clôture : sélection2025, clôture désactivée ; livre/PDF : lire diagnostics et absence d’archivage définitif.
- **Résultat attendu** : Refus avant mutation ; capital1000 inchangé ; stock total inconnu, rapprochementfalse ; PDF lisible.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Technique :simulation400, validation/génération409, clôture400, archivage409 ; archives et écritures définitives inchangées.
- **Statut utilisateur** : Bloqué
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : Captures PDF et preuves techniques313.

## INV313-19 — Préserver un brouillon en présence d’un ancien snapshotNaN.

- **Module** : Inventaire historique
- **Prérequis** : Technicien : cluster nonce et photographie historique avec total/CMUPNaN réellement stockable ; brouillon existant.
- **Données exactes** : Ancien stock snapshot incohérent ; aucune réparation autorisée.
- **Actions interface** : Lire Rapprochement et livre ; tenter de générer via contrôle technique authentifié ; comparer le brouillon et ses lignes avant/après.
- **Résultat attendu** : Lecture diagnostiquée, génération409 ; brouillon conservé ; valeurs figées et archives non réécrites.
- **Écritures attendues** : Aucune écriture nouvelle.
- **Impact fiscal** : Aucun impact fiscal supplémentaire calculé.
- **Contrôles** : Comparaison des IDs/lignes et empreintes ; ne pas supprimer pour obtenir un test vert.
- **Statut utilisateur** : Bloqué
- **Résultat réel** : À renseigner
- **Anomalies/observations** : À renseigner
- **Preuves attendues** : JSON et photographie technique avant/après.
