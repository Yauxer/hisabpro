# Qualification du catalogue de paie — 28 octobre 2026

Le catalogue, ses versions immuables, la séparation IR/CNSS/AMO, l'approbation indépendante et l'habilitation réglementaire dédiée sont livrés pour recette. Le lot 2 complet reste partiel : variables mensuelles et contrôles associés suivent. Aucun moteur de cotisations/IR ni bulletin définitif n'est livré par 889.

## Résultats réellement exécutés

La campagne `paie889_final` a exécuté 12 fichiers pytest : **175 tests distincts réussis**, sans échec, erreur ou ignoré, en **681,19 secondes**. Répartition : 70 unitaires/source, 91 API/SQL PostgreSQL natif isolé, 14 parcours Edge/API/PostgreSQL isolé. Les petites campagnes précédentes ne s'ajoutent pas à ce total.

Build frontend final : code 0, **203 modules**, Vite **7,74 secondes**. Les avertissements xlsx/chunk existants restent visibles. Compilation Python : **12 fichiers modifiés/ajoutés**, tous compilés. Le candidat fige **492 fichiers produit** par SHA-256. Le code produit n'a pas changé pendant la campagne finale ; seuls les documents de livraison ont été ajoutés ensuite.

Le périmètre couvre notamment : catalogue vide sans taux inventé, migration113 rejouée avant et après données/habilitation expert, compatibilité des anciens dossiers, version future et historique figé, refus de requalification passée, erreurs monétaires, plafonds IR/CNSS divergents, refus de cumul supposé, droits, révocation, isolation des sociétés, auto-approbation, autorisation réglementaire distincte, contrôles SQL, décisions concurrentes, navigation ordinateur/mobile et paie historique.

Tous les tests PostgreSQL ont utilisé des instances natives temporaires protégées par nonce et un rôle applicatif non propriétaire. Aucun PostgreSQL utilisateur, fichier `.env` ou secret réel n'a été utilisé. La simple création/approbation d'une rubrique ne crée aucune écriture ni paiement ; cette absence est réellement contrôlée.

## Tentatives et corrections conservées

| Campagne | Résultat | Explication |
|---|---|---|
| Reprise887 ciblée | 1 réussi, 8 désélectionnés ;62,76 s | Contrôle de continuité, pas une nouvelle qualification complète887 |
| Profil881 unitaire | 15 réussis ;1,25 s | Garde des chemins existante |
| paie889_api | 7 réussis, 6 échoués ;88,43 s | Deux défauts produit :verrou de racine immuable incompatible avec les droits SQL minimaux,et Decimal sérialisé en texte dans l'aperçu. Deux attentes de tests sur des chemins inexistants ont été corrigées en404/405,avec tests directs de whitelist en complément. |
| paie889_corrige | 19 réussis, 1 échoué, 13 erreurs ;27,49 s | Helper unitaire avec argument répété et erreur syntaxique JSX empêchant la compilation des fixtures ;corrigés avant la suite. |
| Build initial | code1 | Deux fermetures JSX manquantes ;corrigées |
| Build corrigé | code0 ;6,01 s | Avant derniers contrôles de qualification |
| paie889_catalogue_final | 33 réussis ;86,03 s | Avant ajout de l'habilitation réglementaire dédiée |
| paie889_ui | 2 réussis ;59,18 s | Premiers parcours desktop/mobile |
| paie889_qualification | 50 réussis ;113,14 s | Avec habilitation réglementaire dédiée,avant le dernier test de date/rejeu |
| paie889_final | 175 réussis ;681,19 s | Dernier code produit,référence finale |

Les JUnit et la répartition détaillée sont conservés dans [PREUVE_PAIE_889.json](../../Test/PREUVE_PAIE_889.json). Une tentative échouée n'est pas présentée comme une réussite ; les résultats qui se recouvrent ne sont pas additionnés.

## Documents et limites

[Guide d'utilisation](CATALOGUE_PAIE_889.md), [PDF de recette](RECETTE_CATALOGUE_PAIE_889.pdf), [Excel](SUIVI_CATALOGUE_PAIE_889.xlsx), [données exactes](JEU_CATALOGUE_PAIE_889.json). Le complément contient **12 cas humains**, PDF 6 pages et classeur 3 feuilles, avec tous les statuts **Non testé**, formules de progression et graphique. Les calculs indépendants fictifs couvrent0,300,500 et800,01MAD. Captures : [desktop](preuves/889_1440_catalogue.png), [mobile](preuves/889_390_catalogue.png).

Les références et empreintes de preuves sont déclarées par l'opérateur ; leur saisie n'est pas une certification du document ou de son interprétation. Aucun taux/plafond légal nouveau n'est activé. Le contrôle des types de justificatifs et incompatibilités sur des variables reste à implémenter au lot suivant ; le catalogue les conserve déjà.

| Axe | Statut |
|---|---|
| Développement catalogue et interfaces | Livré pour recette |
| Tests automatisés de ce périmètre | Réussis sur environnement isolé |
| Lot2 complet et moteur de paie | À poursuivre |
| Recette utilisateur | À effectuer |
| Migration113 et déploiement réels | Non effectués ;tester sur copie |
| Mise en production | Non validée |
