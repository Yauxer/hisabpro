# Source officielle431 — loi de finances2026 obtenue

Consultation du14octobre2026. Copie primaire du ministère de la Justice, Adala :
[PDF officiel](https://adala.justice.gov.ma/api/uploads/2025/12/18/loi%20de%20finances%202026-1766048666612.pdf).
[Copie locale identique](../docs/audit/sources/LF2026_Adala_BO7465bis.pdf).

Identification :loi50-25, dahir1-25-67 du10décembre2025, BO7465bis du16décembre2025,103pages.1 862 996octets ;SHA256 :
`048de4ad1bde3bef0cb9232c544d068c71c6c8c17e1563f094fae75425ff2b37`.

## Lecture ciblée

- PagePDF28,BO3837 :modifications151/157,avec ajout relatif aux locations etrenvoi àun modèle administratif. Les paragraphes antérieurs abrégés ne sont pas reconstitués.
- PagePDF32,BO3841 :transition247-XXXXVI par seuils de CAHT du dernier exercice clos :500millions au1juillet2026,350millions au1janvier2027,200millions au1janvier2028. Le paragrapheIV distingue d’autres dates d’effet ;ne pas généraliser une date unique.
- Même page,273 :durée CSS étendue jusqu’à2028. Le code existant la prévoit déjà ;aucune réapplication.

Ces amendements ne constituent ni le CGI consolidé complet,ni un modèle de déclaration,ni un schéma EDI.09F/09G restent absentes ;la qualification intégrale n’est pas acquise. Les échecs d’accès421restent historiques ;cette nouvelle copie apporte une preuve supplémentaire précise.

## Contrôles exécutés et portée technique

TéléchargementHTTPS réel200,signaturePDF,103pages lisibles sans mot de passe,identité du texte etprésence des articles contrôlées parPyMuPDF ;rendus des pages1/28/32 générés etpages28/32inspectées visuellement. Copie locale comparée octet pour octet etSHA vérifié. Le serviceCSS existant aété lu,aucun fichier métier modifié.

L’analyse pour la prochaine implémentation doit distinguer la situation du payeur,celle du bénéficiaire,la nature de rémunération etla date réellement justifiée. Il s’agit d’un travail de conception restant àfaire ;aucune classification déduite d’un nom oucompte seul. Obtenir leCGI consolidé etle modèle applicable avant déclarations officielles. Les saisies etattestationsRAS existantes ne sont pas transformées automatiquement.

Aucun nouveau taux,paramètre,migration oucalcul installé. Aucun PostgreSQL réel ou données réelles utilisé. Les730sources de la suite430en cours restent inchangées. Recette utilisateur etproduction non validées,point6en attente.
