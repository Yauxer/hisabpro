# HisabPro — Utiliser la RAS TVA guidée

Cette fonction rapproche une RAS TVA déclarée d’un règlement réel et prépare une OD. Elle conserve les faits renseignés et la référence des pièces. Elle ne valide pas la qualification fiscale, ne choisit pas le compte et ne génère aucun reversement ou dépôt. La déclaration TVA automatique des périodes et reports concernés reste indisponible jusqu’à qualification de l’imputation et du reversement des retenues.

## Avant de commencer

1. Utilisez la bonne société et le bon exercice. La facture doit être définitive et comptabilisée, avec son tiers réel. Le règlement doit déjà représenter le montant de trésorerie effectivement payé ou reçu.
2. Le premier périmètre couvre 2026, article 117-V-b / liste B : les parties, la prestation, les exclusions et l’attestation doivent être vérifiées sur pièces. Les services ne sont jamais classés automatiquement.
3. Un administrateur doit avoir appliqué la migration 099 après la chaîne existante jusqu’à 098, notamment 083. Cet écran n’exécute aucune migration. L’installation cible doit suivre votre procédure de sauvegarde et de mise à jour.
4. Les règlements immédiats comptabilisés par virement ou espèces sont couverts. RAS HT/historique, avoirs/acomptes affectés et autres paiements actifs sans ventilation RAS TVA tracée restent hors de ce raccordement.

## Préparer la capture depuis l’interface

1. Ouvrez Cycle commercial → Vente ou Achat → Règlements. Sur le règlement concerné, utilisez l’icône « Consulter ou déclarer la RAS ». Choisissez « RAS TVA guidée ».
2. Dépliez « Assistant RAS TVA · 2026 ». La date vient du règlement. Renseignez les situations réelles des parties, la listeB, les exclusions, l’attestation et la quote-part TTC avant retenue avec sa TVA correspondante. Cliquez sur « Simuler la RAS TVA ».
3. Renseignez le justificatif de ventilation, une référence RAS TVA et le compte destination explicitement justifié par le comptable. Aucune valeur de compte n’est proposée comme obligation fiscale.
4. Cliquez sur « Vérifier le règlement et afficher l’aperçu ». Le net doit égaler le règlement et les cumuls doivent rester dans le TTC et la TVA de la facture. Tout changement de saisie impose un nouvel aperçu.
5. Contrôlez les pièces et le rapprochement, cochez la confirmation puis cliquez sur « Préparer la capture RAS TVA et son OD ». Attendez la fin de l’enregistrement : la facture et le règlement se rafraîchissent automatiquement.

## Contrôler, valider et consulter

1. Rouvrez l’icône RAS du règlement : le dossier conserve les montants, la ventilation et les références déclarées. Le rôle lecture peut consulter ce dossier ; il ne peut pas préparer de capture.
2. Dans le Journal, contrôlez l’OD et son vrai tiers, puis validez-la avec le rôle autorisé. L’écriture de trésorerie existante n’est pas créée une seconde fois. La capture et ses lignes restent protégées.
3. Après paiement complet, le lettrage est une action distincte : validez les pièces nécessaires, sélectionnez le compte et le tiers réels, puis rapprochez les débits et crédits équilibrés.
4. Pour corriger, délettrez si nécessaire puis utilisez l’annulation du règlement. Le dossier et les OD originales sont conservés, avec leur contrepassation. Ne remplacez pas les faits d’une ancienne capture pour la requalifier.

## Comprendre les refus

1. « Migration 099 » : l’administrateur doit qualifier l’installation ; aucun clic ne crée les tables.
2. Net différent du règlement : vérifiez la trésorerie réellement versée et la quote-part avant retenue. Un règlement déjà comptabilisé se corrige par annulation, pas par changement silencieux de son montant.
3. Autre paiement non ventilé, avoir, acompte ou RAS HT : ce cas n’est pas encore pris en charge. Conservez les justificatifs et faites qualifier le traitement ; ne choisissez pas une autre situation pour contourner le contrôle.
4. Aperçu périmé ou période fermée : refaites l’aperçu ou faites examiner la période par le rôle autorisé. Un exercice définitivement clôturé reste verrouillé.
5. Déclaration TVA à compléter : le logiciel ne présente ni ancien montant ni zéro comme un solde calculé. Les règles et justificatifs d’imputation/reversement restent à qualifier avec le comptable.

## Exemple fictif

Facture HT1000,00 / TVA200,00 / TTC 1200,00 MAD. Toutes les qualifications et exclusions doivent être justifiées sur pièces.

|Quote-partTTC|TVA|RAS 75 %|Trésorerie|
|---|---|---|---|
|400.00|66.67|50.00|350.00|
|800.00|133.33|100.00|700.00|

Aucun compte destination imposé. Ce guide ne vaut ni recette utilisateur ni validation réglementaire.
