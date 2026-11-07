# Qualification697 — tableaux documentaires ETIC B8/B9

Les préparations de balances permettent désormais de saisir les sûretés et
engagements dans les colonnes du catalogue existant, avec déclaration de tableau,
justification et source par ligne. Les inconnus restent distincts des zéros ;
néant exige une déclaration justifiée sans lignes. Aucun total de natures
hétérogènes n'est fabriqué. Le statut documenté ne vaut pas complétude fiscale.

Chaque conservation crée une version071 immuable avec auteur/date/source et
catalogue figés. Les autres compléments sont conservés ; les pièces ne sont
pas copiées entre versions. Une note non applicable contredisant des lignes
produit une alerte explicite, sans effacement. PDF/Excel/ZIP portent la même
version, les sources, les inconnus et le logo actuel hors empreinte historique.
Les chaînes ne deviennent pas des formules Excel ; montants exacts et manifeste
SHA-256 sont contrôlés. Aucune nouvelle migration ou règle fiscale.

## Tests réellement exécutés

- Cible :26 réussites en 212,74s, API PostgreSQL natif nonce,8 parcours Edge et restauration froide.
- Finale connexe :163 réussites en 625.91s, zéro échec/erreur/ignoré,30 avertissements existants.
- Campagnes recouvrantes :ne pas additionner en tests uniques.
- Build :5,86s, code 0. 10Python compilés et1 077 empreintes SHA app/Test figés.
- Témoin indépendant :écriture validée, versions, notes, financement, pièces,
  rendus, cellules, logos et manifestes inchangés pendant toute la campagne.
- Restauration :83 tables/cinq fichiers, schéma/données/ACL/séquences et exports
  identiques, sources préservées et cibles jetables nettoyées.
-108 fichiers SQL/bootstrap et moteurs liasse/ETIC/import inchangés ; ZIP695 préservés.
- Word/PDF de 6 pages/Excel de 5 feuilles, données exactes et six cas humains Non testé
  vérifiés ; capture mobile390 inspectée, Office non ouvert.

## Historique sans requalification

APIinitiale :1 échec en 40,12 s, mauvaises lignes dans la normalisation ; cause corrigée.
API suivante :16 réussites/1 échec en 62,68 s, le banc attendait du texte Excel alors que les
15 chiffres étaient exactement représentables en numérique ; assertion Decimal corrigée.
Edge initial :4 réussites/1 échec en 89,54 s, ancien libellé de bouton recherché par le banc ; corrigé.
Précontrôle d'empreintes :import models absent avant accès DB ; remplacé par
hachage direct sans import avant vérification des sources figées.

## Limites et reprise

Aucune base réelle ou donnée comptable réelle modifiée. Recette utilisateur à
effectuer sur installation autorisée ; production nonvalidée. LIA-09D partiel :
autres tableaux structurés et compléments fiscaux nécessaires. RAS/EDI selon
spécifications officielles obtenues et vérifiées. RH/paie et point6 différés.
Suite :annexes documentaires A2/A3/B10/C1/C2/C4, puis contrôles croisés.
