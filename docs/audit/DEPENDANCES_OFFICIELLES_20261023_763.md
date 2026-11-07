# Documents officiels manquants — état du23octobre2026

La reprise après761 a vérifié les seules dépendances du périmètre de clôture. **Le catalogue exhaustif et le schéma applicables n’ont toujours pas été obtenus.** Le refus d’accès depuis cet environnement ne démontre pas une absence générale de publication de la DGI. Ne pas relancer ce même audit sans nouvel accès ou nouveau document.

## Accès réellement exécutés

Requêtes HTTP Python en lecture seule, sans authentification, avec timeout connexion10s et lecture15s. Aucun document fiscal réel transmis. Les deux réponses403 sont des pages HTML, pas des catalogues. Aucun des deux PDF n’a été téléchargé ; pas d’empreinte PDF prétendue.

| Adresse primaire | Résultat HTTP de cette session |
|---|---|
| https://www.tax.gov.ma | 403 ; text/html; charset=UTF-8 ; 12763 octets HTML, pas document fiscal |
| https://www.tax.gov.ma/wps/portal/DGI/Tele-services/Simpl-IS | 403 ; text/html; charset=UTF-8 ; 12763 octets HTML, pas document fiscal |
| https://www.finances.gov.ma/Publication/dgi/2010/9370_cahierdescharges.pdf | ConnectTimeout ; connexion limitée à10s |
| https://www.finances.gov.ma/Publication/dgi/2012/4036_adc_030f_08e.pdf | ConnectTimeout ; connexion limitée à10s |

L’outil web a également renvoyé405 sur le portail et des timeouts sur les deux PDF. Le résultat indexé du [cahier MEF V1.0 historique](https://www.finances.gov.ma/Publication/dgi/2010/9370_cahierdescharges.pdf) reprend l’association entre modèle, période de validité et schéma ; cette association avait déjà été documentée dans SOURCES_DGI_MILLESIME_20261008.md. Aucun schéma actuel n’en est déduit. Le [formulaire ADC030F-08E historique](https://www.finances.gov.ma/Publication/dgi/2012/4036_adc_030f_08e.pdf), visible dans l’index officiel, ne prouve pas le modèle applicable2026. Des miroirs commerciaux et liens de stockage tiers sont apparus dans les recherches ; aucun n’est retenu comme spécification primaire validée.

## Paquet à récupérer depuis un accès officiel fonctionnel

| Blocage | Documents précis | Qualification à conserver |
|---|---|---|
|09B catalogue liasse | Catalogue exhaustif des tableaux et cellules, annexe de codification et identification du modèle comptable normal retenu | URL officielle, version, date de publication/effet et période de validité ; distinguer code DGI et repère interne T1…T25. Ne pas déduire les correspondances de l’ordre visuel des tableaux. |
|09C EDI SIMPL-IS | Cahier courant, toutes annexes de codification, XSD principal avec dépendances include/import, exemples XML officiels correspondants et règles conditionnelles | Modèle/période cohérents entre tous les fichiers ; conserver SHA256 des binaires obtenus et date d’accès. Confirmation officielle de validité si période non précisée. |
|09F tiers | Modèle administratif applicable à la déclaration article151 et ses états annexes particuliers, notices, éventuel cahier électronique associé | Identification exacte du formulaire et millésime. Le CGI2026 déjà obtenu est une source de droit, pas le modèle de fichier administratif. |
|09G TP | Modèle et notice de déclaration applicables à la situation de la société, texte consolidé utile à l’assiette et aux régimes particuliers | La simulation brute761 ne remplace pas la qualification de valeur locative/classe, exonération ou montant dû. Ne pas appliquer un minimum universel ou transformer un avis en paiement. |
|RAS TVA | Cahiers officiels du versement et du relevé détaillé, annexes/codifications et éventuelles spécifications de validation | Vérifier version et date d’effet ; liste des pièces déjà précisée dans SOURCES_RAS_MODELES_20261021.md. |

Récupérer les documents depuis les rubriques officielles des téléservices concernés. Il suffit de fournir les documents et leur provenance ; aucun mot de passe ou dossier fiscal réel n’est nécessaire au développement. Aucune prise de contact ni aucun envoi à l’administration n’a été effectué.

## Reprise bornée

1. Lire et qualifier le paquet reçu, sans supposer qu’un ancien numéro de version est encore courant.
2. Comparer les tableaux/champs officiels au référentiel et aux préparations existants ; dresser uniquement les écarts réels.
3. Implémenter les correspondances manquantes avec tests d’oracles, fichiers valides/invalides et schéma complet lorsque applicable.
4. Vérifier les exports et l’intégrité des versions existantes avant livraison. Un XSD valide ne prouve pas un dépôt accepté.

En attendant :09B reste absent,09F/09G partiels etEDI bloqué. Les54cas humains749–761 sont Non testé, aucune recette utilisateur validée. Les justificatifs FEC/ETIC manquants restent visibles. RH/paie etpoint6 différés. Cette liste ferme les dépendances de la reprise ; elle n’ouvre pas une nouvelle série de développements secondaires.
