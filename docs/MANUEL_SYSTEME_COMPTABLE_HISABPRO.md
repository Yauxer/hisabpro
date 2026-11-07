# Manuel du système comptable HisabPro

Version documentaire du 6 octobre 2026. Cette documentation décrit le code du
dépôt ; elle ne constitue ni une certification ni une homologation. La présence
d'une migration dans le dépôt ne prouve pas son application dans une base donnée.

## Références et périmètre

Le projet vise une architecture cohérente avec le CGNC, la **Loi n° 9-88** et
l'**Avis n°24**. Les documents institutionnels de référence sont accessibles sur
le [portail du ministère de l'Économie et des Finances](https://www.finances.gov.ma/fr/Nos-metiers/Pages/cnc-normes.aspx)
et dans le [texte de la loi publié par l'AMDIE](https://amdie.gov.ma/wp-content/uploads/2024/01/Obligations-comptables-commercants.pdf).
Ce manuel n'ajoute aucune règle fiscale ; une évolution normative doit être
vérifiée dans les textes officiels avant son implémentation.

## Paramétrage et périmètres comptables

**Plan comptable par société** : les comptes utilisables sont conservés dans
`comptes_societe`, à partir du référentiel CGNC et des subdivisions propres à la
société. Leur désactivation préserve l'historique. Les comptes et auxiliaires des
factures validées sont conservés dans des snapshots ; un changement de fiche
tiers ne doit pas réécrire les pièces historiques.

**Exercices décalés** : les exercices possèdent une date de début et une date de
fin explicites. Le code contrôle la durée maximale de douze mois calendaires et
les chevauchements ; l'année de référence correspond à celle de la date de fin.
Une clôture définitive ne peut pas être déclenchée avant la date de fin de
l'exercice. Ces contrôles sont des comportements du produit, à tester sur la
base utilisée.

**Périodes comptables (patch 059)** : une période fermée manuellement peut être
rouverte par l'administrateur tant que l'exercice n'a pas fait l'objet d'une
clôture définitive. La réouverture individuelle ou globale est contrôlée et
conserve un audit append-only. Les périodes d'un exercice définitivement clôturé
ne sont pas rouvertes par ces commandes.

## Écritures, validation et corrections

Les états excluent les brouillons et utilisent les écritures validées. La
validation attribue le numéro définitif par société, exercice et journal ; son
exécution concurrente et les contraintes d'irréversibilité nécessitent une recette
PostgreSQL réelle avec les migrations appliquées.

La correction d'une écriture définitive passe par une contrepassation tracée.
Les compléments de justificatifs et d'auxiliaires historiques sont conservés
séparément des lignes définitives. Les opérations de réparation sont réservées
aux rôles autorisés et ne doivent pas être déclenchées automatiquement pendant
une recette en lecture seule.

La clôture utilise un journal dédié. Les états de consultation excluent les
écritures techniques de soldage pour préserver la lecture du CPC après clôture.
Les à-nouveaux constituent l'ouverture de l'exercice suivant et ne doivent pas
être générés une seconde fois après leur génération. Vérifier les garde-fous
dans la base réelle avant toute opération de clôture.

## FEC et rapprochements documentaires

Le FEC conserve les références en texte : `02` et `002` sont deux identifiants
distincts. Les rapprochements automatiques demandent une date et un TTC exacts,
puis une référence non ambiguë. Une référence incompatible ne doit pas être
remplacée par une ressemblance de libellé. L'absence de tiers reste une anomalie
FEC, même lorsqu'une facture peut fournir une échéance documentée pour ETIC.

Une facture associée à plusieurs écritures principales ne peut pas servir à une
réparation automatique. Une écriture déjà documentée participe également au
contrôle d'unicité. Les comptes exacts et le tiers réellement enregistré doivent
être préservés ; aucune subdivision ne doit être reclassée pour effacer un écart.

## ETIC et liasse fiscale

B6/B7 utilisent les dates enregistrées et les tranches d'échéancier recoupant le
TTC. Une date absente reste à compléter. Le préremplissage certain exige une
principale unique, le compte exact et des réductions de solde justifiées à la
clôture. Les annulations postérieures ne modifient pas l'état passé ; un rejet
historique non daté reste explicitement à vérifier.

Les saisies manuelles conservées restent prioritaires. Les échéances doivent
totaliser le solde de la ligne pour confirmer la section ; les données
extra-comptables ne sont pas déduites d'une simple probabilité. Un montant
invalide ne peut pas être remplacé silencieusement par un préremplissage.

La liasse consolide les états et leurs contrôles. Sa finalisation produit un
snapshot avec empreinte SHA-256 ; les lectures de la liasse finalisée utilisent
l'archive. Le PDF et Excel reprennent les ventilations publiées et leurs
diagnostics. Un PDF live reste provisoire. Aucun XML/EDI SIMPL-IS ne doit être
annoncé opérationnel sans spécification applicable vérifiée et implémentation.

## Exploitation, sauvegarde et limites

L'exploitant doit organiser les sauvegardes et tester leur restauration sur un
environnement séparé ; le dépôt ne démontre pas l'existence d'un dispositif de
sauvegarde en production. Le ZIP différentiel livre uniquement les fichiers
modifiés et ne constitue pas une sauvegarde des données.

Restent hors de toute prétention de certification automatique : l'organisation
de l'entreprise, la fiabilité des pièces sources, les sauvegardes, l'archivage durable,
les formalités de dépôt fiscal et l'application effective des migrations.
Les tests unitaires ne remplacent ni le PostgreSQL de recette ni la validation
visuelle et fonctionnelle au navigateur.

## Recette locale sans données réelles

Installer les dépendances applicatives du backend et celles de
`Test/requirements.txt`, puis exécuter :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py
npm.cmd run build
```

Le runner force une base mémoire pour les tests unitaires, propage UTF-8 aux
sous-processus et exclut le test PostgreSQL créant/supprimant un schéma. Cette
base mémoire n'est pas une validation des contraintes PostgreSQL. Les tests de
syntaxe JSX utilisent les parseurs installés avec Vite, sans chemin Linux fixé.
