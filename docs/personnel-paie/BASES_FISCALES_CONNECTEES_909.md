# Bases fiscales reliées au brut et au social — lot 909

## Ce qui est disponible

Dans **05 · Fiscalité salariale**, deux onglets séparent le contrôle annuel IR sur RNI déclaré et la préparation des bases fiscales. Depuis le détail d'une simulation sociale, **Préparer les bases fiscales** ouvre le second onglet avec l'identifiant source prérempli.

Cette préparation conserve un nouveau snapshot : brut imposable, base des frais professionnels, parts salariales déductibles et non déductibles, revenu avant frais et autres déductions. Les variables, versions de rubriques et de branches, confirmations, références, identifiants et empreintes des sources restent attachés au résultat.

**Ce revenu intermédiaire n'est pas un RNI définitif.** Les frais professionnels à déduire, autres déductions, retenue mensuelle, net, bulletin, paiement et écriture ne sont pas calculés ici. Aucune date de paiement n'est déduite de la période des variables. Aucun salaire n'est multiplié par douze.

## Installation et prérequis

Faire sauvegarder et restaurer une **copie isolée** avant d'appliquer `hisabpro-backend/120_paie_preparations_fiscales.sql`, après le socle 113–119. Cette migration ajoute une table et ses protections ; elle ne modifie pas les anciennes lignes. Une installation manquante produit un message explicite, sans casser l'ancien contrôle annuel.

Le module Personnel doit être actif et protégé. Identité et rémunération sont nécessaires à la lecture ; l'habilitation proposer est nécessaire au calcul. Le profil Personnel seul reste limité à ses chemins autorisés.

Préparer une simulation du brut puis une simulation sociale complète. Les rubriques utilisées doivent avoir un traitement IR qualifié et une qualification des frais professionnels ; les branches doivent avoir une qualification de déductibilité IR. Le [guide907](QUALIFICATIONS_FISCALES_907.md) décrit les preuves et l'approbation indépendante. Une ancienne qualification absente reste inconnue.

## Remplir le formulaire

1. Depuis le résultat social, cliquer **Préparer les bases fiscales**, puis **Nouvelle préparation fiscale**. On peut aussi ouvrir directement l'onglet Bases fiscales et saisir l'identifiant de la simulation sociale.
2. Cliquer **Charger le social**. Vérifier société, mois, salariés, base salariale et brut affichés.
3. Pour chaque salarié, saisir **la seule fraction imposable de la base salariale**, puis sa fraction éligible à la base des frais professionnels. Ne pas ajouter les variables : l'application le fait depuis les sources approuvées. Ne pas recopier le brut global. Une case vide reste inconnue ; zéro doit être justifié.
4. Renseigner la référence du contrôle et confirmer les conditions fiscales. Confirmer séparément la déductibilité intégrale des cotisations qualifiées déductibles uniquement si leurs montants sont intégralement éligibles pour ce salarié. Un plafond partiel ou une condition non traitée impose de laisser cette confirmation vide : aucune déduction intégrale ne sera inventée.
5. Donner un motif, confirmer le périmètre du calcul et cliquer **Calculer et conserver les bases**.

La base des frais ne peut dépasser la part de base imposable ; celle-ci ne peut dépasser la base salariale source. Les gains sont ventilés d'après le traitement IR de leur version conservée. Un plafond d'exonération mensuel est regroupé par rubrique ; un plafond par opération est appliqué à chaque variable. Les unités annuelle ou journalière restent bloquées si les faits de cumul ou de jours manquent. Le logiciel ne suppose pas une exemption ou une déduction à partir d'un libellé.

## Lire et vérifier le résultat

Les montants certains restent visibles si une autre base manque. Un total inconnu n'est pas remplacé par zéro. Déplier **Variables et cotisations fiscales**, puis **Qualifications fiscales conservées**, pour retrouver la ventilation et les références. Les anomalies expliquent les traitements manquants ou incohérents.

Les sources courantes sont comparées au brut et au social au moment du calcul. Une nouvelle variable, une modification du dossier ou une nouvelle version sociale applicable peut imposer de refaire les simulations sources. L'ancien résultat fiscal reste consultable avec son empreinte ; il ne se recalcule pas silencieusement. Créer une nouvelle préparation pour un nouveau calcul ; la reprise d'une même requête conserve le même résultat.

## Exemple entièrement fictif de recette

Sur cible isolée uniquement : base salariale 9 000,10 ; gain 800,01 ; exonération IR fictive par opération de 500,00 ; fraction imposable du gain exclue de la base des frais ; cotisations salariales fictives 60,00 intégralement déductibles et 294,00 non déductibles. Les bases CNSS et AMO du jeu existant sont respectivement 9 500,11 et 9 800,11.

Calcul indépendant : imposable du gain = 800,01 − 500,00 = 300,01 ; brut imposable = 9 300,11 ; base des frais = 9 000,10 ; déductible = 60,00 ; non déductible = 294,00 ; revenu avant frais et autres déductions = **9 240,11**. Frais réellement déduits et RNI définitif restent inconnus. Ces chiffres et qualifications sont des hypothèses de test, jamais des barèmes légaux à reprendre pour une paie réelle.

Les sources et limites réglementaires sont consignées dans [SOURCES_FISCALES_907.md](SOURCES_FISCALES_907.md). Ce lot ne crée aucune nouvelle règle chiffrée marocaine et ne constitue pas une certification.
