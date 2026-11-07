# Exports de liasse — bancs actualisés763

21 tests connexes réussis en91.62s, zéro échec/erreur/ignoré dans cette campagne finale. Ciblés11réussis en4.94s,1cas UI désélectionné puis exécuté dans la campagne complète ; recouvrements non additionnés. Compilation des4fichiers Python modifiés OK. Source produit/frontend,117protections et migrations inchangés.

Cause racine : quatre bancs extrayaient la fonction exporterExcel de la page React et remplaçaient XLSX.writeFile. Depuis l’ajout des logos, cette fonction passe par telechargerXlsxAvecLogo : la dépendance n’était pas fournie dans ces bancs. Ce ReferenceError ne démontre pas une panne produit.

Correction limitée aux tests : capteur commun Test/liasse_xlsx_capture.cjs, chargement du sérialiseur construireXlsxAvecLogo de production, interception de la seule destination DOM. Relecture des vrais octets XLSX générés, sans fabriquer de classeur attendu. Les assertions existantes sur T1–T25, codes inconnus, snapshots, montants négatifs, zéros et données inconnues, B6/B7 et immobilisations sont conservées. Le test de numérotation est étendu avec/sanslogo ; présence réelle du média, feuille logo et nom de téléchargement contrôlés.

Deux exécutions initiales échouées sont conservées :2réussis/1échec sur dépendance absente, puis2réussis/1échec lors de la première adaptation du banc (ArrayBuffer à convertir en Uint8Array pour CFB). La campagne finale rejoue les tests corrigés, les6cas du sérialiseur réel, les2téléchargements Edge bureau/mobile et le parcours API/UI du bilan détaillé ainsi que la navigation. Aucun oracle supprimé, délai augmenté ou test ignoré.

Les parcours Edge/API utilisent exclusivement les clusters PostgreSQL temporaires protégés par nonce des fixtures existantes. Le test générique de distinction des références02/002 conserve sa base SQLite mémoire explicitement isolée ; cela ne valide pas les contraintes PostgreSQL. Aucune base réelle utilisée. Aucun build frontend relancé car aucun code frontend modifié. Les résultats287+2 de761 sont historiques, pas une nouvelle campagne763.

[Blocages officiels et pièces exactes à obtenir](../docs/audit/DEPENDANCES_OFFICIELLES_20261023_763.md). Aucune nouvelle règle fiscale, codification officielle ou activation EDI dans ce lot.
