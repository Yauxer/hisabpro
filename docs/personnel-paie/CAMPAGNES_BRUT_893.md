# Paie — campagnes et simulations du brut, livraison 893

La rubrique **03 · Traitement de la paie** devient accessible dans la sidebar. Elle organise les campagnes mensuelles normales et conserve des simulations du brut versionnées. Le périmètre actuel est le salaire mensuel sur mois complet confirmé, augmenté des gains approuvés. Les cotisations, l'IR, le net, le coût employeur et les bulletins ne sont pas encore calculés.

## Préparer la copie et les accès

Sur une copie isolée disposant du Personnel et des lots889/891, appliquer la migration additive `115_paie_campagnes_brut.sql` après114, avec le rôle migrateur. Déployer le code actuel sur toutes les instances. Aucune campagne, valeur fiscale ou donnée salariale n'est créée automatiquement. Les tests n'ont utilisé aucun PostgreSQL de l'utilisateur.

Les consultations demandent les habilitations identité et rémunération, le module actif et la protection Personnel. Une simulation demande aussi **Créer et proposer** et un profil autorisé à écrire le Personnel. Aucun droit d'approbation de paie définitive n'est créé. Les motifs sont masqués aux lecteurs qui ne sont ni auteurs, ni approbateurs, ni auditeurs autorisés.

## Préparer les conditions du mois

Pour chaque salarié, vérifier le contrat et la rémunération mensuelle approuvés, ainsi que la date d'entrée connue. Une date inconnue n'est pas déduite du contrat. Les conditions doivent couvrir le mois complet ; aucun prorata n'est supposé en présence d'une entrée, sortie ou modification dans le mois.

Préparer les variables du mois dans **02 · Éléments de paie > Variables mensuelles**. Une variable en brouillon ou soumise bloque le total concerné : elle n'est pas ignorée. Les variables rejetées ou annulées n'entrent pas dans le calcul. Les gains approuvés sont ajoutés à la base ; les retenues ou remboursements dont l'impact n'est pas encore qualifié produisent une anomalie.

## Simuler

Ouvrir **03 · Traitement de la paie > Nouvelle simulation du brut**. Choisir le mois, rechercher et sélectionner les salariés, saisir un motif, puis confirmer que la sélection concerne des mois complets et que les variables ont été préparées. La sélection est limitée à50 salariés ; les listes de recherche sont paginées par25, sans perdre la sélection lors du passage d'une page à l'autre.

Cliquer **Simuler et conserver**. Le résultat affiche la base, les gains et le brut de la sélection, les références des contrats/rémunérations/variables et les anomalies individuelles. Le brut d'une ligne incomplète et les totaux globaux concernés restent **À compléter**, jamais un faux zéro. Les autres lignes peuvent conserver leurs montants connus. Les rubriques fiscales/sociales restent **Non calculées**, y compris lorsque le brut est complet.

Une campagne normale est unique par société et mois. Une nouvelle simulation conserve une nouvelle version dans cette campagne. Une reprise de la même requête après incident réutilise le snapshot précédent ; elle ne génère pas deux versions. Après changement volontaire des données, lancer une nouvelle simulation pour obtenir une nouvelle version.

## Consulter l'historique

Dans la liste, ouvrir **Consulter la simulation ID** ou **Historique de la campagne ID**, puis **Ouvrir la version N**. Les snapshots précédents restent identiques après approbation de variables ou modification de règles futures. Chaque simulation conserve une empreinte SHA-256, son auteur et ses sources. Cette empreinte permet un contrôle d'intégrité technique ; elle ne certifie ni la paie ni les règles juridiques.

Les références de pièces des variables restent consultables par leur propre circuit, sous les habilitations appropriées. Le snapshot du brut ne recopie pas les coordonnées bancaires, numéros sociaux ou motifs privés des variables.

## Recette chiffrée fictive

Continuer les cahiers887,889 et891. Pour **P001 — Salma FICTIVE**, base mensuelle de novembre2026 **9000.10MAD**, renseigner et faire approuver la date d'entrée fictive **2025-12-15** si elle manque : fiche salariée > **Proposer une modification** > nature **Identité**, rubrique des coordonnées facultatives > **Date d'entrée connue**. Conserver le nom, saisir le motif `Entrée fictive P001 pour recette893`, enregistrer, soumettre puis faire approuver selon le circuit RH. Il s'agit d'une donnée de recette déclarée, pas d'une date déduite du contrat.

Avec les deux gains approuvés du cahier891 :

| Élément fictif | Montant MAD |
|---|---:|
| Base mensuelle P001 | 9000,10 |
| PRIME_FICTIVE889 | 800,01 |
| QUANT_FICTIVE891 :3 ×0,335, arrondi à la ligne | 1,01 |
| Gains | 801,02 |
| Brut illustratif | **9801,12** |

Mois de simulation : `2026-11`, sélection : P001 seulement, motif : `Simulation fictive novembre893`. Confirmer le mois complet, puis simuler. Le brut doit être9801,12MAD. Cotisations, IR et net restent non calculés ; aucun bulletin ni OD n'est créé.

Pour vérifier l'incomplétude sans modifier une donnée approuvée, utiliser P002 sur une copie séparée du scénario principal : préparer une variable sans la soumettre, simuler, constater l'anomalie et l'absence de total ; faire approuver cette variable puis simuler de nouveau. Ouvrir ensuite l'ancienne version : elle conserve son état incomplet. Ne pas changer le statut d'une variable déjà approuvée pour fabriquer ce test.

Le [complément PDF](RECETTE_CAMPAGNES_PAIE_893.pdf), le [classeur](SUIVI_CAMPAGNES_PAIE_893.xlsx) et le [jeu](JEU_CAMPAGNES_PAIE_893.json) donnent les autres contrôles et résultats attendus.

## Ce qui reste à développer

Ce lot ne délivre pas une paie définitive : moteurs de cotisations par branche, IR, exonérations conditionnelles, prorata, cas complexes, verrouillage et approbation de campagne, bulletin/livre PDF avec identité et logo de la société, comptabilisation, paiements et déclarations restent à poursuivre dans l'ordre du master. Les simulations brutes restent explicitement `NON_VALIDE_JURIDIQUEMENT` et ne peuvent pas être transformées en approbation définitive par un simple champ d'API.

Les campagnes complémentaires/régularisations ne sont pas proposées comme livrées. Au-delà de500 variables approuvées pour un salarié/mois, un contrôle explicite bloque le total plutôt que publier une somme tronquée. Les sources d'une variable approuvée qui ne correspondent plus aux conditions actuelles sont signalées ; son snapshot n'est pas réécrit.

Recette utilisateur et production non validées. Aucun mouvement comptable réel ni accès à la base utilisateur n'a été effectué.
