# RNI mensuel préparatoire — lot921

Ce contrôle relie les bases fiscales déjà préparées au revenu net imposable sur des déductions **déclarées et justifiées**. Il conserve ensuite une équivalence mathématique du barème annuel2026 divisée par12. Ce résultat n’est pas une retenue à prélever : frais mensuels réglementaires, arrondis de liquidation et régularisations restent à qualifier. Net, bulletin, montant à déclarer et versement demeurent indisponibles.

## Installation sur copie

Installer le code du ZIP, puis appliquer123 et124 dans l’ordre sur une copie isolée, après les migrations des bases fiscales120 et leurs prérequis. Ne pas réécrire les migrations déjà appliquées.124 crée une table de contrôles immuables et ses garde-fous ; aucun ancien contrôle annuel n’est recalculé. La base habituelle n’a pas été utilisée par cette session.

## Utilisation

1. Dans **05 · Fiscalité salariale → Bases fiscales**, préparer des sources réellement approuvées : brut, social, puis bases fiscales. Les confirmations concernent les faits connus et justifiés.
2. Dans le résultat du salarié, ouvrir **Préparer le RNI mensuel**. Identité, période et montants sources sont repris sans ressaisie.
3. Saisir frais professionnels et autres déductions avec leurs références. Zéro doit être explicite et justifié ; une donnée inconnue reste vide. Le produit ne calcule pas un forfait mensuel légal à partir du cumul annuel.
4. Confirmer le cadre mensuel seulement s’il est établi. Renseigner séparément le nombre de personnes éligibles et sa preuve. Laisser la date de versement vide lorsqu’elle n’est pas connue : aucune date automatique de paiement.
5. Conserver le contrôle pédagogique, puis lire les bases, déductions, anomalies, variables et fractions exactes. Le lien vers la préparation permet d’examiner la provenance. Les contrôles antérieurs sont consultables dans l’onglet **RNI mensuel**.

Une prime non mensuelle, une période de référence différente ou un versement source sur une autre année bloque le calcul mensuel général, même si la case de confirmation est cochée. Des versements connus distincts sont signalés. Les déductions excessives ne sont pas ramenées arbitrairement à zéro. Une source devenue périmée nécessite une nouvelle préparation ; les contrôles déjà conservés restent historiques.

## Recette entièrement fictive

[PDF avec données et six cas](RECETTE_RNI_MENSUEL_PAIE_921.pdf) · [Excel de suivi](SUIVI_RNI_MENSUEL_PAIE_921.xlsx) · [Données exactes](JEU_RNI_MENSUEL_PAIE_921.json) · [Préparation des bases909](BASES_FISCALES_CONNECTEES_909.md) · [Dates et rattachement919](RATTACHEMENT_REVENUS_919.md).

Créer la rubrique de gain **mensuelle avant approbation** dans une société de recette vierge ; ne pas modifier l’ancienne rubrique ponctuelle909. Les taux sociaux FISC909 et leurs preuves sont uniquement des hypothèses de test, jamais les taux CNSS/AMO à utiliser pour un salarié réel.

Oracle indépendant :9300.11−60.00−2250.03−0.00=6990.08. Les2250.03 sont une déduction fictive déclarée, pas un forfait réglementaire. Équivalence annuelle83880.96 :2000+4000+1164.288=7164.288 ; /12=597.0240. Réduction mathématique pour deux personnes :2×600/12=100.0000 ; résultat497.0240, fraction62128/125. Ce montant ne doit servir ni au paiement ni à la déclaration. L’affichage à quatre décimales n’est pas un arrondi fiscal de retenue.

## Sources et limites

Barème annuel et réduction annuelle : CGI2026 DGI, articles73–75, [copie publiée par le CRI Casablanca](https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf). La transformation annuelle/12 est ici une inférence mathématique explicitement identifiée, sans qualification d’une méthode complète de liquidation mensuelle. Aucun taux annuel2011 n’a été repris.

Les primes et rappels exigent une analyse de leurs périodes de référence : note circulaire DGI717 tome1, pages360–361, [copie hébergée par Monexpert](https://www.monexpert.ma/download/documents/kAuCgJLbx5gugjWaPhYvhgvdW9zLB5HW4gFxNK2q.pdf). Cet hébergeur n’est pas gouvernemental. Cette source ne suffit pas à valider les plafonds, arrondis et régularisations mensuels2026.

La recette utilisateur et la mise en production restent à effectuer séparément. Prochaine étape : qualifier la politique de liquidation mensuelle et les cas de régularisation avant de calculer une retenue effective, le net et les bulletins.
