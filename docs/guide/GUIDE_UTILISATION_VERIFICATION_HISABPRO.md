# HISABPRO — MODE D’EMPLOI ET VÉRIFICATION DES AVANCÉES

Version 15 du 19 octobre 2026 — Guide de démonstration à deux et de prise en main.

Ce document décrit les fonctions présentes dans le dépôt : facturation et validation, inventaire, contrôle des mouvements et du CMUP, calendrier comptable, familles à TVA inconnue et polices/icônes locales. Il explique comment les utiliser et observer leurs résultats. Le produit reste en développement ; ce guide ne constitue ni une certification, ni une validation réglementaire ou une autorisation de production.

Cette version précise les annulations avec date et motif, la lecture des règlements et réceptions, l’entrée commande → réception, les documents RAS et les correspondances entre sociétés. Les compléments en fin de guide renvoient aux jeux chiffrés récents. Les 17 résultats humains restent Non testé. RH/paie restent différées ; la fiche 16 est conservée comme référence de l’existant.

Toutes les manipulations de démonstration se font dans une installation de recette isolée, avec des sociétés et documents fictifs. Demander au technicien de préparer cette installation : créer une société dans la base de production ne suffit pas à isoler un test. Aucun accès à votre base réelle n’est nécessaire pour utiliser ce guide.

## Comment organiser votre présentation

Une personne manipule ; l’autre suit les résultats attendus et prend les captures. Commencer par les fiches 01 à 06 pour montrer le parcours vente complet. Présenter ensuite les autres fonctions dans leurs dossiers distincts. La clôture, l’archivage définitif et le changement de mot de passe sont à effectuer en dernier sur des dossiers ou comptes de test.

Durée indicative : 45 à 60 minutes pour une démonstration des écrans et du parcours vente ; davantage pour exécuter toutes les vérifications. Cette durée n’est pas une mesure de performance de l’application.

Pour chaque fiche, noter : Non testé, Réussi, Échoué ou Bloqué. Un résultat attendu n’est jamais un résultat déjà obtenu par vous. Si une action échoue, conserver le message et la capture, arrêter ce parcours dépendant et poursuivre une fiche indépendante. Ne pas supprimer ou modifier une pièce définitive pour obtenir le résultat attendu.

### Navigation sur téléphone

Sur un écran de 767 pixels ou moins, le menu latéral est replié pour laisser toute la largeur au contenu. Toucher le bouton de menu en haut à gauche, puis ouvrir le module et la page souhaités. Le menu se ferme après navigation. Pour le fermer sans changer de page, utiliser sa croix, toucher la zone extérieure ou appuyer sur Échap au clavier ; le focus revient au bouton d’ouverture. Le sélecteur de société et l’exercice restent dans le bandeau. Un tableau large peut conserver un défilement horizontal : vérifier ses colonnes dans la page concernée.

## Sommaire

- 01 — Préparer le dossier, les modules et l’exercice
- 02 — Créer les tiers et les articles
- 03 — Devis et chaîne commerciale de vente
- 04 — Factures, filtres, échéances et préfixes
- 05 — Paiements, édition et statuts
- 06 — Journal, validation et lettrage
- 07 — Acomptes clients et fournisseurs
- 08 — Achats et réceptions partielles
- 09 — Avoirs, chèques et impayés
- 10 — Banque et rapprochement
- 11 — Immobilisations et amortissements
- 12 — Inventaire physique et valeur du stock
- 13 — Balances, grand livre et liasse détaillée
- 14 — TVA, IS et retenues déclarées
- 15 — Clôture, à-nouveaux et archives
- 16 — Dossiers salariés, congés et préparation de paie
- 17 — Utilisateurs, mot de passe et sauvegardes
- 18 — Fiche de suivi, dépannage et documents de référence
- Compléments du 19 octobre 2026 — Annulations datées, lectures, documents RAS, sociétés liées et reprises

## 01 — Préparer le dossier, les modules et l’exercice

### Où aller

Sélecteur de société dans le bandeau ; Paramètres → Fiche société et Modules ; Comptabilité → Clôture d’exercice → Gestion des exercices. La gestion des exercices est réservée à l’administrateur. Le bandeau Exercice sert à sélectionner un exercice existant.

### Prérequis et données

Installation de recette isolée préparée par le technicien. Compte administrateur de test. Créer DEMO PARTENAIRES HISABPRO, devise MAD. Exercice 2025 : du 01/01/2025 au 31/12/2025, ouvert. Les références juridiques/fiscales restent celles du dossier fictif préparé ; ne pas inventer un ICE ou IF officiel.

### Manipulations

1. Se connecter avec le compte de test. Vérifier le nom de la société dans le bandeau.
2. Dans Paramètres → Fiche société, renseigner les informations de démonstration et enregistrer. Recharger pour constater leur conservation.
3. Dans Modules, vérifier que Facturation, Comptabilité et Paie/GRH sont activés pour les fiches concernées.
4. Ouvrir Comptabilité → Clôture d’exercice, puis le bloc Gestion des exercices et Créer un exercice. Créer explicitement 2025 avec les dates ci-dessus si cet exercice est absent. Ne pas compter sur une création implicite pour ce guide.
5. Sélectionner 2025 dans le bandeau Exercice. Vérifier les dates et le statut ouvert.
6. Dans Comptabilité → Plan de comptes, vérifier que le plan de cette société est disponible. Si une initialisation est proposée, la faire effectuer par l’administrateur sur le dossier de test.

### Résultats à vérifier

- Le nom, la devise et les dates correspondent au dossier choisi.
- Les menus des modules activés sont visibles ; une société différente affiche son propre contexte.
- Le plan contient les comptes utilisés ensuite ; aucun compte d’une autre société n’est proposé.

### Preuve et limite

Capture du nom de société, exercice et paramètres. Ne pas fermer de périodes avant la démonstration. La réparation de données historiques et la réouverture d’un exercice définitivement clos ne font pas partie de cette préparation.

## 02 — Créer les tiers et les articles

### Où aller

Facturation → Clients / Fournisseurs ; Facturation → Articles.

### Prérequis et données

Fiche 01 effectuée. CLIENT DEMO VENTE : client, délai 30 jours, collectif 3421. FOURNISSEUR DEMO ACHAT : fournisseur, délai 30 jours, collectif 4411. Article SERV-DEMO : Prestation de démonstration, non stockable, prix vente HT 500, prix achat HT 0, TVA 20%, emballage 0 et transport 0. Le taux 20% est une hypothèse de laboratoire et ne qualifie pas une opération réelle.

### Manipulations

1. Créer les deux tiers dans les rôles appropriés, sans renseigner de faux identifiants officiels.
2. Créer l’article SERV-DEMO. Indiquer qu’il n’est pas stockable et saisir explicitement ses prix et son taux de TVA.
3. Enregistrer, puis rouvrir les fiches. Vérifier les valeurs sans devoir faire F 5.
4. Pour démontrer les frais, créer un article indépendant FRAIS-DEMO : emballage HT 2,50/unité et transport HT 7,25/unité. Modifier ensuite en 3,75 et 8,50 ; rouvrir pour vérifier. Ne pas utiliser cet article dans le scénario chiffré suivant.
5. Dans le formulaire de famille, constater que le nom suffit à la saisie utilisateur ; les paramètres techniques internes restent conservés.
6. Si une famille historique affiche « TVA à vérifier », la sélectionner dans la fiche article : le taux proposé devient vide. Essayer Enregistrer sans choisir un taux : un message doit demander une valeur explicite et aucun article ne doit être créé/modifié. Choisir ensuite 20 % pour ce laboratoire et enregistrer ; la famille historique doit rester inconnue. Dans la création rapide depuis une facture, le sélecteur « TVA proposée pour cet article » apparaît seulement pour une famille inconnue. Le renseigner explicitement. Ne pas demander au technicien de corrompre une famille pour reproduire ce cas : utiliser la fixture prévue, ou noter Bloqué si aucune famille inconnue n’est disponible.
7. Tester un prix négatif sur une nouvelle fiche de test : l’enregistrement doit être refusé avec un message exploitable. Ne pas saisir de Na N ou d’infini directement dans une base.

### Résultats à vérifier

- Les rôles et délais sont conservés ; le service ne porte pas de mouvement de stock.
- Les frais facultatifs sont conservés dans l’article. Leur report et leur qualification dans un document restent explicites : ne pas présumer une TVA automatique.
- Une valeur historique signalée À vérifier reste inconnue et n’est pas assimilée à zéro.

### Preuve et limite

Captures des fiches rouvertes, de la TVA à vérifier et du refus de saisie. Les familles historiques sont lisibles avec diagnostic ; certains autres consommateurs du stock nécessitent encore des contrôles complémentaires. Une TVA historique connue ne prouve pas son applicabilité fiscale à une nouvelle opération.

## 03 — Devis et chaîne commerciale de vente

### Où aller

Facturation → Cycle commercial → Vente → Devis, Bons de commande, Bons de livraison et Factures.

### Prérequis et données

Fiches 01/02 effectuées. Date 10/01/2025 ; CLIENT DEMO VENTE ; SERV-DEMO quantité 2 à 500 HT ; TVA 20% ; tous frais/remises zéro ; note DEMO-VENTE-001. Attendu : HT 1000, TVA 200, TTC 1200 MAD.

### Manipulations

1. Dans Vente → Devis, cliquer Nouveau devis. Choisir le client dans les propositions et saisir les données ci-dessus.
2. Créer le devis. Noter le numéro réellement attribué : ne pas imposer un numéro exemple.
3. Ouvrir sa consultation et vérifier la note DEMO-VENTE-001. Télécharger le PDF et retrouver cette note et les montants.
4. Accepter le devis selon les actions proposées, puis utiliser l’action de conversion en bon de commande.
5. Depuis ce bon, créer le bon de livraison des deux unités ; depuis le BL, créer la facture. Utiliser les conversions, pas trois créations indépendantes.
6. Revenir aux onglets et vérifier les références et liens. Dans Factures, constater la pièce créée. Contrôler les quantités restantes avant toute nouvelle conversion.

### Résultats à vérifier

- Devis, commande, livraison et facture gardent le même tiers et les mêmes quantités/montants.
- Les étapes commerciales ne créent pas chacune une seconde facture ou un second mouvement.
- Le service n’affecte pas le stock. Les nouveaux éléments apparaissent en tête des listes concernées.

### Variante : devis à approvisionner

Dans un autre dossier ou avec un autre article stockable, reprendre les données de l’annexe commerciale : stock 5, deux lignes de quantité 3 chacune, PU 10 HT. L’alerte porte sur la demande cumulée 6 et le manque 1 ; le devis reste autorisé. Un service ne doit pas être signalé en rupture. L’alerte indique le stock actuel ; elle ne réserve pas le stock ni ne promet une disponibilité future.

### Preuve et limite

Captures des quatre documents et du PDF. Les bons de réception externes du client se conservent côté Vente → Réception client, avec les pièces jointes du BL. Leur dépôt ne vaut pas authentification d’une signature.

## 04 — Factures, filtres, échéances et préfixes

### Où aller

Facturation → Factures ; Paramètres → Fiche société → Numérotation des documents pour les préfixes.

### Prérequis et données

Facture de la fiche 03, encore brouillon. Date 10/01/2025, délai 30 jours : échéance 09/02/2025. Pour conserver cet oracle, saisir ou contrôler ce délai sur la pièce. HT 1000/TVA 200/TTC 1200 ; aucune RAS.

### Manipulations

1. Ouvrir la facture et contrôler le tiers, la date, le délai, l’échéance et les totaux.
2. Dans un brouillon distinct, changer volontairement le délai 30 → 0 : l’échéance doit suivre la date de facture. Une échéance manuelle n’est pas à écraser par une modification sans rapport.
3. Sur la facture du scénario, utiliser Valider définitivement. Si aucune écriture n’a encore été créée, utiliser Générer l’écriture comptable ; ne pas générer une seconde pièce.
4. Filtrer la liste du 01/01/2025 au 31/01/2025. Dans le dossier simple, retrouver 1200 TTC et 1000 HT de facturation, avant paiement.
5. Consulter le filtre des retards et le tableau de bord : au jour de cette démonstration, l’échéance passée d’une facture non soldée doit être prise en compte.
6. Dans un essai séparé, modifier le préfixe dans Paramètres, enregistrer, puis créer une nouvelle facture. Comparer l’aperçu et le nouveau numéro ; les anciennes pièces restent inchangées.

En cas d’échec de chargement, les compteurs En attente/En retard affichent « — », la liste est indiquée indisponible et l’export CSV est désactivé. Utiliser Réessayer pour relancer la lecture. Une erreur ne signifie pas zéro facture. Si elle persiste, conserver la capture de l’alerte et transmettre le défaut au technicien ; ne pas remplacer un ancien montant inconnu par zéro. Une liste vide correctement chargée reste affichée à zéro.

### Variante : facture historique aux montants inconnus

Utiliser uniquement un jeu fictif préparé sur une installation isolée par le technicien avec le banc de lecture historique363. Ne pas injecter de NaN, d’infini ou de valeurs manquantes dans une base existante. Si ce jeu n’est pas disponible, noter Bloqué pour cette variante et poursuivre la démonstration normale.

1. Dans Factures, retrouver les deux pièces du jeu : la facture saine HT100/TVA20/TTC120 et la facture indiquée « Montants à vérifier ».
2. Ouvrir la pièce défaillante. Vérifier ses identifiants, sa description et les diagnostics. Un prix ou une quantité inconnue affiche « À vérifier ». Les montants non calculables ne doivent pas afficher zéro.
3. Constater la lecture seule et l’absence d’opération financière depuis ce détail. Dans la liste, validation, duplication, édition financière et règlement de cette pièce sont désactivés. Le PDF ne doit pas être émis à partir de ces données.
4. Vérifier l’alerte au-dessus des indicateurs et les tirets de disponibilité. Un CSV contenant la pièce défaillante est désactivé. Le technicien conserve le diagnostic et recherche les justificatifs ; aucune valeur n’est remplacée automatiquement.
5. Utiliser Réessayer pour relire les données. Ce bouton ne répare aucune pièce. Le banc automatisé remet uniquement son brouillon fictif à une valeur connue pour vérifier la reprise sans F5 ; cette manipulation n’est pas une procédure de réparation de vos données.

Le zéro explicite reste un montant connu. Le statut enregistré d’une facture historique est conservé ; la lecture ne prétend pas recalculer son solde. Une anomalie d’un avoir ou règlement lié peut également rendre la situation financière indéterminable. Conserver une capture de la liste et du détail et laisser le résultat de cette vérification à Non testé jusqu’à votre propre essai.

### Résultats à vérifier

- Validation documentaire et validation comptable sont deux étapes distinctes ; la fiche 06 traite le journal.
- Délai est une durée, échéance est une date. Les indicateurs de liste correspondent aux filtres affichés.
- Les avoirs prennent leur propre date dans la facturation nette ; ces indicateurs documentaires ne sont pas une certification du chiffre d’affaires comptable.
- Sur une copie isolée préparée par le technicien, une source monétaire non finie doit refuser la validation ou la conversion de proforma. Aucun nouveau numéro définitif ni mouvement : le brouillon/proforma et ses lignes restent conservés. Un prix réellement nul reste distinct d’un prix inconnu.

### Preuve et limite

Capture de la pièce validée, filtres et numéros avant/après. Ne pas tenter de modifier les lignes financières d’une facture définitive pour démontrer le préfixe.

## 05 — Paiements, édition et statuts

### Où aller

Facturation → Factures ; Cycle commercial → Vente ou Achat → Règlements.

### Prérequis et données

Facture 1200 de la fiche 04, validée et comptabilisée. Virement 400 le 10/02/2025, référence VIR-DEMO-400 ; puis 800 le 20/02/2025, référence VIR-DEMO-800. Banque 5141 dans le dossier de démonstration.

### Manipulations

1. Sur la facture, utiliser Encaisser le client. Pour un achat, l’action correspondante est Payer le fournisseur.
2. Enregistrer le premier virement 400 avec sa date et sa référence. Vérifier le compte bancaire proposé avant confirmation.
3. Fermer le formulaire : vérifier le paiement et le solde 800 sans recharger manuellement.
4. Enregistrer le second virement 800. Contrôler que le solde devient 0 et le statut Payée.
5. Ouvrir l’onglet Règlements du cycle correspondant. Retrouver les deux références et leurs liens à la facture.
6. Pour démontrer l’édition, utiliser un règlement distinct encore non comptabilisé et non engagé dans un cycle bancaire. Modifier montant/date/mode/commentaire avec l’action Modifier, puis rouvrir. Un règlement déjà comptabilisé doit refuser la modification financière.

### Résultats à vérifier

- Après 400 : total réglé 400, reste 800, statut Partiellement payée.
- Après 800 supplémentaires : total réglé 1200, reste 0, statut Payée ; l’alerte de retard disparaît après actualisation.
- En vente, les virements produisent 5141 débit/3421 crédit pour 400 puis 800. En achat, le sens est 4411 débit/5141 crédit.
- Les écritures des règlements restent à contrôler et valider dans le Journal selon leur statut.

### Preuve et limite

Captures avant/après chaque paiement. Annuler une pièce comptabilisée suit une contrepassation traçable, datée du jour local du navigateur ; vérifier sa cohérence avec la RAS associée. La variante suivante permet une saisie ventilée sur plusieurs factures ; chaque ventilation reste un règlement individuel.

### Variante — ventiler un paiement par tiers

Utiliser une société fictive distincte « VENTILATION DÉMO 2026 » dans l’installation de test isolée, avec exercice 2026 ouvert. Cette variante ne doit pas être mélangée aux chiffres du parcours principal 2025. Créer un client « Client ventilation Démo », une prestation non stockable avec TVA 20 % et le compte bancaire 5141 du laboratoire. Date des opérations : 11/10/2026, uniquement si cette date n’est pas future au moment de la recette.

1. Créer deux factures du même client : première quantité 1/prix HT 100/TVA 20/TTC 120, référence VENT-DEMO-1 ; deuxième quantité 1/prix HT 200/TVA 40/TTC 240, référence VENT-DEMO-2. Noter les numéros réellement attribués. Valider chacune, puis utiliser Générer l’écriture comptable. À ce stade, le client doit 360 MAD ; les deux factures sont non payées.
2. Aller dans Cycle commercial → Vente → Règlements et cliquer Ventiler par tiers. Sélectionner le client. Saisir date 11/10/2026, montant du paiement 240, mode Virement, banque du laboratoire et référence VIR-VENT-DEMO-240.
3. Saisir 120 devant le numéro de la première facture, puis 120 devant la seconde. Après la première saisie, le bouton doit rester indisponible : 120 MAD manquent à la ventilation. Après la seconde, attendre Total ventilé 240 et Reste à ventiler 0. Confirmer Enregistrer la ventilation.
4. Sans F5, vérifier deux règlements de 120 avec la même référence et leurs liens distincts. Première facture : Soldée, solde 0. Deuxième : Partiel, solde 120. Recharger ensuite la page et retrouver les mêmes lignes.
5. Rouvrir Ventiler par tiers pour le même client. La première facture soldée n’est plus proposée. Saisir montant 120, ventilation 120 sur la seconde, même date, référence VIR-VENT-DEMO-120. Enregistrer : les deux factures sont maintenant soldées, avec trois règlements totalisant 360 MAD.
6. Ouvrir le Journal : deux écritures de facture et trois de règlement, toutes équilibrées. Attendu cumulé : ventes 7111 crédit 300, TVA 4455 crédit 60, client 3421 débit 360/crédit 360 et banque 5141 débit 360. Total des débits du journal = total des crédits = 720 MAD pour ces cinq pièces seules. Valider les cinq écritures ; dans Lettrage, sélectionner 3421, le client et les cinq lignes collectives. Le lettrage doit être équilibré à 360/360 et porter un code d’au moins trois lettres.

Pour la variante achat, créer un fournisseur distinct avec les mêmes deux montants et références fournisseur propres. Utiliser Cycle commercial → Achat → Règlements. Attendre achats 6111 débit 300, TVA récupérable 34552 débit 60, fournisseur 4411 crédit 360/débit 360 et banque 5141 crédit 360 ; lettrer les cinq lignes 4411. Les taux et comptes de ces deux variantes sont les hypothèses du laboratoire, pas une nouvelle règle réglementaire.

Contrôles négatifs : saisir 121 sur la facture de 120 doit afficher le dépassement et empêcher l’enregistrement. Un total différent de la ventilation reste bloquant. Les factures de tiers distincts, proformas, brouillons ou montants à vérifier ne doivent pas être proposées ensemble. Un lecteur ne voit pas le bouton. Un acompte imputé, un avoir comptabilisé ou une RAS déclarée doivent réduire le solde proposé ; une simple estimation RAS ne suffit pas. Faire préparer ces variantes complémentaires par le technicien dans le banc isolé si nécessaire ; sinon noter Bloqué pour cette seule variante.

Capturer le formulaire avant confirmation, les deux lignes après 240, les trois après le complément et le lettrage. Chaque ventilation crée son règlement et son écriture ; l’annulation individuelle reste traçable. Une annulation collective du lot natif est décrite ci-dessous. Chèques et effets conservent leur règlement individuel et leur cycle dédié. Maximum 50 factures par saisie. Le rapprochement de cette ventilation avec une seule ligne bancaire est décrit dans la fiche10. Les écritures individuelles restent conservées ; le regroupement des chèques/effets en un instrument unique reste à traiter. Les historiques sans tiers natif ne sont pas rapprochés arbitrairement. Une facture au-delà des 100 premières doit rester visible dans les listes de règlements du bon cycle.

### Variante indépendante — annuler toute une ventilation

Préparer une société de recette distincte ANNULATION VENTILATION DÉMO, un exercice 2026 ouvert du 01/01/2026 au 31/12/2026, un client natif et deux factures de 120 et 240 MAD TTC datées du 17/10/2026. Sans acompte, avoir ni RAS pour cette variante fictive. Ne pas utiliser les factures déjà lettrées de la variante précédente.

1. Dans Vente → Règlements → Ventiler par tiers, enregistrer le 17/10/2026 un virement de 240 MAD ventilé en 120 et 120. Valider les quatre écritures dans le Journal : débits = crédits = 600 MAD, dix lignes. Conserver les numéros et une capture des originaux.
2. Dans Règlements, utiliser le bouton dont l’infobulle indique Annuler toute la ventilation. Le formulaire annonce deux règlements, leurs numéros et 240 MAD pour le lot entier. Cliquer sur Fermer une première fois : aucun statut ni écriture ne doit changer.
3. Refaire l’action, choisir le 18/10/2026 comme Date d’annulation et saisir le motif ANNULATION FICTIVE DE DEMONSTRATION. Le motif reste facultatif dans l’application. Cliquer sur Confirmer l’annulation. Les deux lignes restent visibles avec le statut annulé. Les soldes des factures redeviennent 120 et 240 MAD sans F5. Les deux contrepassations doivent porter la date choisie et le motif saisi.
4. Dans le Journal, contrôler deux nouvelles contrepassations de 120 MAD et leurs liens d’origine, puis les valider selon le circuit normal. Les quatre originaux restent définitifs et inchangés. Totaux après annulation : six écritures, quatorze lignes, débits = crédits = 840 MAD.
5. Répéter sur un fournisseur distinct dans Achat, avec les comptes 4411 et 5141 dans le sens inverse. Capturer la confirmation, les statuts et les contrepassations.

Un lot déjà partiellement annulé est refusé collectivement : vérifier ses règlements individuellement. Une erreur sur une seule ligne doit refuser tout le lot. Les historiques sans UUID natif ne sont pas regroupés sur la seule référence. Les contrepassations de captures RAS déclarées sont couvertes par un banc distinct ; ne pas inventer une retenue pour cette démonstration.

### Variante indépendante — payer une facture de l’exercice précédent

Préparer une autre société de recette, exercices 2025/2026 ouverts, et une facture client du 01/06/2025 TTC 120 MAD. Enregistrer 60 MAD le 15/06/2025 puis 60 MAD le 15/02/2026, avec leurs références distinctes. Sélectionner 2026 dans le bandeau, puis Vente → Règlements : seule la ligne payée en 2026 est attendue pour ce jeu, avec le numéro de la facture 2025 et Soldée. Refaire en Achat pour un fournisseur. Pour la variante partielle, un complément 2026 de seulement 20 MAD laisse 40 MAD et l’indication Partiel.

La liste reste filtrée par année de règlement ; elle ne transforme pas la date de facture ni son exercice. Une facture étrangère à la société active ne doit jamais fournir ses informations. Le parcours annuel automatisé incluant clôture, reports et lettrage utilise l’oracle séparé oracle_annee_ventilation_2025_2026.json ; ce contrôle ne marque pas votre recette humaine comme réussie.

### Variante négative — règlement historique à vérifier

Faire préparer par le technicien le banc fictif isolé du lot 368 ; ne jamais injecter une valeur invalide dans un dossier existant. Si le jeu manque, noter Bloqué pour cette variante et poursuivre les opérations ordinaires. Sélectionner la société fictive et l’exercice 2026 de ce banc, distincts du scénario principal 2025. Le banc contient une facture HT 100 / TVA 20 / TTC 120 et deux règlements non comptabilisés, dont un sain de 20 et un historique défaillant.

1. Aller dans Cycle commercial → Vente ou Achat → Règlements. Retrouver les deux lignes ; la source défaillante ne doit pas masquer la ligne saine.
2. Vérifier l’alerte Total à vérifier et la mention Situation à vérifier. Une somme inconnue ne doit pas devenir zéro ou une facture prétendument soldée.
3. Pour un montant non fini, attendre À vérifier. Pour le cas explicitement nul, attendre 0,00 accompagné du diagnostic : zéro reste une valeur connue, mais un règlement nul est inadmissible à la saisie.
4. Sur la ligne défaillante, constater que Modifier, Supprimer et la RAS sont indisponibles. Les appels financiers du banc doivent être refusés avant toute mutation. Conserver une capture et les références d’origine.
5. Fermer et rouvrir l’onglet : le diagnostic reste présent. Aucune lecture ne répare la source. Transmettre cette anomalie au technicien avec les justificatifs nécessaires ; ne pas supprimer la pièce pour masquer le contrôle.

Cette variante n’écrit aucune nouvelle comptabilité. Elle ne constitue pas une procédure de réparation historique. Laisser son résultat à Non testé jusqu’à votre propre essai ; le rapport automatisé368 reste une preuve distincte.

## 06 — Journal, validation et lettrage

### Où aller

Comptabilité → Journal, puis Comptabilité → Lettrage.

### Prérequis et données

Fiches 03 à 05 terminées dans le dossier vente. Compte 3421, CLIENT DEMO VENTE. Une facture 1200 et deux virements 400/800. Choisir les intitulés exacts du plan de cette société.

### Manipulations

1. Ouvrir le Journal. Retrouver l’écriture de facture et les deux écritures de règlement grâce aux références et montants.
2. Contrôler la facture :3421 débit 1200 ; produit configurécrédit 1000 ; TVA collectée 4455 crédit 200. Contrôler les deux paiements de la fiche 05.
3. Valider les brouillons concernés avec Valider ou Valider les brouillons, après avoir vérifié leur contenu. Ne pas sélectionner d’autres pièces d’une recette parallèle.
4. Ouvrir Lettrage. Choisir le compte 3421, puis le client. Sélectionner la ligne débit 1200 et les deux crédits 400/800.
5. Vérifier que la sélection est équilibrée, puis cliquer Lettrer 3 lignes. Dans une société vierge de lettrage, le premier code attendu est AAA ; sinon noter le code réel.
6. Recharger et sélectionner à nouveau compte/tiers. Vérifier que les trois lignes conservent le même code et que le collectif du client est soldé.

### Résultats à vérifier

- Trois écritures, sept lignes ; total des débits = total des crédits =2400 MAD.
- Solde client 0, banque+1200, produit créditeur 1000 et TVA collectée créditrice 200.
- Les libellés du plan sont respectés. Lettrer change le rapprochement des lignes, pas leurs montants, dates ou références.

### Variante de contrôle

Dans un nouveau brouillon manuel, saisir débit 1000/crédit 900 : refus de l’écriture déséquilibrée. L’erreur doit être lisible et aucune pièce ne doit être enregistrée. Ne jamais passer une écriture erronée puis la modifier définitivement pour obtenir ce contrôle.

### Preuve et limite

Export du journal et capture des trois lignes lettrées. Paiement commercial, validation comptable et lettrage restent des états différents.

## 07 — Acomptes clients et fournisseurs

### Où aller

Facturation → Acomptes ; Facturation → Factures ; Comptabilité → Journal et Lettrage.

### Prérequis et données

Utiliser un dossier fictif distinct, exercice ouvert. Facture HT 1000+TVA 200=1200. Acompte 400, virement, puis paiement du solde 800 ; aucune RAS ni frais. Choisir explicitement le traitement TVA de laboratoire adapté au scénario avant confirmation.

### Manipulations

1. Dans Acomptes, créer un acompte Client ou Fournisseur, choisir le tiers, le montant 400, la date et la référence.
2. Vérifier les options de paiement/TVA et la case Comptabiliser automatiquement. Noter la situation de l’acompte.
3. Créer et valider la facture 1200 du même tiers, avec son écriture comptable.
4. Sur l’acompte, utiliser Imputer sur une facture ; sélectionner cette facture et 400, puis Imputer l’acompte.
5. Relire le détail et l’historique : montant imputé 400 et disponible 0 si cet acompte est intégralement affecté.
6. Régler le reste 800 sur la facture. Contrôler les écritures, les valider puis lettrer le collectif du tiers.

### Résultats à vérifier

- La facture conserve son total 1200 ; acompte 400 et paiement 800 soldent sa situation.
- L’imputation est liée à la vraie facture et ne fait pas une seconde entrée de trésorerie 400.
- Le socle utilise 4421 pour un acompte client et 3411 pour un acompte fournisseur ; contrôler les lignes réelles et leur transfert au collectif.
- Le scénario fournisseur déjà testé aboutit à quatre écritures, neuf lignes et débits/crédits 2800. Comparer cet oracle uniquement si les mêmes options et aucune autre opération sont utilisés.

### Preuve et limite

Captures acompte, historique, facture et lettrage. Les acomptes commerciaux sont différents des acomptes d’IS. Les variantes de TVA et d’annulation doivent suivre le cahier complet ; une imputation annulée conserve son historique.

## 08 — Achats et réceptions partielles

### Où aller

Facturation → Cycle commercial → Achat → Bons de commande, Bons de réception, Factures et Règlements.

Depuis Bons de réception, Préparer depuis une commande ouvre les commandes achat, sans créer de BC ni de BR. Utiliser ensuite Nouveau BC, ou la commande existante concernée, puis Créer un bon de réception sur le reliquat. Une réception est ainsi liée à la bonne commande. La bascule Vente/Achat reste entièrement visible sur mobile. En consultation seule, l’entrée de préparation n’est pas proposée.

### Prérequis et données

Dossier indépendant ACHATS DEMO, exercice 2025 ouvert. Fournisseur fictif ; article stockable ACH-DEMO, stock initial 0, achat HT 500, TVA 20%, frais 0. Commande de 4 unités. Première réception 1 unité, seconde 3 unités. Factures 600 et 1800 TTC ; qualification Charge/achat courant et déduction TVA 100% pour ce laboratoire uniquement.

Dans Paramètres → Fiche société → Gestion du stock, régler Achats — entrée de stock sur « À la réception — BR passé en “livré” », puis enregistrer. Ce prérequis est nécessaire aux résultats de stock ci-dessous. Dates du laboratoire : BC le 10/03/2025 ; premier BR et facture le 11/03/2025 ; second BR et facture le 14/03/2025 ; deux règlements le 18/03/2025. Contrôler ces dates dans les formulaires, même si une autre date est proposée automatiquement.

### Manipulations

1. Créer un bon de commande Achat pour 4 unités, daté du 10/03/2025. Vérifier HT 2000/TVA 400/TTC 2400.
2. Depuis ce BC, créer le premier bon de réception d’une unité et effectuer l’action de réception/validation proposée.
3. Créer la facture depuis ce BR : une confirmation apparaît dans la page, avec l’identifiant du brouillon et le numéro du BR, sans dialogue de succès bloquant. Ouvrir Factures, compléter le numéro fournisseur puis vérifier 600 TTC avant validation et comptabilisation.
4. Depuis le BC, recevoir les trois unités restantes. Créer la seconde facture liée à ce BR et vérifier 1800 TTC.
5. Ouvrir Articles et Mouvements & CMUP : constater le stock 1 puis 4, jamais une nouvelle entrée lors de la facturation déjà issue du BR.
6. Régler les factures 600/1800, valider les écritures et lettrer les quatre lignes du collectif fournisseur.

### Résultats à vérifier

- Une seule commande, deux BR, deux factures ; liens et quantités source conservés.
- Deux mouvements de stock :0 → 1 puis 1 → 4, coût 500 ; stock final 4 et valeur 2000.
- Achat 6111 débit 2000, TVA 34552 débit 400, fournisseur 4411 crédit 2400 ; paiements 5141 crédit 2400 et 4411 débit 2400.
- Après validation : quatre écritures, dix lignes, débits=crédits 4800 ; fournisseur soldé et lettré.

### Preuve et limite

Capturer chaque conversion et le stock final. Les comptes et taux ci-dessus sont des hypothèses du laboratoire. Consulter l’annexe achats partiels.

Pour un refus de coût à la réception, consulter le dépannage de la fiche18.

## 09 — Avoirs, chèques et impayés

### Où aller

Facturation → Avoirs ; Facturation → Effets & Chèques ; Cycle commercial → Règlements.

### Prérequis et données

Utiliser des dossiers distincts des fiches 03/08. Avoir fournisseur : achat de 2 unités à 500 HT, TVA 20%, retour 1 unité et avoir 600 TTC. Chèque client : facture 1200 TTC, chèque 1200, sans frais, puis virement de remplacement 1200.

### Manipulations : avoir

1. Ouvrir la facture source et utiliser le flux d’avoir lié ; sélectionner une seule unité retournée.
2. Vérifier HT 500/TVA 100/TTC 600 et le lien à la facture avant validation.
3. Contrôler le retour de stock selon les options du flux et l’écriture d’avoir ; ne pas créer un second retour manuel.
4. Régler le reste 600 et valider/lettrer les lignes correspondantes. Comparer avec l’annexe de recette appropriée.

### Manipulations : chèque impayé

1. Enregistrer le règlement par chèque avec référence et date explicites ; consulter sa fiche dans Effets & Chèques.
2. Vérifier que la date proposée est le jour local, puis effectuer la remise à sa date réelle et simuler le rejet sans frais dans le dossier isolé.
3. Contrôler que la facture redevient due et que les écritures originales restent visibles.
4. Enregistrer le virement de remplacement 1200, valider les écritures et lettrer le client.

### Résultats à vérifier

- Avoir fournisseur : stock final 1 ; dette initiale 1200, réduction 600, paiement 600, fournisseur soldé.
- Chèque rejeté : un statut de portefeuille n’est pas un encaissement définitif ; le paiement de remplacement solde ensuite la facture.
- Le parcours chèque de laboratoire testé conserve cinq écritures/onze lignes, débits=crédits 6000 et banque+1200.

### Preuve et limite

Captures historique et écritures originales/contrepassations. L’escompte anticipé des effets n’est pas un flux complet actuellement disponible : ne pas réduire arbitrairement le nominal d’un effet pour le simuler.

## 10 — Banque et rapprochement

### Où aller

Paramètres → Comptes bancaires ; Comptabilité → Rapprochement bancaire → Import Excel / CSV ou Saisie manuelle.

### Prérequis et données

Utiliser le dossier vente des fiches 03 à 06 : deux virements 400/800, banque 5141. Préparer un relevé fictif de février 2025 avec dates 10/02/2025 et 20/02/2025, crédits 400 et 800, références VIR-DEMO-400/800. Solde début 0 et fin 1200 si aucune autre opération bancaire. Suivre le format décrit dans docs/recette/IMPORT_RELEVES_BANCAIRES.md ; choisir l’encodage correspondant au fichier.

### Manipulations

1. Sélectionner la banque et la période de février 2025. Photographier les filtres et soldes avant import.
2. Ouvrir Import Excel / CSV et charger le fichier fictif. Examiner les colonnes, dates et montants dans l’aperçu.
3. Corriger le fichier hors application si une ligne est signalée invalide ; ne pas ignorer silencieusement cette ligne.
4. Enregistrer l’import. Rapprocher chaque ligne de relevé avec la ligne comptable définitive exacte 400 ou 800.
5. Recharger la page et vérifier les deux rapprochements conservés. Réimporter le même fichier de test pour contrôler la détection des doublons.
6. Changer de période, banque ou société, puis revenir. Les dates sélectionnées et les résultats ne doivent pas être remplacés par une réponse tardive d’un ancien contexte.

Alternative à l’import : utiliser Saisie manuelle dans un dossier où ces deux lignes n’ont pas déjà été importées. Sélectionner février2025, puis saisir date10/02/2025, libelléVIR-DEMO-400, montant400, sensCrédit ; ajouter. Saisir ensuite date20/02/2025, libelléVIR-DEMO-800, montant800, sensCrédit ; ajouter. Contrôler leur apparition immédiate, puis effectuer les mêmes rapprochements. Ne pas cumuler les deux méthodes pour le même relevé.

Dans l’exercice courant, vérifier que la date proposée est le jour local. Pour un exercice passé ou futur, elle se place dans ses bornes ; cette proposition ne constitue pas la date de l’opération bancaire. Saisir la date exacte du relevé avant ajout. Une date saisie dans l’exercice doit rester affichée à l’arrivée des informations de l’exercice ; changer d’exercice doit proposer une date dans ses nouvelles bornes.

### Résultats à vérifier

- Deux lignes correctes, solde du relevé 1200 et banque comptable 1200 dans ce dossier simple.
- Un rapprochement conserve la ligne et l’écriture source ; il ne modifie pas les montants du journal.
- L’import invalide est refusé avant insertion partielle. Les doublons exacts sont signalés selon les informations disponibles.

### Preuve et limite

Conserver le fichier, l’aperçu et le résultat après rechargement. Le pointage manuel est disponible ; un rapprochement automatique exhaustif n’est pas promis. Deux opérations bancaires parfaitement identiques peuvent être indiscernables sans une référence supplémentaire.

### Variante indépendante — une ligne bancaire pour plusieurs factures

Utiliser une société fictive distincte RAPPROCHEMENT VENTILATION DÉMO 2026, exercice 2026 ouvert, client natif et banque 5141. Faire préparer l’activation de cette fonction dans l’installation de recette par le technicien ; ne pas appliquer une migration sur la base réelle pendant la démonstration. Les chiffres ne sont pas à mélanger au dossier principal 2025.

1. Créer et valider deux factures client du 11/10/2026, référencesBQ-VENT-1 etBQ-VENT-2 : quantité 1, HT 100/TVA 20/TTC 120 puis HT 200/TVA 40/TTC 240. Utiliser Générer l’écriture comptable.
2. Dans Vente → Règlements → Ventiler par tiers, enregistrer un virement de 240 MAD le 11/10/2026, référenceBQ-VIR-240, banque 5141, affectations 120/120. Noter les deux règlements. Valider les quatre écritures dans le Journal. Total débit=crédit=600 MAD ; client 3421 reste débiteur de 120 ; banque 5141 est débitrice de 240.
3. Dans Rapprochement bancaire, sélectionner 2026, le compte 5141 et la période du 01/01/2026 au 31/12/2026. Dans Saisie manuelle, ajouter UNE ligne de relevé : date 11/10/2026, libelléBQ-VIR-240, montant 240, sensCrédit. Un crédit de relevé correspond ici à une entrée et à un débit du compte banque.
4. Dans Écriture comptable associée de cette ligne, choisir « Ventilation · BQ-VIR-240 · … · 2 règlements · 240 MAD ». La proposition dépend du lot natif créé par Ventiler par tiers : une référence libre identique ne suffit pas. Les deux lignes comptables banque 120/120 doivent devenir Rapprochée ; le relevé reste composé d’une seule ligne 240. Recharger et retrouver le choix.
5. Saisir solde initial 0 et solde final 240 ; quitter chaque champ pour enregistrer. Contrôler « Équilibré » et « Initial + mouvements = final ». Comparer les écritures du Journal à la capture initiale : aucun montant, compte, numéro ou validation changé ; aucune écriture supplémentaire créée par le pointage.
6. Dans la même sélection, choisir « Non rapprochée ». Les deux lignes comptables doivent revenir À rapprocher et la ligne de relevé reste présente. Sélectionner de nouveau le lot pour vérifier le repointage. L’édition ou la suppression du relevé nécessitent ce dérapprochement préalable.
7. Refaire dans une société de recette achat distincte : fournisseur, mêmes factures et ventilation 240, relevéDébit 240, compte 5141 créditeur 240. Dans ce dossier seul, soldes initial 0/final−240. Le fournisseur 4411 reste créditeur 120. Ne pas mélanger cette sortie au relevé du dossier vente.

Contrôles négatifs : relevé 240,01, sens opposé, autre banque, écritures non validées, lot partiellement annulé ou autre société doivent être refusés ou ne pas être proposés. Une ligne déjà rapprochée individuellement ne peut pas être réutilisée dans le lot ; un lot pointé ne peut pas être repris par une deuxième ligne bancaire. Dérapprocher avant de remplacer. Après clôture, lecture conservée et dérapprochement interdit. Un lecteur ne peut pas modifier le pointage.

Capturer la sélection, les deux lignes Rapprochée et l’unique relevé, puis le résultat après rechargement. Les montants nets de frais bancaires, les règlements sans lot natif et les chèques/effets groupés restent hors de cette variante ; aucune différence n’est absorbée automatiquement.

### Variante annuelle bancaire — contrôle complémentaire

Dans le dossier annuel fictif de la recette technique, l’apport 1000 et les ventilations client 240/fournisseur 240 donnent trois lignes de relevé 2025, cinq lignes comptables pointées et solde final 1000. Les montants pointés bruts totalisent 1480 ; ils ne représentent pas le solde bancaire. Après clôture 2025, ces liens sont conservés en lecture seule. Les compléments client 120/fournisseur 120 de 2026 donnent deux autres lignes de relevé : initial 1000, final 1000, montants bruts 240. Le scénario garde les attendus de clôture, reports auxiliaires, lettrage, FEC et balance décrits dans le dossier livré. Le classeur complémentaire ANNEXE_RECETTE_RAPPROCHEMENT_VENTILATIONS.xlsx fourni dans les livrables contient les cas à renseigner : tous sont Non testé pour la recette humaine.

### Proposer des rapprochements exacts, puis confirmer

Dans le dossier fictif de la variante précédente, conserver le virement BQ-VIR-240 ventilé 120/120, ses deux écritures validées et son relevé Crédit 240 du 11/10/2026. Commencer avec la ligne non rapprochée. Cette fonction ne remplace pas le contrôle des justificatifs bancaires.

1. Choisir le compte 5141 et la période du 01/01/2026 au 31/12/2026. Attendre le chargement de la société, de l’exercice et de la situation. Cliquer sur Proposer les rapprochements.
2. Dans Propositions de rapprochement, vérifier la date, la référence BQ-VIR-240, le sens Crédit et le montant 240. La sélection propose uniquement une correspondance exacte et unique : même date, même montant au centime, même sens et même référence entière, après retrait des espaces de début/fin. La casse reste significative. Un relevé dont le libellé ajoute du texte restera à traiter manuellement.
3. Cocher uniquement les opérations souhaitées, puis Rapprocher la sélection. Le lot natif peut pointer ses deux lignes comptables avec une ligne de relevé. Un règlement bancaire simple peut aussi être proposé. La proposition seule ne pointe rien. Vérifier les lignes Rapprochée et recharger la page : le pointage doit persister et le Journal doit conserver les mêmes écritures.
4. Dans un dossier négatif distinct, créer deux lignes de relevé identiques BQ-VIR-240, chacune Crédit 240, même date. Aucun choix automatique entre les deux : vérifier le compteur de lignes ambiguës. Dérapprocher ou traiter manuellement avec un justificatif ; ne pas supprimer une opération réelle pour obtenir une proposition.
5. Vérifier que le changement de compte, de période, de société ou d’exercice ferme les propositions devenues hors contexte. Si le relevé ou son pointage a changé depuis l’aperçu, la confirmation est refusée et aucune sélection n’est partiellement pointée ; fermer et recalculer. Après clôture, le pointage reste en lecture seule. Les permissions d’écriture restent nécessaires.

Limites : seules les correspondances exactes et uniques sont proposées ; aucune détection approximative, reconstitution d’historique, différence de frais absorbée, ni écriture comptable créée. Un lot natif collectif nécessite l’activation de recette 084 décrite plus haut. Une référence libre ne transforme pas plusieurs règlements en un lot natif.

Lorsqu’une ligne historique affiche À vérifier, consulter son justificatif. Les totaux concernés restent inconnus et cette ligne ne peut pas être pointée. Les autres correspondances certaines restent utilisables ; la donnée source historique est conservée.

### Encaissement individuel avec frais au centime

Utiliser une autre société fictive ENCAISSEMENT FRAIS DÉMO, exercice 2026 ouvert, client natif, compte banque 5141. Ne pas mélanger ces chiffres au dossier principal ou à la variante de ventilation.

1. Créer une facture vente du 11/10/2026 : un service fictif, quantité 1, HT 100, TVA de laboratoire 20, TTC 120. Valider la facture, générer son écriture puis valider celle-ci dans Journal. Cette donnée de test ne qualifie pas le régime fiscal d’une activité réelle.
2. Depuis la facture, Encaisser le client : montant 120, date 11/10/2026, mode Chèque, référence ENCAISSE-FRAIS-FICTIF. Dans Chèques et effets, filtre Tous, retrouver la référence et Remettre à l’encaissement, date 11/10/2026. Pour la variante Effet, utiliser un dossier distinct avec même montant, échéance 11/10/2026 ; ne pas constater son encaissement avant son échéance.
3. Confirmer l’encaissement, date 11/10/2026, frais bancaires retenus 10,01. Attendu : banque 5141 au débit 109,99, charges 61472 au débit 10,01, valeur à l’encaissement au crédit 120. Ces frais ne sont pas une nouvelle facture ou une TVA bancaire calculée automatiquement. La facture est soldée pour 120, et non pour le net bancaire.
4. Dans Journal, valider les trois nouvelles écritures. Le dossier contient quatre pièces et dix lignes, total débit = crédit = 480. Le client 3421 et les comptes d’attente sont soldés ; banque débitrice 109,99 et frais débiteurs 10,01. Pour le chèque : 51111 puis 51112 ; pour l’effet : 3425 puis 51132.
5. Ajouter UNE ligne de relevé du 11/10/2026, compte 5141, Crédit 109,99, libellé ENCAISSE-FRAIS-FICTIF. Proposer les rapprochements puis confirmer la seule ligne exacte. Vérifier qu’une ligne comptable bancaire est pointée et que le journal est inchangé. Un relevé Crédit 120 ne correspond pas au net de cet avis bancaire.
6. Dans Lettrage, sélectionner 3421 et ce client, cocher les deux lignes 120/120, puis Lettrer 2 lignes. Attendu AAA dans un dossier vierge ; débit et crédit du tiers restent égaux. Exporter le FEC 2026 après les validations : dix lignes comptables, débit = crédit = 480. Le pointage et le lettrage ne doivent pas modifier les montants des pièces.

Contrôles négatifs sur copie isolée : des frais à trois décimales (10,005), négatifs ou non finis sont refusés avant mutation. Des frais sur une remise ou un paiement fournisseur, opérations qui ne les traitent pas, ne sont pas silencieusement ignorés ; les enregistrer séparément avec leur justificatif. Ce parcours ne couvre pas l’escompte ni un instrument chèque/effet unique regroupant plusieurs factures.

Le classeur ANNEXE_RECETTE_PROPOSITIONS_FRAIS.xlsx complète les cas humains à renseigner. Tous ses statuts restent Non testé ; les tests automatiques ne remplacent pas votre recette. Capturer le détail de l’encaissement, le Journal, le pointage conservé, le lettrage et l’export FEC.

### Variante annuelle indépendante — frais 2025, clôture et ouverture 2026

Le cas RPF-009 du classeur complémentaire décrit un autre dossier fictif, séparé de tous les précédents : mêmes HT 100/TVA 20/TTC 120, chèque 120, frais 10,01 et banque 109,99, mais opérations du 15/06/2025, référenceENCAISSE-FRAIS-FICTIF. Préparer 2025 et 2026 ouverts,2026 sans opérations ;faire préparer au technicien le profil fiscal de laboratoire existant :IS,TVAencaissement mensuelle,MAD,exercice_debut 2020. L’impôt 3000 ci-dessous est l’attendu de ce seul profil de test ;il ne qualifie aucun dossier réel.

Suivre les étapes de paiement, remise, encaissement, validation, pointage et lettrage dans 2025. Le résultat avant impôt est 89,99. Dans Clôture,clôturer 2025 :après impôt de laboratoire 3000,perte 2910,01. Les à-nouveaux 2026 doivent être validés,composés de quatre lignes et équilibrés à 3020 :5141 au débit 109,99,1199 au débit 2910,01,4455 au crédit 20 et 4453 au crédit 3000. Les comptes d’attente et client sont soldés. Exporter les FEC 2025 et 2026 :tous deux équilibrés ;celui de 2026 comporte les quatre lignes d’ouverture. Revenir au rapprochement 2025 :pointage conservé,lecture seule et dérapprochement interdit. Comparer les pièces originales à leur capture initiale.

Cette variante annuelle réduite ne remplace pas le scénario complet avec stocks,immobilisations et toutes les opérations du cahier de recette. Son statut humain reste Non testé.

## 11 — Immobilisations et amortissements

### Où aller

Comptabilité → Immobilisations ; Comptabilité → Journal ; Liasse fiscale → T1 · Bilan.

### Prérequis et données

Dossier indépendant IMMO DEMO, exercice 2025 ouvert. Bien fictif : matériel de bureau, acquisition/mise en service 01/01/2025, HT 10000, TVA 20%, durée 3 ans, linéaire. Choisir les comptes proposés adaptés à la catégorie, par exemple 2352/28352, et consigner les comptes effectivement utilisés. Aucun coefficient dégressif n’est à appliquer à cet exemple.

### Manipulations

1. Créer le bien avec ses dates, sa durée, son mode et sa qualification TVA explicites.
2. Enregistrer et contrôler l’écriture d’acquisition. Si elle manque, utiliser l’action de comptabilisation prévue avant de poursuivre.
3. Ouvrir le plan d’amortissement. Contrôler les annuités et utiliser Générer pour l’année autorisée, puis valider le brouillon dans le Journal.
4. Comparer la valeur brute, le cumul amorti et la VNC à la date affichée ; ne pas comparer des dates différentes.
5. Pour vérifier les annuités 2026/2027, préparer les exercices et réaliser la recette dédiée aux dates pertinentes. Ne pas générer automatiquement des dotations futures uniquement pour la démonstration du jour.
6. Dans un autre essai, utiliser Cession / mise au rebut, puis Comptabiliser la sortie ; contrôler les lignes et la conservation de l’original. Une cession différée propose son encaissement ultérieur.

### Résultats à vérifier

- Brut 10000 ; plan linéaire 3333,33 +3333,33 +3333,34 =10000, VNC finale 0.
- Acquisition HT,TVA et dette/trésorerie correspondent aux options réellement retenues.
- Une dotation ne peut pas être comptabilisée deux fois pour la même année ; le bilan reprend les valeurs comptables validées.

### Preuve et limite

Fiche, plan, journal et bilan à même date. Une variante dégressive précise est décrite ci-dessous ; les autres dates/biens, réévaluations et cessions partielles restent à compléter. La génération des dotations est une action explicite ; aucune exécution annuelle planifiée n’est annoncée par ce guide.

### Variante indépendante — dégressif sur cinq ans

Sur une société de recette distincte IMMO DÉGRESSIF DÉMO, préparer les exercices 2021 à 2025 ouverts. Bien fictif Matériel informatique : acquisition et mise en service 01/01/2021, HT 60000 MAD, TVA 20 %, durée cinq ans, méthode Dégressif, coefficient proposé 2. Vérifier les comptes 2355/28355/61935, TVA 34551 et dette 4481 du laboratoire avant enregistrement. Ces données vérifient le calcul existant ; elles ne qualifient pas l’éligibilité fiscale d’un investissement réel.

1. Créer le bien puis contrôler et valider l’acquisition : 2355 débit 60000, 34551 débit 12000, 4481 crédit 72000. Conserver l’original.
2. Ouvrir le tableau d’amortissement. Comparer les cinq lignes avec les valeurs ci-dessous. La bascule linéaire intervient en année 4 dans cet exemple.
3. Utiliser Générer pour chaque année autorisée, puis sélectionner chaque exercice dans le Journal et valider sa dotation. Les exercices de cet exemple sont antérieurs au jour de démonstration ; ne pas substituer des années futures.
4. Après les cinq validations, retrouver six écritures définitives et débits = crédits = 132000 MAD. Amortissement cumulé 60000, VNC comptable 0 ; acquisition initiale conservée.
5. Régénérer les dotations 2025 : zéro nouvelle écriture. Capturer le plan, les comptes et le résultat de reprise.

| Année | Dotation MAD | Cumul MAD | VNC MAD |
|---|---:|---:|---:|
| 2021 | 24000 | 24000 | 36000 |
| 2022 | 14400 | 38400 | 21600 |
| 2023 | 8640 | 47040 | 12960 |
| 2024 | 6480 | 53520 | 6480 |
| 2025 | 6480 | 60000 | 0 |

Oracle indépendant livré : oracle_degressif_60000_5_ans.json. Cette variante reste Non testé dans votre fiche jusqu’à votre propre exécution.

## 12 — Inventaire physique et valeur du stock

### Où aller

Facturation → Inventaire & stock : Comptage physique, Valeur du stock, Mouvements & CMUP et Rapprochement comptable ; Comptabilité → Livre d’inventaire.

### Prérequis et données

Dossier autonome RECETTE INVENTAIRE 313, exercice 2025 ouvert. Reprendre l’annexe inventaire complète pour créer capital 1000, achat 10 unités à 20 HT+TVA 40=240, paiement 240 et stock initialement acheté 10. Comptage 31/12/2025 :8 unités. Ne pas simplement saisir un stock initial 10 et prétendre avoir testé le parcours d’achat.

### Manipulations

1. Dans Valeur du stock, vérifier 10 unités, CMUP 20 et valeur 200 avant comptage.
2. Dans Comptage physique, sélectionner 31/12/2025. Saisir toutes les quantités, y compris 0 pour un article réellement compté à zéro.
3. Vérifier 8 unités sur l’article principal, écart−2 et valeur d’écart−40 ; un champ laissé vide n’est pas un comptage zéro.
4. Utiliser Valider l’inventaire. Examiner les mouvements ; le stock devient 8.
5. Dans Rapprochement comptable, utiliser Générer l’écriture de stock. Contrôler 3111 débit 160/6114 crédit 160, puis valider dans le Journal.
6. Dans Livre d’inventaire, comparer la photographie, exporter le PDF/CSV disponibles et conserver les preuves. N’archiver qu’après résolution des contrôles.

### Résultats à vérifier

- Stock 200 → 160, perte physique 40. Ne pas ajouter une seconde OD de perte 40 : achat 200 et variation au crédit de 160 donnent déjà la charge nette 40 dans cet oracle.
- Avec capital 1000 et paiement 240 : banque 760, fournisseur 0, résultat avant impôt−40, actif=passif 960.
- Quatre écritures/neuf lignes, total débits=crédits 1640.
- Une source historique inconnue apparaît « À vérifier » ; génération/clôture/archivage concernés sont refusés sans inventer une valeur zéro.

### Preuve et limite

Comptage, mouvements, écritures et exports. Les cas Na N/Inf historiques demandent une préparation technique sur cluster isolé ; le testeur ne doit pas injecter ces valeurs sur la base réelle. L’annexe inventaire comporte 19 cas détaillés.

### Vérifier le contrôle des mouvements et du CMUP

1. Dans Inventaire & stock, ouvrir Mouvements & CMUP. Retrouver l’article compté à 8 unités avec son CMUP connu de 20. Contrôler sa quantité, son coût et les diagnostics. L’audit ne crée pas de mouvement ou d’écriture.
2. Cocher Afficher uniquement les anomalies. Les lignes sans anomalie disparaissent de la liste ; les compteurs de synthèse continuent de porter sur tous les articles contrôlés. Cliquer Recontrôler pour actualiser le contrôle réel.
3. Si l’environnement de test contient un historique préparé avec nombre absent ou non fini, vérifier À vérifier dans la quantité ou le coût concernés et Audit incomplet au-dessus du tableau. Le diagnostic doit indiquer le champ et, pour une source de mouvement, son identifiant. Ne pas interpréter une inconnue comme zéro ou comme rupture de stock.
4. Une valeur courante connue peut rester visible malgré une chaîne historique incomplète. Conserver le diagnostic pour demander une analyse des sources ; ne pas ajouter de correction physique afin de faire disparaître un avertissement.

Les lectures API des alertes et des mouvements bruts sont également protégées, mais elles n’ajoutent pas de nouvel écran dans Articles. Les tests de bureau et mobile vérifient l’onglet Mouvements & CMUP sur une API connectée et une base isolée. La validation manuelle de votre dossier reste à effectuer.

## 13 — Balances, grand livre et liasse détaillée

### Où aller

Comptabilité → Balances, Grand livre et Liasse fiscale. Les écrans Bilan/CPC/ETIC de présentation sont regroupés dans la liasse.

### Prérequis et données

Reprendre le dossier vente des fiches 03 à 06 pour les soldes 1200, puis le dossier IMMO ou inventaire pour les détails d’actif. Toujours contrôler société, exercice, dates et inclusion des écritures validées avant comparaison.

### Manipulations

1. Dans Grand livre, sélectionner 5141 et la période du 01/01/2025 au 31/12/2025. Vérifier les virements 400/800 et le solde 1200 du dossier vente.
2. Dans Balances, consulter générale, auxiliaire et âgée. Le client soldé ne doit plus porter une créance 1200 restante.
3. Exporter Excel/PDF et ouvrir les fichiers. Comparer titres, filtres, dates et totaux avec l’écran.
4. Dans Liasse fiscale, ouvrir T1 · Bilan : examiner les sous-postes d’immobilisations, brut, amortissements/provisions, net et N−1 ; utiliser un dossier contenant des écritures d’immobilisation validées.
5. Ouvrir T2 · CPC, ESG, Financement et T3–T25 · ETIC. Lire les diagnostics B6/B7 avant de compléter les ventilations à partir de pièces fiables.
6. Exporter Excel/PDF de la liasse et retrouver les mêmes détails et repères. Les anciens snapshots archivés ne sont pas recalculés automatiquement.

### Import de balance externe

Le bloc de préparation dans Liasse fiscale accepte CSV/XLSX, une feuille, colonnescompte/debit/credit ; intitule facultatif. Importer N, éventuellement N−1, contrôler l’aperçu, conserver la préparation et la rouvrir. Cette action produit une préparation versionnée ; elle ne crée pas les écritures du journal ni un dossier fiscal complet automatiquement.

### Résultats à vérifier

- Mêmes périmètres et chiffres entre écran et exports ; filtre conservé après chargement tardif.
- T1…T25 est une numérotation interne ; les codes ETIC d’origine sont conservés.
- Les justificatifs, échéances ou ventilations inconnus restent À compléter. Une balance techniquement clôturée peut rendre CPC/CAF indisponibles : ne pas interpréter l’indisponibilité comme zéro.

### Preuve et limite

Captures du détail et fichiers ouverts. La numérotation n’est pas une codification officielle DGI ; XML/EDI SIMPL-IS reste désactivé.

## 14 — TVA, IS et retenues déclarées

### Où aller

Comptabilité → Déclaration TVA et Résultat fiscal / IS ; Facturation → Factures/Règlements pour la RAS déclarée ; Paramètres → Fiscalité.

### Prérequis

Dossier fictif qualifié pour la recette fiscale. Le jeu principal et ses annexes fixent leurs hypothèses de laboratoire. Ne pas déduire l’assujettissement, le droit à récupération ou une obligation de RAS du seul taux affiché.

### Manipulations : TVA et IS

1. Dans Déclaration TVA, choisir la période et le régime configurés. Vérifier les factures et encaissements concernés, puis comparer les montants aux opérations du dossier.
2. Contrôler crédit antérieur/prorata explicitement saisis et l’identité de la société dans l’impression/PDF.
3. Dans Résultat fiscal / IS, relire le résultat comptable, les réintégrations, déductions et déficits séparément.
4. Examiner impôt théorique,CM/CSS si applicables, crédits/retenues, acomptes versés et solde. Documenter les justificatifs ; ne pas assimiler un acompte prévu à un paiement.
5. Confirmer la liquidation uniquement dans un dossier préparé pour cela, après tous les contrôles. Retrouver son snapshot et son historique.

### Manipulations : estimation RAS

Créer une facture distincte HT 1000/TVA 200/TTC 1200, estimation RAS 100. Après paiement 1100 sans capture, le reste dû doit être 100. L’estimation ne vaut ni règlement, ni attestation, ni crédit IS.

### Manipulations : capture déclarative

Sur une installation isolée où la migration 083 a été activée par le technicien, suivre l’annexe capture RAS : virement 400 puis capture 30 → reste 770 ; virement 700 → reste 70 ; capture 70 → reste 0. Saisir explicitement montant, date, référence et compte. Utiliser les mêmes dates cohérentes et dossiers indépendants que l’annexe. Si la fonction indique indisponible, noter Bloqué ; le testeur n’exécute pas de SQL pour contourner ce message.

### Résultats à vérifier

- Une capture produit une OD traçable qui reste à valider ; aucune proratisation universelle du taux n’est inventée.
- La qualification fiscale et les attestations restent à justifier. Annulation ou délettrage doivent suivre le flux explicite et conserver les originaux.
- Une OD historique absente, ambiguë ou incohérente peut bloquer l’annulation : conserver ce diagnostic.

### Preuve et limite

Exports, snapshots et références des justificatifs de laboratoire. RASTVA, qualification exhaustive IR/IS/TVA, pont vers crédits IS et déclarations complètes restent incomplets. L’application ne dépose pas automatiquement ces déclarations.

## 15 — Clôture, à-nouveaux et archives

### Où aller

Comptabilité → Clôture d’exercice, Livre d’inventaire et Liasse fiscale.

### Prérequis

Dossier annuel fictif complet du cahier principal ; exercice passé, préparé et ouvert. La simple démonstration de vente des fiches 03–06 ne remplit pas les travaux d’inventaire, paramètres fiscaux et justificatifs nécessaires. Consulter d’abord les contrôles sans cliquer Clôturer.

### Manipulations

1. Ouvrir Clôture d’exercice et lire chaque bloc : brouillons, dotations, inventaire physique, rapprochement stock/immobilisations, impôt et FEC.
2. Traiter les prérequis dans leurs modules ; ne pas modifier une écriture validée pour supprimer une alerte. Compléter uniquement les données justifiées.
3. Quand le dossier de test est prêt, relever les balances et exporter les pièces avant clôture.
4. Cliquer Clôturer l’exercice 2025 et confirmer. Vérifier le statut Clôturé ; tenter un nouveau brouillon daté de 2025 sur ce dossier de test : refus attendu.
5. Sélectionner l’exercice suivant préparé par le flux ; contrôler les à-nouveaux équilibrés et les auxiliaires conservés, puis les exports 2025/2026.
6. Dans Liasse fiscale, lire les contrôles ; utiliser Finaliser uniquement lorsque le bouton est disponible. Relever version et SHA-256, recharger et télécharger PDF/Excel archivés.

### Résultats à vérifier

- Un exercice définitivement clôturé reste verrouillé ; une permission administrateur ordinaire ne signifie pas qu’il peut être rouvert par un bouton existant.
- Les à-nouveaux reprennent les vrais comptes et auxiliaires ; les postes client/fournisseur ne disparaissent pas simplement parce que leur collectif net est nul.
- L’archive fiscale devient immuable et conserve son contenu même si les paramètres courants changent ensuite.

### Preuve et limite

Captures des contrôles, refus après clôture, écritures AN et empreinte d’archive. Finalisation interne ne vaut pas dépôt DGI. La procédure exceptionnelle de réouverture définitive reste à définir. Ne pas tenter cette démonstration sur un dossier annuel réel.

## 16 — Dossiers salariés, congés et préparation de paie

### Où aller

Paie / GRH → Paie & GRH : Équipe, Préparation mensuelle et Congés & absences.

### Prérequis et données

Dossier GRH fictif distinct ; module activé ; administrateur ou rôle autorisé. Salariée DEMO GRH, matricule DEMO-GRH-01, poste Assistante, salaire brut 6000 MAD, date d’embauche 01/09/2026. Ne pas inventer un numéro CNSS officiel. Type de contrat choisi explicitement ou laissé À compléter lorsque la fiche le permet.

### Manipulations

1. Dans Équipe, cliquer Ajouter un salarié. Saisir les données fictives, enregistrer puis rouvrir avec Modifier.
2. Vérifier contrat/date/salaire et les informations à compléter ; aucun CDI automatique ne doit masquer un contrat inconnu.
3. Tester Archiver puis Réactiver sur ce salarié de démonstration ; vérifier son statut et sa conservation.
4. Dans Congés & absences, cliquer Nouvelle demande : typecongé, du 12/10/2026 au 13/10/2026, motif Démonstration. Enregistrer puis approuver ou refuser avec commentaire ; Confirmer la décision.
5. Vérifier les dates, les jours calendaires informatifs et la décision après rechargement. Consulter également avec un rôlelecture.
6. Dans Préparation mensuelle, choisir le mois/année, examiner les paramètres et preuves documentaires. Utiliser uniquement la simulation proposée si ses prérequis sont satisfaits ; lire les motifs d’indisponibilité ou de péremption.

### Résultats à vérifier

- Dossier conservé, archivage traçable, dates non présumées et actions réservées aux rôles autorisés.
- Demande et décision visibles ; les jours affichés ne constituent pas un calcul du solde légal de congés.
- Les versions documentaires restent figées ; une modification des références peut rendre une capture Périmée.

### Preuve et limite

Captures fiche, décision et préparation. Variables, bulletins définitifs, déclarations CNSS et écritures SA automatiques ne sont pas encore un parcours terminé. Aucun net légal attendu n’est imposé ici ; les références sociales doivent être complétées. Les paramètres de calcul existants sont encore partagés par année, pas tous propres à chaque société : ne pas modifier un taux commun pour une simple démonstration.

## 17 — Utilisateurs, mot de passe et sauvegardes

### Où aller

Paramètres → Utilisateurs, Mon compte, Fiche société et Sécurité & contrôle.

### Prérequis

Comptes de démonstration ; administrateur et lecteur distincts. Image PNG/JPEG fictive pour le logo. Préparer un compte sacrifiable pour le changement de mot de passe ; conserver l’accès administrateur principal de test.

### Manipulations

1. Dans Utilisateurs, inviter un utilisateur de test et lui attribuer le rôle Lecture dans la société de recette. Ne pas retirer le dernier administrateur.
2. Se connecter avec ce lecteur : consulter les pièces, constater l’absence ou le refus des actions de modification. Revenir ensuite à l’administrateur de test.
3. Dans Fiche société, charger le logo fictif, enregistrer et télécharger un PDF facture pour retrouver le logo. Tester le retrait dans ce dossier uniquement.
4. Dans Mon compte, saisir le mot de passe actuel, un nouveau mot de passe d’au moins huit caractères et sa confirmation. Cliquer Modifier mon mot de passe.
5. Se reconnecter avec le nouveau mot de passe. Vérifier le message de succès ; ne pas communiquer de mot de passe dans vos captures partagées.
6. Pour la sauvegarde, demander au technicien une recette isolée sauvegarde → restauration → contrôle des pièces. Fournir la procédure EXPLOITATION_HISABPRO.md ; ce flux utilise les outilsops, pas un bouton de restauration supposé dans l’interface.

### Résultats à vérifier

- Les accès restent limités à la société et au rôle attribués ; le mot de passe protège le compte dans ses différentes sociétés.
- Les nouvelles sessions versionnées concernées sont révoquées après changement ; les anciens JWT sans version conservent les limites de compatibilité documentées jusqu’à expiration.
- Une restauration de recette conserve données, pièces, chemins et empreintes vérifiés ; les rôles/ACL doivent être reprovisionnés séparément lorsque le dump les exclut.

### Preuve et limite

Captures sans secret,PDF avec logo et rapport technique de restauration. Aucun test destructif sur PostgreSQL réel. Sauvegarde de production, restauration à chaud, rétention et reprise après sinistre restent à valider.

## 18 — Fiche de suivi, dépannage et documents de référence

### Fiche à compléter ensemble

| Fiche | Vérification | Statut initial | Résultat réel / preuve |
|---|---|---|---|
| 01 | Société, modules, exercice | Non testé | À renseigner |
| 02 | Tiers, articles, frais | Non testé | À renseigner |
| 03 | Devis → BC → BL → facture | Non testé | À renseigner |
| 04 | Factures, échéances, filtres | Non testé | À renseigner |
| 05 | Règlements et édition | Non testé | À renseigner |
| 06 | Journal validé et lettrage | Non testé | À renseigner |
| 07 | Acompte 400 + solde 800 | Non testé | À renseigner |
| 08 | Achat partiel 1 +3 | Non testé | À renseigner |
| 09 | Avoir, chèque et impayé | Non testé | À renseigner |
| 10 | Relevé et rapprochement | Non testé | À renseigner |
| 11 | Immobilisations | Non testé | À renseigner |
| 12 | Inventaire 200 → 160 | Non testé | À renseigner |
| 13 | États et exports | Non testé | À renseigner |
| 14 | TVA, IS, RAS qualifiée | Non testé | À renseigner |
| 15 | Clôture et archives | Non testé | À renseigner |
| 16 | GRH et simulation limitée | Non testé | À renseigner |
| 17 | Accès et sauvegardes | Non testé | À renseigner |

Pour une anomalie, relever : fiche, société fictive, exercice, numéro de pièce, date/heure, actions, message exact, attendu, résultat réel et capture. Ne pas mettre de mot de passe ou de données personnelles réelles dans ce compte rendu.

### Dépannage rapide

- 401 Unauthorized : la session n’est pas reconnue ; se reconnecter. Un OPTIONS 200 ne prouve pas qu’un POST de connexion a réussi.
- Coût de réception inconnu : dans une copie isolée préparée par le technicien, vérifier le refus. Le BR reste en cours ; lignes, stocks et écritures restent conservés, même si la seconde ligne échoue. Ne pas assimiler l’absence à zéro.
- Conversion BL/BR refusée pour prix ou total invalide : aucun brouillon ni lien de facture ajouté. Le formulaire reste ouvert et permet de reprendre après vérification des sources. Une ligne invalide non sélectionnée ne bloque pas une facturation partielle valide.
- Menu absent : vérifier les modules activés, le rôle et la société sélectionnée.
- Période fermée/exercice clôturé : respecter le refus ; demander une vérification des périodes, jamais une suppression des contrôles. Un calendrier partiel sans période couvrant la date doit également être refusé. La création normale d’un nouvel exercice prépare ses périodes ; ce correctif ne déverrouille aucun exercice historique.
- Polices et icônes : elles sont désormais livrées avec l’application. Après déploiement du ZIP cumulatif, les écrans doivent se charger sans attendre un fournisseur externe de fontes. Les symboles restent visibles et les boutons Achat/Vente conservent leur libellé accessible. Cela ne supprime pas la nécessité du backend ni ne rend l’application entièrement utilisable sans réseau.
- Valeur À vérifier/À compléter : chercher la source fiable. Ne pas remplacer l’inconnu par zéro pour avancer.
- Totaux différents : comparer société, exercice, dates, statut de validation et nombre de pièces avant de conclure à un bug.
- Une ancienne erreur de contrainte GRH au démarrage : transmettre le journal complet au technicien et vérifier les fichiers déployés. Ne pas exécuter une réparation SQL improvisée.
- En cas de HTTP 500 ou écran bloqué : conserver message et logs, noter Échoué/Bloqué et arrêter les actions dépendantes.

### Références du dossier livré

- docs/recette/CAHIER_RECETTE_HISABPRO.pdf et .xlsx : scénario annuel 218 cas, résultats utilisateur à effectuer.
- docs/recette/ANNEXE_RECETTE_COMMERCIALE.pdf : devis à approvisionner et documents client.
- docs/recette/ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.pdf : réception 1+3 et paiements/lettrage.
- docs/recette/ANNEXE_RECETTE_BILAN_DETAILLE.pdf : détails de bilan et cohérence des exports.
- docs/recette/ANNEXE_RECETTE_INVENTAIRE_20261010.pdf et .xlsx :19 cas, oracle 1640 et bilan 960.
- docs/recette/ANNEXE_RECETTE_RAS_ESTIMATION_20261009.pdf et ANNEXE_RECETTE_RAS_CAPTURE_20261010.pdf : retenues et limites distinctes.
- docs/recette/ANNEXE_RECETTE_PAIE_GRH.pdf et .xlsx :26 cas de recette GRH.
- docs/EXPLOITATION_HISABPRO.md ; docs/MISE_A_JOUR_RAS_20261009.md : procédures réservées au technicien.
- docs/audit/MATRICE_COUVERTURE_HISABPRO.md ; CHECKLIST_UTILISATEUR_20261007.md ; REGISTRE_ANOMALIES_HISABPRO.md : couverture et limites.

### Comment lire les validations

Les preuves sont dans CODEX_PROGRESS.md et Test. La globale336 a réussi3009cas avant341/343/344 ; les69tests343 et91tests344 sont distincts. La globale346 compte3105réussites et7échecs, conservés avec les anciens échecs315. Après les corrections de dates351/352, la consolidation354 a réussi3126tests, avec686empreintes inchangées. Cette globale précède les lots357/360/363. Le diagnostic359 conserve2réussites et6échecs comme preuve antérieure. Le lot363 rétablit la lecture qualifiée :40tests ciblés réussis,6tests de sources globales/avoirs liés réussis et8Edge finaux sur ordinateur/mobile. Le diagnostic original passe désormais ses8cas. La consolidation365 possède un rapport distinct à consulter pour son résultat réel. Le lot368 possède son rapport de lecture des règlements et ses tests ciblés après365 ; consulter les résultats réellement exécutés sans étendre la portée de la globale365. Les suites ne s’additionnent pas. Générer ce guide ne relance aucun test métier et ne touche à aucune base.

Développement global : partiel. Recette utilisateur : à effectuer ; 17 statuts Non testé. Mise en production : non validée. Paie réglementaire complète, annexes officielles09E/09F/09G, codification officielle DGI et XML/EDI applicable restent à terminer ou bloqués par leurs prérequis. Les justificatifs historiques manquants ne sont pas inventés.

## Compléments du 19 octobre 2026

Ces compléments précisent les fiches existantes et leurs jeux indépendants. Reporter vos résultats dans les fiches concernées ; ils ne constituent pas de nouvelles validations humaines déjà acquises.

### Règlements : annuler à une date choisie

Dans Cycle commercial → Vente ou Achat → Règlements, ouvrir Annuler par contrepassation sur un règlement comptabilisé admissible. Vérifier le tiers et le montant, choisir Date d’annulation, renseigner si nécessaire Motif (facultatif), puis Confirmer l’annulation. La date du jour est proposée et reste modifiable. Un refus conserve les valeurs saisies ; les règles du serveur restent applicables, notamment pour les périodes fermées et les lignes lettrées.

Pour un lot, Annuler toute la ventilation présente tous ses numéros et son total, y compris les lignes masquées par les filtres. La date et le motif concernent tout le lot ; un refus d’une ligne empêche l’opération collective. Après succès, contrôler et valider les contrepassations dans le Journal. Une RAS liée est également contrepassée. Les écritures d’origine sont conservées.

Le rôle Consultation seule conserve la liste, Actualiser et le dossier RAS. Les commandes Modifier, Supprimer, Annuler et Ventiler ne sont pas proposées dans Règlements. Une consultation ne crée pas automatiquement d’OD. Mode d’emploi détaillé : docs/ANNULATION_REGLEMENT_655.md.

### Distinguer une panne d’une vraie liste vide

Les listes Règlements et Bons de réception affichent une alerte si leur lecture échoue. Aucun total ou compteur n’est alors présenté comme disponible. Utiliser Réessayer après rétablissement du service, ou Actualiser pour relire une liste déjà affichée. Une réponse vide correctement chargée conserve Aucun règlement trouvé ou Aucun bon de réception. Les réponses tardives d’un ancien exercice ou jeton sont écartées dans ces deux listes.

Les montants historiques à vérifier conservent leur diagnostic propre. Ne pas remplacer une valeur inconnue par zéro ou supprimer une pièce pour faire disparaître l’avertissement. Les autres listes et les opérations en cours restent des périmètres distincts ; conserver le message précis d’un refus.

### Documents des OD RAS : parcours chiffré complet

Ouvrir l’annexe docs/recette/ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.docx, sa version PDF ou son Excel de suivi. Utiliser sa révision2, dans la société fictive et l’exercice 2026 qu’elle décrit. Les faits fiscaux y sont explicitement supposés pour le laboratoire et doivent être qualifiés séparément pour toute opération réelle.

Le jeu fixe un capital de 100 000 MAD, un achat de 10 000 HT + 2 000 TVA = 12 000 TTC, une quote-part de 6 000 dont TVA 1 000, un virement de 5 250 et une capture RAS de 750. Avant annulation : quatre pièces/neuf lignes, débit = crédit = 118 000, banque 94 750, fournisseur 6 000 et résultat −10 000. Après annulation : six pièces/treize lignes, débit = crédit = 124 000, banque 100 000, fournisseur 12 000 et résultat −10 000. Les pièces ajoutées ne créent aucune ligne comptable. Le compte 4457 est choisi pour ce jeu.

1. Dans Déclaration TVA, ouvrir Registre des retenues TVA ou Préparation mensuelle des retenues opérées. Choisir l’année civile ou le mois prévu du jeu ; ce mois ne prouve pas un versement.
2. Déplier Documents liés aux OD. Vérifier Capture · OD et, après annulation, Contrepassation · OD. Les documents de ces deux pièces sont distincts.
3. Avec le rôle autorisé, utiliser Joindre un fichier sur la bonne OD. Le PDF fictif fourni est DOCUMENT_FICTIF_649.pdf. Deux fichiers homonymes ne doivent pas s’écraser. Une référence sans fichier reste une référence, sans fichier supposé.
4. Vérifier l’actualisation sans F5, puis les exports CSV, Excel et PDF. Les références, dates et noms de fichiers apparaissent ; télécharger séparément l’original pour contrôler ses octets.
5. Annuler le règlement avec la date et le motif du cas RDO-008, contrôler les deux contrepassations, ajouter le document sur la nouvelle OD et vérifier les soldes prévus par l’annexe.

Les 12 cas humains de l’annexe restent Non testé. Le registre et la préparation sont internes ; aucun dépôt officiel, versement, crédit ou attestation n’est validé automatiquement. L’empreinte de l’export couvre les données documentaires affichées ; les fichiers joints se téléchargent séparément. Mode d’emploi : docs/RAS_DOCUMENTS_647.md.

### Vente et achat correspondants entre sociétés

Dans Paramètres → Sociétés liées, un administrateur autorisé dans les deux sociétés déclare explicitement leur association et leurs tiers respectifs. Cette association ne crée aucune facture, écriture ou stock et ne qualifie pas un groupe fiscal.

Sur une vente validée, ouvrir le détail puis Correspondance entre sociétés. Choisir la liaison, associer chaque ligne à un article de l’acheteur et déclarer les paramètres de TVA de l’achat. Préparer le brouillon correspondant, puis le contrôler, le valider et le comptabiliser chez l’acheteur selon son propre circuit. Les deux comptabilités restent distinctes. Les paiements, avoirs et livraisons ne sont pas répliqués par ce mécanisme.

Suivre les données exactes et étapes de docs/recette/ANNEXE_RECETTE_SOCIETES_LIEES_20261019.docx et de son Excel. Les guides docs/SOCIETES_LIEES_633.md et docs/FACTURES_CORRESPONDANTES_635.md donnent les droits et limites. La fonctionnalité est partielle ; son ancien statut Absent dans la checklist est actualisé.

### Reprises partielles de provisions et clôture

Dans Clôture, ouvrir Reprises partielles de provisions, sélectionner une dotation validée liée, relire les reprises, réservations et le disponible, puis préparer l’opération avec date, montant et justification. Contrôler l’aperçu avant création et la nouvelle écriture avant validation dans le Journal. Une source historique incertaine conserve son diagnostic.

Utiliser le jeu indépendant docs/recette/ANNEXE_RECETTE_REPRISES_PROVISIONS_20261019.docx et son Excel. Le guide docs/REPRISES_PROVISIONS_615.md précise les étapes et exports. Le suivi ne détermine ni la disparition d’un risque ni une déductibilité fiscale et ne remplace pas le grand livre.

### Lire le bilan d’avancement actuel

Consulter docs/audit/RAPPORT_SESSION_20261019_645_671.md, la matrice et la checklist actualisées. Les résultats automatisés sont des preuves distinctes de votre recette. Le guide conserve ses 17 statuts humains Non testé et les preuves restent à renseigner. Les annexes complètent le cahier annuel et ne le remplacent pas. Développement global partiel, recette utilisateur à effectuer et production non validée ; RH/paie et le point6 réservé au retour humain restent différés.
