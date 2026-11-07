# Cumuls et frais professionnels annuels — 913

Dans **05 · Fiscalité salariale → Cumuls et frais annuels**, sélectionner les préparations fiscales d'un salarié pour conserver un contrôle annuel relié à ses sources. Ce contrôle calcule les frais du cadre général2026 lorsque les faits nécessaires sont confirmés ; il ne calcule aucune retenue mensuelle, somme à verser ou paie définitive.

## Installation et données nécessaires

Sur une copie isolée et sauvegardée, faire appliquer `hisabpro-backend/121_paie_frais_annuels.sql` après120. Elle ajoute deux tables et leurs liens/protections, sans réécrire les anciennes données. La migration peut être rejouée. Son absence laisse l'ancien contrôle annuel IR disponible et affiche un message d'installation pour le nouvel onglet.

Préparer le brut, le social et les [bases fiscales909](BASES_FISCALES_CONNECTEES_909.md). Identité et rémunération sont nécessaires à la lecture ; proposer est nécessaire au calcul. Chaque source doit concerner le salarié et la société sélectionnés et rester cohérente avec les données actuelles. Le changement d'une variable ou d'une règle applicable peut imposer de refaire les simulations sources.

## Choisir les périodes

Créer un contrôle, choisir le salarié par matricule et nom, puis **Charger les préparations**. Chaque mois propose les versions réellement présentes. Choisir une seule version par mois. Le bouton **Choisir les mois à version unique** remplit uniquement les mois comportant exactement une version ; il laisse les mois ambigus vides.

Un contrôle partiel est possible pour consulter les cumuls des périodes choisies, mais les frais annuels restent inconnus tant que les douze mois ne sont pas couverts. Aucun mois n'est extrapolé, aucun mois absent n'est remplacé par zéro. Les préparations en anomalie restent signalées.

Ce périmètre du moteur couvre les mois complets ; les cas d'entrée/sortie et les années partielles nécessitent un traitement distinct, encore à développer.

## Confirmer le cadre et les déductions

Le calcul des frais porte sur le cadre général59-I-A. Confirmer uniquement s'il s'applique : catégoriesB/C, autres employeurs et situations particulières non traitées restent hors de ce calcul. Vérifier l'exhaustivité et la correspondance des revenus annuels, notamment les paiements, et renseigner la référence de contrôle. La date d'une période ne prouve pas une date de paiement.

Le [CGI2026, documentDGI diffusé par leCRI](https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf), article59-I-A et paragraphes suivants, pages imprimées98–99, a été consulté : le taux dépend du revenu brut annuel imposable, tandis que la base de la déduction exclut les avantages concernés. Le seuil annuel est78000, les taux35%/25% et le plafond35000 dans le cadre pris en charge. Ces paramètres annuels ne sont pas convertis en paramètres mensuels dans ce lot. Document :SHA-256 `fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1`, consultation28/10/2026.

Saisir les **autres déductions annuelles déjà établies**, leur référence et confirmer leur contrôle, y compris une déclaration justifiée de zéro. L'application ne calcule pas ici leurs conditions particulières. Une valeur inconnue laisse le RNI inconnu, même si les frais professionnels sont connus.

## Résultats et historique

Les montants certains sont conservés : cumuls des périodes, frais annuels arithmétiques, revenu après frais avant autres déductions et RNI annuel arithmétique avant arrondis. Des déductions supérieures au revenu ne créent ni zéro de secours ni déficit salarial inventé. Déplier les sources pour retrouver mois, versions, identifiants et empreintes.

Un nouveau contrôle conserve de nouvelles références sans modifier l'ancien. La reprise exacte d'une requête conserve son résultat historique ; elle ne prétend pas revalider les sources à la date de consultation. Les nouveaux calculs vérifient les sources actuelles.

## Exemple exclusivement fictif

Douze préparations du jeu909 : cumul du brut imposable111601.32 ; base des frais108001.20 ; cotisations déductibles720.00. Taux annuel25%, frais27000.3000, revenu après frais83881.0200. Autres déductions0.00 explicitement établies et confirmées : RNI arithmétique83881.0200. Ces montants découlent des douze préparations réelles de test ; ils ne sont pas une mensualisation ou une preuve de paiement.

Recette utilisateur et production restent à valider. Le RNI obtenu n'est pas encore une retenue de paie ni un versement.
