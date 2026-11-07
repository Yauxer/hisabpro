# Vérifier les refus ETIC, les pièces manquantes et l'archive

Fiches du [cahier](CAHIER_RECETTE_HISABPRO.pdf) :**HP-NEG-034/035/036/041**. Utiliser exclusivement une copie fictive ouverte, distincte du dossier annuel clôturé. Les résultats humains restent à renseigner dans le [classeur](CAHIER_RECETTE_HISABPRO.xlsx).

## Montants B6/B7

Dans ETIC, B6 ou B7, une valeur négative, non numérique ou non finie doit être refusée **même sans cocher la confirmation**. Les tests emploient−1,NaN,Infinity,−Infinity etabc. Le refus ne doit modifier ni le complément précédemment conservé ni une écriture.

Un champ manquant reste conservable dans un brouillon. **Sans source certaine**, il reste À compléter ;**avec une facture et une échéance certaines**, le programme peut proposer la valeur automatiquement. Vider une saisie ne supprime pas cette source certaine. Un zéro explicitement saisi reste prioritaire sur la proposition automatique ;il ne doit pas être remplacé par une autre valeur.

Un brouillon manuel ne qualifie pas à lui seul les dates ou les analyses fiscales. Conserver les justificatifs et vérifier les ventilations avant confirmation.

## Total480, ventilation479

Préparer une facture fournisseur400HT+80TVA=480TTC, datée01/12/2025, échéance31/12/2025, validée et comptabilisée dans la copie. B7, compte4411 :saisir échues479,+1an0,−1an0. Le brouillon est conservable avec une incohérence visible ;la confirmation doit être refusée422 et la finalisation de la liasse409. Le total comptable reste480.

## Référence absente et reliquat non qualifié

Le laboratoire prépare deux factures client480TTC chacune, puis une opération OD3421de480sans référence de pièce. Solde1440 ;factures documentées960 ;reliquat480non reclassé automatiquement. Le FEC signale la référence absente et l'ETIC reste à compléter. Consulter ces contrôles ne doit pas réparer l'opération définitive ni inventer une échéance.

**HP-NEG-036 reste partiel** :les nouveaux enregistrements reçoivent une date de pièce par défaut, selon le comportement existant. Le test ne désactive pas les triggers pour fabriquer une ancienne dateNULL. Il prouve la conservation de la référence absente, du reliquat et de la date présente ;la validation PostgreSQL d'un véritable ancien enregistrement sans date documentaire reste distincte. Aucune donnée historique réelle n'est modifiée.

## Archive figée après N+1

Le test d'archive utilise un dossier fictif complet capital-seul2025, distinct du scénario annuel encore à20/23ETIC. Il finalise l'archive interne, conserve sa version et son empreinte, refuse les modifications ETIC et fiscales2025, puis crée et valide un apport fictif10MAD en2026. L'archive2025 et son empreinte doivent rester identiques. Les tentatives SQL de modification/suppression de cette seule archive de laboratoire sont refusées par les protections natives.

Ce test ne finalise pas le dossier annuel du cahier, ne dépose aucun fichier DGI et ne constitue pas une validation réglementaire.

[Résultats](RESULTATS_MVP_949.md) · [Correspondances](../../Test/QUALIFICATION_FICHES_949.json) · [Suivi automatique](SUIVI_AUTOMATISATION_CAHIER_949.xlsx).
