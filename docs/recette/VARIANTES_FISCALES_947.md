# Vérifier les déficits, déductions et refus fiscaux

Ces essais utilisent exclusivement des copies fictives indépendantes. Le [cahier complet](CAHIER_RECETTE_HISABPRO.pdf), le [classeur humain](CAHIER_RECETTE_HISABPRO.xlsx) et les [données chiffrées](jeu_donnees_recette.json) restent les références. Les fiches concernées sont **HP-FIS-031/032 et HP-NEG-029 à033** ;aucun résultat humain n'est rempli automatiquement.

## Préparer une copie avant IS

Partir d'une copie du scénario avant l'écritureIS-2025 et son imputationPPRF-IMP. Ne pas modifier une liquidation confirmée ou des écritures définitives du dossier principal. Le résultat comptable avantIS doit être **129 830 MAD**.

Les tests techniques reconstituent par API les48opérations prévues avantIS, dans l'ordre chronologique, avec les tiers réellement désignés par le jeu. Ils ne prétendent pas restaurer les fichiers ou registres complets du dossier. Les références de recette ne remplacent pas des justificatifs historiques ;aucune date de pièce manquante n'est inventée. Les contrôles FEC éventuels restent visibles.

Dans FiscalitéIS, renseigner les deux réintégrations explicites du scénario :

| Type | Catégorie | Compte | Montant | Libellé / source fictive |
|---|---|---|---:|---|
| Réintégration | Provisions à contrôler |61955|1 500|REC-LIT01,provision non admise selon hypothèse du jeu|
| Réintégration | Provisions à contrôler |61964|2 000|REC-DEP01,dépréciation non admise selon hypothèse du jeu|

L'amende de500est déjà détectée automatiquement. Total réintégré4000 ;bénéfice fiscal133830 ;IS théorique du jeu2025à17,5% :23420,25. Ces chiffres vérifient le scénario ;ils ne qualifient pas automatiquement le régime d'une société réelle.

Ajouter le créditPPRF prévu :montant200, déjà imputé0,date30/11/2025,référenceINT-PPRF. Sans autre versement enregistré dans cette copie, le solde simulé est23220,25. Les références fiscales antérieures manquantes restent à documenter avant toute liquidation définitive.

## HP-FIS-031 — déficit antérieur documenté

Utiliser une **variante de reprise**, dont l'existence antérieure et la pièce fiscale2024sont explicitement prévues. Ne pas ajouter ce déficit à la nouvelle société principale créée en2025.

1. Dans FiscalitéIS2025, section Déficits fiscaux reportables, saisir Exercice d'origine2024, Part ordinaire10000, Part amortissements2000, Commentaire `DEF-2024 : attestation FICTIVE de reprise du scénario`.
2. Ajouter un millésime antérieur. Contrôler la proposition12000, puis Confirmer l'imputation.
3. Vérifier bénéfice121830 ;IS21320,25 ;crédit200 ;solde simulé21120,25.
4. Recharger et relire :même proposition confirmée, une seule consommation de10000ordinaire et2000amortissements ;aucune nouvelle écriture comptable.

L'éligibilité et la durée du report doivent être revues sur les pièces et textes applicables par le responsable fiscal. Une proposition mécanique n'est pas une attestation de déficit. L'absence d'une référence d'acomptes antérieurs ne doit pas être remplacée arbitrairement pour finaliser.

## HP-FIS-032 — reprise antérieurement taxée

Utiliser une autre copie avantIS, avec la provision1518existante et la justification fictive de sa taxation antérieure prévue par la fiche.

**Prérequis du plan de comptes :**71955est une subdivision utilisée par ce scénario ;elle n'est pas livrée comme compte standard universel. Si elle manque, l'administrateur ouvre Plan comptable → Ajouter une subdivision, numéro71955, libellé `Reprise de provision REC-REPRISE — subdivision FICTIVE947`. Elle doit se rattacher à la racine active7195. Ne pas changer le référentiel global pour contourner un compte manquant.

1. Journal, ODdu31/12/2025, référenceREC-REPRISE :D1518/C71955=1000. Enregistrer puis valider selon le parcours normal. Les écritures antérieures restent intactes.
2. Consulter FiscalitéIS avant tout retraitement :résultat avantIS130830 ;bénéfice fiscal134830. La reprise n'est pas automatiquement déduite.
3. Saisir Déduction, catégorie Reprises de provisions antérieurement taxées, compte71955,montant1000,libellé `REC-REPRISE : provision antérieurement taxée, justificatif FICTIF HP-FIS-032`.
4. Contrôler bénéfice133830 etIS23420,25, puis recharger. La déduction n'ajoute pas une seconde écriture de reprise et ne confirme pas la liquidation.

## HP-NEG-029 à033 — contrôles négatifs

Sur des copies dédiées, vérifier :

- Provision1500non qualifiée :diagnostic visible, aucun impact choisi arbitrairement. Dans ce jeu, le candidat de provisions peut regrouper1500+2000=3500détectés ;son montant fiscal reste inconnu tant qu'il n'est pas qualifié.
- Crédit200avec déjà imputé201 :refus ;pas de crédit négatif créé.
- Référence annuelle forcée20000avec justification vide :refus, paramètres antérieurs inchangés.
- Confirmation de liquidation sur exercice ouvert :refus409 ;simulation lisible, aucun snapshot final.
- IS attendu23420,25mais charge1 :clôture refusée pour incohérence. Ne pas modifier le calcul ou une écriture définitive afin d'accepter1.

Les cinq cas négatifs techniques utilisent une note de synthèse fictive du seul résultat, dérivée des comptes6/7du jeu. Cette isolation évite qu'un contrôle de stock ou d'immobilisations non préparé masque le refus fiscal recherché. Ce n'est pas une clôture du dossier annuel complet.

[Résultats](RESULTATS_MVP_947.md) · [Rattachement des fiches](../../Test/QUALIFICATION_FICHES_947.json) · [Suivi automatisé](SUIVI_AUTOMATISATION_CAHIER_947.xlsx).
