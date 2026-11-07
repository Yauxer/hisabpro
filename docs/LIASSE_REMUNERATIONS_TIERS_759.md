# MODE D’EMPLOI ET RECETTE — RÉMUNÉRATIONS DES TIERS HISABPRO

Version 1 du 23 octobre 2026. Lot759 : formulaire de préparation interne dans le mode Liasse seule.

## Fonction disponible et accès

Saisir un profil, des identités et des mouvements. Chaque conservation crée une nouvelle version et préserve les autres compléments. Le dossier contient JSON/PDF/Excel avec logo et manifeste SHA256. Aucun taux de retenue calculé, aucune écriture générée ou fiche tiers modifiée. Ce document n’est pas un formulaire DGI ; les modèles151 et annexes applicables restent à obtenir. Une revue déclarée ne prouve pas la conformité fiscale. La CNSS concerne le bénéficiaire tiers, pas la paie.

Installer le ZIP différentiel dans l’environnement de test avec son arborescence puis redémarrer les services habituels. Aucune migration nouvelle : conserver le socle des préparations104 déjà installé. Utiliser une société fictive MAD et un admin ou comptable. Lecture peut consulter et exporter sans conserver.

Ouvrir Comptabilité → Liasse fiscale → mode Liasse seule. Importer et conserver une balance de test, ou sélectionner une préparation fictive existante. Les CSV755 peuvent servir de support technique. Le jeu1400/740/37 ci-dessous est documentaire et indépendant : il n’est pas une ventilation exhaustive des21500 d’honoraires du scénario755. Il ne modifie pas les comptes et ne vérifie pas leur rapprochement. Pour un dossier réel, établir le rapprochement et l’exhaustivité sur pièces.

Ouvrir « Préparer les rémunérations des tiers ». Dans « Rubrique tiers à documenter », choisir successivement T151-P, T151-B et T151-M, codes internes. Pour chaque rubrique, choisir « Saisie documentée — à revoir », saisir la justification ci-dessous puis ajouter les lignes. Passer de rubrique conserve le brouillon ; les trois rubriques sont enregistrées ensemble.

## Données exactes du jeu fictif

Copier les identifiants des bénéficiaires dans leurs mouvements. Les références de mouvements sont uniques. Un champ indiqué vide reste vide, pas zéro. Les montants sont fournis par le scénario, sans taux fiscal prescrit.

### T151-P — Profil documentaire annuel

Justification du tableau : Revue du dossier entièrement fictif759

Ligne 1 :

- Désignation du dossier tiers = Prestataires fictifs2026
- Période comptable vérifiée = oui
- Exhaustivité des sources revue = oui
- Absence de rémunérations confirmée = non
- Référence de source de la ligne = NOTE759

### T151-B — Identités documentaires des bénéficiaires

Justification du tableau : Identités fournies dans le jeu de recette uniquement

Ligne 1 :

- Nom ou raison sociale du bénéficiaire = OMEGA CONSEIL FICTIF759
- Identifiant interne du bénéficiaire = B759-A
- Adresse du bénéficiaire = Adresse fictive A, Casablanca
- Profession ou activité du bénéficiaire = Conseil fictif
- Identification fiscale du bénéficiaire = IF-FICTIF759-A
- Identification taxe professionnelle = (laisser vide)
- CNSS du bénéficiaire = CNSS-FICTIF759-A
- Régime déclaré du bénéficiaire = Personne morale IS
- Identité revue sur pièces = oui
- Référence de source de la ligne = FICHE759-A

Ligne 2 :

- Nom ou raison sociale du bénéficiaire = PRESTATAIRE FICTIF759 B
- Identifiant interne du bénéficiaire = B759-B
- Adresse du bénéficiaire = Adresse fictive B, Rabat
- Profession ou activité du bénéficiaire = Intermédiation fictive
- Identification fiscale du bénéficiaire = (laisser vide)
- Identification taxe professionnelle = TP-FICTIF759-B
- CNSS du bénéficiaire = CNSS-FICTIF759-B
- Régime déclaré du bénéficiaire = Personne physique RNR ou RNS
- Identité revue sur pièces = oui
- Référence de source de la ligne = FICHE759-B

### T151-M — Mouvements et retenues documentés

Justification du tableau : Trois pièces fictives et montants explicitement fournis, aucun taux calculé

Ligne 1 :

- Désignation du mouvement tiers = Honoraires fictifs
- Bénéficiaire du mouvement = B759-A
- Catégorie déclarée de rémunération = Honoraires
- Sens documentaire du mouvement = Allocation
- Date comptable source = 2026-06-20
- Somme comptabilisée = 1000
- Événement fiscal déclaré = Versement
- Date de cet événement justifiée = 2026-07-10
- Somme soumise à retenue = 600
- Montant retenu = 30
- Référence du mouvement corrigé = (laisser vide)
- Source du mouvement revue = oui
- Référence de source de la ligne = M759-A

Ligne 2 :

- Désignation du mouvement tiers = Commission fictive
- Bénéficiaire du mouvement = B759-B
- Catégorie déclarée de rémunération = Commissions, courtages et rémunérations similaires
- Sens documentaire du mouvement = Allocation
- Date comptable source = 2026-07-01
- Somme comptabilisée = 500
- Événement fiscal déclaré = Mise à disposition
- Date de cet événement justifiée = 2026-07-12
- Somme soumise à retenue = 200
- Montant retenu = 10
- Référence du mouvement corrigé = (laisser vide)
- Source du mouvement revue = oui
- Référence de source de la ligne = M759-B

Ligne 3 :

- Désignation du mouvement tiers = Correction fictive documentée
- Bénéficiaire du mouvement = B759-A
- Catégorie déclarée de rémunération = Honoraires
- Sens documentaire du mouvement = Correction documentée
- Date comptable source = 2026-08-01
- Somme comptabilisée = 100
- Événement fiscal déclaré = Inscription en compte
- Date de cet événement justifiée = 2026-08-01
- Somme soumise à retenue = 60
- Montant retenu = 3
- Référence du mouvement corrigé = M759-A
- Source du mouvement revue = oui
- Référence de source de la ligne = M759-C

## Conservation et contrôles

Cocher « Je confirme les données et déclarations saisies, sans valider une liasse complète » puis « Conserver les rémunérations des tiers dans une nouvelle version ». Le numéro change et les données reparaissent sans F5. Rouvrir le formulaire pour voir les contrôles conservés.

Oracles indépendants : comptabilisé1000+500−100=1400MAD ; soumis600+200−60=740MAD ; retenu30+10−3=37MAD. B759-A/Honoraires :900/540/27 ; B759-B/Commissions :500/200/10. La correction est soustraite selon son sens explicite et conserve l’origine M759-A. Aucun taux ou paiement n’est déduit.

Les contrôles portent sur la version enregistrée ; modifier un brouillon ne les change pas avant conservation. Les points manquants sont indiqués par bénéficiaire/mouvement. L’identification TP peut renseigner l’identité lorsque l’identifiant fiscal est absent ; RC/ICE ne sont pas substitués. Une CNSS vide permet une version partielle et reste signalée à qualifier.

## Inconnus, refus et droits

Vider CNSS du bénéficiaireA : conservation partielle, identité à compléter. Vider une somme soumise : ce total devient indisponible, jamais zéro. NaN, Infinity, négatifs directs et précision supérieure à deux décimales sont refusés. Pour soustraire une correction documentaire, choisir Correction documentée et référencer une origine distincte. Aucune écriture historique n’est réparée.

Un bénéficiaire référencé mais absent, un identifiant interne en doublon ou une référence de mouvement en doublon est refusé. Retenu supérieur au soumis saisi est refusé. Aucune retenue déclarée exige0/0 explicites et date fiscale vide. CPU/autoentrepreneur, location, autres catégories et événements hors période restent à qualifier ; leurs données ne sont pas effacées. Une identification fiscale partagée alerte sans fusion. Les crédits IS reçus sur les ventes ne remplacent pas les rémunérations versées aux tiers.

## Exports et justificatifs

Télécharger le dossier ZIP. Vérifier les feuilles T151-P/B/M, contrôle, regroupements et points à revoir ; mêmes références et montants dans PDF/JSON, logo dans PDF/Excel. Le manifeste fournit taille/SHA256. Les totaux portent sur les seules pièces saisies, sans rapprochement comptable automatique.

Joindre JUSTIFICATIFS_FICTIFS_TIERS759.pdf à la version depuis les justificatifs complémentaires si souhaité. Pièce de recette sans valeur réelle. Consulter l’ancienne version : elle reste intacte. Renseigner les preuves et résultats dans le suivi Excel après exécution humaine.

## Cas de recette utilisateur

| ID | Actions | Résultat attendu et preuve | Statut |
|---|---|---|---|
|TIERS759-01|Ouvrir une préparation fictive MAD et parcourir les trois rubriques du formulaire tiers.|Profil/identités/mouvements accessibles, codes internes et limites visibles. Capture d’accès.|Non testé|
|TIERS759-02|Saisir exactement les trois rubriques ci-dessus et conserver.|Nouvelle version, totaux1400/740/37, groupes900/540/27 et500/200/10 ; aucune écriture. Capture version/contrôles.|Non testé|
|TIERS759-03|Modifier seulement un brouillon puis consulter l’ancienne version.|Totaux enregistrés et version historique intacts, aucun changement comptable. Captures avant/après.|Non testé|
|TIERS759-04|Sur copie, vider CNSS puis une somme soumise ; conserver des versions distinctes.|Identité à compléter ; total soumis indisponible si une valeur manque, zéro non inventé. Captures points à revoir.|Non testé|
|TIERS759-05|Sur copie, saisir NaN puis Infinity dans Somme comptabilisée et tenter de conserver ; corriger ensuite1000.|Refus lisible, brouillon préservé, aucune version parasite ; reprise sans F5. Captures refus/reprise.|Non testé|
|TIERS759-06|Sur copie, dupliquer un bénéficiaire puis une référence de mouvement ; retirer les doublons et supprimer l’origine de la correction.|Trois refus sans mutation comptable ni nouvelle version. Captures des références et refus.|Non testé|
|TIERS759-07|Consulter avec lecture, refaire avec comptable sur390px et tenter un accès depuis une autre société.|Lecture sans conservation, comptable autorisé, autre société refusée ; écran lisible. Captures rôles/mobile.|Non testé|
|TIERS759-08|Télécharger ZIP ; ouvrir PDF/Excel/JSON/manifeste, joindre la pièce fictive et consulter l’ancienne version.|Sources/totaux concordants, logos, manifeste et pièce traçable ; ancien état intact. Conserver fichiers/preuves.|Non testé|

## Limites et suite

Ces huit cas restent Non testé humainement. Les tests automatisés sont détaillés au rapport759 ; Word/Excel natifs et environnement cible restent à vérifier. Modèles administratifs et états particuliers à obtenir avant dépôt. Sources proposées automatiquement depuis le Journal et import en masse hors de ce lot. Aucun rapprochement comptable, droit fiscal, paiement ou dépôt validé. RH/paie etpoint6 différés.
