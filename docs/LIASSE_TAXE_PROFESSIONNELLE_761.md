# MODE D’EMPLOI ET RECETTE — TAXE PROFESSIONNELLE HISABPRO

Version 1 du 23 octobre 2026. Lot761 : préparation interne et simulation brute sur bases et classes fournies.

## Fonction et limites

Le formulaire conserve un profil annuel et des établissements avec valeurs locatives, classes et avis explicitement sourcés. Il calcule un brut arithmétique et compare les avis fournis, sans calculer une imposition, un montant dû, une échéance ou un paiement. Aucune écriture ni immobilisation n’est créée/modifiée. Les modèles administratifs ne sont pas intégrés.

Les taux normaux C3=10%,C2=20%,C1=30% ont été lus dans les extraits officiels indexés du guideDGCT2024,page120,article9-I. Les noticesDGCT07-20/14-25 ont été consultées. Les PDF complets ont rencontré des timeouts/cachemiss ; aucune lecture intégrale ou empreinte binaire n’est revendiquée. Le référentiel applicable et la situation réelle doivent être revus sur pièces. Ni la VL ni la classe ne sont déduites d’un loyer, compte ou valeur nette amortie.

Le brut n’applique pas automatiquement les règles de base de l’article7, exonérations/réductions, hôtel, prorata, droit minimum, franchise ou émission. Un brut inférieur à200MAD n’est pas rendu artificiellement nul ou présenté comme dû. Sans local ou sans ligne, aucune taxe nulle n’est déduite. Arrondi HALF_UP au centime par établissement : convention documentaire, pas arrondi légal validé ; le calcul exact est conservé.

## Prérequis et accès

Installer les fichiers du ZIP différentiel sur environnement de test avec l’arborescence exacte et redémarrer les services habituels. Aucune migration nouvelle, conserver le socle des préparations104. Société fictive MAD, rôles admin/comptable ou lecture pour consultation. RH/paie restent hors périmètre.

Ouvrir Comptabilité → Liasse fiscale → mode Liasse seule, importer/conserver une balance fictive ou sélectionner une préparation existante. Les CSV755 peuvent servir de support technique. Les bases ci-dessous sont fictives et indépendantes de ces balances : aucune qualification TP réelle n’est attestée. Ouvrir « Préparer la taxe professionnelle » puis « Rubrique TP à documenter ».

Choisir successivement TP-P et TP-E, codes internes. Dans chaque rubrique choisir Saisie documentée — à revoir, saisir justification puis lignes exactes ci-dessous. Les deux rubriques sont conservées ensemble. Une année TP2026 est explicitement saisie, distincte de la période comptable importée ; les références sont fictives.

## Données exactes à saisir

Tous les noms, activités, classes, bases et avis sont pédagogiques. Aucune classe de métier réelle n’est affirmée. Les confirmations sont celles du jeu fictif, pas une validation d’un dossier fiscal réel.

### TP-P — Profil documentaire TP annuel

Justification du tableau : Profil et millésime fictifs revus, aucun droit réel attesté

Ligne 1 :

- Désignation du dossier TP = Simulation pédagogique TP2026
- Année civile TP déclarée = 2026
- Période fiscale revue = oui
- Liste des établissements exhaustive revue = oui
- Référentiel applicable revu sur pièces = oui
- Référence de source de la ligne = NOTE761

### TP-E — Établissements, bases et avis

Justification du tableau : Bases et classes choisies uniquement pour vérifier le calcul, pas une qualification réelle

Ligne 1 :

- Désignation de l’établissement = Local fictif A
- Identifiant interne de l’établissement = E761-A
- Commune déclarée = Casablanca fictif
- Adresse de l’établissement = Adresse pédagogique A
- Activité principale déclarée = Activité fictive A sans classement réel
- Classe déclarée et justifiée = C2
- Valeur locative annuelle fournie = 30000
- Base annuelle complète revue = oui
- Classe revue sur référence = oui
- Périmètre déclaré de l’établissement = Établissement avec local — hors régime particulier, exonération et réduction
- Situation au premier janvier revue = oui
- Montant de l’avis fourni = 6200
- Référence de l’avis fourni = AVIS761-A
- Avis rattaché à l’année TP déclaré = oui
- Référence de source de la ligne = BASE-CLASSE761-A

Ligne 2 :

- Désignation de l’établissement = Local fictif B
- Identifiant interne de l’établissement = E761-B
- Commune déclarée = Rabat fictif
- Adresse de l’établissement = Adresse pédagogique B
- Activité principale déclarée = Activité fictive B sans classement réel
- Classe déclarée et justifiée = C3
- Valeur locative annuelle fournie = 12000
- Base annuelle complète revue = oui
- Classe revue sur référence = oui
- Périmètre déclaré de l’établissement = Établissement avec local — hors régime particulier, exonération et réduction
- Situation au premier janvier revue = oui
- Montant de l’avis fourni = 1200
- Référence de l’avis fourni = AVIS761-B
- Avis rattaché à l’année TP déclaré = oui
- Référence de source de la ligne = BASE-CLASSE761-B

## Conserver et vérifier

Cocher « Je confirme les données et déclarations saisies, sans valider une liasse complète » puis « Conserver la préparation TP dans une nouvelle version ». Rouvrir le formulaire : version actualisée sans F5, contrôles conservés.

Oracles indépendants : A30000×20%=6000 ; B12000×10%=1200 ; brut7200MAD. Avis fournis6200+1200=7400MAD. Écart brut−avis=−200MAD, visible sans modifier l’avis ni la comptabilité. L’avis reste une donnée déclarée, aucune émission ou imposition n’est confirmée.

Modifier seulement le brouillon ne modifie pas les contrôles conservés. Un champ VL vide laisse le brut indisponible, jamais zéro. Une classe, base, situation de janvier ou régime non revu laisse le brut qualifié global indisponible même si un calcul arithmétique existe. Hors2026 ou année différente de la préparation, aucune proposition globale qualifiée.

## Erreurs, avis et situations particulières

Saisir NaN/Infinity, négatif direct ou précision de plus de deux décimales : refus sans nouvelle version, brouillon gardé. Dupliquer un identifiant interne d’établissement : refus. Même avis référencé sur deux établissements : montants conservés, total global des avis inconnu, alerte contre double addition sans ventilation justifiée.

Vider la référence d’avis ou le rattachement à l’année : avis non comparable, aucune date d’échéance supposée. Une différence avec le brut n’est pas une erreur comptable à réparer automatiquement. Une situation particulière reste à qualifier sans perte de données.

Pour tester le brut faible, sur copie choisir C3 etVL100 pourA : brutA10 et total1210, sans montant dû ou exonération déduit. Pour l’arrondi documentaire, C3/VL0,05 donne exact0,005 et centime0,01 ; aucun arrondi fiscal officiel validé.

## Exports et justificatifs

Télécharger le dossier ZIP de la version. Contrôler JSON TP, PDF, Excel et manifeste SHA256. Feuilles TP-P/TP-E, Simulation brute TP et revue établissements ; valeurs7200/7400/−200 et sources concordantes ; logo dans PDF/Excel. Le calcul exact et les points à revoir restent exportés. Les autres compléments et versions historiques sont préservés.

Joindre JUSTIFICATIFS_FICTIFS_TP761.pdf depuis les justificatifs complémentaires si souhaité. Il n’a aucune valeur fiscale réelle. Consulter la version précédente et conserver les captures/fichiers de preuve. Le suivi Excel reste vierge jusqu’à exécution humaine ; les formules Office doivent être recalculées dans Office.

## Cas de recette utilisateur

| ID | Actions | Résultat attendu et preuve | Statut |
|---|---|---|---|
|TP761-01|Ouvrir une préparation fictive MAD et les rubriques TP-P/TP-E.|Accès lisible et limites visibles, codes internes et source DGCT indiqués. Capture accès.|Non testé|
|TP761-02|Saisir exactement profil et deux établissements, confirmer puis conserver.|Nouvelle version, VL42000, brut7200, avis7400, écart−200, aucun dû confirmé. Capture contrôles/version.|Non testé|
|TP761-03|Sur copie, vider la VL puis retirer la revue de base ; conserver des versions séparées.|Brut inconnu si VL manque ; brut arithmétique connu mais proposition globale indisponible si revue manque. Captures des états.|Non testé|
|TP761-04|Saisir NaN et Infinity dans la VL et tenter de conserver ; corriger ensuite30000.|Refus sans version parasite ou écriture ; brouillon gardé et reprise sans F5. Captures refus/reprise.|Non testé|
|TP761-05|Sur copie, dupliquer l’identifiant établissement puis partager la référence d’avis entre deux lignes.|Doublon établissement refusé ; avis partagé signalé et total des avis inconnu sans double addition. Captures références.|Non testé|
|TP761-06|Sur copie, testerA C3/VL100 puis C3/VL0,05 ; consulter l’ancien état.|BrutsA10 puis0,01 avec exact0,005 conservé ; aucun dû/exonération déduit. Ancienne version intacte. Captures/exports.|Non testé|
|TP761-07|Tester lecture, comptable390px et accès d’une autre société.|Lecture ne conserve pas, comptable autorisé, autre société refusée ; écran lisible. Captures rôles/mobile.|Non testé|
|TP761-08|Télécharger ZIP et vérifier PDF/Excel/JSON/manifeste/logo ; joindre pièce fictive puis consulter l’ancienne version.|Sources et montants concordants, pièce traçable ; autres compléments et version antérieure intacts. Conserver fichiers/preuves.|Non testé|

## Limites et suite

Huit cas Non testé humainement. La simulation brute normale est disponible ; taxation complète, régime particulier, base réglementaire calculée, modèle administratif et dépôt restent à qualifier. Recette cible/Office et imposition réelle non validées. Aucun PostgreSQL réel utilisé ; RH/paie etpoint6 différés.
