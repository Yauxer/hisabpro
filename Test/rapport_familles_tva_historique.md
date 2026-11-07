# Familles d’articles — TVA historique inconnue, lot324

## Problème reproduit

Le modèle conserve des familles dont `tva_defaut` est absent ou non fini.
La sortie exigeait pourtant un nombre et l’article imbriquait cette sortie.
Sur PostgreSQL nonce, une famille NULL provoquait quatre HTTP500 : liste des
familles, liste des articles, modification de description et création d’un
article avec TVA explicitement connue. NaN et les deux infinis échouaient à
la sérialisation JSON. Les deux mutations avaient réellement commité avant
leur réponse500. Les valeurs historiques−1/101 étaient exposées sans diagnostic.

La baseline finale isole chaque famille dans une société fictive : six échecs,
20,08s, code1. Une première baseline en société partagée avait six échecs en
18,35s ; les lectures contaminées par NULL ne remplacent pas la preuve isolée.
Logs/XML : `.codex-tests/familles_324_avant_isole_par_cas.xml` et
`familles_324_api_echec_*.log`.

Après la projection backend, quatre Edge ont reproduit les erreurs UI en
68,90s : choisir une famille inconnue conservait20 dans la fiche article ;
la création rapide de facture utilisait aussi un repli20 sans choix explicite.
Cette baseline distingue donc le défaut de lecture et le défaut de formulaire.

## Correction minimale

`FamilleOut` expose une TVA inconnue comme NULL avec `nombres_diagnostics`.
La projection ne répare pas le modèle et conserve les valeurs historiques
finies0/10/20. Une valeur omise en sortie reste inconnue ; le défaut20 d’une
nouvelle saisie est distinct et demeure inchangé. `FamilleCreate` refuse les
booléens et nombres non finis/hors0..100. Le contrôle existant des taux proposés
reste dans le routeur : aucune nouvelle règle fiscale n’est créée.

La fiche article vide la TVA lorsqu’une famille inconnue est choisie et exige
un choix explicite avant enregistrement. La création rapide propose un
sélecteur seulement dans ce cas. Aucun POST/PATCH ne part avec un choix vide.
Familles connues,0 et20, et parcours sans famille sont conservés ; une famille
inconnue n’est jamais modifiée silencieusement. TVA0 ne qualifie pas à elle
seule une exonération : la qualification du document commercial reste requise.

## Tests réellement exécutés

Backend final : **347 réussis,25avertissements,79,79s,code0**, dont39nouveaux
et308connexes, sur quatre modules. Ne pas additionner les37 tests de la passe
intermédiaire en23,33s. Compilation `schemas.py` et du nouveau test : code0.
Preuve : `.codex-tests/familles_324_connexes_fin.xml`.

Une commande intermédiaire avait cité un fichier absent : zéro test,code1,
0,01s ; elle a été corrigée après recherche des noms réels.

UI : baseline quatre échecs68,90s. Premier retest : deux réussites/deux échecs
68,45s, causés par les noms accessibles pollués par les glyphes décoratifs
chargés localement. Cause distincte documentée/corrigée par326, sans élargir les
sélecteurs ni les délais. Le diagnostic supplémentaire1365 donne un échec
39,80s, sans erreur JS/API500. Après326 : **4réussis,29,99s,25avertissements,
code0**, deux parcours aux largeurs1365/390. Les choix0/20, annulations,
édition, famille connue0 après un choix20 et les refus sans requête sont
vérifiés. Snapshots SQL des familles et comptes d’écritures/stock inchangés.
Preuve : `.codex-tests/fam324_ui_apres326.{log,xml,exit}`.

Connexes UI exécutés par le principal après stabilisation : **6réussis,
85,04s,25avertissements,code0**, articles/frais, stocks inconnus et autres
nombres historiques. XML : `.codex-tests/familles_324_ui_connexes.xml`.
Les347backend et4nouveaux Edge ont été exécutés par les agents dédiés ; le
principal a relu leurs preuves XML/log avant livraison. Ces suites sont
distinctes et ne doivent pas être additionnées aux anciennes globales.

Build final après stabilisation324/326 : **139modules,4,56s,code0**. Les avertissements
existants XLSX et taille de bundle restent visibles.

## Limites

Les tests API utilisent exclusivement des clusters PostgreSQL éphémères
vérifiés par URL/répertoire/nonce, avec dotenv désactivé. Les tests Edge sont
connectés au même banc isolé. Aucune base utilisateur, migration ou écriture
réelle modifiée. Une TVA historique10 conservée ne prouve pas son applicabilité
à une nouvelle opération. Recette utilisateur sur dossier fictif à effectuer.
