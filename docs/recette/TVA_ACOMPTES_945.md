# Acomptes : date effective et vérification de TVA

Utiliser une **copie fictive indépendante, exercice2025 ouvert**, avec le module Comptabilité actif. Ne pas modifier le régime ou les écritures de la société annuelle déjà clôturée pour effectuer ces essais.

Préparer dans chaque copie : banque **Banque Recette**, compte5141, RIB fictif `000000000000000000000001`, deviseMAD ; tiers **Tiers FICTIF945**, client ou fournisseur selon le cas. Les montants d'acomptes ci-dessous sont **TTC**. Le taux20% est une donnée de ce jeu, pas une qualification automatique de toutes les activités.

## Chèque ou effet reçu avant son encaissement

1. Régime société **encaissement**. Dans Acomptes, créer un acompte client de24000MAD, daté01/06/2025, TVA20%, modechèque, référence `AC-FICTIF945`, banque ci-dessus. Pour l'effet, renseigner aussi l'échéance05/07/2025.
2. Vérifier « En attente ». Déclaration TVA, exercice2025, juin : aucune TVA collectée sur cet acompte.
3. Ouvrir le détail par l'icôneœil. **Date de l’opération** vaut aujourd'hui par défaut ; saisir explicitement **05/07/2025**, puis Confirmer l'encaissement. Relire la date effective dans le détail et vérifier que la liste se rafraîchit sansF5.
4. Déclaration TVA : juin0, juillet4000, année4000. Calcul indépendant :24000÷1,20=20000HT ;TVA4000.

L'encaissement utilise l'écriture existante de réception, datée05/07/2025 :D5141/C4421=24000TTC pour un client, ouD3411/C5141 pour un fournisseur. La correction ne crée pas une nouvelle OD de TVA et ne modifie pas ces modèles. La ventilation comptable des avances entre périodes et les déclarations déjà déposées restent à qualifier avec le responsable comptable avant production.

## Rejet sans encaissement

Dans une nouvelle copie, reprendre le chèque24000du01/06/2025. Sans l'encaisser ni l'imputer, choisir la date05/06/2025 et Marquer rejeté. TVAjuin et annuelle :0pour ce seul acompte ;aucune écriture de réception bancaire n'a été créée. Ce cas ne valide pas le traitement d'un rejet intervenant dans une période ultérieure à un encaissement antérieur déjà déclaré.

## Imputations partielles sur deux factures

Dans une nouvelle copie, régime **débit**, recevoir par virement24000TTC le01/06/2025. Créer et valider deux factures de vente du même tiers :10000HT+2000TVA chacune, les15et16juin. Imputer **6000TTC**, le20juin, sur chacune ;ne pas imputer le montant total de l'avance sur chaque facture.

- Avant affectations :TVAjuin8000 (4000sur avance +2000sur chaque facture).
- Après la première affectation6000 :7000 ;après la seconde :6000. Disponible de l'avance12000 ;deux affectations distinctes dans l'historique.
- Les écritures d'imputation existantes sontD4421/C3421,6000par affectation ;elles restent traçables. Le calcul TVA lit chaque montant du registre, sans se fier à un seul numéro de facture affiché.
- Variante fournisseur :deux factures d'achat10000HT+2000TVA, avance versée24000TTC ;TVA récupérable0avant rattachement,1000après6000affectés à la première facture,2000après la seconde. Le reliquat non affecté n'est pas déduit automatiquement. Comptabilisation existanteD4411/C3411par affectation.

Annuler une affectation depuis l'historique crée sa contrepassation ;elle ne doit pas disparaître du registre. Les dates d'opération et les périodes déjà déclarées doivent être revues :ces tests ne constituent pas un mécanisme de gel d'une déclaration déposée.

## Sources historiques et permissions

Un ancien chèque/effet marqué encaissé mais sans date effective reste **à qualifier**, avec un avertissement dans la déclaration. Le programme ne remplace pas cette date par l'échéance. Une avance immédiate historique par virement conserve sa date d'origine. Ces lectures ne réparent ni ne réécrivent les données.

L'administrateur et le comptable peuvent saisir l'opération. Le lecteur voit le détail mais pas les commandes de paiement ;l'API refuse une tentative de mutation403.

Le test ciblé de la variante **HP-FIS-033** reprend l'avance24000TTC puis la facture120000HT, son solde120000TTC et une facture impayée14400TTC avec chèque rejeté2000. Il vérifie juin24000de TVA et décembre0sur l'impayée. C'est une copie TVA ciblée, pas un rejeu des50opérations annuelles :la fiche complète reste partielle et son résultat humain Non testé.

[Sources officielles et limites](../audit/SOURCES_TVA_ACOMPTES_945.md) · [Cahier humain complet](CAHIER_RECETTE_HISABPRO.pdf) · [Suivi humain](CAHIER_RECETTE_HISABPRO.xlsx).

## Reproduire les contrôles techniques

Les fixtures créent exclusivement des serveurs et PostgreSQL temporaires, avec vérification de nonce. Ne pas lancer `main.py` contre une base réelle pour reproduire ces tests. Les commandes et les identifiants réellement exécutés sont conservés dans la preuve945. Le build reproductible est `node Test/build_frontend_isole.mjs` ;il utilise un répertoire d'environnement vide, une URL API inerte et une sortie privée sous `.codex-tests`.
